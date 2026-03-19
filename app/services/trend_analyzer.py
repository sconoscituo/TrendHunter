"""
트렌드 분석 서비스
Gemini AI를 이용해 트렌드 키워드의 기회/위험/관련 테마주를 분석
"""
import json
import logging

import google.generativeai as genai
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.trend import Trend
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _build_analysis_prompt(keyword: str, category: str) -> str:
    """Gemini에게 보낼 트렌드 분석 프롬프트 생성"""
    return f"""
당신은 한국 시장 트렌드 전문 분석가입니다.
다음 트렌드 키워드를 분석하고 JSON 형식으로 응답해주세요.

키워드: {keyword}
카테고리: {category}

다음 JSON 형식으로 정확히 응답하세요 (마크다운 코드블록 없이):
{{
  "summary": "트렌드 요약 (2~3문장)",
  "opportunity": "이 트렌드가 만들어내는 사업/투자 기회 (구체적으로)",
  "risk": "주의해야 할 위험 요소",
  "related_stocks": "관련 한국 상장 테마주 3~5개 (회사명, 쉼표 구분)",
  "content_ideas": "유튜브/SNS 콘텐츠 아이디어 2가지"
}}
"""


async def analyze_trend(trend_id: int):
    """
    단일 트렌드 AI 분석 실행
    Gemini API 호출 후 결과를 DB에 업데이트
    """
    if not settings.gemini_api_key:
        logger.warning("GEMINI_API_KEY가 설정되지 않아 분석을 건너뜁니다.")
        return

    async with AsyncSessionLocal() as session:
        # 트렌드 조회
        result = await session.execute(select(Trend).where(Trend.id == trend_id))
        trend = result.scalar_one_or_none()
        if not trend or trend.is_analyzed:
            return

        try:
            # Gemini API 설정
            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")

            prompt = _build_analysis_prompt(
                keyword=trend.keyword,
                category=trend.category or "기타",
            )

            # Gemini 호출 (동기 → 비동기 처리)
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: model.generate_content(prompt),
            )

            # JSON 파싱
            raw_text = response.text.strip()
            # 혹시 마크다운 코드블록이 포함된 경우 제거
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]

            analysis = json.loads(raw_text)

            # 분석 결과 DB 업데이트
            trend.ai_summary = analysis.get("summary", "")
            trend.opportunity = analysis.get("opportunity", "")
            trend.risk = analysis.get("risk", "")
            trend.related_stocks = analysis.get("related_stocks", "")
            trend.is_analyzed = True

            await session.commit()
            logger.info(f"트렌드 분석 완료: {trend.keyword} (id={trend_id})")

        except json.JSONDecodeError as e:
            logger.error(f"Gemini 응답 파싱 실패 (id={trend_id}): {e}")
        except Exception as e:
            await session.rollback()
            logger.error(f"트렌드 분석 오류 (id={trend_id}): {e}")


async def analyze_unanalyzed_trends(limit: int = 10):
    """
    미분석 트렌드를 일괄 분석
    스케줄러 또는 수동 호출 시 사용
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Trend)
            .where(Trend.is_analyzed == False)  # noqa: E712
            .limit(limit)
        )
        trends = result.scalars().all()

    logger.info(f"미분석 트렌드 {len(trends)}개 분석 시작")
    for trend in trends:
        await analyze_trend(trend.id)
