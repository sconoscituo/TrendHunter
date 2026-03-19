# TrendHunter - 프로젝트 설정 가이드

## 프로젝트 소개

TrendHunter는 Google Trends(pytrends)와 Google Gemini AI를 활용하여 실시간 트렌드를 수집·분석하고, 주간 트렌드 리포트를 자동 생성하는 SaaS 서비스입니다. APScheduler로 6시간마다 트렌드를 수집하며, 매주 월요일 자동으로 리포트를 생성합니다.

- **기술 스택**: FastAPI, SQLAlchemy (asyncio), SQLite, pytrends, Google Gemini AI, APScheduler
- **인증**: JWT 24시간 만료
- **결제**: PortOne (포트원)
- **트렌드 수집 국가**: 기본 KR (한국)

---

## 필요한 API 키 / 환경변수

| 환경변수 | 설명 | 발급 URL |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini AI API 키 | [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) |
| `SECRET_KEY` | JWT 서명용 비밀 키 | 직접 생성 (`openssl rand -hex 32`) |
| `PORTONE_API_KEY` | 포트원 결제 API 키 (선택) | [https://admin.portone.io](https://admin.portone.io) |
| `PORTONE_API_SECRET` | 포트원 결제 API 시크릿 (선택) | [https://admin.portone.io](https://admin.portone.io) |
| `DATABASE_URL` | DB 연결 URL (기본: SQLite) | - |
| `DEBUG` | 디버그 모드 (기본: `true`) | - |
| `TREND_GEO` | 트렌드 수집 국가 코드 (기본: `KR`) | - |
| `COLLECT_INTERVAL_HOURS` | 트렌드 수집 주기(시간) (기본: `6`) | - |
| `REPORT_DAY_OF_WEEK` | 주간 리포트 생성 요일 (기본: `mon`) | - |

---

## GitHub Secrets 설정 방법

저장소의 **Settings > Secrets and variables > Actions** 에서 아래 Secrets를 등록합니다.

```
GEMINI_API_KEY        = <Google AI Studio에서 발급한 키>
SECRET_KEY            = <openssl rand -hex 32 으로 생성한 값>
PORTONE_API_KEY       = <포트원 API 키> (선택)
PORTONE_API_SECRET    = <포트원 API 시크릿> (선택)
```

---

## 로컬 개발 환경 설정

### 1. 저장소 클론

```bash
git clone https://github.com/sconoscituo/TrendHunter.git
cd TrendHunter
```

### 2. Python 가상환경 생성 및 의존성 설치

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 환경변수 파일 생성

프로젝트 루트에 `.env` 파일을 생성합니다.

```env
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite+aiosqlite:///./trendhunter.db
DEBUG=true
TREND_GEO=KR
COLLECT_INTERVAL_HOURS=6
REPORT_DAY_OF_WEEK=mon
PORTONE_API_KEY=
PORTONE_API_SECRET=
```

---

## 실행 방법

### 로컬 실행 (uvicorn)

```bash
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 문서 확인: [http://localhost:8000/docs](http://localhost:8000/docs)

### Docker Compose로 실행

```bash
docker-compose up --build
```

### 테스트 실행

```bash
pytest tests/
```
