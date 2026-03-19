"""
트렌드 조회 라우터
트렌드 목록 조회, 검색, 카테고리별 필터, 리포트 조회 엔드포인트
"""
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.database import get_db
from app.models.trend import Trend
from app.models.report import TrendReport
from app.models.user import User
from app.schemas.trend import TrendResponse, TrendListResponse, TrendReportResponse
from app.utils.auth import get_current_active_user
from app.services.trend_collector import collect_trends
from app.services.trend_analyzer import analyze_trend

router = APIRouter()


@router.get("/", response_model=TrendListResponse)
async def list_trends(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    source: Optional[str] = Query(None, description="출처 필터 (google_trends/news_rss)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    트렌드 목록 조회 (최신순, 페이지네이션)
    - 카테고리, 출처 필터 지원
    """
    query = select(Trend).order_by(desc(Trend.created_at))

    # 카테고리 필터 적용
    if category:
        query = query.where(Trend.category == category)

    # 출처 필터 적용
    if source:
        query = query.where(Trend.source == source)

    # 전체 개수 조회
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # 페이지네이션 적용
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()

    return TrendListResponse(total=total, items=list(items))


@router.get("/search", response_model=TrendListResponse)
async def search_trends(
    keyword: str = Query(..., min_length=1, description="검색 키워드"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    키워드로 트렌드 검색
    - 트렌드 키워드 컬럼에서 부분 일치 검색
    """
    query = (
        select(Trend)
        .where(Trend.keyword.ilike(f"%{keyword}%"))
        .order_by(desc(Trend.score))
        .limit(50)
    )
    result = await db.execute(query)
    items = result.scalars().all()

    return TrendListResponse(total=len(items), items=list(items))


@router.get("/top", response_model=List[TrendResponse])
async def get_top_trends(
    limit: int = Query(10, ge=1, le=50, description="반환할 트렌드 수"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    점수 기준 TOP 트렌드 조회
    - 오늘의 핫 트렌드를 빠르게 확인
    """
    result = await db.execute(
        select(Trend).order_by(desc(Trend.score)).limit(limit)
    )
    return result.scalars().all()


@router.get("/categories", response_model=List[str])
async def get_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """수집된 트렌드의 카테고리 목록 조회"""
    result = await db.execute(
        select(Trend.category).distinct().where(Trend.category.isnot(None))
    )
    categories = [row[0] for row in result.fetchall()]
    return categories


@router.get("/{trend_id}", response_model=TrendResponse)
async def get_trend(
    trend_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """특정 트렌드 상세 조회"""
    result = await db.execute(select(Trend).where(Trend.id == trend_id))
    trend = result.scalar_one_or_none()
    if not trend:
        raise HTTPException(status_code=404, detail="트렌드를 찾을 수 없습니다.")
    return trend


@router.post("/{trend_id}/analyze", response_model=TrendResponse)
async def analyze_single_trend(
    trend_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    특정 트렌드 AI 분석 요청
    - 백그라운드로 Gemini 분석 실행
    - 프리미엄 사용자만 사용 가능
    """
    if not current_user.is_premium:
        raise HTTPException(
            status_code=403,
            detail="AI 분석은 프리미엄 구독 사용자만 이용 가능합니다.",
        )

    result = await db.execute(select(Trend).where(Trend.id == trend_id))
    trend = result.scalar_one_or_none()
    if not trend:
        raise HTTPException(status_code=404, detail="트렌드를 찾을 수 없습니다.")

    # 백그라운드로 분석 실행
    background_tasks.add_task(analyze_trend, trend_id)
    return trend


@router.post("/collect", status_code=202)
async def trigger_collect(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
):
    """
    수동 트렌드 수집 트리거
    - 백그라운드로 구글 트렌드 + 뉴스 RSS 수집 실행
    """
    background_tasks.add_task(collect_trends)
    return {"message": "트렌드 수집을 시작했습니다. 잠시 후 결과를 확인하세요."}


@router.get("/reports/list", response_model=List[TrendReportResponse])
async def list_reports(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """주간 트렌드 리포트 목록 조회 (최신순)"""
    result = await db.execute(
        select(TrendReport).order_by(desc(TrendReport.created_at)).limit(limit)
    )
    return result.scalars().all()


@router.get("/reports/{report_id}", response_model=TrendReportResponse)
async def get_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """특정 주간 리포트 조회"""
    result = await db.execute(select(TrendReport).where(TrendReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다.")
    return report
