"""
트렌드 관련 Pydantic 스키마
API 요청/응답 직렬화 및 유효성 검사
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class TrendBase(BaseModel):
    """트렌드 공통 필드"""
    keyword: str = Field(..., description="트렌드 키워드", example="AI 반도체")
    source: str = Field(..., description="수집 출처 (google_trends/news_rss/youtube)")
    score: float = Field(default=0.0, ge=0, le=100, description="트렌드 점수 (0~100)")
    category: Optional[str] = Field(None, description="카테고리 (기술/경제/엔터 등)")


class TrendCreate(TrendBase):
    """트렌드 생성 요청 스키마"""
    pass


class TrendResponse(TrendBase):
    """트렌드 단건 응답 스키마"""
    id: int
    related_stocks: Optional[str] = Field(None, description="관련 테마주 (쉼표 구분)")
    ai_summary: Optional[str] = Field(None, description="AI 분석 요약")
    opportunity: Optional[str] = Field(None, description="트렌드 기회")
    risk: Optional[str] = Field(None, description="트렌드 위험")
    is_analyzed: bool = Field(False, description="AI 분석 완료 여부")
    created_at: datetime

    model_config = {"from_attributes": True}


class TrendListResponse(BaseModel):
    """트렌드 목록 응답 스키마"""
    total: int = Field(..., description="전체 트렌드 수")
    items: List[TrendResponse]


class TrendReportResponse(BaseModel):
    """주간 트렌드 리포트 응답 스키마"""
    id: int
    title: str
    summary: str
    opportunities: Optional[str] = None
    risks: Optional[str] = None
    top_keywords: Optional[str] = None
    recommended_stocks: Optional[str] = None
    content_ideas: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    """사용자 등록 요청 스키마"""
    email: str = Field(..., description="이메일 주소")
    username: str = Field(..., min_length=2, max_length=50, description="사용자 이름")
    password: str = Field(..., min_length=8, description="비밀번호 (8자 이상)")


class UserResponse(BaseModel):
    """사용자 응답 스키마"""
    id: int
    email: str
    username: str
    is_active: bool
    is_premium: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """JWT 토큰 응답 스키마"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """토큰 페이로드 스키마"""
    email: Optional[str] = None
