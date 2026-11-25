# 02. 검증 — 변경을 확인하는 방법

> 작성일: 2026-11-25
> [SSOT](01-ssot.md) §3의 상세다. SSOT와 다르면 SSOT를 따르고, 이 문서의 변경은 사람이 한다.
> 참고 원문: [01_architecture.md](../01_architecture.md) · [03_api_and_byok.md](../03_api_and_byok.md) · [04_cache_and_limit.md](../04_cache_and_limit.md)

---

## 1. 핵심 규칙

[SSOT](01-ssot.md) §3의 **VER-1~5**를 따른다. 규칙 원본은 SSOT다.

이 문서는 **판정만** 다룬다. 실패했을 때 몇 번까지 다시 시도하고 언제 멈추는지는 [03-loop.md](03-loop.md)가 맡는다.

### 검증의 세 층

| 층 | 판정자 | 구속력 | 대상 |
| :--- | :--- | :--- | :--- |
| **기계 검증** | `python scripts/verify.py` | **게이트** | 보호 영역, 타입, 린트/포맷, 아키텍처 규칙(`A1~A4, A7`), pytest(공통 + Issue 테스트), FastAPI 스모크 |
| **LLM 리뷰** | 독립 서브에이전트 AI | **경고 (자문)** | Issue 종료 조건 ↔ 구현·테스트 대조, 보호 영역 침범, 범위 밖 변경 (`04-decision.md` §3) |
| **사람 검증** | 사람 | **게이트** | `(수동)` 종료 조건, 실제 웹 UI 동작 · `localStorage` 동작 · 에러 문구 확인 |

- **게이트**를 통과하지 못한 변경은 완료가 아니다.
- **경고(LLM 리뷰)**는 완료를 막지 않지만, 정해진 자리(CI 통과 뒤)에서 실행하고 결과를 PR 코멘트로 남긴다.
- **검사 불능**(도구 미설치, 환경 오류, 타임아웃 등)은 통과가 아니라 **실패**로 본다.

---

## 2. 파이프라인 — `python scripts/verify.py`

한 명령이 전부다. `pytest`나 `ruff`를 낱개로 돌리는 것은 개발 중 확인일 뿐 판정이 아니다.
먼저 실패한 단계에서 즉시 중단하며, 뒤 단계는 실행하지 않는다.

```text
Protected → Types → Lint & Format → Architecture → Test → Smoke
```

| 단계 | 실행 | 잡는 것 | 잡지 않는 것 |
| :--- | :--- | :--- | :--- |
| **1/6 Protected** | Git 추적 금지 파일 + 사람 소유 보호 경로 변경 검사 | `.env` · `data/cache/` · `data/limits/` 추적 여부, SSOT §0 보호 영역 무단 수정 (`Bootstrap` 모드 Phase 1의 `requirements.txt` · `.env.example` 최초 생성만 예외 허용) | 수정 내용의 타당성 |
| **2/6 Types** | `python -m mypy --ignore-missing-imports src` | 정적 타입 오류, 타입 힌트 불일치 | 런타임 동작 |
| **3/6 Lint & Format** | `python -m ruff check .` · `ruff format --check .` | 정적 린트 위반, 코드 포맷 불일치 | 도메인 로직 오류 |
| **4/6 Architecture** | `scripts/verify.py` 정적 패턴 · AST 스캔 (`A1~A4`, `A7`) | `requests` · 크롤링 라이브러리 · 헤더/API 키 로깅 및 `print` · `encoding` 없는 텍스트 I/O | 런타임 동시성 경합 |
| **5/6 Test** | `verify.py` 사전 게이트 + `python -m pytest` | `tests/conftest.py`(`autouse=True` 네트워크 차단), Phase 3 이후 `tests/test_invariants.py`, `src/static/app.js` 존재 시 `tests/test_static_contract.py` 확인 후 전체 `pytest` 실행 | 실제 외부 API 스펙 변경, 브라우저 시각 UI |
| **6/6 Smoke** | 더미 환경변수 주입 후 `from src.main import app` | 앱 초기화 · 설정 로딩 · 임포트 순환 오류 | 실제 요청/응답 시나리오 |

CI는 `.github/workflows/verify.yml` (ubuntu · Python 3.12 · `TZ=Asia/Seoul`)에서 로컬과 동일한 `python scripts/verify.py`를 실행한다.

---

## 3. 아키텍처 규칙 — `scripts/verify.py`

| # | 규칙 | 검사 방식 | 근거 |
| :--- | :--- | :--- | :--- |
| **A1** | 블로킹 `requests` 라이브러리 import 금지 (`httpx.AsyncClient` 사용) | `verify.py` 정적 스캔 | `ARCH-3` |
| **A2** | 크롤링 라이브러리(`bs4`, `selenium`, `playwright`, `scrapy`) import 금지 | `verify.py` 정적 스캔 | `REQ-8` |
| **A3** | `request.headers` 또는 `X-Flight-Api-Key`를 `logger`/`logging`으로 출력 금지 | `verify.py` 정적 스캔 | `ARCH-4` |
| **A4** | `request.headers` 또는 `X-Flight-Api-Key`를 `print()`로 출력 금지 | `verify.py` 정적 스캔 | `ARCH-4` |
| **A5** | 공유 JSON 파일 쓰기 시 `asyncio.Lock` + Atomic Write(`.tmp` → `os.replace`) | `tests/test_invariants.py` 동시 쓰기 불변식 테스트 + 리뷰 | `ARCH-2` |
| **A6** | `tests/`에서 실제 Gemini / SerpApi 네트워크 호출 금지 (Mock 필수) | `verify.py` `tests/conftest.py`(`autouse=True`) 사전 게이트 + `pytest` 격리 | `ARCH-6` |
| **A7** | `src/` 내 텍스트 파일 I/O(`.read_text()`, `.write_text()`, `open()`, `Path.open()`) 시 `encoding` 명시 (바이너리 모드 제외) | `verify.py` AST 스캔 | `ARCH-2` |

---

## 4. Issue 단위 검증

공통 기계 검증은 저장소 전체의 규칙을 본다. 개별 Issue의 종료 조건은 Issue 전용 테스트가 판정한다.

| 항목 | 규칙 |
| :--- | :--- |
| 파일 경로 | `tests/issues/test_issue_{번호}_{기능명}.py` (예: `tests/issues/test_issue_3_byok_bypass_limit.py`). 기능명은 영문 소문자 `snake_case` |
| 조건 ↔ 테스트 | Issue 3번의 자동 검증 조건(`(수동)` 제외)마다 테스트 함수 1개 이상 (`def test_c1_...` 또는 docstring에 `C1.` 명시) |
| 변경 전 실패 확인 | 구현 전 코드에서 새 테스트가 **실패**하는 것을 먼저 확인한다 |
| 데이터 격리 | `pytest`의 `tmp_path` · `monkeypatch`를 사용해 `data/` 실제 디렉토리를 오염시키지 않는다 |
| 다른 Issue 테스트 | 고치지 않는다. 수정이 필요하면 전제를 사람에게 검토받는다 (`VER-4`) |

---

## 5. 알려진 빈틈 · 예정 · 미정

**알려진 빈틈**
- `src/static/`의 정적 서빙, `index.html` ID ↔ `app.js` 참조 교차 검사, 백엔드 응답 스키마 필드 ↔ `app.js` 참조 교차 검사, 필수 헤더·`localStorage` 키·API 경로는 `tests/test_static_contract.py`가 자동 검증하지만, JS 런타임 동작·시각 레이아웃·클릭 흐름은 `pytest`가 잡지 못한다 → `(수동)` 조건으로 사람이 확인한다.
- `tests/conftest.py`의 `autouse=True` 픽스처와 `tests/test_invariants.py`의 실제 검증 강도는 `verify.py`가 파일·키워드 존재까지만 확인하므로, 세부 단언은 LLM 리뷰와 사람 검토로 보완한다.
- `src/`가 아직 생성되지 않은 초기 단계에서는 `Types`, `Architecture`, `Smoke` 단계가 경고(`WARN`) 후 건너뛰어진다.

**예정**
- `data/cache/` TTL 4시간 vs 365일 삭제 경계 불변식 공통 테스트(`tests/test_invariants.py` 확장) 추가

**미정**
- 실제 Gemini · SerpApi 키를 사용하는 수동 통합 스모크 워크플로 분리 여부
- CI `verify` 체크를 GitHub Branch Protection의 PR 병합 필수 조건으로 강제할지 여부

**확정 (1인 운영 기준)**
- 보호 영역 변경은 사람이 `main`에 직접 커밋해 반영하므로, CI PR 리뷰의 `Approved-Protected:` 예외 로직은 두지 않는다 (`01-ssot.md` §0). 협업 전환 시 재검토한다.
