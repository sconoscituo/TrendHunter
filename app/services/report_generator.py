"""
주간 트렌드 리포트 생성 서비스
최근 1주일 트렌드를 집계하고 Gemini AI로 종합 리포트 생성
"""
import json
import logging
from datetime import datetime, timedelta, timezone

import google.generativeai as genai
from sqlalchemy import select, desc

from app.database import AsyncSessionLocal
from app.models.trend import Trend
from app.models.report import TrendReport
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _build_report_prompt(trends_summary: str, week_label: str) -> str:
    """주간 리포트 생성용 Gemini 프롬프트"""
    return f"""
당신은 한국 시장 트렌드 전문 애널리스트입니다.
아래는 {week_label} 수집된 주요 트렌드 데이터입니다.

{trends_summary}

이 데이터를 바탕으로 종합 트렌드 리포트를 JSON 형식으로 작성해주세요:
{{
  "title": "리포트 제목 (예: {week_label} 트렌드 리포트)",
  "summary": "이번 주 트렌드 전체 요약 (3~5문장, 핵심 흐름 설명)",
  "opportunities": ["기회1: 설명", "기회2: 설명", "기회3: 설명"],
  "risks": ["위험1: 설명", "위험2: 설명"],
  "top_keywords": ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5"],
  "recommended_stocks": ["종목명1 (이유)", "종목명2 (이유)", "종목명3 (이유)"],
  "content_ideas": ["콘텐츠 아이디어1", "콘텐츠 아이디어2", "콘텐츠 아이디어3"]
}}
"""


async def generate_weekly_report():
    """
    주간 트렌드 리포트 자동 생성 (매주 월요일 오전 9시 실행)
    최근 7일간 트렌드를 집계하여 Gemini로 리포트 생성
    """
    if not settings.gemini_api_key:
        logger.warning("GEMINI_API_KEY 미설정 - 리포트 생성 건너뜀")
        return

    # 날짜 범위 설정 (최근 7일)
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    week_label = f"{now.year}년 {now.month}월 {now.isocalendar()[1]}주차"

    async with AsyncSessionLocal() as session:
        # 최근 7일 트렌드 조회 (점수 높은 순)
        result = await session.execute(
            select(Trend)
            .where(Trend.created_at >= week_ago)
            .order_by(desc(Trend.score))
            .limit(50)
        )
        trends = result.scalars().all()

    if not trends:
        logger.warning("리포트 생성할 트렌드 데이터 없음")
        return

    # 트렌드 요약 문자열 생성
    trend_lines = []
    for t in trends[:30]:  # 상위 30개만 사용
        line = f"- [{t.source}] {t.keyword} (점수: {t.score:.0f}, 카테고리: {t.category})"
        if t.related_stocks:
            line += f" | 관련주: {t.related_stocks}"
        trend_lines.append(line)

    trends_summary = "\n".join(trend_lines)

    try:
        # Gemini 호출
        import asyncio
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = _build_report_prompt(trends_summary, week_label)

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(prompt),
        )

        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]

        report_data = json.loads(raw_text)

        # 리포트 DB 저장
        async with AsyncSessionLocal() as session:
            report = TrendReport(
                title=report_data.get("title", f"{week_label} 트렌드 리포트"),
                summary=report_data.get("summary", ""),
                opportunities=json.dumps(report_data.get("opportunities", []), ensure_ascii=False),
                risks=json.dumps(report_data.get("risks", []), ensure_ascii=False),
                top_keywords=", ".join(report_data.get("top_keywords", [])),
                recommended_stocks=json.dumps(report_data.get("recommended_stocks", []), ensure_ascii=False),
                content_ideas=json.dumps(report_data.get("content_ideas", []), ensure_ascii=False),
            )
            session.add(report)
            await session.commit()
            logger.info(f"주간 리포트 생성 완료: {report.title}")

    except json.JSONDecodeError as e:
        logger.error(f"리포트 JSON 파싱 실패: {e}")
    except Exception as e:
        logger.error(f"리포트 생성 오류: {e}")
