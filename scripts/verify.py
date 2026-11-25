"""Flight Finder 6단계 통합 검증 파이프라인.

실행: python scripts/verify.py
단계: Protected -> Types -> Lint/Format -> Architecture -> Test -> Smoke
규칙 원본: docs/harness/01-ssot.md (§0 · §3), docs/harness/02-verification.md
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
SSOT_PATH = ROOT_DIR / "docs" / "harness" / "01-ssot.md"
ROADMAP_PATH = ROOT_DIR / "docs" / "05_roadmap.md"
AI_MAY_WRITE_RE = re.compile(r"수정|작성")
BOOTSTRAP_PHASE1_CREATE_ALLOWLIST = {"requirements.txt", ".env.example"}


def run_cmd(
    step_name: str,
    cmd: list[str],
    extra_env: dict[str, str] | None = None,
) -> None:
    """외부 명령어를 실행하고 실패 시 즉시 종료한다."""
    print(f"\n[{step_name}] RUN: {' '.join(cmd)}")
    env = os.environ.copy()
    if extra_env:
        for key, value in extra_env.items():
            env.setdefault(key, value)

    result = subprocess.run(cmd, cwd=ROOT_DIR, env=env, check=False)
    if result.returncode != 0:
        print(f"[FAIL] [{step_name}] exit code: {result.returncode}")
        sys.exit(result.returncode)
    print(f"[PASS] [{step_name}]")


def _git(args: list[str]) -> str:
    """Git 명령을 실행하고 stdout을 반환한다."""
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _parse_current_mode_from_ssot() -> str:
    """docs/harness/01-ssot.md 상단에서 현재 모드(Bootstrap | Maintenance)를 읽는다."""
    if not SSOT_PATH.exists():
        return "Maintenance"
    text = SSOT_PATH.read_text(encoding="utf-8")
    match = re.search(
        r"^>\s*현재 모드:\s*(Bootstrap|Maintenance)\b", text, re.MULTILINE
    )
    return match.group(1) if match else "Maintenance"


def _detect_current_phase_from_roadmap() -> int | None:
    """docs/05_roadmap.md에서 미완료('[ ]')가 남은 가장 앞선 Phase 번호를 반환한다."""
    if not ROADMAP_PATH.exists():
        return None
    current_phase: int | None = None
    for line in ROADMAP_PATH.read_text(encoding="utf-8").splitlines():
        phase_match = re.match(r"^##\s+Phase\s+(\d+)\b", line.strip())
        if phase_match:
            current_phase = int(phase_match.group(1))
            continue
        if current_phase is not None and re.match(r"^-\s+\[\s\]\s+", line.strip()):
            return current_phase
    return None


def _exists_in_commit(commit: str, file_path: str) -> bool:
    """특정 커밋에 해당 파일이 이미 존재했는지 확인한다."""
    normalized = file_path.replace("\\", "/")
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}:{normalized}"],
        cwd=ROOT_DIR,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _parse_protected_paths_from_ssot() -> list[tuple[str, str]]:
    """docs/harness/01-ssot.md의 보호 정책 표에서 사람 소유 보호 경로를 추출한다."""
    if not SSOT_PATH.exists():
        return []

    text = SSOT_PATH.read_text(encoding="utf-8")
    marker = "### 보호 정책"
    start = text.find(marker)
    if start == -1:
        return []
    rest = text[start:]
    next_section = rest.find("\n---")
    section = rest if next_section == -1 else rest[:next_section]

    protected: list[tuple[str, str]] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) != 4:
            continue
        area, target, ai_perm, _human_perm = cells
        if area in ("영역", ":---") or area.startswith("---"):
            continue
        if AI_MAY_WRITE_RE.search(ai_perm):
            continue
        for match in re.finditer(r"`([^`]+)`", target):
            protected.append((match.group(1), area))
    return protected


def _covers(rule: str, file_path: str) -> bool:
    """보호 경로 규칙(파일 또는 디렉토리)이 대상 파일을 덮는지 판정한다."""
    normalized = file_path.replace("\\", "/")
    if rule.endswith("/"):
        return normalized.startswith(rule)
    return normalized == rule or normalized.startswith(rule + "/")


def _resolve_base_commit() -> tuple[str, str] | None:
    """비교 기준 브랜치(VERIFY_BASE -> GITHUB_BASE_REF -> origin/main -> main)의 merge-base를 찾는다."""
    candidates: list[str] = []
    if env_base := os.environ.get("VERIFY_BASE"):
        candidates.append(env_base)
    if gh_base := os.environ.get("GITHUB_BASE_REF"):
        candidates.append(f"origin/{gh_base}")
    candidates.extend(["origin/main", "main"])

    for ref in candidates:
        try:
            _git(["rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"])
            merge_base = _git(["merge-base", "HEAD", ref])
            return ref, merge_base
        except subprocess.CalledProcessError:
            continue
    return None


def check_protected() -> None:
    """1단계: 금지 파일 Git 추적 여부 + SSOT §0 사람 소유 보호 경로 변경 여부를 검사한다."""
    print("\n[1/6 Protected] Checking forbidden tracked files & SSOT protected paths")
    if not (ROOT_DIR / ".git").exists():
        print("[WARN] Git repository not initialized; skipping Protected check.")
        return

    # 1-1. .env 및 data/ 런타임 파일 추적 금지
    tracked_files = _git(["ls-files"]).splitlines()
    forbidden_tracked = [
        f
        for f in tracked_files
        if f == ".env" or f.startswith(("data/cache/", "data/limits/"))
    ]
    if forbidden_tracked:
        print("[FAIL] [1/6 Protected] Tracked forbidden files detected:")
        for f in forbidden_tracked:
            print(f"  - {f}")
        sys.exit(1)

    # 1-2. SSOT §0 보호 정책(사람 소유 경로) 변경 검사
    mode = _parse_current_mode_from_ssot()
    phase = _detect_current_phase_from_roadmap() if mode == "Bootstrap" else None
    mode_label = (
        f"{mode} (Phase {phase})" if mode == "Bootstrap" and phase is not None else mode
    )
    print(f"  Mode: {mode_label}")

    protected_rules = _parse_protected_paths_from_ssot()
    base = _resolve_base_commit()
    if protected_rules and base:
        base_ref, merge_base = base
        diff_files = _git(
            ["diff", "--name-only", "--no-renames", merge_base]
        ).splitlines()
        untracked = _git(["ls-files", "--others", "--exclude-standard"]).splitlines()
        changed = sorted({f for f in [*diff_files, *untracked] if f})

        violations: list[tuple[str, str, str]] = []
        for file_path in changed:
            normalized = file_path.replace("\\", "/")
            # Bootstrap Phase 1에 한해 기존에 없던 requirements.txt / .env.example 최초 생성만 허용
            if (
                mode == "Bootstrap"
                and phase == 1
                and normalized in BOOTSTRAP_PHASE1_CREATE_ALLOWLIST
                and not _exists_in_commit(merge_base, normalized)
            ):
                print(f"  [ALLOW] {normalized} (Bootstrap Phase 1 최초 생성 예외)")
                continue

            for rule, area in protected_rules:
                if _covers(rule, normalized):
                    violations.append((normalized, area, rule))
                    break

        if violations:
            print(
                f"[FAIL] [1/6 Protected] Human-owned protected paths modified "
                f"(base: {base_ref} @ {merge_base[:7]}, mode: {mode_label}):"
            )
            for file_path, area, rule in violations:
                print(f"  - {file_path}  ({area}: {rule})")
            print(
                "  SSOT §0 보호 정책에 따라 AI는 이 영역을 직접 수정할 수 없습니다. "
                "변경안을 제시하고 사람의 승인을 받으세요."
            )
            sys.exit(1)
    else:
        print(
            "[WARN] Base branch (origin/main or main) not found; skipping protected-path diff."
        )

    print("[PASS] [1/6 Protected]")


def _is_binary_mode(node: ast.Call, mode_pos_index: int) -> bool:
    """open() / Path.open() 호출의 mode 인자가 바이너리 모드('b' 포함)인지 판별한다."""
    mode_arg: ast.expr | None = None
    if len(node.args) > mode_pos_index:
        mode_arg = node.args[mode_pos_index]
    else:
        for kw in node.keywords:
            if kw.arg == "mode":
                mode_arg = kw.value
                break
    return (
        isinstance(mode_arg, ast.Constant)
        and isinstance(mode_arg.value, str)
        and "b" in mode_arg.value
    )


def _check_a7_encoding(tree: ast.AST, rel_path: Path) -> list[str]:
    """A7: read_text/write_text/open/Path.open 텍스트 모드 호출 시 encoding 명시를 검사한다."""
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        has_encoding_kw = any(kw.arg == "encoding" for kw in node.keywords)

        # Path.read_text() / Path.write_text()
        if isinstance(node.func, ast.Attribute) and node.func.attr in (
            "read_text",
            "write_text",
        ):
            if not has_encoding_kw:
                violations.append(
                    f"[A7] {rel_path}:{node.lineno} -> "
                    f"'{node.func.attr}()' must specify encoding='utf-8' (Windows/Ubuntu safety)"
                )
        # 내장 open(file, mode=...)
        elif isinstance(node.func, ast.Name) and node.func.id == "open":
            if not _is_binary_mode(node, mode_pos_index=1) and not (
                has_encoding_kw or len(node.args) >= 4
            ):
                violations.append(
                    f"[A7] {rel_path}:{node.lineno} -> "
                    "'open()' in text mode must specify encoding='utf-8' (Windows/Ubuntu safety)"
                )
        # Path.open(mode=...)
        elif (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "open"
            and not _is_binary_mode(node, mode_pos_index=0)
            and not (has_encoding_kw or len(node.args) >= 3)
        ):
            violations.append(
                f"[A7] {rel_path}:{node.lineno} -> "
                "'Path.open()' in text mode must specify encoding='utf-8' (Windows/Ubuntu safety)"
            )
    return violations


def check_architecture() -> None:
    """4단계: 아키텍처 규칙 A1~A4 및 A7(UTF-8 인코딩 명시) 위반을 스캔한다."""
    print("\n[4/6 Architecture] Scanning architecture & security rules (A1~A4, A7)")
    if not SRC_DIR.exists():
        print("[WARN] src/ directory not found; skipping Architecture check.")
        return

    forbidden_patterns: list[tuple[str, str, str]] = [
        (
            "A1",
            r"^\s*(import|from)\s+requests\b",
            "Blocking 'requests' is forbidden (use httpx.AsyncClient — ARCH-3)",
        ),
        (
            "A2",
            r"^\s*(import|from)\s+(bs4|selenium|playwright|scrapy)\b",
            "Crawling libraries are forbidden (REQ-8)",
        ),
        (
            "A3",
            r"(logger|logging)\.\w+\(.*(request\.headers|X-Flight-Api-Key)",
            "Security violation: logging request headers or user API key is forbidden (ARCH-4)",
        ),
        (
            "A4",
            r"\bprint\(.*(request\.headers|X-Flight-Api-Key)",
            "Security violation: printing request headers or user API key is forbidden (ARCH-4)",
        ),
    ]

    violations: list[str] = []
    for py_file in SRC_DIR.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        rel_path = py_file.relative_to(ROOT_DIR)
        for line_no, line in enumerate(content.splitlines(), start=1):
            for rule_id, pattern, reason in forbidden_patterns:
                if re.search(pattern, line):
                    violations.append(f"[{rule_id}] {rel_path}:{line_no} -> {reason}")

        # A7: 텍스트 파일 I/O(read_text/write_text/open) 시 encoding 명시 확인 (AST 기반)
        try:
            tree = ast.parse(content, filename=str(rel_path))
        except SyntaxError:
            continue
        violations.extend(_check_a7_encoding(tree, rel_path))

    if violations:
        print("[FAIL] [4/6 Architecture] Rule violations detected:")
        for v in violations:
            print(f"  - {v}")
        sys.exit(1)
    print("[PASS] [4/6 Architecture]")


def check_test_prerequisites(tests_dir: Path) -> None:
    """5단계 사전 게이트: 테스트 격리(conftest.py) 및 Phase 3 이후 공통 불변식(test_invariants.py) 존재를 검증한다."""
    conftest_path = tests_dir / "conftest.py"
    if not conftest_path.exists():
        print(
            "[FAIL] [5/6 Test] tests/conftest.py is required before running pytest "
            "(must block real external network calls with an autouse=True fixture — ARCH-6)."
        )
        sys.exit(1)

    conftest_text = conftest_path.read_text(encoding="utf-8")
    if not re.search(r"autouse\s*=\s*True", conftest_text):
        print(
            "[FAIL] [5/6 Test] tests/conftest.py must define an autouse=True fixture "
            "to block real external API calls during tests (ARCH-6)."
        )
        sys.exit(1)

    mode = _parse_current_mode_from_ssot()
    phase = _detect_current_phase_from_roadmap() if mode == "Bootstrap" else None
    require_invariants = mode == "Maintenance" or (
        mode == "Bootstrap" and (phase is None or phase >= 4)
    )
    invariants_path = tests_dir / "test_invariants.py"
    if require_invariants and not invariants_path.exists():
        print(
            "[FAIL] [5/6 Test] tests/test_invariants.py is required from Phase 4 / Maintenance "
            "(BYOK non-leakage ARCH-4, SerpApi <= 4 calls REQ-2, concurrent write safety ARCH-2)."
        )
        sys.exit(1)

    if (SRC_DIR / "static" / "app.js").exists() and not (
        tests_dir / "test_static_contract.py"
    ).exists():
        print(
            "[FAIL] [5/6 Test] tests/test_static_contract.py is required when src/static/app.js exists "
            "(must verify static serving, headers, localStorage keys, and API paths)."
        )
        sys.exit(1)


def main() -> None:
    py = sys.executable

    # 1. Protected
    check_protected()

    # 2. Types (mypy)
    if SRC_DIR.exists():
        run_cmd("2/6 Types", [py, "-m", "mypy", "--ignore-missing-imports", "src"])
    else:
        print("\n[WARN] [2/6 Types] src/ directory not found; skipping.")

    # 3. Lint & Format (ruff)
    run_cmd("3/6 Lint", [py, "-m", "ruff", "check", "."])
    run_cmd("3/6 Format", [py, "-m", "ruff", "format", "--check", "."])

    # 4. Architecture (A1~A4, A7)
    check_architecture()

    # 5. Test (pytest + 사전 게이트)
    tests_dir = ROOT_DIR / "tests"
    if tests_dir.exists() and any(tests_dir.rglob("test_*.py")):
        check_test_prerequisites(tests_dir)
        run_cmd("5/6 Test", [py, "-m", "pytest"])
    else:
        print("\n[WARN] [5/6 Test] No test files found; skipping.")

    # 6. Smoke Check (FastAPI 앱 로딩 확인 — 더미 환경변수 주입)
    if (SRC_DIR / "main.py").exists():
        dummy_env = {
            "LLM_API_KEY": "dummy-llm-key",
            "FLIGHT_API_KEY": "dummy-flight-key",
            "INVITE_CODE": "dummy-invite",
            "DAILY_FREE_LIMIT": "5",
        }
        run_cmd(
            "6/6 Smoke",
            [py, "-c", "from src.main import app; assert app is not None"],
            extra_env=dummy_env,
        )
    else:
        print("\n[WARN] [6/6 Smoke] src/main.py not found; skipping.")

    print("\n[ALL PASS] Verification pipeline succeeded.")


if __name__ == "__main__":
    main()
