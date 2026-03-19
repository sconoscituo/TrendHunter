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

## 시작하기

```bash
# 1. 환경변수 설정
cp .env.example .env
# .env 파일에서 GEMINI_API_KEY, SECRET_KEY 입력

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 서버 실행
uvicorn app.main:app --reload
```

## API 문서

서버 실행 후 http://localhost:8000/docs 접속

## 수익 구조

- 무료: 주간 트렌드 요약 5개
- 프로($29/월): 실시간 트렌드 + 테마주 분석 + 리포트 무제한
- 엔터프라이즈($99/월): API 접근 + 커스텀 카테고리

## 기술 스택

- Backend: FastAPI, SQLAlchemy (async), SQLite
- AI: Google Gemini API
- 스케줄러: APScheduler
- 인증: JWT (python-jose)
