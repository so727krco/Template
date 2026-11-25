---
name: issue-loop
description: GitHub Issue 하나를 하네스 규칙대로 끝까지 처리한다 — 브랜치 생성 → 테스트·구현 → `python scripts/verify.py` → 시도 코멘트 → 커밋·푸시·PR → `gh`로 CI 폴링 → LLM 리뷰 코멘트 → 「사람 차례」로 넘김. "이슈 처리해줘", "이슈 12번 해줘", "#3 작업 시작", "이어서 해줘", "이슈 이어서 진행", "PR 올려줘", "CI 끝나면 리뷰 달아줘", "issue 처리" 같은 말이 나오면 이슈 번호를 대지 않았거나 재개·복구 상황이어도 반드시 이 스킬을 쓴다. 이 저장소에서 Issue 기반 작업을 하는 유일한 경로이며, `docs/harness/`의 LOOP-1~25 · DEC-1~10 · VER-1~5를 지키는 절차가 여기에 있다. 이슈와 무관한 단순 질문·탐색에는 쓰지 않는다.
---

# 이슈 처리 루프 (Flight Finder)

Issue 하나를 받아 **기계 구간이 할 수 있는 데까지 전부 밀고**, 사람이 승인 · 반려를 판단할 수 있는
자리에 정확히 세워 두고 끝난다. 사람 대신 판단하지 않는 것이 이 스킬의 값어치다.

```text
Issue 확정 → 계약 확인 → 세션 복구 → 브랜치
  → [시도] 테스트·구현 → python scripts/verify.py → 시도 코멘트   ← 실패하면 상한까지 반복
  → 커밋 · 푸시 · PR → CI 폴링(re-run 1회) → LLM 리뷰 코멘트
  → 「사람 차례」 코멘트 → 멈춤
```

**규칙의 원본은 `docs/harness/`다.** 이 문서와 다르면 그쪽이 맞다.
헷갈리면 `03-loop.md`(시도 · 기록) · `04-decision.md`(사람 · 리뷰) · `01-ssot.md` §0(소유권)의 해당 절만 읽는다.

**한 번 호출 = Issue 하나.** 여러 이슈를 동시에 잡지 않는다 — 시도 번호가 겹친다 (`03-loop.md` §6).

---

## 0. 시작 전 확인

```bash
gh auth status                    # 인증 안 되면 여기서 멈추고 사람에게 알린다
git status --short                # 작업 트리가 더러우면 사람에게 물어본다 (남의 작업일 수 있다)
git fetch origin && git log --oneline -1 origin/main
python --version                  # Python 3.12+ 확인
```

마지막 `gh issue view <N> --comments`에서 `진행 중` 코멘트가 닫히지 않은 채 남아 있으면 **시작하지 않고** 사람에게 확인한다 (`LOOP-21`).

작업 트리에 손대지 않은 변경이 남아 있으면 **치우지 말고 물어본다.** 기록에 없는 시도의 흔적일 수 있고,
그건 `DEC-1` ⑤(기록과 실제 상태가 어긋남)에 해당한다.

---

## 1. 대상 Issue 확정

번호를 들었으면 그 번호다. 못 들었으면:

```bash
gh issue list --state open
```

열린 이슈가 하나면 그것으로 진행하되 **무엇을 잡았는지 먼저 한 줄 말한다.**
여럿이면 목록을 보여주고 고르게 한다. 열린 이슈가 없으면 그 사실을 알리고 끝낸다.

---

## 2. Issue 읽기 — 계약 확인

```bash
gh issue view <N>                 # 본문: 6개 항목
```

Issue는 **그 작업의 SSOT**다 (SSOT §0 Issue 절). 대화 · 로드맵(`docs/05_roadmap.md`)에 다른 말이 있어도 Issue를 따른다.
본문에서 이 여섯 개를 뽑아 적어 둔다.

| 항목 | 쓰임 |
| :--- | :--- |
| 1 배경 | 왜 하는가 |
| 2 변경할 내용 | 손댈 파일 · 모듈의 범위 |
| 3 종료 조건 | C1 · C2 … 와 `(수동)` 표시 |
| 4-1 테스트 기능명 | 브랜치 이름과 테스트 파일 이름이 여기서 나온다 |
| 4-2 기계 검증 | 조건 ↔ `test_c{번호}_...` 매핑 |
| 5 건드리면 안 되는 것 | 보호 영역 (기본 + 이 작업 추가분) |
| 6 최대 횟수 | 시도 상한 M |

**6개 항목이 비었거나 종료 조건을 참 · 거짓으로 판정할 수 없으면 추측으로 채우지 않는다** (`DEC-1` ③).
`중단(NEEDS_HUMAN)` 코멘트를 달고 멈춘다 — 이것도 시도 1회다 (`LOOP-6`).

---

## 3. 세션 복구 — 지금 누구 차례이고 몇 회차인가

```bash
gh issue view <N> --comments      # 뒤에서부터 읽는다
```

**시도 횟수의 원본은 Issue 코멘트뿐이다** (`LOOP-4`).
`사람 판단 · 판단 확정` 코멘트가 있으면 **그 뒤의 시도만** 센다 (`LOOP-7`). 코멘트가 없으면 0회.

마지막 코멘트로 턴을 판정한다 (`03-loop.md` §4 표).

| 마지막 코멘트 | 턴 | 다음 |
| :--- | :--- | :--- |
| 없음 · `시도 N/M · 실패` · `복귀` · `사람 판단 · 반려` | AI | 남은 시도 확인 후 §5 |
| `사람 판단 · 판단 확정` | AI | 시도 0/M 으로 초기화하고 §5 (`LOOP-25` 확인) |
| `시도 N/M · 통과` | AI | 이미 통과했으면 §7(커밋 · PR)부터 |
| `진행 중 · 세션 …` (닫는 코멘트 없음) | **사람** | 시작하지 않고 사람에게 확인 (`LOOP-21`) |
| `보류 · 커밋` | **사람** | 커밋 · 푸시 · PR을 하지 않는다 (`LOOP-20`) |
| `사람 차례` · `사람 판단 · 승인` · `사람 판단 · 요구사항 변경` · `중단(…)` · `종료(…)` | **사람** | **손대지 않는다** |

턴이 사람이면 무엇을 기다리는 중인지 한 줄로 보고하고 끝낸다.
남은 시도 = M − N. **0이면 새 시도를 시작하지 않고** `중단(상한 소진)`으로 사람에게 넘긴다 (`LOOP-3`).
이어서 할 때 `python scripts/verify.py`를 **먼저 돌려보지 않는다.** 그 자체로 한 시도를 쓴다 (`LOOP-1`).

---

## 4. 브랜치

`main`에서 딴다. 이름은 Issue 4-1의 기능명을 kebab-case로 바꿔 쓴다.

```bash
git checkout main && git pull --ff-only
git checkout -b feat/issue-<N>-<기능명>      # 이미 있으면 checkout 만
```

문서만 고치는 이슈면 `docs/…`, 버그 수정이면 `fix/…`로 접두사를 바꾼다.

---

## 5. 기계 구간 — 한 시도

**시도 1회 = 구현부터 `python scripts/verify.py` 실행까지다** (`LOOP-1`). `verify.py` 이전의 수정(타입 오류 정정 · `ruff` 포맷 · 개별 `pytest` 확인)은 전부 같은 시도 안이다.

1. **종료 조건 → 테스트 작성**
   `tests/issues/test_issue_<N>_<기능명>.py`에 자동 검증 조건마다 `test_c1_...`, `test_c2_...` 테스트 함수를 작성한다.
   - `(수동)`이 붙은 조건은 자동 테스트하지 않는다 — 사람이 브라우저에서 확인한다.
   - **실제 Gemini / SerpApi를 호출하지 않고 반드시 Mock 응답을 사용한다** (`ARCH-6`).
   - 파일 캐시 · 횟수 제한 테스트는 `tmp_path` · `monkeypatch`로 격리해 실제 `data/` 폴더를 건드리지 않는다.

2. **변경 전 코드에서 실패하는 것을 확인** (Issue 4-2 체크 항목)
   ```bash
   git stash push -- src/
   python -m pytest tests/issues/test_issue_<N>_<기능명>.py
   git stash pop
   ```
   실패하지 않는 테스트는 아무것도 지키지 못한다.

3. **구현**
   Issue 2번 범위 안에서만 고친다. **Issue에 없는 변경은 하지 않는다.**
   아키텍처 규칙 `A1~A7` (`requests` 금지 · 크롤링 금지 · `request.headers`/`X-Flight-Api-Key` 로깅/출력 금지 · `asyncio.Lock` + Atomic Write · Mock 우선 · 텍스트 I/O `encoding="utf-8"`)과 타입 힌트를 지킨다.

4. **`python scripts/verify.py`** — 한 번. 여기서 이 시도는 끝난다.
   ```bash
   python scripts/verify.py    # Protected → Types → Lint/Format → Architecture → Test → Smoke
   ```
   실패하면 **멈춘 단계를 적어 둔다.**

5. **시도 코멘트를 즉시 단다** (§6). 통과든 실패든 예외 없다 (`LOOP-5`).

실패했고 시도가 남아 있으면 1~5를 다시 돈다. 상한을 다 쓰면 `중단(상한 소진)`으로 사람에게 넘긴다.

---

## 6. 시도 코멘트

양식 오타를 막기 위해 `scripts/log_attempt.py` 헬퍼 사용을 권장한다 (`--post` 생략 시 미리보기).

```bash
python scripts/log_attempt.py attempt --issue <N> --n <시도> --m <상한> --status <통과|실패|중단(NEEDS_HUMAN)|중단(상한 소진)> \
  --base <sha|uncommitted> --verify "<결과>" --done "<파일 — 한 일>" --post
```

직접 올릴 때는 `gh issue comment <N> --body-file <파일>`을 쓰며, 양식은 `docs/harness/03-loop.md` §3 그대로다. AI가 채운다 (`DEC-7`).

```markdown
### 시도 N/M · 통과 | 실패 | 중단(NEEDS_HUMAN) | 중단(상한 소진)
- 기준: <커밋 sha | uncommitted | PR #N · sha>
- verify: 로컬 통과 · CI 통과 | 실패(<멈춘 단계>) | 실행 안 함
- 한 일:
  - <파일 경로> — <무엇을 왜>
- 사람 판단이 필요한 것: 없음 | <내가 스스로 정한 것까지 전부>
- 다음 시도에서 할 것: 없음(종료) | <내용>
```

---

## 7. 통과 후 — 커밋 · 푸시 · PR

로컬 `python scripts/verify.py`가 통과한 뒤에만 연다 (`03-loop.md` §5).
사람 지시에 "커밋 · 푸시 하지 마"(보류)가 있으면 이 절을 건너뛰고 `보류 · 커밋` 코멘트를 남긴다 (`LOOP-20`).

```bash
git add <변경한 파일들> && git commit
git push -u origin <브랜치>
gh pr create --title "<제목>" --body "$(cat <<'EOF'
Closes #<N>

시도 기록은 그 Issue 코멘트에 있다.
EOF
)"
```

---

## 8. CI 폴링

같은 커밋이면 로컬 `verify.py`와 CI `verify`는 **한 시도**다 (`LOOP-11`).

```bash
gh pr checks --watch
```

| 결과 | 처리 | 카운트 |
| :--- | :--- | :--- |
| 통과 | §9 LLM 리뷰로 | ⊕0 |
| 실패 | **같은 커밋 그대로 re-run 1회** → `gh run rerun <run-id> --failed` | — |
| re-run 통과 | 환경 문제. 시도 코멘트에 `CI 통과(re-run)` 보탬 | ⊕0 |
| re-run 재실패 | 코드 문제. `복귀` 코멘트 후 §5 복귀 | **⊕1** |

---

## 9. LLM 리뷰 — CI 통과 뒤의 자문

CI 통과 후 **구현 대화 맥락이 없는 독립 서브에이전트**를 띄워 Issue 계약을 심사한다 (`DEC-10`).
프롬프트 전문은 `references/llm-review-prompt.md`에 있다 — 리뷰를 돌릴 때 읽는다.

결과는 PR 코멘트로 단다 (`gh pr comment <PR번호> --body-file <파일>`).
**합격 · 불합격을 쓰지 않는다.** 첫 줄에 `## LLM 리뷰`를 반드시 박는다.

---

## 10. 사람 차례로 넘기고 멈춘다

```markdown
### 사람 차례 · PR #<번호>
- 기준: <sha> · 시도 N/M 까지 씀
- 사람이 할 것:
  - (수동) 종료 조건 <C번호> — <브라우저에서 무엇을 확인하면 되는지>
  - 리뷰 · CI 확인 후 merge · 승인 (`DEC-4`)
```

여기서 **끝난다.** merge도 승인도 하지 않는다 (`DEC-5`).

사람이 답하면 네 갈래(**승인 · 반려 · 판단 확정 · 요구사항 변경**)로 분류해 `사람 판단` 코멘트로 옮겨 적고 (`04-decision.md` §3) 그에 따라 처리한다.

---

## 절대 하지 않는 것

- **Issue 본문 수정** — 코멘트로 제안만 한다 (SSOT §0)
- **보호 영역 수정** — `docs/harness/` · `AGENTS.md` · `.agents/rules/` · `.agents/skills/` · `docs/01~05` · `scripts/verify.py` · `scripts/log_attempt.py` · `.github/workflows/` · `.env` · `requirements.txt` (승인 없이 수정 금지)
- **검증 우회** — `verify.py` 완화, `# type: ignore` / `# noqa` 남발, 기존 테스트 기대값 임의 수정 금지 (`VER-3` · `VER-4`)
- **merge · 완료 선언 · 승인** — 사람 몫이다 (`DEC-4` · `DEC-5`)
- **Issue 범위 밖의 개선** — 새 Issue로 제안만 한다
