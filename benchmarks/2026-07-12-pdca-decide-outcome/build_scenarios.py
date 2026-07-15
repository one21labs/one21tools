#!/usr/bin/env python3
"""Build the remaining scenario bundles for the /decide outcome corpus (stdlib only).

Companion to build_b1.py. Materializes:
  - B3 snapshot (scenario-b3/snapshot/): this repo at parent commit 405be20, refs/reflog
    stripped, .claude filtered from ALL history (never existed; no removal commit),
    docs/decisions kept (pre-decision at the parent), ISSUE-106.md placed untracked.
  - B4 snapshot (scenario-b4/snapshot/): same recipe at 3ae165c with ISSUE-109.md.
  - S1-S4 synthetic workdirs (scenario-s{n}/workdir/): small fresh git repos built from the
    committed source records in scenario-s{n}/ (MEMO.md + supporting files), 2-3 pinned commits.

Determinism: parent commits are fixed; filter-branch is content-deterministic and every
synthetic commit pins author + committer identity AND date, so all git HEADs are
byte-identical across rebuilds.

Sources (one home): the committed scenario-s{n}/ files are the memo/support source of truth;
this script copies them, it never embeds their text. Output dirs are gitignored (regenerable).
"""
import os
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]

# Pinned identity + dates so every generated commit is reproducible.
AUTHOR = ("owner", "owner@example.com")           # matches build_b1.py's removal-commit identity
S_AUTHOR = ("Sam Ellis", "sam@example.com")       # synthetic-project author


def sh(*args, cwd, env=None):
    return subprocess.run(args, cwd=str(cwd), check=True, capture_output=True, text=True,
                          env=env)


def commit_env(name, email, date):
    import os
    env = dict(os.environ)
    env.update(
        GIT_AUTHOR_NAME=name, GIT_AUTHOR_EMAIL=email, GIT_AUTHOR_DATE=date,
        GIT_COMMITTER_NAME=name, GIT_COMMITTER_EMAIL=email, GIT_COMMITTER_DATE=date,
    )
    return env


# --------------------------------------------------------------------------- backtests

def build_backtest(bid, commit, issue_file, deny_globs, extra_check=None):
    """build_b1.py's recipe, parametrized. deny_globs are asserted ABSENT at the commit
    (deny-list guard); .claude is filtered from all history; docs/decisions stays."""
    bdir = HERE / f"scenario-{bid}"
    snap = bdir / "snapshot"
    if snap.exists():
        shutil.rmtree(snap)
    sh("git", "clone", "-q", "--no-hardlinks", f"file://{REPO}", str(snap), cwd=HERE)
    sh("git", "checkout", "-q", commit, cwd=snap)
    sh("git", "branch", "-f", "main", commit, cwd=snap)
    sh("git", "checkout", "-q", "main", cwd=snap)
    sh("git", "remote", "remove", "origin", cwd=snap)
    # strip every other ref + reflog so history ends at the reconstruction point
    for ref in sh("git", "for-each-ref", "--format=%(refname)", cwd=snap).stdout.split():
        if ref != "refs/heads/main":
            sh("git", "update-ref", "-d", ref, cwd=snap)
    sh("git", "reflog", "expire", "--expire=now", "--all", cwd=snap)
    sh("git", "gc", "-q", "--prune=now", "--aggressive", cwd=snap)

    # deny-list globs must not exist at this commit (else the reconstruction leaks an outcome)
    for glob in deny_globs:
        hits = list(snap.glob(glob))
        assert not hits, f"{bid}: deny-listed path present at {commit}: {hits}"

    # Hermeticity, third design (2026-07-12, audits 1-2; see build_b1.py): the machinery
    # must never have EXISTED — filter .claude/ from all history (no removal commit, nothing
    # recoverable via git show/log -p). docs/decisions STAYS: pre-decision at the parent by
    # construction (outcome-free, audit-verified); its absence was the loudest tamper tell.
    # Memo lands UNTRACKED. Panel agents exported for arm-C-only injection (grid_i2.py).
    agents_src = snap / ".claude" / "agents"
    panel = bdir / "panel-agents"
    if panel.exists():
        shutil.rmtree(panel)
    if agents_src.exists():
        shutil.copytree(agents_src, panel)
    fb_env = {**os.environ, "FILTER_BRANCH_SQUELCH_WARNING": "1"}
    subprocess.run(["git", "filter-branch", "-f", "--index-filter",
                    "git rm -rq --cached --ignore-unmatch .claude",
                    "--", "--all"],
                   cwd=str(snap), check=True, capture_output=True, text=True, env=fb_env)
    subprocess.run(["git", "update-ref", "-d", "refs/original/refs/heads/main"],
                   cwd=str(snap), capture_output=True)
    subprocess.run(["git", "clean", "-qfdx"], cwd=str(snap), check=True, capture_output=True)
    sh("git", "reset", "-q", "--hard", "HEAD", cwd=snap)
    sh("git", "reflog", "expire", "--expire=now", "--all", cwd=snap)
    sh("git", "gc", "-q", "--prune=now", "--aggressive", cwd=snap)

    shutil.copy(bdir / issue_file, snap / issue_file)  # untracked by design

    if extra_check:
        extra_check(snap)

    # assertions: .claude never in history; decisions present; memo untracked; count kept
    hist = subprocess.run(["git", "log", "--all", "--oneline", "--", ".claude"],
                          cwd=str(snap), capture_output=True, text=True).stdout.strip()
    assert not hist, f"{bid}: .claude still in history: {hist[:200]}"
    assert (snap / "docs" / "decisions").exists(), f"{bid}: docs/decisions missing (must stay)"
    status = sh("git", "status", "--porcelain", cwd=snap).stdout.strip()
    assert status == f"?? {issue_file}", f"{bid}: unexpected status: {status[:200]}"
    orig_n = sh("git", "rev-list", "--count", commit, cwd=REPO).stdout.strip()
    new_n = sh("git", "rev-list", "--count", "HEAD", cwd=snap).stdout.strip()
    assert orig_n == new_n, f"{bid}: commit count changed {orig_n} -> {new_n}"

    head = sh("git", "rev-parse", "HEAD", cwd=snap).stdout.strip()
    n = sh("git", "rev-list", "--count", "HEAD", cwd=snap).stdout.strip()
    print(f"{bid.upper()} snapshot HEAD {head[:12]} ({n} commits), .claude filtered, "
          f"decisions kept, {issue_file} untracked")
    return head


def b3_char_budget_check(snap):
    """B3 deny list keeps char-budget.mjs's post-fix (merge-skew) state out. At parent 405be20
    the file is naturally pre-fix; assert the merge-skew fix marker is absent. (DOC_BUDGETS is
    pre-existing at this commit and is NOT the fix marker, so it is not asserted on.)"""
    f = snap / "pdca-workflow" / "scripts" / "char-budget.mjs"
    assert f.exists(), "B3: char-budget.mjs missing at parent?!"
    text = f.read_text().lower()
    for marker in ("merge-skew", "#164"):
        assert marker not in text, f"B3: unexpected merge-skew fix marker {marker!r} present"


# --------------------------------------------------------------------------- synthetic

# Each commit: (message, [source filenames], date). Files are copied from scenario-s{n}/.
SYNTHETIC = {
    "s1": [
        ("Add free-tier usage export", ["free_tier_usage.csv"], "2026-06-27T09:00:00+00:00"),
        ("Add free-tier cap decision memo", ["MEMO.md"], "2026-06-28T14:30:00+00:00"),
    ],
    "s2": [
        ("Add monolith module coupling map", ["modules.md"], "2026-06-10T11:00:00+00:00"),
        ("Add monolith split decision memo", ["MEMO.md"], "2026-06-15T16:45:00+00:00"),
    ],
    "s3": [
        ("Add nightly warehouse sync script", ["nightly_sync.py"], "2026-06-30T08:15:00+00:00"),
        ("Add sync run log export", ["sync_runs.csv"], "2026-06-30T08:20:00+00:00"),
        ("Add orchestration-adoption decision memo", ["MEMO.md"], "2026-07-01T10:00:00+00:00"),
    ],
    "s4": [
        ("Add API version traffic export", ["version_traffic.csv"], "2026-06-18T09:30:00+00:00"),
        ("Add forwarded customer emails", ["complaints.md"], "2026-06-18T09:35:00+00:00"),
        ("Add v1 sunset decision memo", ["MEMO.md"], "2026-06-20T13:00:00+00:00"),
    ],
}


def build_synthetic(sid, commits):
    sdir = HERE / f"scenario-{sid}"
    workdir = sdir / "workdir"
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True)

    # guard: the commit plan must account for exactly the source files present (one home)
    planned = [f for _, files, _ in commits for f in files]
    present = sorted(p.name for p in sdir.iterdir() if p.name != "workdir")
    assert sorted(planned) == present, f"{sid}: plan {sorted(planned)} != sources {present}"

    sh("git", "init", "-q", "-b", "main", str(workdir), cwd=sdir)
    for msg, files, date in commits:
        for fn in files:
            shutil.copy(sdir / fn, workdir / fn)  # copy source bytes; never embed text here
        env = commit_env(*S_AUTHOR, date)
        sh("git", "add", "--", *files, cwd=workdir, env=env)
        sh("git", "commit", "-q", "-m", msg, cwd=workdir, env=env)

    status = sh("git", "status", "--porcelain", cwd=workdir).stdout.strip()
    assert not status, f"{sid}: workdir not clean:\n{status}"
    head = sh("git", "rev-parse", "HEAD", cwd=workdir).stdout.strip()
    n = sh("git", "rev-list", "--count", "HEAD", cwd=workdir).stdout.strip()
    files = sorted(p.name for p in workdir.iterdir() if p.name != ".git")
    print(f"{sid.upper()} workdir HEAD {head[:12]} ({n} commits) files={files}")
    return head


def main():
    heads = {}
    # deny_globs = outcome paths asserted ABSENT at the parent (docs/decisions is always
    # present at the parent and is removed unconditionally, so it is not a deny_glob).
    heads["B3"] = build_backtest("b3", "405be20", "ISSUE-106.md",
                                 deny_globs=[],
                                 extra_check=b3_char_budget_check)
    heads["B4"] = build_backtest("b4", "3ae165c", "ISSUE-109.md",
                                 deny_globs=["benchmarks/2026-07-10-routing-escalation*"])
    for sid, commits in SYNTHETIC.items():
        heads[sid.upper()] = build_synthetic(sid, commits)
    print("\nHEADs:", " ".join(f"{k}={v[:12]}" for k, v in heads.items()))


if __name__ == "__main__":
    main()
