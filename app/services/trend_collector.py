"""
트렌드 수집 서비스
구글 트렌드(pytrends)와 뉴스 RSS 피드에서 키워드를 수집하여 DB에 저장
"""
import asyncio
import logging
from typing import List, Dict

import feedparser
import httpx
from pytrends.request import TrendReq

from app.database import AsyncSessionLocal
from app.models.trend import Trend
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# 수집할 뉴스 RSS 피드 목록 (한국 주요 매체)
NEWS_RSS_FEEDS = [
    "https://rss.etnews.com/Section901.xml",          # 전자신문 IT
    "https://feeds.feedburner.com/zdnetkorea",         # ZDNet Korea
    "https://rss.hankyung.com/economy.xml",            # 한국경제
    "https://www.mk.co.kr/rss/30000001/",              # 매일경제
]

# 트렌드 카테고리 키워드 매핑
CATEGORY_KEYWORDS = {
    "기술": ["AI", "반도체", "챗GPT", "로봇", "메타버스", "클라우드", "블록체인"],
    "경제": ["금리", "환율", "주식", "코스피", "달러", "인플레이션", "부동산"],
    "엔터": ["아이돌", "드라마", "영화", "웹툰", "게임", "유튜브"],
    "정치": ["대통령", "국회", "선거", "정책", "법안"],
}


def _classify_category(keyword: str) -> str:
    """키워드를 카테고리로 분류 (단순 키워드 매핑)"""
    keyword_lower = keyword.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in keyword_lower:
                return category
    return "기타"


async def _collect_google_trends() -> List[Dict]:
    """
    구글 트렌드에서 한국 실시간 급상승 키워드 수집
    pytrends는 동기 라이브러리이므로 스레드 풀에서 실행
    """
    def _fetch():
        try:
            pytrends = TrendReq(hl="ko", tz=540)  # 한국 시간대 (UTC+9)
            # 실시간 급상승 검색어 조회
            trending_df = pytrends.trending_searches(pn="south_korea")
            results = []
            for i, keyword in enumerate(trending_df[0].tolist()[:20]):
                results.append({
                    "keyword": str(keyword),
                    "source": "google_trends",
                    # 순위가 높을수록 높은 점수 (1위=100점, 20위=5점)
                    "score": max(100 - i * 5, 5),
                    "category": _classify_category(str(keyword)),
                })
            return results
        except Exception as e:
            logger.warning(f"구글 트렌드 수집 실패: {e}")
            return []

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _fetch)


async def _collect_news_rss() -> List[Dict]:
    """
    뉴스 RSS 피드에서 제목 키워드 수집
    feedparser로 RSS 파싱 후 제목에서 주요 키워드 추출
    """
    results = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        for feed_url in NEWS_RSS_FEEDS:
            try:
                resp = await client.get(feed_url)
                feed = feedparser.parse(resp.text)
                for entry in feed.entries[:10]:  # 피드당 최신 10개
                    title = entry.get("title", "").strip()
                    if title and len(title) > 2:
                        results.append({
                            "keyword": title[:100],  # 제목을 키워드로 사용 (100자 제한)
                            "source": "news_rss",
                            "score": 50.0,  # 뉴스 RSS는 기본 점수 50
                            "category": _classify_category(title),
                        })
            except Exception as e:
                logger.warning(f"RSS 수집 실패 ({feed_url}): {e}")

    return results


async def collect_trends():
    """
    메인 트렌드 수집 함수 (스케줄러에서 주기적으로 호출)
    구글 트렌드 + 뉴스 RSS 수집 후 DB 저장
    """
    logger.info("트렌드 수집 시작...")

    # 구글 트렌드 + 뉴스 RSS 병렬 수집
    google_results, news_results = await asyncio.gather(
        _collect_google_trends(),
        _collect_news_rss(),
    )

    all_trends = google_results + news_results
    logger.info(f"수집된 트렌드 수: {len(all_trends)}")

    if not all_trends:
        logger.warning("수집된 트렌드 없음")
        return

    # DB에 저장
    async with AsyncSessionLocal() as session:
        try:
            for trend_data in all_trends:
                trend = Trend(
                    keyword=trend_data["keyword"],
                    source=trend_data["source"],
                    score=trend_data["score"],
                    category=trend_data.get("category", "기타"),
                )
                session.add(trend)
            await session.commit()
            logger.info(f"트렌드 {len(all_trends)}개 저장 완료")
        except Exception as e:
            await session.rollback()
            logger.error(f"트렌드 저장 실패: {e}")
