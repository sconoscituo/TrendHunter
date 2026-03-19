"""
애플리케이션 설정 관리
환경변수를 읽어 전역 설정으로 제공
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Gemini AI API 키
    gemini_api_key: str = ""

    # 데이터베이스 연결 URL
    database_url: str = "sqlite+aiosqlite:///./trendhunter.db"

    # JWT 시크릿 키
    secret_key: str = "change-this-secret-key-in-production"

    # JWT 알고리즘
    algorithm: str = "HS256"

    # 액세스 토큰 만료 시간 (분)
    access_token_expire_minutes: int = 60 * 24  # 24시간

    # 디버그 모드
    debug: bool = True

    # 앱 이름
    app_name: str = "TrendHunter"

    # 구글 트렌드 수집 국가 코드
    trend_geo: str = "KR"

    # 트렌드 수집 주기 (시간)
    collect_interval_hours: int = 6

    # 주간 리포트 생성 요일 (0=월요일)
    report_day_of_week: str = "mon"

    # 포트원(PortOne) 결제 연동
    portone_api_key: str = ""
    portone_api_secret: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """설정 싱글톤 반환 (캐시됨)"""
    return Settings()
