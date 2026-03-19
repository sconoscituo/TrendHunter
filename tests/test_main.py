"""
TrendHunter 기본 동작 테스트
FastAPI TestClient로 주요 엔드포인트 검증
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database import get_db, Base

# 테스트용 인메모리 SQLite DB
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db():
    """테스트용 DB 세션 오버라이드"""
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture(autouse=True)
async def setup_db():
    """각 테스트 전 테이블 생성, 후 삭제"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.dependency_overrides[get_db] = override_get_db
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_check():
    """헬스체크 엔드포인트 정상 응답 확인"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_root():
    """루트 엔드포인트 서비스명 확인"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "TrendHunter"
    assert data["status"] == "running"


@pytest.mark.asyncio
async def test_register_and_login():
    """회원가입 후 로그인하여 JWT 토큰 발급 확인"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 회원가입
        reg_response = await client.post(
            "/api/users/register",
            json={
                "email": "test@example.com",
                "username": "테스터",
                "password": "password123",
            },
        )
        assert reg_response.status_code == 201
        user_data = reg_response.json()
        assert user_data["email"] == "test@example.com"
        assert user_data["username"] == "테스터"

        # 로그인
        login_response = await client.post(
            "/api/users/login",
            data={"username": "test@example.com", "password": "password123"},
        )
        assert login_response.status_code == 200
        token_data = login_response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_duplicate_register():
    """동일 이메일 중복 가입 시 400 오류 확인"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "email": "dup@example.com",
            "username": "중복유저",
            "password": "password123",
        }
        await client.post("/api/users/register", json=payload)
        dup_response = await client.post("/api/users/register", json=payload)
    assert dup_response.status_code == 400


@pytest.mark.asyncio
async def test_trends_require_auth():
    """인증 없이 트렌드 조회 시 401 응답 확인"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/trends/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me():
    """로그인 후 내 정보 조회 확인"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 회원가입 + 로그인
        await client.post(
            "/api/users/register",
            json={"email": "me@example.com", "username": "나", "password": "password123"},
        )
        login = await client.post(
            "/api/users/login",
            data={"username": "me@example.com", "password": "password123"},
        )
        token = login.json()["access_token"]

        # 내 정보 조회
        me_response = await client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "me@example.com"
