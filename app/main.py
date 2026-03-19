"""
TrendHunter FastAPI 메인 애플리케이션
앱 초기화, 라우터 등록, 스케줄러 설정
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings
from app.database import init_db
from app.routers import trends, users

settings = get_settings()

# APScheduler 인스턴스 (전역)
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    앱 시작/종료 시 실행되는 라이프사이클 핸들러
    - 시작: DB 초기화, 스케줄러 등록 및 시작
    - 종료: 스케줄러 정지
    """
    # --- 시작 ---
    await init_db()

    # 트렌드 수집 스케줄 등록 (설정된 시간 간격마다 실행)
    from app.services.trend_collector import collect_trends
    scheduler.add_job(
        collect_trends,
        trigger="interval",
        hours=settings.collect_interval_hours,
        id="collect_trends",
        replace_existing=True,
    )

    # 주간 리포트 생성 스케줄 등록 (매주 월요일 오전 9시)
    from app.services.report_generator import generate_weekly_report
    scheduler.add_job(
        generate_weekly_report,
        trigger="cron",
        day_of_week=settings.report_day_of_week,
        hour=9,
        minute=0,
        id="weekly_report",
        replace_existing=True,
    )

    scheduler.start()
    print("✅ TrendHunter 서버 시작 - 스케줄러 활성화")

    yield

    # --- 종료 ---
    scheduler.shutdown(wait=False)
    print("🛑 TrendHunter 서버 종료")


# FastAPI 앱 인스턴스
app = FastAPI(
    title="TrendHunter API",
    description="AI 트렌드 선점 도구 - 구글 트렌드 + 뉴스 + 테마주 연결 분석",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 설정 (프론트엔드 연동을 위해 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(trends.router, prefix="/api/trends", tags=["trends"])


@app.get("/", tags=["health"])
async def root():
    """헬스체크 엔드포인트"""
    return {"service": "TrendHunter", "status": "running", "version": "1.0.0"}


@app.get("/health", tags=["health"])
async def health_check():
    """서버 상태 확인"""
    return {"status": "ok"}
