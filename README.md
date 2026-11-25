# Antigravity (Gemini) AI Harness Template

Antigravity(Gemini) 환경에서 AI 에이전트와 안전하고 일관되게 소프트웨어를 개발·유지보수하기 위한 **프로젝트 하네스 템플릿**입니다.
현재 예제 프로젝트 스펙으로 **Flight Finder**(자연어 기반 최저가 항공권 조회 웹 서비스) 설계 문서가 포함되어 있습니다.

> **규칙의 원본(SSOT)은 [docs/harness/01-ssot.md](docs/harness/01-ssot.md)입니다.** 이 README는 템플릿 안내 및 빠른 시작용 문서이며, 상세 규칙은 각 원본 문서를 따릅니다.

---

## 핵심 특징

- **단일 진실 공급원 (SSOT):** 요구사항(`REQ-*`) · 아키텍처(`ARCH-*`) · 검증(`VER-*`) · 충돌 정책 · 소유권 경계를 `docs/harness/01-ssot.md` 한 곳에서 관리합니다.
- **컨텍스트 라우팅:** `AGENTS.md` 라우터와 `.agents/rules/` 조건부 규칙으로 필요한 문서만 선택적으로 로드합니다.
- **2단계 작업 모드 (`Bootstrap` → `Maintenance`):** 초기 MVP 구축(`Bootstrap`)은 Phase 체크리스트로 빠르게 진행하고, 완성 후 `Maintenance`로 전환해 6항목 GitHub Issue 기반의 엄격한 유지보수 루프를 적용합니다.
- **로컬 = CI 단일 검증 관문:** `python scripts/verify.py` 한 명령으로 6단계(`Protected → Types → Lint/Format → Architecture → Test → Smoke`)를 로컬과 GitHub Actions CI에서 동일하게 실행합니다.

---

## 폴더 구조

```text
Template/
├── AGENTS.md                        # Antigravity 루트 진입점 (질문별 탐색 라우터)
├── .agents/
│   ├── rules/                       # Antigravity 조건부 자동 로드 규칙 [프로젝트별 교체]
│   └── skills/
│       └── issue-loop/              # GitHub Issue 처리 루프 스킬 & 독립 LLM 리뷰 프롬프트 [공통]
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   └── maintenance.yml          # 6항목 유지보수 작업 계약서 [공통]
│   └── workflows/
│       └── verify.yml               # GitHub Actions CI 워크플로 [공통]
├── docs/
│   ├── harness/                     # 하네스 핵심 규칙 4종 (SSOT · 검증 · 루프 · 사람 개입) [공통]
│   │   ├── 01-ssot.md               # (§1~§2는 프로젝트별 교체, §0·§3~§5는 공통)
│   │   ├── 02-verification.md
│   │   ├── 03-loop.md
│   │   └── 04-decision.md
│   ├── 01_architecture.md           # 프로젝트 상세 스펙 & 로드맵 [프로젝트별 교체]
│   ├── 02_llm_spec.md
│   ├── 03_api_and_byok.md
│   ├── 04_cache_and_limit.md
│   └── 05_roadmap.md
├── scripts/
│   ├── verify.py                    # 6단계 통합 검증 파이프라인 [공통 + 아키텍처 규칙 커스텀]
│   └── log_attempt.py               # GitHub Issue 시도 코멘트 양식 생성·등록 헬퍼 [공통]
├── issue.md                         # 하네스 1차 보완 이력 메모 (참고용)
└── issue2.md                        # 하네스 2차 교차 검증 이력 메모 (참고용)
```

---

## 새 프로젝트에서 이 템플릿 쓰는 법

### 1. 저장소 복제 및 초기 설정
1. GitHub에서 **Use this template**으로 새 저장소를 생성합니다. *(저장소 Settings → General → `Template repository` 활성화 필요)*
2. 로컬에 클론한 뒤 작성자 정보를 확인합니다.
   ```bash
   git config --local user.name "<본인 이름>"
   git config --local user.email "<본인 이메일>"
   ```

### 2. 새 프로젝트 스펙으로 교체
- `docs/01~05`의 예제(Flight Finder) 문서를 새 프로젝트 설계서와 MVP 로드맵으로 교체합니다.
- `docs/harness/01-ssot.md`의 **§1 요구사항(`REQ-*`) · §2 아키텍처(`ARCH-*`)**를 새 프로젝트 핵심 규칙으로 수정합니다.
- `.agents/rules/`의 조건부 규칙과 `scripts/verify.py`의 `check_architecture()` 규칙을 프로젝트 스택에 맞게 조정합니다.
- 불필요하다면 참고 메모(`issue.md`, `issue2.md`)는 삭제합니다.

### 3. `Bootstrap` 모드로 초기 MVP 구축 (Phase 1~4)
- `docs/harness/01-ssot.md` 상단이 `> 현재 모드: Bootstrap` 상태인지 확인합니다.
- Phase 단위로 구현을 진행하고, 각 Phase가 끝날 때마다 `python scripts/verify.py` 통과를 확인한 뒤 사람이 `main`에서 `docs/05_roadmap.md` 체크박스를 `[x]`로 갱신합니다.
- `Bootstrap` 모드에서도 Phase당 연속 실패 상한은 기본 3회이며, 초과 시 AI는 `NEEDS_HUMAN`을 보고하고 멈춥니다.

### 4. `Maintenance` 모드로 전환 (유지보수 시작)
- Phase 1~4 체크박스가 모두 완료되고 로컬 실테스트를 통과하면, 사람이 `docs/harness/01-ssot.md` 상단을 **`> 현재 모드: Maintenance`**로 변경해 `main`에 커밋합니다.
- 이후부터는 GitHub `Issues` 탭에서 **"유지보수 작업"** 템플릿으로 Issue를 생성하고 `issue-loop` 스킬로 작업합니다.
- 1인 운영 기준 보호 영역(`docs/`, `AGENTS.md`, `.agents/`, `scripts/`, `.github/workflows/` 등) 수정은 사람이 `main`에 직접 커밋하고, AI 작업 브랜치·PR은 `src/`와 `tests/`만 수정합니다.

---

## 자주 쓰는 명령어

```bash
# 1. 가상환경 생성 및 개발·검증 도구 설치 (Windows PowerShell 기준)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install ruff mypy pytest httpx
# requirements.txt 생성 후: pip install -r requirements.txt

# 2. 6단계 통합 검증 (로컬 = CI 동일)
python scripts/verify.py

# 3. GitHub Issue 시도 코멘트 생성 (미리보기 / --post 추가 시 실제 등록)
python scripts/log_attempt.py attempt --issue 1 --n 1 --m 3 --status 통과 \
  --base abc1234 --verify "로컬 통과" --done "src/main.py — 초기 구현"

# 4. 로컬 서버 실행 (Flight Finder 예제 기준)
uvicorn src.main:app --reload
```

---

## 핵심 문서 바로가기

| 문서 | 역할 |
| :--- | :--- |
| [AGENTS.md](AGENTS.md) | 모든 작업의 시작점 (질문별 1차·2차·3차 탐색 라우터) |
| [docs/harness/01-ssot.md](docs/harness/01-ssot.md) | 프로젝트 규칙 원본 (모드 · 충돌 정책 · 보호 정책 · `REQ-*` · `ARCH-*`) |
| [docs/harness/02-verification.md](docs/harness/02-verification.md) | 3층 검증 체계 및 `verify.py` 6단계 파이프라인 상세 |
| [docs/harness/03-loop.md](docs/harness/03-loop.md) | 시도 횟수 · 세션 복구 · Issue 코멘트 양식 · PR/CI 연동 |
| [docs/harness/04-decision.md](docs/harness/04-decision.md) | `NEEDS_HUMAN` 사유 · 사람 결정 4갈래 · 독립 LLM 리뷰 자문 |
| [docs/05_roadmap.md](docs/05_roadmap.md) | MVP Phase 1~4 체크리스트 |
