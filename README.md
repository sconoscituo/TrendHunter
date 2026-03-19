# TrendHunter

AI 트렌드 선점 도구 — 구글 트렌드 + 뉴스 RSS + 테마주 연결 분석

## 개요

마케터, 투자자, 유튜버를 위한 SaaS 트렌드 분석 플랫폼입니다.
구글 트렌드와 뉴스 RSS를 수집하고, Gemini AI가 기회/위험을 분석하여 관련 테마주와 사업 아이디어를 제시합니다.

## 주요 기능

- 구글 트렌드 실시간 키워드 수집 (pytrends)
- 뉴스 RSS 피드 키워드 분석 (feedparser + BeautifulSoup)
- Gemini AI 트렌드 기회·위험 분석
- 관련 테마주 자동 추출
- 주간 트렌드 리포트 자동 생성 (APScheduler)
- JWT 기반 사용자 인증

## 수익 구조

| 플랜 | 기능 | 대상 | 가격 |
|------|------|------|------|
| 무료 | 주간 트렌드 요약 5개 | 개인 | 무료 |
| 프로 | 실시간 트렌드 + 테마주 분석 + 리포트 무제한 | 마케터 / 투자자 | $29/월 |
| 엔터프라이즈 | API 접근 + 커스텀 카테고리 | 유튜버 / 기업 | $99/월 |

## 기술 스택

| 영역 | 기술 |
|------|------|
| Backend | FastAPI, SQLAlchemy (async), SQLite |
| AI 분석 | Google Gemini API (gemini-1.5-flash) |
| 트렌드 수집 | pytrends (Google Trends) |
| 뉴스 파싱 | feedparser, BeautifulSoup4 |
| 스케줄러 | APScheduler |
| 인증 | JWT (python-jose) |

## 설치 및 실행

### 로컬 실행

```bash
# 1. 저장소 클론
git clone https://github.com/sconoscituo/TrendHunter.git
cd TrendHunter

# 2. 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경변수 설정
cp .env.example .env
# .env 파일에서 GEMINI_API_KEY, SECRET_KEY 입력

# 5. 서버 실행
uvicorn app.main:app --reload
```

### Docker 실행

```bash
cp .env.example .env
# .env 파일 편집

docker-compose up -d
```

서버 실행 후 http://localhost:8000/docs 에서 Swagger UI 확인

## 환경변수

| 변수 | 설명 | 필수 |
|------|------|------|
| `GEMINI_API_KEY` | Google Gemini API 키 | O |
| `SECRET_KEY` | JWT 서명 비밀키 | O |
| `DATABASE_URL` | SQLite DB 경로 | O |
| `DEBUG` | 디버그 모드 (true/false) | 선택 |

## 주요 API

### 인증

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/users/register` | 회원가입 |
| POST | `/api/users/login` | 로그인 (JWT 발급) |
| GET | `/api/users/me` | 내 정보 조회 |

### 트렌드 분석

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/trends` | 트렌드 목록 조회 |
| GET | `/api/trends/latest` | 최신 트렌드 분석 |
| POST | `/api/trends/run` | 트렌드 수집 즉시 실행 |
| GET | `/api/reports` | 주간 리포트 목록 |
| GET | `/api/reports/latest` | 최신 주간 리포트 |

## 트렌드 카테고리

| 카테고리 | 설명 | 예시 키워드 |
|---------|------|------------|
| 테크 | IT·AI·반도체 관련 급등 키워드 | AI 에이전트, 양자컴퓨터, 온디바이스AI |
| 금융 | 주식·코인·경제 이슈 | 금리 인하, 비트코인 ETF, FOMC |
| 라이프스타일 | 소비·트렌드·문화 | 무지출 챌린지, 디지털 노마드 |
| 정치·사회 | 선거·정책·이슈 | 총선, 부동산 정책, ESG |
| 엔터 | 드라마·유튜브·스포츠 | OTT 신작, 쇼츠 트렌드 |
| 건강 | 의료·다이어트·웰니스 | GLP-1, 마음챙김, 수면 트래커 |

## 주간 리포트 예시

```json
{
  "week": "2025-W12",
  "generated_at": "2025-03-23T09:00:00",
  "top_trends": [
    {
      "keyword": "AI 에이전트",
      "category": "테크",
      "score": 94,
      "related_stocks": ["NVDA", "MSFT", "035420.KS"],
      "opportunity": "AI 에이전트 관련 SaaS 제품 수요 급증. B2B 자동화 솔루션 진입 적기.",
      "risk": "빅테크 직접 출시 시 경쟁 심화 가능성."
    },
    {
      "keyword": "비트코인 ETF",
      "category": "금융",
      "score": 87,
      "related_stocks": ["COIN", "MSTR", "HOOD"],
      "opportunity": "기관 자금 유입으로 관련 인프라 기업 수혜 예상.",
      "risk": "규제 강화 리스크 상존."
    }
  ],
  "summary": "이번 주 가장 빠르게 상승한 키워드는 'AI 에이전트'로, 전주 대비 검색량 340% 증가. 투자자에게는 관련 테마주, 마케터에게는 콘텐츠 기회로 활용 가능."
}
```

## 테스트

```bash
pytest tests/ -v --asyncio-mode=auto
```

## 라이선스

MIT
