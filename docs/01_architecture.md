# 01. 시스템 아키텍처 및 프로젝트 구조

## 1. 시스템 개요
별도의 로그인이나 외부 DB(Oracle, MariaDB 등) 없이 단독 실행되는 지인 공유용 최저가 항공권 조회 웹 서비스.
FastAPI 백엔드가 정적 웹페이지(HTML/CSS/Vanilla JS)를 직접 서빙하며, 서버 캐시와 횟수 제한은 로컬 `data/` 폴더의 JSON 파일로, 개인별 최근 검색값과 BYOK 키는 브라우저 `localStorage`로 관리한다.

## 2. 4단계 핵심 파이프라인
1. **자연어 입력 (Frontend):** 사용자가 웹페이지에서 초대 코드와 여행 조건을 입력하고 검색 요청 전송
2. **조건 추출 (LLM):** Gemini 2.5 Flash(Structured Output)로 출발지, 도착지(IATA), 날짜 후보, 직항 여부, 예산을 Pydantic 스키마로 파싱
3. **2단계 비동기 조회 (Flight API):**
   - **1단계:** 유연한 날짜/월간 최저가 탐색으로 저렴한 날짜 후보 2~3개 선별
   - **2단계:** 선별된 날짜의 상세 항공편을 `httpx.AsyncClient`와 `asyncio.gather`로 병렬 호출
4. **필터링 및 브리핑 (LLM):** 예산·조건에 맞는 상위 3~5개 옵션을 추려 시간대·경유·가성비 장단점을 한국어로 요약

## 3. 프로젝트 디렉토리 구조
```text
flight-finder/
├── AGENTS.md                  # 루트 에이전트 라우터 (Antigravity 진입점)
├── .env                       # 실제 API 키 및 설정 (Git 제외)
├── .env.example               # 환경 변수 템플릿
├── .gitignore                 # .env, .venv/, data/cache/, data/limits/ 제외
├── requirements.txt           # Python 패키지 목록
├── .agents/
│   ├── rules/                 # Antigravity 조건부 자동 라우팅 규칙
│   │   ├── llm-parsing.md
│   │   ├── api-byok.md
│   │   └── cache-limit.md
│   └── skills/
│       └── issue-loop/        # Issue 단위 구현·검증·PR·LLM 리뷰 루프 스킬
│           ├── SKILL.md
│           └── references/
│               └── llm-review-prompt.md
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   └── maintenance.yml    # 6항목 유지보수 작업 계약서
│   └── workflows/
│       └── verify.yml         # CI 통합 검증 워크플로
├── docs/                      # 상세 설계 스펙 및 하네스 규칙
│   ├── harness/               # 하네스 핵심 규칙 (SSOT)
│   │   ├── 01-ssot.md
│   │   ├── 02-verification.md
│   │   ├── 03-loop.md
│   │   └── 04-decision.md
│   ├── 01_architecture.md
│   ├── 02_llm_spec.md
│   ├── 03_api_and_byok.md
│   ├── 04_cache_and_limit.md
│   └── 05_roadmap.md
├── scripts/
│   └── verify.py              # 6단계 통합 자동 검증 파이프라인
├── src/
│   ├── main.py                # FastAPI 앱 진입점, 정적 파일 서빙, 진입 시 만료 캐시 정리
│   ├── config.py              # pydantic-settings 기반 .env 로딩
│   ├── schemas/               # 요청/응답/LLM 파싱 Pydantic v2 모델
│   ├── api/                   # FastAPI 라우터, BYOK 의존성, 커스텀 예외 핸들러
│   ├── services/
│   │   ├── llm.py             # Gemini 2.5 Flash 파싱 및 브리핑
│   │   ├── flight.py          # SerpApi Google Flights 2단계 비동기 조회
│   │   ├── cache.py           # 파일 캐시(TTL 3~6시간) 및 365일 경과 삭제
│   │   └── limiter.py         # 초대 코드 검증, 일일 횟수 제한(Lock + Atomic Write)
│   └── static/                # 단순 웹페이지
│       ├── index.html
│       ├── style.css
│       └── app.js             # API 호출 및 localStorage(BYOK 키, 최근 검색값) 관리
├── data/                      # 서버 로컬 저장소 (런타임 자동 생성, Git 제외)
│   ├── cache/
│   └── limits/
└── tests/                     # pytest 단위·통합 테스트 (Mock 필수)
    └── issues/                # Issue별 종료 조건 검증 테스트
```

## 4. 배포 및 보안 참고
- 외부 지인 공유 시 `X-Flight-Api-Key` 헤더 보호를 위해 반드시 HTTPS(Cloudflare Tunnel, Caddy, Nginx 등)를 앞단에 적용한다.
