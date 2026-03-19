"""
Gemini API를 활용한 트렌드 기반 콘텐츠 아이디어 자동 생성 서비스
"""
import logging
from typing import List, Optional
import google.generativeai as genai

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

genai.configure(api_key=settings.gemini_api_key)


def generate_content_ideas(
    keywords: List[str],
    platform: str = "유튜브",
    count: int = 5,
    tone: Optional[str] = None,
) -> str:
    """
    트렌드 키워드 목록을 기반으로 콘텐츠 아이디어를 생성합니다.

    Args:
        keywords: 트렌드 키워드 목록
        platform: 대상 플랫폼 (유튜브, 인스타그램, 블로그, 틱톡 등)
        count: 생성할 아이디어 수
        tone: 콘텐츠 톤 (정보형, 엔터테인먼트, 감성, 교육 등)
    """
    tone_text = f"톤은 '{tone}'으로" if tone else "적절한 톤으로"
    keywords_str = ", ".join(keywords)

    prompt = f"""
당신은 SNS 콘텐츠 전략가입니다.
아래 트렌드 키워드들을 활용하여 {platform} 플랫폼에 최적화된 콘텐츠 아이디어 {count}개를 생성해주세요.

## 트렌드 키워드
{keywords_str}

## 작성 조건
- 플랫폼: {platform}
- 아이디어 수: {count}개
- {tone_text} 작성
- 현재 트렌드를 적극 반영

## 각 아이디어 형식
### 아이디어 N: [제목]
- **콘텐츠 요약**: (2~3문장)
- **핵심 키워드**: #태그1 #태그2 #태그3
- **예상 반응**: (왜 이 콘텐츠가 바이럴될 수 있는지)
- **제작 팁**: (실제 제작 시 주의사항 1가지)

한국어로 작성하세요.
"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini idea generation failed: {e}")
        return f"[생성 실패] 콘텐츠 아이디어 생성 중 오류가 발생했습니다: {str(e)}"


def analyze_trend_opportunity(keyword: str, trend_score: int) -> str:
    """
    특정 키워드의 트렌드 점수를 기반으로 콘텐츠 기회를 분석합니다.
    """
    prompt = f"""
당신은 디지털 마케팅 전문가입니다.
키워드 '{keyword}'의 현재 트렌드 점수는 {trend_score}/100 입니다.

다음 항목을 분석해주세요:
1. **트렌드 평가**: 현재 트렌드 상태 및 지속 가능성
2. **타겟 오디언스**: 이 키워드에 관심 있는 주요 타겟층
3. **콘텐츠 기회**: 지금 바로 만들면 좋은 콘텐츠 유형 3가지
4. **경쟁 강도**: 예상 경쟁 수준 (낮음/중간/높음) 및 이유
5. **최적 타이밍**: 콘텐츠 발행 최적 시간대 및 요일

한국어로 간결하게 작성하세요.
"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Trend opportunity analysis failed for '{keyword}': {e}")
        return f"[분석 실패] 트렌드 기회 분석 중 오류가 발생했습니다: {str(e)}"
