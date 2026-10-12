"""One home for the paid-run refusal shared by every spending entry point.

`bench` is model-invocable (ADR 0016), so a paid subcommand must refuse by default rather than
rely on the caller remembering a flag. Two entry points spend — `bench_skill.py` (generation +
judge calls) and `run_eval.py` (one `claude -p` per query per run) — and they had the same
refusal copy-pasted, which is exactly the drift the one-home rule exists to stop.
"""
import sys

REFUSAL = "Refusing to spend without --yes (spend guard). Re-run with --yes to proceed."


def add_spend_flag(parser, what="paid runs"):
    """Register the shared `--yes` flag so the flag name cannot drift between entry points."""
    parser.add_argument("--yes", action="store_true", help=f"confirm {what} (spend guard)")


def require_yes(yes, cost_line, out=sys.stderr, exit_fn=sys.exit):
    """Print the cost estimate, then refuse with exit 2 unless `yes`. `exit_fn` is injected so
    the decision is testable without ending the process."""
    print(f"[cost] {cost_line}", file=out)
    if not yes:
        print(REFUSAL, file=out)
        exit_fn(2)
