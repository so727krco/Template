# AGENTS.md — Flight Finder 진입점

이 파일이 모든 작업의 시작점이다. **이 파일은 규칙의 원본이 아니라 라우터다.**
**문서를 한꺼번에 읽지 않는다.** 질문 유형을 아래 표에서 고르고, 1차 문서의 **해당 절만** 읽는다. 거기서 판단할 수 없을 때만 한 단계씩 넓힌다.

규칙의 원본은 [docs/harness/01-ssot.md](docs/harness/01-ssot.md)(이하 SSOT)다.
**파일을 수정하는 작업이면 SSOT §0(충돌 정책 · 보호 정책)을 먼저 읽는다.**

---

## 1. 라우팅

| 질문 유형 | 1차 | 2차 (판단 안 될 때) | 3차 |
| :--- | :--- | :--- | :--- |
| 충돌 · 권한 — "이거 고쳐도 돼?", 문서끼리 다름 | SSOT §0 | `docs/harness/04-decision.md` §1 (`DEC-1` · `DEC-2`) | — (넓히지 않고 `NEEDS_HUMAN` 선언) |
| 작업 모드 · 현재 Phase — "지금 Bootstrap이야?", "어떤 Phase야?" | SSOT §0 (작업 모드) · `docs/05_roadmap.md` | — | — (선행 Phase 미완료 상태에서 이후 Phase 요청 시 `NEEDS_HUMAN`) |
| 사람의 개입 — 승인 · 반려 · `NEEDS_HUMAN` · 완료 판정 · merge | `docs/harness/04-decision.md` 해당 절 (§1 `DEC-*` · §2 경계 · §3 코멘트·LLM 리뷰) | SSOT §0 (소유권) · §5 | `docs/harness/03-loop.md` §1 (시도 카운트) |
| 기능 요구 · 범위 — "이 기능 해야 해?", "범위 밖이야?" | SSOT §1 (`REQ-*`) | `docs/05_roadmap.md` · 해당 GitHub Issue (`gh issue view <N>`) | `docs/01_architecture.md` §1~§2 |
| LLM 자연어 파싱 · IATA 매핑 · 브리핑 | SSOT §1 (`REQ-1` · `REQ-2`) · `.agents/rules/llm-parsing.md` | `docs/02_llm_spec.md` 해당 절 | `src/schemas/` · `src/services/llm.py` |
| API 명세 · Stateless BYOK · 커스텀 에러 · `localStorage` | SSOT §1 (`REQ-3` · `REQ-7`) · §2 (`ARCH-4`) · `.agents/rules/api-byok.md` | `docs/03_api_and_byok.md` 해당 절 | `src/api/` · `src/services/flight.py` · `src/static/` |
| 초대 코드 · 일일 횟수 제한 · 파일 캐시(TTL vs 365일 삭제) · 동시성 | SSOT §1 (`REQ-4`~`REQ-6`) · §2 (`ARCH-2` · `ARCH-5`) · `.agents/rules/cache-limit.md` | `docs/04_cache_and_limit.md` 해당 절 | `src/services/cache.py` · `src/services/limiter.py` |
| 구조 · 기술 스택 · 디렉토리 · 환경 변수 | SSOT §2 (`ARCH-*`) | `docs/01_architecture.md` 해당 절 | `.env.example` · `src/config.py` · `src/main.py` |
| 검증 · 테스트 · 완료 기준 | SSOT §3 (`VER-*`) | `docs/harness/02-verification.md` 해당 절 (§2 파이프라인 · §3 아키텍처 규칙 `A1~A7` · §5 빈틈) | `scripts/verify.py` · `tests/` |
| 루프 · 시도 횟수 · 세션 복구 — "몇 번까지 해?", "이어서 하려면?" | `docs/harness/03-loop.md` 해당 절 (§1 `LOOP-*` · §3 기록 양식 · §4 복구 · §5 PR·CI) | 해당 Issue의 코멘트 이력 (시도 횟수의 원본) | SSOT §4 (검증과의 경계) · `04-decision.md` |
| 실행 명령어 · 로컬 구동 · 개발 단계 | `docs/05_roadmap.md` | `docs/01_architecture.md` · `requirements.txt` | — |

---

## 2. 탐색 범위를 넓히는 규칙

1. 1차 문서에서 답이 나오면 **거기서 멈춘다.**
2. 넓힐 때는 표의 **다음 칸 하나씩**만 넓힌다. 원문은 파일 전체가 아니라 해당 절만 읽는다.
3. 표에 없는 질문은 SSOT §1 · §2에서 시작해 가장 가까운 행을 따른다.
4. 3차까지 봐도 판단할 수 없으면 추측하지 않고 `NEEDS_HUMAN`을 선언한다. SSOT의 **미정** 항목이면 "미정"이라고 답한다.
5. 읽은 문서끼리 또는 문서와 코드가 다르면 SSOT §0 충돌 정책을 따르고, 거기 없는 경우는 `NEEDS_HUMAN`을 선언한다.
6. 답할 때는 근거로 삼은 문서와 절을 밝힌다.

---

## 3. 작업 진입 절차 — 모드 확인 후 진행

코드 구현 요청을 받으면 **먼저 [docs/harness/01-ssot.md](docs/harness/01-ssot.md) 상단의 `현재 모드`를 확인한다.**

1. **`Bootstrap` 모드일 때:**
   - [docs/05_roadmap.md](docs/05_roadmap.md)에서 미완료(`[ ]`)가 남아 있는 **가장 앞선 Phase**를 현재 Phase로 확정한다.
   - 사용자의 요청이 현재 Phase와 일치하는지 대조한다(선행 Phase가 미완료인데 이후 Phase를 요청하면 임의로 건너뛰지 않고 `NEEDS_HUMAN`으로 확인).
   - Phase 단위로 구현하고, 완료 시 `python scripts/verify.py` 통과 후 사람에게 확인을 받는다. Phase당 `verify.py` 연속 실패 상한은 기본 3회이며, 초과 시 대화창에 `NEEDS_HUMAN`을 보고하고 중단한다.
2. **`Maintenance` 모드일 때 (또는 GitHub Issue 작업을 명시한 경우):**
   - **새 Issue를 시작할 때는 새 채팅창(새 세션)에서 시작하는 것을 권장한다** (이전 대화 맥락 섞임 방지 · 상태 원본은 Issue 코멘트 `LOOP-4`).
   - Issue 초안 작성이 필요하면 `.agents/skills/issue-loop/references/issue-draft-template.md`를 참고해 6항목 초안을 작성한다.
   - `이슈 처리해줘` · `12번 이슈 해줘` · `이어서 진행해줘` 처럼 Issue 작업을 요청받으면, 구현에 들어가기 전에 **`issue-loop` 스킬을 쓸지 사람에게 먼저 묻는다.** (이미 스킬 호출을 명시한 경우는 생략)

| 답 | 진행 |
| :--- | :--- |
| 쓴다 | `.agents/skills/issue-loop/SKILL.md` 절차대로 끝까지 돈다 — 브랜치 · 테스트/구현 · `python scripts/verify.py` · Issue 코멘트 · 커밋 · 푸시 · PR · CI 폴링 · LLM 리뷰 · 사람 차례 |
| 쓰지 않는다 | 스킬 없이 이 파일과 `docs/harness/` 규칙대로 수동 진행한다. 커밋 · 푸시 · PR은 따로 요청받았을 때만 한다 |

이 질문은 작업당 **한 번만** 한다.

---

## 4. 이 파일에 대하여

- Antigravity는 프로젝트 루트의 `AGENTS.md`를 진입점으로 자동 로드한다.
- 작업 성격에 따라 `.agents/rules/`의 조건부 규칙과 `.agents/skills/`의 스킬이 자동 탐색된다.
