# Flight Finder 하네스 보완 이슈 정리 (`issue.md`)

현재 `flight_finder_ans` 하네스 규칙에서 예상되는 **6가지 단점**과, 기존 규칙(`SSOT §0`, `REQ/ARCH/VER/LOOP/DEC`)과 **충돌하지 않는 해결 방법**을 정리한 문서다.
각 항목은 `.github/ISSUE_TEMPLATE/maintenance.yml`의 6항목 계약서 양식에 맞춰 실제 GitHub Issue로 옮겨 사용할 수 있도록 구성했다.

---

## 한눈에 보기

| # | 예상 단점 | 충돌 없는 해결 방법 | 정합성 기준 |
| :--- | :--- | :--- | :--- |
| **1** | 초기 구축(Phase 1~4) 시 유지보수형 루프 오버헤드 및 보호 파일 충돌 | **[반영 완료]** `Bootstrap` / `Maintenance` 모드 분리 + 파일 원본(`01-ssot.md`·`05_roadmap.md`)과 질문 대조 규칙 적용 | `SSOT §0`, `VER-3`, `DEC-2` |
| **2** | 정당한 보호 경로 수정 PR도 CI `Protected` 단계에서 무조건 실패 | **[반영 완료]** 방안 1(1인 운영): 보호 경로는 사람이 `main`에 직접 커밋, AI 브랜치·PR은 엄격 차단 유지 | `SSOT §0`, `VER-3`, `DEC-2` |
| **3** | 정적 검사(`A1~A4`)로 간접 로깅 · 호출 상한(`<=4`) · 실 API 호출 차단 불가 | **[반영 완료]** 선택 B + `verify.py` 사전 게이트(`conftest.py` `autouse=True` · Phase 4+/Maintenance `test_invariants.py` 필수 강제) 및 문서·로드맵 규칙화 | `VER-1`, `VER-2`, `REQ-2`, `ARCH-2/4/6` |
| **4** | 프론트엔드(`src/static/`) · `localStorage` 계약이 `(수동)` 검증에만 의존 | **[반영 완료]** `verify.py` 사전 게이트(`src/static/app.js` 존재 시 `tests/test_static_contract.py` 필수) 및 문서·로드맵 규칙화 | `REQ-8`, `DEC-4` |
| **5** | Issue 코멘트 수동 작성 누락 · 양식 불일치 위험 | **[반영 완료]** `03-loop.md §3` 양식 자동 생성·등록 헬퍼(`scripts/log_attempt.py`) 구현 및 `SKILL.md` · `03-loop.md` 반영 | `LOOP-4`, `LOOP-5`, `03-loop.md §7` |
| **6** | Windows 로컬(cp949, 파일 락)과 Ubuntu CI(UTF-8, POSIX) 간 파일 처리 차이 | **[반영 완료]** `encoding="utf-8"` · `with` 종료 후 `os.replace()` 규칙 명시 + `verify.py` AST 검사(`A7`) 및 `test_invariants.py` 항목 반영 | `VER-1`, `ARCH-2` |

---

## Issue 1. 초기 구축(Phase 1~4) 작업 모드 분리 (`Bootstrap` vs `Maintenance`) — **[반영 완료]**

### 단점 및 원인
- 기존 하네스는 완성된 앱의 유지보수(작은 Issue 1건씩)에 최적화되어 있었다.
- 아직 `src/`가 없는 초기 구축 단계에서 보호 파일(`requirements.txt`, `.env.example`)까지 AI 작업 브랜치로 처리하면 `1/6 Protected` 단계에 걸리고 6항목 Issue·PR 절차 오버헤드가 컸다.

### 적용한 해결 방법 (방법 A: 모드 분리 + 파일 원본 · 질문 대조)
- **작업 모드 원본 (`docs/harness/01-ssot.md` 상단):** `현재 모드: Bootstrap` 선언. Phase 1~4 완료 후 사람이 직접 `Maintenance`로 전환한다.
- **현재 Phase 원본 (`docs/05_roadmap.md`):** 질문 내용만으로 Phase를 추측하지 않고, `05_roadmap.md`에서 미완료(`[ ]`)가 남은 **가장 앞선 Phase**를 현재 Phase로 확정한 뒤 사용자 요청과 대조한다(선행 미완료 상태에서 이후 Phase 요청 시 `NEEDS_HUMAN` 확인).
- **보호 경로 예외 (`scripts/verify.py`):** `Bootstrap (Phase 1)`에 한해 기준 커밋에 없던 `requirements.txt`, `.env.example`의 **최초 생성**만 예외 허용한다(`.env` 및 기타 보호 경로는 모드와 무관하게 차단).

### 반영된 파일
- `docs/harness/01-ssot.md` (`현재 모드: Bootstrap` 및 §0 작업 모드 · 질문 대조 규칙 추가)
- `AGENTS.md` (라우팅 표 보강 및 §3 작업 진입 절차에 모드·Phase 확인 분기 추가)
- `docs/harness/02-verification.md` (`1/6 Protected` 설명에 Phase 1 최초 생성 예외 반영)
- `scripts/verify.py` (`_parse_current_mode_from_ssot()`, `_detect_current_phase_from_roadmap()`, `_exists_in_commit()` 및 `1/6 Protected` 예외 로직 구현)

### 시작 전 남은 확인 사항
- [ ] 실제 개발 시작 전 `git init` 및 `main` 최초 기준 커밋 생성 (`1/6 Protected` diff 검사 활성화 조건)
- [ ] 반영 내용 검토 후 사람 최종 완료 승인 (`DEC-4`)

---

## Issue 2. 보호 경로 변경 절차 확정 (1인 운영 기준) — **[반영 완료]**

### 단점 및 원인
- `scripts/verify.py`의 `1/6 Protected`는 보호 경로 13개가 수정되면 AI와 사람을 구별하지 않고 무조건 실패하므로, 사람이 직접 스펙 문서나 `requirements.txt`를 수정해 PR을 열어도 CI가 실패한다.
- 1인 GitHub 계정 저장소에서는 본인 PR에 본인이 `APPROVED` 리뷰를 남길 수 없어 협업용 `Approved-Protected:` 리뷰 방식을 그대로 쓰기 어렵다.

### 적용한 해결 방법 (방안 1: 1인 운영 역할 분리)
- **사람 소유 보호 영역 수정:** PR을 거치지 않고 **사람이 `main` 브랜치에 직접 커밋**해 반영한다 (`main` push 시 `HEAD == origin/main`이므로 `Protected` diff 0건으로 CI 통과).
- **AI 작업 브랜치 · PR:** `src/`와 `tests/`(`Bootstrap Phase 1` 최초 생성 예외 포함)만 수정하며, `scripts/verify.py`의 `1/6 Protected`는 로컬과 PR CI 모두에서 예외 없이 보호 경로 변경을 차단한다.
- 추후 2인 이상 협업으로 전환할 때만 CI `Approved-Protected:` 리뷰 예외 도입을 재검토한다.

### 반영된 파일
- `docs/harness/01-ssot.md` (§0 보호 정책에 1인 운영 기준 보호 영역 변경 절차 명시)
- `docs/harness/02-verification.md` (§5 미정 항목에서 `Approved-Protected:`를 1인 운영 확정 사항으로 정리)

### 남은 확인 사항
- [ ] 반영 내용 검토 후 사람 최종 완료 승인 (`DEC-4`)

---

## Issue 3. `pytest` 공통 격리 픽스처 및 보안·비용·동시성 불변식 테스트 규칙화 — **[반영 완료]**

### 단점 및 원인
- `scripts/verify.py`의 `A3`·`A4` 정적 정규식은 변수에 담은 간접 로깅이나 에러 트레이스 내 BYOK 키 유출을 잡지 못한다.
- `A5`(동시성 Lock + Atomic Write), `A6`(테스트 실 API 호출 차단), `REQ-2`(1회 검색당 SerpApi 최대 4회 상한)가 자동 검증에 빠져 있었다.

### 적용한 해결 방법 (선택 B + `verify.py` 사전 게이트)
- 아직 `src/`·`tests/`가 없는 하네스 설계 단계에서는 순수 문서·하네스 폴더를 유지하되, **구현 시 누락을 막기 위해 `scripts/verify.py`의 `5/6 Test` 실행 직전에 기계적 사전 게이트(`check_test_prerequisites`)**를 추가했다.
  1. `tests/`에 `test_*.py`가 1개라도 존재하면 `tests/conftest.py`와 `autouse=True` 네트워크 차단 픽스처가 반드시 있어야 `pytest`를 실행한다 (`ARCH-6`).
  2. Phase 3 완료 이후(`Bootstrap Phase 4` 또는 `Maintenance` 모드)에는 `tests/test_invariants.py`가 반드시 존재해야 통과한다 (BYOK 키 비유출 `ARCH-4` · SerpApi `<= 4`회 `REQ-2` · 동시 쓰기 무결성 `ARCH-2`).

### 반영된 파일
- `scripts/verify.py` (`check_test_prerequisites()` 사전 게이트 구현)
- `docs/harness/02-verification.md` (§2 `5/6 Test`, §3 `A5`·`A6`, §5 알려진 빈틈 갱신)
- `docs/05_roadmap.md` (Phase 1 `tests/conftest.py`, Phase 3 `tests/test_invariants.py` 필수 체크 항목 추가)

### 남은 확인 사항
- [ ] Phase 1 구현 시 `tests/conftest.py` 작성, Phase 3 구현 시 `tests/test_invariants.py` 작성
- [ ] 반영 내용 검토 후 사람 최종 완료 승인 (`DEC-4`)

---

## Issue 4. 정적 웹페이지(`src/static/`) 및 `localStorage` 경량 계약 테스트 규칙화 — **[반영 완료]**

### 단점 및 원인
- `mypy`, `ruff`, 백엔드 `pytest`가 파이썬 파일만 검사하므로, `src/static/app.js`에 `localStorage` 키(`ff_invite_code`, `ff_flight_api_key`, `ff_recent_searches`), 요청 헤더(`X-Invite-Code`, `X-Flight-Api-Key`), API 경로(`/api/search`, `/api/quota`) 오타가 들어가도 `verify.py`를 통과해 버렸다.

### 적용한 해결 방법 (레벨 1 경량 계약 테스트 + `verify.py` 사전 게이트)
- 크롤링/브라우저 자동화 도구(`REQ-8` 혼동 소지) 없이 순수 Python만으로 Phase 4 구현 시 `tests/test_static_contract.py`에서 아래 4가지를 검증하도록 규칙화했다.
  1. `FastAPI TestClient` 정적 서빙 (`GET /`, CSS, JS `200 OK`)
  2. `index.html`의 `id` 목록 ↔ `app.js`의 `getElementById`/`querySelector` ID 교차 일치 검사
  3. 백엔드 Pydantic 응답 스키마(`SearchResponse`, `FlightOption`, `QuotaResponse`, `ErrorResponse`) 주요 필드 ↔ `app.js` 참조 교차 검사
  4. 필수 요청 헤더 · `localStorage` 키 · API 경로 존재 확인
- 누락 방지를 위해 `scripts/verify.py`의 `check_test_prerequisites()`에 **`src/static/app.js`가 존재할 때 `tests/test_static_contract.py`가 없으면 `5/6 Test`에서 즉시 실패**하는 사전 게이트를 추가했다.
- 실제 화면 디자인·반응형·클릭 흐름은 기존대로 `(수동)` 조건으로 사람이 최종 확인한다 (`DEC-4`).

### 반영된 파일
- `scripts/verify.py` (`check_test_prerequisites()`에 `test_static_contract.py` 사전 게이트 추가)
- `docs/harness/02-verification.md` (§2 `5/6 Test`, §5 알려진 빈틈 갱신)
- `docs/05_roadmap.md` (Phase 4에 `tests/test_static_contract.py` 필수 체크 항목 추가)

### 남은 확인 사항
- [ ] Phase 4 구현 시 `tests/test_static_contract.py` 작성
- [ ] 반영 내용 검토 후 사람 최종 완료 승인 (`DEC-4`)

---

## Issue 5. Issue 시도 코멘트 자동 포맷팅 헬퍼(`scripts/log_attempt.py`) 도입 — **[반영 완료]**

### 단점 및 원인
- 시도 횟수와 턴의 유일한 원본은 GitHub Issue 코멘트(`LOOP-4`, `LOOP-5`)이지만, 매번 수동으로 마크다운을 타이핑하면 양식이 어긋나거나 필수 항목이 빠져 다음 세션 복구에 차질이 생길 수 있었다.

### 적용한 해결 방법 (선택 A: 표준 라이브러리 CLI 헬퍼 선행 구현)
- `03-loop.md §3`의 `attempt`(시도 N/M) · `start`(진행 중) · `close`(진행 닫음) · `handoff`(사람 차례) 양식을 생성하고 `--post` 시 `gh issue comment`로 등록하는 `scripts/log_attempt.py`를 구현했다.
- Python 표준 라이브러리만 사용해 외부 의존성이 없으며, `scripts/verify.py`와 책임을 분리해 두었다 (`03-loop.md §2`).

### 반영된 파일
- `scripts/log_attempt.py` (CLI 양식 생성 · `--post` 등록 헬퍼 구현)
- `.agents/skills/issue-loop/SKILL.md` (§6 시도 코멘트에 `scripts/log_attempt.py` 사용 안내 추가)
- `docs/harness/03-loop.md` (§6 알려진 빈틈 갱신)

### 남은 확인 사항
- [ ] 반영 내용 검토 후 사람 최종 완료 승인 (`DEC-4`)

---

## Issue 6. Windows 로컬 · Ubuntu CI 크로스 플랫폼 파일 처리 안전성 규칙화 — **[반영 완료]**

### 단점 및 원인
- 로컬 개발 환경(Windows: 기본 `cp949`, 열린 파일 대상 `os.replace()` 시 `PermissionError`)과 CI 환경(Ubuntu: `UTF-8`, POSIX)의 차이로 인해 로컬 JSON 캐시·일일 횟수 제한 코드가 한쪽 환경에서만 실패할 위험이 있었다.

### 적용한 해결 방법 (규칙 명시 + `verify.py` `A7` AST 검사 + 불변식 테스트)
- `docs/04_cache_and_limit.md` §4와 `.agents/rules/cache-limit.md`에 `pathlib.Path` + `encoding="utf-8"` 필수 및 `.tmp` 쓰기 `with` 블록 종료 후 `os.replace()` 실행 규칙을 명시했다.
- `scripts/verify.py`의 `4/6 Architecture`에 AST 기반 `A7` 규칙을 추가해 `src/` 내 `.read_text()` / `.write_text()` 호출 시 `encoding` 인자가 빠지면 즉시 차단하도록 구현했다.
- `docs/05_roadmap.md` Phase 3의 `tests/test_invariants.py` 항목에 한글 UTF-8 라운드트립 및 `.tmp` 잔여 파일 없음 검증을 추가했다.

### 반영된 파일
- `docs/04_cache_and_limit.md` (§4 크로스 플랫폼 파일 안전성 규칙 보강)
- `.agents/rules/cache-limit.md` (`encoding="utf-8"` 및 `with` 종료 후 `os.replace()` 규칙 추가)
- `docs/harness/02-verification.md` (§2 `4/6 Architecture`, §3 `A7` 규칙 추가)
- `docs/05_roadmap.md` (Phase 3 `test_invariants.py` 항목 보강)
- `scripts/verify.py` (`check_architecture()`에 AST 기반 `A7` 검사 추가)

### 남은 확인 사항
- [ ] Phase 3 구현 시 `tests/test_invariants.py`에 한글 UTF-8 · 동시 쓰기 · `.tmp` 잔여 없음 테스트 작성
- [ ] 반영 내용 검토 후 사람 최종 완료 승인 (`DEC-4`)
