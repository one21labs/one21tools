#!/usr/bin/env python3
"""Deterministic substrate builder for the ADR 0052 plumbing pilot (stdlib only).

Builds under ./substrate/ (gitignored — regenerable, home is this script, lib README
convention): a bare origin + a work clone whose `origin/main...HEAD` range carries TWO seeded
process defects from the Instrument 1 taxonomy (`../2026-07-12-pdca-retrospect-recall/seeds.json`):
  R1 backstory-drift  — README gains a how-it-got-here History section (commit on work branch)
  R2 gate-piped-filter — ci.sh pipes the validate gate through `grep -v WARN` (masks exit code)
plus the orchestrator inputs a retrospect cell needs (friction.md; no session-log — optional
per the skill). The pilot scores plumbing, not the grid: seeds here are a signal sanity check
only and are NOT drawn from the pre-registered per-substrate assignments.

Also builds ./substrate/decide-scenario/: a throwaway judgment call (log retention) with two
project agents (.claude/agents/) for the subagent-spawn cell. Deliberately NOT one of the 8
pre-registered Instrument 2 scenarios (no contamination of committed specs).
"""
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SUB = HERE / "substrate"


def sh(*args, cwd):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)


def commit(repo, msg, date):
    env_date = {"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date}
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "-c", "user.name=dev", "-c", "user.email=dev@example.com",
                    "commit", "-q", "-m", msg],
                   cwd=repo, check=True, capture_output=True, text=True,
                   env={**__import__("os").environ, **env_date})


def build_retro_repo():
    bare = SUB / "origin.git"
    repo = SUB / "repo"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)

    (repo / "CLAUDE.md").write_text(
        "# demo-tool\n\nGates: `python3 scripts/validate.py docs/` is Sacred — run it bare and "
        "read its exit code; never pipe it through a filter.\nDocs: state the current truth; "
        "never narrate how it got there (no History/Learned sections).\nShipping: PR bodies "
        "carry Purpose / Changes / Testing.\n")
    (repo / "README.md").write_text("# demo-tool\n\nValidates doc structure for small teams.\n")
    (repo / "scripts").mkdir()
    (repo / "scripts" / "validate.py").write_text(
        "#!/usr/bin/env python3\nimport sys\nsys.exit(0 if len(sys.argv) > 1 else 2)\n")
    (repo / "docs").mkdir()
    (repo / "docs" / "guide.md").write_text("# Guide\n\nRun validate before pushing.\n")
    commit(repo, "Initial: validator, docs, CLAUDE.md", "2026-07-01T10:00:00")

    (repo / "scripts" / "ci.sh").write_text(
        "#!/bin/sh\nset -e\npython3 scripts/validate.py docs/\n")
    commit(repo, "Add CI entrypoint running the validate gate", "2026-07-02T10:00:00")
    sh("git", "remote", "add", "origin", str(bare), cwd=repo)
    sh("git", "push", "-q", "-u", "origin", "main", cwd=repo)

    # work branch = the range under retrospection
    sh("git", "checkout", "-q", "-b", "work", cwd=repo)

    # R2 gate-piped-filter
    (repo / "scripts" / "ci.sh").write_text(
        "#!/bin/sh\nset -e\npython3 scripts/validate.py docs/ | grep -v WARN\n")
    commit(repo, "Quiet noisy validator output in CI", "2026-07-10T09:00:00")

    (repo / "docs" / "guide.md").write_text(
        "# Guide\n\nRun validate before pushing.\nCI runs it automatically on every push.\n")
    commit(repo, "Document CI auto-run", "2026-07-10T11:00:00")

    # R1 backstory-drift
    (repo / "README.md").write_text(
        "# demo-tool\n\nValidates doc structure for small teams.\n\n## History\n\nThis started "
        "as check.sh, was renamed to validate.py in the v2 rewrite, and the old flag syntax was "
        "retired after the June refactor. We keep this section so newcomers know the journey.\n")
    commit(repo, "README: add project history for newcomers", "2026-07-11T09:00:00")

    (repo / "friction.md").write_text(
        "Session friction (orchestrator-supplied):\n"
        "1. CI showed green while docs validation had actually failed once; had to rerun the "
        "gate by hand to see the failure. (git-visible: yes)\n"
        "2. A reviewer asked what the README History section was for. (git-visible: yes)\n")
    commit(repo, "Record session friction for retrospective", "2026-07-11T10:00:00")
    return repo


def build_decide_scenario():
    sc = SUB / "decide-scenario"
    agents = sc / ".claude" / "agents"
    agents.mkdir(parents=True)
    (sc / "question.md").write_text(
        "# Judgment call: default log retention\n\nOur service writes ~2 GB/day of logs. "
        "Storage is $0.02/GB-month. 90% of debugging sessions look at the last 48 hours; the "
        "longest incident investigation this year needed 21 days of history. Support wants "
        "'keep everything'; finance flagged the storage line item. Decide the default retention "
        "(7 vs 30 days) and record the decision with rationale.\n")
    (agents / "advisor.md").write_text(
        "---\nname: advisor\ndescription: Cost-realism advisor for retention calls. Advises, "
        "does not decide.\nmodel: sonnet\ntools: Read\n---\n\nYou advise on operational-cost "
        "trade-offs. Read the files you are pointed at, then return: a recommendation, effort x "
        "risk x value in one line each, and THE one assumption your recommendation depends on. "
        "Terse. You advise; the caller decides.\n")
    (agents / "pm.md").write_text(
        "---\nname: pm\ndescription: Accountable decider — weighs advice and records the "
        "decision.\nmodel: sonnet\ntools: Read\n---\n\nYou are the accountable decider. Weigh "
        "the advice you are given, then output a decision record: Decision / Justification / "
        "THE weakest assumption (tagged) / one revisit trigger. Fragments, terse. You may "
        "overrule advice on priority; say so if you do.\n")
    return sc


if __name__ == "__main__":
    if SUB.exists():
        shutil.rmtree(SUB)
    SUB.mkdir()
    build_retro_repo()
    build_decide_scenario()
    print(f"substrate built under {SUB}")
