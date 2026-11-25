"""Flight Finder Issue 코멘트 양식 자동 생성 및 등록 헬퍼.

규칙 및 양식 원본: docs/harness/03-loop.md §3
주의: 이 스크립트는 코멘트 포맷팅 보조 도구이며, 검증(scripts/verify.py)과 책임을 분리한다.

사용 예:
  python scripts/log_attempt.py attempt --issue 3 --n 1 --m 3 --status 통과 \
    --base abc1234 --verify "로컬 통과" --done "src/api/search.py — BYOK 우회 추가"
  python scripts/log_attempt.py attempt ... --post
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

VALID_ATTEMPT_STATUSES = (
    "통과",
    "실패",
    "중단(NEEDS_HUMAN)",
    "중단(상한 소진)",
)


def format_attempt(
    n: int,
    m: int,
    status: str,
    base: str,
    verify: str,
    done: list[str],
    needs_human: str,
    next_step: str,
) -> str:
    """03-loop.md §3 시도 코멘트 양식을 생성한다."""
    done_lines = "\n".join(f"  - {item}" for item in done) if done else "  - 없음"
    return (
        f"### 시도 {n}/{m} · {status}\n"
        f"- 기준: {base}\n"
        f"- verify: {verify}\n"
        f"- 한 일:\n"
        f"{done_lines}\n"
        f"- 사람 판단이 필요한 것: {needs_human}\n"
        f"- 다음 시도에서 할 것: {next_step}\n"
    )


def format_start(session: str, base: str, n: int, m: int) -> str:
    """03-loop.md §3 진행 중 코멘트 양식을 생성한다."""
    now_kst = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M")
    return (
        f"### 진행 중 · 세션 {session}\n"
        f"- 시각: {now_kst}\n"
        f"- 기준: {base}\n"
        f"- 시도 {n}/{m} 부터 이어감\n"
    )


def format_close(session: str, reason: str) -> str:
    """03-loop.md §3 진행 닫음 코멘트 양식을 생성한다."""
    return f"### 진행 닫음 · 세션 {session}\n- 사유: {reason}\n"


def format_handoff(pr: str, base: str, n: int, m: int, todos: list[str]) -> str:
    """03-loop.md §3 사람 차례 코멘트 양식을 생성한다."""
    todo_items = todos or ["리뷰 · CI 확인 후 merge · 승인 (`DEC-4`)"]
    todo_lines = "\n".join(f"  - {item}" for item in todo_items)
    return (
        f"### 사람 차례 · {pr}\n"
        f"- 기준: {base} · 시도 {n}/{m} 까지 씀\n"
        f"- 사람이 할 것:\n"
        f"{todo_lines}\n"
    )


def post_comment(issue: int, body: str) -> None:
    """gh CLI로 GitHub Issue에 코멘트를 등록한다."""
    result = subprocess.run(
        ["gh", "issue", "comment", str(issue), "--body-file", "-"],
        input=body,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode != 0:
        print(
            f"[FAIL] gh issue comment exited with code {result.returncode}",
            file=sys.stderr,
        )
        sys.exit(result.returncode)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Flight Finder Issue 코멘트 양식 생성 및 gh 등록 헬퍼 (03-loop.md §3)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # 1. attempt
    p_attempt = sub.add_parser("attempt", help="시도 코멘트(시도 N/M) 생성")
    p_attempt.add_argument("--issue", type=int, required=True, help="GitHub Issue 번호")
    p_attempt.add_argument("--n", type=int, required=True, help="현재 시도 번호 N")
    p_attempt.add_argument("--m", type=int, required=True, help="최대 시도 상한 M")
    p_attempt.add_argument(
        "--status",
        choices=VALID_ATTEMPT_STATUSES,
        required=True,
        help="시도 결과 상태",
    )
    p_attempt.add_argument(
        "--base", required=True, help="커밋 sha | uncommitted | PR #N · sha"
    )
    p_attempt.add_argument(
        "--verify", required=True, help="로컬 통과 | 실패(<단계>) | 실행 안 함"
    )
    p_attempt.add_argument(
        "--done",
        action="append",
        default=[],
        help="파일 단위 작업 요약 (여러 번 지정 가능)",
    )
    p_attempt.add_argument(
        "--needs-human", default="없음", help="사람 판단이 필요한 항목"
    )
    p_attempt.add_argument(
        "--next-step", default="없음(종료)", help="다음 시도에서 할 것"
    )
    p_attempt.add_argument(
        "--post", action="store_true", help="gh issue comment로 실제 등록"
    )

    # 2. start
    p_start = sub.add_parser("start", help="진행 중 코멘트 생성 (LOOP-21)")
    p_start.add_argument("--issue", type=int, required=True, help="GitHub Issue 번호")
    p_start.add_argument("--session", required=True, help="세션 식별자")
    p_start.add_argument("--base", required=True, help="커밋 sha | uncommitted")
    p_start.add_argument("--n", type=int, required=True, help="마지막 시도 번호 N")
    p_start.add_argument("--m", type=int, required=True, help="최대 시도 상한 M")
    p_start.add_argument(
        "--post", action="store_true", help="gh issue comment로 실제 등록"
    )

    # 3. close
    p_close = sub.add_parser("close", help="진행 닫음 코멘트 생성 (LOOP-21)")
    p_close.add_argument("--issue", type=int, required=True, help="GitHub Issue 번호")
    p_close.add_argument("--session", required=True, help="세션 식별자")
    p_close.add_argument(
        "--reason", required=True, help="턴 넘김 | 멈춤(<종류>) | 종료"
    )
    p_close.add_argument(
        "--post", action="store_true", help="gh issue comment로 실제 등록"
    )

    # 4. handoff
    p_handoff = sub.add_parser("handoff", help="사람 차례 코멘트 생성 (LOOP-10)")
    p_handoff.add_argument("--issue", type=int, required=True, help="GitHub Issue 번호")
    p_handoff.add_argument("--pr", default="PR 없음", help="PR #N | PR 없음")
    p_handoff.add_argument("--base", required=True, help="커밋 sha")
    p_handoff.add_argument("--n", type=int, required=True, help="사용한 시도 번호 N")
    p_handoff.add_argument("--m", type=int, required=True, help="최대 시도 상한 M")
    p_handoff.add_argument(
        "--todo",
        action="append",
        default=[],
        help="사람이 확인할 항목 (여러 번 지정 가능)",
    )
    p_handoff.add_argument(
        "--post", action="store_true", help="gh issue comment로 실제 등록"
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "attempt":
        if args.n < 1 or args.m < 1 or args.n > args.m:
            parser.error("시도 번호는 1 <= n <= m 이어야 합니다.")
        body = format_attempt(
            n=args.n,
            m=args.m,
            status=args.status,
            base=args.base,
            verify=args.verify,
            done=args.done,
            needs_human=args.needs_human,
            next_step=args.next_step,
        )
    elif args.command == "start":
        body = format_start(session=args.session, base=args.base, n=args.n, m=args.m)
    elif args.command == "close":
        body = format_close(session=args.session, reason=args.reason)
    elif args.command == "handoff":
        body = format_handoff(
            pr=args.pr,
            base=args.base,
            n=args.n,
            m=args.m,
            todos=args.todo,
        )
    else:
        parser.error(f"지원하지 않는 명령입니다: {args.command}")

    if args.post:
        post_comment(args.issue, body)
        print(f"[OK] Posted {args.command} comment to Issue #{args.issue}")
    else:
        print(body, end="")


if __name__ == "__main__":
    main()
