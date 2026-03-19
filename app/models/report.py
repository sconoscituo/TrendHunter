"""
트렌드 리포트 ORM 모델
주간 AI 분석 리포트 저장
"""
from datetime import datetime
from sqlalchemy import String, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TrendReport(Base):
    """주간 트렌드 리포트 테이블"""
    __tablename__ = "trend_reports"

    # 기본 키
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 리포트 제목 (예: "2024년 3월 2주차 트렌드 리포트")
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    # Gemini가 생성한 전체 요약
    summary: Mapped[str] = mapped_column(Text, nullable=False)

    # 이번 주 주목할 기회 목록 (JSON 문자열)
    opportunities: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 주의해야 할 리스크 목록 (JSON 문자열)
    risks: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 이번 주 TOP 키워드 (쉼표 구분 문자열)
    top_keywords: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 추천 테마주 목록 (JSON 문자열)
    recommended_stocks: Mapped[str | None] = mapped_column(Text, nullable=True)

    # SNS 콘텐츠 방향 제안
    content_ideas: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 리포트 생성 시각
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<TrendReport id={self.id} title={self.title}>"
