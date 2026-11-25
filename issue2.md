# Flight Finder 하네스 2차 검증 이슈 정리 (`issue2.md`)

1차 보완(`issue.md` Issue 1~6) 반영 이후, `flight_finder_ans` 하네스 파일들을 교차 검증하며 추가로 발견한 **5가지 빈틈 · 불일치**와 해결 방안을 정리한 문서다.

---

## 한눈에 보기

| # | 심각도 | 발견된 문제 | 기존 규칙과 충돌 없는 해결 방법 | 영향 파일 |
| :--- | :--- | :--- | :--- | :--- |
| **2-1** | **중요** | `docs/05_roadmap.md`가 보호 정책 표에 없는데 `verify.py`가 이 파일로 현재 Phase를 판정함 (게이트 우회 여지 · 소유권 모호) | **[반영 완료]** `docs/05_roadmap.md`를 `01-ssot.md §0` 보호 정책 표에 사람 소유로 명시 (Phase 완료 시 사람이 체크) | `docs/harness/01-ssot.md` |
| **2-2** | **중요** | `verify.py` `A7` AST 검사가 `.read_text()`/`.write_text()`만 잡고 텍스트 모드 `open()`의 `encoding` 누락은 못 잡음 | **[반영 완료]** `A7` AST 검사에 내장 `open()` · `Path.open()` 텍스트 모드 `encoding` 검증 추가 (바이너리 모드 제외) | `scripts/verify.py`, `docs/harness/02-verification.md` |
| **2-3** | **중간** | `Bootstrap` 모드에서 GitHub Issue 없이 작업할 때 시도 상한 및 `NEEDS_HUMAN` 기록 위치가 미정의 | **[반영 완료]** `01-ssot.md §0` `Bootstrap` 표 및 `AGENTS.md` §3에 Phase당 시도 상한 기본 3회 · 초과 시 대화창 `NEEDS_HUMAN` 보고 명시 | `docs/harness/01-ssot.md`, `AGENTS.md` |
| **2-4** | **경미** | 새로 추가한 `scripts/log_attempt.py`가 `01-ssot.md §0` 보호 경로 표에서 누락됨 | **[반영 완료]** `01-ssot.md §0` 보호 정책 표에 `scripts/log_attempt.py` 추가 (보호 경로 총 15개) | `docs/harness/01-ssot.md` |
| **2-5** | **경미** | 문서 간 아키텍처 규칙 번호 불일치 (`A1~A6` / `A1~A4` 구버전 표기 잔존) | **[반영 완료]** 관련 문서 5곳을 `A1~A7` (`verify.py` 정적 스캔 `A1~A4, A7`)로 통일 | `01-ssot.md`, `04-decision.md`, `AGENTS.md`, `SKILL.md`, `llm-review-prompt.md` |

---

## Issue 2-1. `docs/05_roadmap.md` 소유권 명시 및 Phase 판정 무결성 보호 — **[반영 완료]**

### 1. 배경
- 현상: `docs/harness/01-ssot.md` §0 보호 정책 표에는 `docs/01~04`만 포함되어 있고 `docs/05_roadmap.md`가 빠져 있었다. 반면 `scripts/verify.py`는 `docs/05_roadmap.md`의 체크박스(`[ ]`)를 읽어 현재 Phase를 판정한다.
- 위험: AI가 `docs/05_roadmap.md`를 직접 수정할 수 있으면 체크박스 변경을 통해 `Bootstrap Phase 1` 예외나 `test_invariants.py` 필수 게이트가 의도치 않게 우회될 수 있었다.
- 관련 규칙: `SSOT §0` (작업 모드 · 보호 정책), `VER-3`, `DEC-4`

### 2. 적용한 해결 방법
- `docs/harness/01-ssot.md` §0 보호 정책 표에 `docs/05_roadmap.md`를 사람 소유(AI 읽기 전용 · 체크박스 갱신 제안)로 추가했다.
- 코드 구현·테스트(`src/`, `tests/`)는 AI가 자율적으로 수행하고, Phase 단위 완료 시에만 사람이 확인 후 `main`에서 체크박스를 `[x]`로 갱신한다(총 4회).

### 3. 종료 조건
- [x] C1. `docs/harness/01-ssot.md` §0 보호 정책 표에 `docs/05_roadmap.md`가 사람 소유 영역으로 명시되어 있다
- [x] C2. `scripts/verify.py`의 `_parse_protected_paths_from_ssot()` 결과에 `docs/05_roadmap.md`가 포함된다

---

## Issue 2-2. `A7` AST 검사에 내장 `open()` 텍스트 모드 `encoding` 검증 추가 — **[반영 완료]**

### 1. 배경
- 현상: `scripts/verify.py`의 `A7` AST 검사는 `Path.read_text()`와 `Path.write_text()`만 검사했다.
- 위험: `docs/04_cache_and_limit.md` §4의 Atomic Write(`.tmp` 쓰기 후 `os.replace()`)는 `with open(tmp_path, "w") as f:` 형태로 구현되는 경우가 많은데, `encoding="utf-8"`을 빠뜨려도 `A7`이 잡지 못해 Windows(`cp949`)에서 한글 깨짐·오류가 발생할 수 있었다.
- 관련 규칙: `ARCH-2`, `VER-1`, `docs/04_cache_and_limit.md` §4

### 2. 적용한 해결 방법
- `scripts/verify.py`에 `_is_binary_mode()`와 `_check_a7_encoding()`을 추가해 내장 `open()` 및 `Path.open()` 텍스트 모드 호출에 `encoding`이 없으면 `[A7]` 위반으로 차단하도록 확장했다(바이너리 모드 `"rb"`/`"wb"` 등은 자동 제외).
- `docs/harness/02-verification.md` §3 `A7` 설명에 `open()` · `Path.open()` 텍스트 모드 포함을 명시했다.

### 3. 종료 조건
- [x] C1. `src/`에서 `open("a.json", "w")`처럼 `encoding` 없는 텍스트 모드 `open()` 호출 시 `4/6 Architecture`가 `[A7]`로 실패한다
- [x] C2. `open("a.json", "w", encoding="utf-8")` 및 바이너리 모드 `open("a.bin", "wb")`는 정상 통과한다

---

## Issue 2-3. `Bootstrap` 모드 시도 상한 및 중단(`NEEDS_HUMAN`) 기록 규칙 명시 — **[반영 완료]**

### 1. 배경
- 현상: `Maintenance` 모드에서는 GitHub Issue 코멘트에 시도 횟수를 기록하고 상한(기본 3회)에 도달하면 멈춘다(`LOOP-3`, `LOOP-4`). 그러나 `Bootstrap` 모드에서는 GitHub Issue 없이 `05_roadmap.md` Phase 체크리스트로 작업할 수 있게 열었기 때문에, 연속 실패 시 멈춤 기준과 기록 위치가 정의되어 있지 않았다.
- 관련 규칙: `LOOP-3`, `DEC-1`, `docs/harness/01-ssot.md` §0 (작업 모드)

### 2. 적용한 해결 방법
- `docs/harness/01-ssot.md` §0 `작업 모드 — Bootstrap vs Maintenance` 표와 `AGENTS.md` §3에 Phase당 `python scripts/verify.py` 연속 실패 상한 기본 3회 및 초과 시 대화창 `NEEDS_HUMAN` 보고·중단 규칙을 추가했다.

### 3. 종료 조건
- [x] C1. `docs/harness/01-ssot.md` §0 `Bootstrap` 모드 표에 시도 상한(기본 3회)과 `NEEDS_HUMAN` 보고 방식이 명시되어 있다
- [x] C2. `AGENTS.md` §3 `Bootstrap` 진입 절차에도 동일 기준이 일관되게 반영되어 있다

---

## Issue 2-4. `scripts/log_attempt.py` 보호 경로 등록 — **[반영 완료]**

### 1. 배경
- 현상: Issue 5에서 `scripts/log_attempt.py`를 새로 추가했지만, `docs/harness/01-ssot.md` §0 보호 정책 표의 `검증 스크립트 · CI` 칸에는 `scripts/verify.py`, `.github/workflows/`만 적혀 있었다.
- 관련 규칙: `SSOT §0` (보호 정책)

### 2. 적용한 해결 방법
- `docs/harness/01-ssot.md` §0 보호 정책 표의 `검증 · 하네스 스크립트 · CI` 행에 `scripts/log_attempt.py`를 추가했다.

### 3. 종료 조건
- [x] C1. `scripts/verify.py`의 `_parse_protected_paths_from_ssot()` 결과에 `scripts/log_attempt.py`가 포함된다

---

## Issue 2-5. 문서 간 아키텍처 규칙 번호 통일 (`A1~A7`) — **[반영 완료]**

### 1. 배경
- 현상: Issue 6에서 `A7`(UTF-8 인코딩 명시 AST 검사)을 추가했으나, 기존 문서들에 옛날 번호(`A1~A6` 또는 `A1~A4`)가 남아 있어 문서 간 불일치가 발생했다.

### 2. 적용한 해결 방법
- `docs/harness/01-ssot.md`, `docs/harness/04-decision.md`, `AGENTS.md`, `.agents/skills/issue-loop/SKILL.md`, `.agents/skills/issue-loop/references/llm-review-prompt.md` 5개 파일의 아키텍처 규칙 번호 표기를 `A1~A7` (`verify.py` 정적 스캔 `A1~A4, A7`)로 통일했다.

### 3. 종료 조건
- [x] C1. `flight_finder_ans` 전체 문서에서 `A1~A6` 구버전 표기가 0건이다
- [x] C2. `verify.py` 정적 스캔 범위가 모든 문서에서 `A1~A4, A7`로 일치한다
