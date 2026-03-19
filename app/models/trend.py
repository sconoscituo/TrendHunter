"""
트렌드 ORM 모델
구글 트렌드 및 뉴스에서 수집한 키워드 저장
"""
from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Trend(Base):
    """트렌드 키워드 테이블"""
    __tablename__ = "trends"

    # 기본 키
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 트렌드 키워드
    keyword: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # 수집 출처 (google_trends / news_rss / youtube)
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # 트렌드 점수 (0~100, 구글 트렌드 기준)
    score: Mapped[float] = mapped_column(Float, default=0.0)

    # 카테고리 (경제 / 기술 / 엔터 / 스포츠 / 정치 등)
    category: Mapped[str] = mapped_column(String(100), nullable=True)

    # Gemini가 추출한 관련 테마주 (쉼표 구분 문자열)
    related_stocks: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Gemini 분석 요약
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 트렌드 기회 설명
    opportunity: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 트렌드 위험 설명
    risk: Mapped[str | None] = mapped_column(Text, nullable=True)

    # AI 분석 완료 여부
    is_analyzed: Mapped[bool] = mapped_column(default=False)

    # 데이터 수집 시각
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<Trend id={self.id} keyword={self.keyword} source={self.source}>"
