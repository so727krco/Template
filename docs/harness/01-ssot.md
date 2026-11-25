# 01. SSOT — Flight Finder 규칙 원본

> 작성일: 2026-11-25
> 현재 모드: Bootstrap
> 참고 원문: [01_architecture.md](../01_architecture.md) · [02_llm_spec.md](../02_llm_spec.md) · [03_api_and_byok.md](../03_api_and_byok.md) · [04_cache_and_limit.md](../04_cache_and_limit.md) · [05_roadmap.md](../05_roadmap.md)

---

## 0. SSOT 규칙

1. **이 문서가 요구사항 · 아키텍처 규칙의 원본이다.** `docs/01~05` 원문은 상세 스펙 참고용이다.
2. 여기에는 **핵심 규칙만** 둔다. 스키마 상세 표 · 프롬프트 예시 · 에러 JSON 예시는 원문을 본다.
3. 규칙을 바꿀 때는 **이 문서를 먼저 고치고, 코드는 그다음**에 고친다. 이 문서의 변경은 사람이 한다 (아래 보호 정책).
4. 원문에 근거가 없는 내용은 지어내지 않고 **미정**에 남긴다.
5. 사람의 판단이 필요한 경우 **`NEEDS_HUMAN`** 상태를 선언한다. 아래 충돌 정책 · 보호 정책에서 사람에게 넘기는 경우가 모두 여기에 해당한다. 선언 사유와 넘기는 절차는 §5다.
6. **개별 작업의 원본은 모드에 따라 정한다.** `Maintenance` 모드에서는 GitHub Issue, `Bootstrap` 모드에서는 `docs/05_roadmap.md`의 현재 Phase 체크리스트다 (아래 작업 모드 · Issue 절).

### 작업 모드 — `Bootstrap` vs `Maintenance`

초기 구축(0 → 1)과 유지보수(1 → N)의 절차 강도를 구분한다. **모드의 원본은 이 문서 상단의 `현재 모드` 줄**이며, 전환(`Bootstrap` → `Maintenance`)은 Phase 1~4 완료 후 **사람이 직접** 한다.

| 항목 | `Bootstrap` 모드 (초기 구축) | `Maintenance` 모드 (유지보수) |
| :--- | :--- | :--- |
| **현재 Phase 원본** | `docs/05_roadmap.md`에서 미완료(`[ ]`)가 남은 **가장 앞선 Phase** | 해당 없음 (MVP 완료) |
| **작업 계약 단위** | 현재 Phase 체크리스트 (또는 Phase당 Issue 1건) | 6항목 GitHub Issue 1건 (`.github/ISSUE_TEMPLATE/maintenance.yml`) |
| **보호 경로 예외** | **Phase 1에 한해** 기존에 없던 `requirements.txt`, `.env.example`의 **최초 생성**만 허용 (`.env` 및 기타 보호 경로는 여전히 금지) | 예외 없음 (보호 정책 표 전체 엄격 차단) |
| **검증 및 완료** | Phase 종료마다 `python scripts/verify.py` 통과 + 사람 확인 | `python scripts/verify.py` + CI + LLM 리뷰 + 사람 승인(`DEC-4`) |
| **시도 상한 · 중단** | Phase당 `verify.py` 연속 실패 상한 기본 3회 (초과 시 대화창에 `NEEDS_HUMAN` 보고 후 중단) | Issue §6 상한(기본 3회, 최대 5회) · Issue 코멘트에 `중단(상한 소진)` 기록 (`LOOP-3`) |

**질문(요청)과 현재 Phase 대조 규칙 (`Bootstrap` 모드):** AI는 질문 내용만으로 Phase를 추측하지 않고, `docs/05_roadmap.md`의 현재 Phase와 요청을 대조한다.
- **요청 ∈ 현재 Phase:** `Bootstrap` 규칙대로 구현하고, `python scripts/verify.py` 통과 후 체크박스 갱신을 제안한다.
- **요청 ∈ 이후 Phase (선행 Phase 미완료):** 임의로 건너뛰지 않고 `NEEDS_HUMAN`으로 선행 Phase 먼저 진행할지 확인한다.
- **요청 ∈ 이전 완료 Phase:** 현재 Phase 구현에 필요한 연계 수정이면 진행 후 기록하고, 무관한 변경이면 사람에게 확인한다.
- **`Maintenance` 모드 전환 후:** 질문 내용과 무관하게 반드시 6항목 Issue 루프로만 진행한다.

### Issue — 개별 작업의 SSOT

작업은 Issue 하나에서 시작하고 Issue 하나로 끝난다. 양식은 `.github/ISSUE_TEMPLATE/maintenance.yml`(유지보수 계약서 6개 항목)이다.

- 작업의 배경 · 변경할 내용 · 종료 조건 · 기계 검증 · 건드리면 안 되는 것 · 구현 루프 최대 횟수는 **Issue를 기준으로 판단**한다. 대화 · 로드맵(`docs/05_roadmap.md`)에 다른 내용이 있어도 그 작업에서는 Issue를 따른다.
- Issue에 없는 변경은 하지 않는다. 필요하다고 판단하면 직접 넓히지 않고 새 Issue를 제안한다.
- Issue는 이 문서의 규칙(§0~§5)을 넘어서지 못한다. 충돌하면 아래 충돌 정책대로 중단한다.
- 6개 항목이 비어 있거나 종료 조건을 참 · 거짓으로 판정할 수 없으면 추측으로 채우지 않고 `NEEDS_HUMAN`을 선언한다.
- Issue 본문은 사람이 고친다. AI는 바꿔야 할 내용을 Issue 코멘트로 제안한다.
- 작업 완료는 ① 자동 검증 종료 조건이 `tests/issues/test_issue_{번호}_{기능명}.py`에서 통과하고 ② `python scripts/verify.py`가 통과하고 ③ `(수동)` 종료 조건을 사람이 확인했을 때다. **판정은 사람이 한다** (§5 · `DEC-4`).

### 충돌 정책 — 사람에게 넘길 판단

| 충돌 | 판단 |
| :--- | :--- |
| 작업 요청(Issue)이 요구사항 · 아키텍처 · 하네스 규칙과 충돌 | **중단**하고 사람에게 확인한다 (`NEEDS_HUMAN`) |
| 로드맵(`docs/05_roadmap.md`)이 그 작업의 Issue와 다름 | 그 작업에서는 **Issue**를 따른다 |
| 참고 문서(`docs/01~05` 원문)가 SSOT와 다름 | **SSOT**를 따르고 불일치를 보고한다 |
| 로드맵(`docs/05_roadmap.md`)이 요구사항(`REQ-*`)과 다름 | **요구사항**을 따른다 |
| SSOT 규칙끼리 충돌 (예: `REQ-*` ↔ `ARCH-*`) | 사람이 기준을 고치기 전까지 **구현하지 않는다** (`NEEDS_HUMAN`) |

> **에이전트가 임의로 충돌을 해소하면 판단 기준 하나를 지우는 것이다.**
> 중단할 때는 어느 규칙과 어느 규칙이 충돌하는지 적어서 사람에게 넘긴다.

### 보호 정책 — 영역별 소유권

읽기 권한과 변경 권한을 영역별로 나눈다.

| 영역 | 대상 | AI | 사람 |
| :--- | :--- | :--- | :--- |
| 작업 요청 | GitHub Issue 본문 | **읽기** · 코멘트로 제안 | 작성 · 변경 |
| 애플리케이션 코드 | `src/` | Issue 범위 안에서 수정 | 최종 승인 |
| Issue별 테스트 | `tests/` (Issue 종료 조건은 `tests/issues/`) | 작성 · 수정 | 전제 검토 |
| 요구사항 · 아키텍처 · 로드맵 | 이 문서 §1 · §2, `docs/01_architecture.md`, `docs/02_llm_spec.md`, `docs/03_api_and_byok.md`, `docs/04_cache_and_limit.md`, `docs/05_roadmap.md` | **읽기** · 체크박스 갱신 제안 | 변경 · 승인 (Phase 완료 시 체크) |
| 하네스 핵심 규칙 | 이 문서 §0, `docs/harness/`, `AGENTS.md`, `.agents/rules/`, `.agents/skills/` | **읽기** | 변경 · 승인 |
| 검증 · 하네스 스크립트 · CI | `scripts/verify.py`, `scripts/log_attempt.py`, `.github/workflows/` | **실행** | 정책 변경 승인 |
| 환경 변수 · 의존성 | `.env`, `.env.example`, `requirements.txt` | **읽기** · 변경 전 확인 | 변경 · 승인 |

> AI가 읽기 전용 영역을 바꿔야 한다고 판단하면, 직접 고치지 않고 변경안을 제안해서 사람에게 넘긴다.
> **보호 영역 변경 절차 (1인 운영 기준):** 사람 소유 보호 영역의 수정은 PR을 거치지 않고 **사람이 `main` 브랜치에 직접 커밋**해 반영한다. AI 작업 브랜치·PR은 `src/`와 `tests/`(`Bootstrap Phase 1` 최초 생성 예외 포함)만 수정하며, `scripts/verify.py`의 `1/6 Protected`는 브랜치·PR에서 보호 경로 변경을 예외 없이 차단한다.
> **이 표는 소유권**(누가 바꿀 수 있나)이고, **넘기고 받는 절차는 §5**(사람의 개입)다.

---

## 1. 요구사항

사용자의 자연어 여행 조건을 LLM으로 구조화하고, 항공권 API를 비동기 조회해 최저가 옵션을 브리핑하는 지인 공유용 단독 실행 웹 서비스.
별도의 로그인이나 외부 DB 없이 동작하며, 기본 무료 횟수는 운영자 공용 키로 제공하고 초과 사용자는 본인 API 키(BYOK)를 입력해 사용한다.
상세 → [02_llm_spec.md](../02_llm_spec.md) · [03_api_and_byok.md](../03_api_and_byok.md) · [04_cache_and_limit.md](../04_cache_and_limit.md)

**핵심 규칙**
- **REQ-1 (자연어 파싱 · IATA 매핑)** Gemini 2.5 Flash Structured Output으로 `FlightSearchQuery` 스키마를 추출하며, 매 요청마다 KST 현재 날짜(요일 포함)를 시스템 프롬프트에 주입해 상대 날짜를 계산한다.
- **REQ-2 (2단계 비동기 조회 · 호출 상한)** 1단계 최저가 날짜 탐색 후 2단계 상세 항공편을 병렬 조회하며, **1회 검색당 SerpApi 호출은 최대 4회**(탐색 1회 + 상세 병렬 최대 3회)로 제한한다.
- **REQ-3 (Stateless BYOK · 브라우저 저장)** 사용자 개인 API 키와 최근 검색값(최대 10건)은 서버가 아닌 브라우저 `localStorage`에만 보관한다. 기본 BYOK 대상은 항공권 API 키(`X-Flight-Api-Key`)이며 LLM은 운영자 공용 키를 사용한다.
- **REQ-4 (초대 코드 필수)** LLM 할당량 보호를 위해 공용 키 · BYOK 여부와 관계없이 모든 검색 요청에 `X-Invite-Code` 검증을 필수 적용한다.
- **REQ-5 (일일 무료 횟수 제한 · BYOK 우회)** 공용 키 요청은 클라이언트 IP 기준 `DAILY_FREE_LIMIT`(기본 5회)을 적용하고, 유효한 `X-Flight-Api-Key` 헤더가 있을 때만 횟수 제한을 우회한다.
- **REQ-6 (캐시 TTL과 물리 삭제 분리)** 로컬 JSON 캐시 적중 유효기간은 **4시간**(3~6시간 범위)이며, 캐시 적중 시 공용 키 횟수를 차감하지 않는다. 디스크 물리 삭제는 `GET /` 진입 시 백그라운드 태스크(최소 1시간 스캔 가드)로 `data/cache/` **365일**, `data/limits/` **30일** 경과 파일만 삭제한다.
- **REQ-7 (친절한 커스텀 에러)** 키 오류 · 한도 초과 · 파싱 실패 · 외부 API 오류 시 `500` 원시 오류 대신 `ErrorResponse`(`error_code`, 한국어 `message`)를 반환한다.
- **REQ-8 (크롤링 금지)** 항공사 · 메타검색 사이트 크롤링은 구현하지 않으며 공식 · 서드파티 API만 호출한다.

**미정** — LLM 사용자 키(BYOK) 선택 입력 UI 제공 시점, 외부 공유용 HTTPS 리버스 프록시(Cloudflare Tunnel/Caddy/Nginx) 운영 표준, 다중 인스턴스 확장 시 캐시 공유 방안

---

## 2. 아키텍처

Python 3.12+ · FastAPI · Pydantic v2 · `httpx.AsyncClient` · 정적 웹페이지(HTML/CSS/Vanilla JS) · No-DB(로컬 `data/` JSON + 브라우저 `localStorage`).
상세 → [01_architecture.md](../01_architecture.md) · [03_api_and_byok.md](../03_api_and_byok.md) · [04_cache_and_limit.md](../04_cache_and_limit.md)

**핵심 규칙**
- **ARCH-1 (단독 실행 · No-DB)** 외부 DB 서버를 두지 않는다. 서버 상태는 `data/cache/`와 `data/limits/`의 로컬 JSON으로 관리하며 `data/` 런타임 파일과 `.env`는 Git에 커밋하지 않는다.
- **ARCH-2 (파일 동시성 보호)** 공유 JSON 파일 쓰기 시 모듈 전역 `asyncio.Lock`으로 임계 구역을 보호하고, 임시 파일(`.tmp`) 기록 후 `os.replace()`로 Atomic Write를 수행한다.
- **ARCH-3 (비동기 HTTP 전용)** 외부 API 호출은 블로킹 `requests` 대신 `httpx.AsyncClient`와 `async/await`로만 구현한다.
- **ARCH-4 (BYOK 키 비유출)** `X-Flight-Api-Key`는 함수 인자로만 전달해 메모리에서 일회성 사용하며, 파일 · 로그 · `print` · 에러 응답 본문에 절대 남기지 않는다.
- **ARCH-5 (상수 시간 초대 코드 비교)** `X-Invite-Code` 검증은 `hmac.compare_digest`를 사용한다.
- **ARCH-6 (Mock 우선 테스트 · 타입 힌트)** `pytest`는 실제 외부 API를 호출하지 않고 Mock 응답만 사용하며, 모든 함수 파라미터와 반환값에 Python 타입 힌트를 명시한다.

**환경 변수 계약 (`.env`)** — `LLM_API_KEY`, `FLIGHT_API_KEY`, `INVITE_CODE`, `DAILY_FREE_LIMIT`

**미정** — 프론트엔드 정적 자산 번들링 도입 여부, 프로덕션 로깅 포맷(JSON 로거) 표준

---

## 3. 검증

`python scripts/verify.py` — Protected → Types(`mypy`) → Lint/Format(`ruff`) → Architecture → Test(`pytest`) → Smoke.
이 절은 **판정만** 다룬다. 몇 번까지 다시 시도하고 언제 멈추는지는 §4 구현 루프가 맡는다.
상세 → [02-verification.md](02-verification.md) (파이프라인 §2 · 아키텍처 규칙 `A1~A7` §3 · 알려진 빈틈 §5)

**핵심 규칙**
- **VER-1** 자동 검증 관문은 `python scripts/verify.py` 하나다. 로컬과 CI(PR · `main` push)가 같은 명령을 쓴다.
- **VER-2** Smoke 및 테스트는 실제 `.env`나 외부 API에 의존하지 않고 더미 환경변수와 Mock으로 격리 실행한다.
- **VER-3** 한 단계라도 실패하면 즉시 멈춘다. 검증 스크립트를 완화 · 삭제하거나 `# type: ignore` · `# noqa`를 남발해 통과시키지 않는다 — 검증 정책 변경은 사람이 승인한다 (§0 보호 정책).
- **VER-4** 기존 테스트의 기대값을 바꿔야 하면 그 전제를 사람에게 검토받는다 (§0 보호 정책).
- **VER-5** `verify.py` 통과는 완료가 아니다. 완료는 Issue 종료 조건(자동 + `(수동)`)이 모두 확인되었을 때다.

**미정** — 실제 API 통합 스모크 테스트(수동 워크플로) 분리 여부, CI 체크의 PR 병합 필수 지정 (상세 → `02-verification.md` §5)

---

## 4. 구현 루프

**책임 분리.** 검증(§3, `python scripts/verify.py`)은 변경이 옳은지만 판정한다. 루프는 시도 횟수 · 멈춤 · 턴 · 기록을 관리한다.
`verify.py`는 시도 횟수를 모르고, 루프는 `verify.py`의 내부 단계를 모른다.

- **세는 단위:** 시도 1회 = 구현 시작부터 `python scripts/verify.py` 실행까지. 결과와 무관하게 한 번 실행하면 그 시도는 끝난다 (`LOOP-1`).
- **기록의 원본:** 대상 Issue의 코멘트. 시도가 끝날 때마다 `시도 N/M · 결과`를 남긴다. 세션이 끊기면 다음 세션은 마지막 코멘트의 N/M과 턴부터 이어간다 (`LOOP-4` · `LOOP-5`).
- **상한:** Issue 본문 §6(기본값 3회, 최대 5회). 다 쓰면 `중단(상한 소진)`으로 사람에게 넘긴다 (`LOOP-3`).
- **멈춤:** `NEEDS_HUMAN` 중단도 시도 1회를 쓴다. `verify.py`를 돌리지 않았어도 센다 (`LOOP-6`).
- **초기화:** 사람이 **판단 확정**을 주었을 때만 0으로 돌아간다. 재작업 지시만으로는 돌아가지 않는다 (`LOOP-7`).
- **턴:** 사람 차례인 동안 AI는 Issue와 작업 트리를 건드리지 않는다 (`LOOP-12`).
- **커밋 보류 · 진행 표시:** 커밋 보류 시 `보류 · 커밋` 코멘트(`LOOP-20`), 작업 시작 시 `진행 중` · 종료 시 `진행 닫음` 코멘트를 남긴다 (`LOOP-21`).

루프는 사람의 결정을 **네 이름**(승인 · 반려 · 판단 확정 · 요구사항 변경)으로만 받는다. 그 이름을 정의하고 사람의 말을 거기에 맞추는 일은 §5가 맡는다.

규칙의 원본은 [03-loop.md](03-loop.md)다.

**미정 (`NEEDS_HUMAN`)** — 3번째 판단 확정의 처리(`LOOP-25`) · 외부 변화(`main` 이동)로 생긴 CI 실패의 카운트(`LOOP-14`) · 되돌림 여부 기록 필드 위치(`LOOP-24`) (상세 → `03-loop.md` §7)

---

## 5. 사람의 개입

**§0이 소유권(누가 바꿀 수 있나)을 정하고, 이 절은 그 소유권을 주고받는 절차를 정한다.**
AI가 멈춰야 하는 지점 · 사람의 결정을 받는 경로 · 그 결정을 가르는 네 갈래가 여기에 속한다.

규칙의 원본은 [04-decision.md](04-decision.md)다.

**핵심 규칙**
- **DEC-1** 해석이 갈리거나 §0 충돌 정책에 걸리면 추측하지 않고 `NEEDS_HUMAN`을 선언한다 (사유 5가지 → `04-decision.md` §1).
- **DEC-4** **완료 판정은 사람이 한다.** 루프의 끝은 완료가 아니다.
- **DEC-5** **merge · 승인은 사람이 한다.** AI는 PR 생성까지만 한다.
- **DEC-6 · DEC-7** 사람은 **자연어로 말하면 된다.** 코멘트 양식을 채우는 것은 AI의 몫이다.
- **DEC-9** 사람의 결정은 **승인 · 반려 · 판단 확정 · 요구사항 변경** 넷 중 하나로 적는다. 애매하면 분류하지 않고 되묻는다.

**미정** — `NEEDS_HUMAN` 선언 전 탐색 기준, 승인 뒤 무응답 처리, 협업자가 여러 명일 때의 권한 (상세 → `04-decision.md` §5)
