#!/usr/bin/env python3
"""Canonical grid-runner TEMPLATE (#170).

COPY this file into a new dated benchmark dir and adapt every `ADAPT` block; never clone a
sibling dated dir (those are frozen measurement records, ADR 0041). The shape you keep:

  - per-cell fresh-copy hermetics: every call runs in its own private copy of the bundle
  - per-arm allow-lists + extra args: arms differ ONLY in the treatment (arm symmetry, ADR 0023)
  - resumable outputs: an existing non-error cell file is skipped on re-run
  - --pilot mode + cost gate + spend backstop: cost-pilot-first, the grid never runs ungated;
    the backstop reserves each call's estimate BEFORE launch, so concurrent calls cannot jointly
    pass the cap on their estimates; a call costing more than its estimate still can. Exit is
    nonzero only for a halt or refusal (an ERROR cell re-runs, it is not a halt)
  - artifact capture for EVERY arm, never pre-existing corpus files (#185 lesson, #191)
  - an infrastructure failure records an ERROR cell (resumable), never a quality 0 (#191)
"""
import argparse
import json
import os
import shutil
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
# ADAPT: path to skill-measure/scripts/lib — repo checkout shown; installed plugin:
# Path(os.environ["CLAUDE_PLUGIN_ROOT"]) / "scripts" / "lib"
sys.path.insert(0, str(HERE.parents[1] / "skill-measure" / "scripts" / "lib"))
from cost_gate import (DEFAULT_FAILED_CALL_CHARGE_USD, admit, cell_spend, charged_usd,  # noqa: E402
                       gate, spent_so_far)
from hermetic_driver import (build_env, capture_artifacts, do_call,  # noqa: E402
                             fresh_copy, summarize_call)

MODEL = "sonnet"   # ADAPT and PIN to an exact claude-* id — deltas are model-relative, and only an
                   # exact id lets summarize_call refuse a substituted model
REPS = 3           # ADAPT (>=3 to separate reliably-good from lucky, ADR 0058)
TIMEOUT_S = 2400

# ADAPT: scenario id -> (bundle dir relative to HERE, context prompt). The bundle is copied
# fresh per cell; the context is the prompt prefix every arm shares.
SCENARIOS = {
    "S1": ("scenario-s1/workdir", "Read MEMO.md in this directory — it asks for a decision."),
}

# ADAPT: arm -> what differs. suffix = the arm's prompt tail; allow = tools carved out of the
# deny list; extra_args = raw CLI args (e.g. --plugin-dir for a treatment arm).
ARMS = {
    "A": {"suffix": " Decide this and record your decision with rationale.",
          "allow": ("Read", "Grep", "Glob", "Bash", "Write", "Edit"),
          "extra_args": ("--permission-mode", "acceptEdits")},
    # "C": {..., "extra_args": ("--plugin-dir", "<treatment>", "--permission-mode", "acceptEdits")},
}
PILOT_ARM = "A"    # ADAPT: pilot the most expensive arm first


def run_cell(scenario, src, context, rep, arm, env, out, state, lock, cap, est):
    cell = f"{scenario}-{arm}-r{rep}"
    path = out / f"{cell}.json"
    old = json.loads(path.read_text()) if path.exists() else None
    if old and not old["summary"]["error"]:
        print(f"[{cell}] exists, skipped", flush=True)
        return
    with lock:  # reserve this call's estimate so concurrent workers cannot all pass the check
        if state["halt"] or not admit(state["spent"], state["reserved"], est[arm], cap):
            state["halt"] = True
            return
        state["reserved"] += est[arm]
    spec = ARMS[arm]
    workdir = fresh_copy(src)
    call = do_call(context + spec["suffix"], MODEL, env, workdir, timeout=TIMEOUT_S,
                   allow=spec["allow"], extra_args=spec["extra_args"])
    artifacts = capture_artifacts(workdir, src)
    shutil.rmtree(workdir, ignore_errors=True)
    summary = summarize_call(call, requested_model=MODEL)
    summary["cell_cost_usd"] = summary.get("cost_usd") or 0.0
    summary["charged_usd"] = charged_usd(summary.get("cost_usd"), est[arm])
    # The overwritten ERROR cell's calls were billed: carry them forward (spent_so_far sums them).
    summary["prior_attempts_usd"] = cell_spend(old) if old else 0.0
    record = {"cell": cell, "scenario": scenario, "arm": arm, "rep": rep, "model": MODEL,
              "summary": summary, "response": call["response"], "artifacts": artifacts}
    path.write_text(json.dumps(record, indent=1), encoding="utf-8")
    with lock:
        state["reserved"] -= est[arm]
        state["spent"] += summary["charged_usd"]  # prior attempts are already in the seed
    print(f"[{cell}] cost={summary['charged_usd']:.3f} spent={state['spent']:.2f} "
          f"err={summary['error']}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true",
                    help=f"first scenario x {PILOT_ARM} x {REPS} reps under the pilot cap")
    args = ap.parse_args()

    # metadata.json: {"cost": {"ceiling_usd": .., "pilot_cap_usd": .., "per_arm_estimate_usd":
    # {arm: null-until-piloted}, "failed_call_charge_usd": optional}} — the pre-registered spend
    # contract, written BEFORE any run. The pilot has no estimate yet: it reserves (and charges a
    # failed call) failed_call_charge_usd per cell — ADAPT it up for long agentic cells.
    # ceiling_usd = 2x the notional estimate (the stop-rule of record, ADR 0073), NEVER the
    # estimate itself — encoding the estimate band's top forces a mid-run revision the moment a
    # pilot projects above it (cost-and-verdict.md owns the rule).
    meta = json.loads((HERE / "metadata.json").read_text(encoding="utf-8"))
    ceiling = meta["cost"]["ceiling_usd"]
    # The grid's cap is what the pilot left of the ceiling, not the whole ceiling.
    cap = (meta["cost"]["pilot_cap_usd"] if args.pilot
           else ceiling - spent_so_far(HERE / "pilot-outputs"))
    out = HERE / ("pilot-outputs" if args.pilot else "outputs")
    out.mkdir(exist_ok=True)
    env = build_env()
    # Seed with prior invocations' committed spend so the ceiling backstop below compares
    # CUMULATIVE cost across checkpoint/resume, not this invocation's alone (#233).
    state = {"spent": spent_so_far(out), "reserved": 0.0, "halt": False}
    if state["spent"]:
        print(f"resuming: ${state['spent']:.2f} already spent in {out.name}/", flush=True)
    lock = threading.Lock()

    if args.pilot:
        est = dict.fromkeys(ARMS, meta["cost"].get("failed_call_charge_usd",
                                                   DEFAULT_FAILED_CALL_CHARGE_USD))
        sub, (src_rel, context) = next(iter(SCENARIOS.items()))
        tasks = [(sub, HERE / src_rel, context, r, PILOT_ARM) for r in range(1, REPS + 1)]
    else:
        per = meta["cost"]["per_arm_estimate_usd"]
        if any(per[a] is None for a in ARMS):
            sys.exit("cost gate: per_arm_estimate_usd incomplete — run --pilot first")
        n_cells = len(SCENARIOS) * len(ARMS) * REPS
        ok, projected = gate(n_cells, [per[a] for a in ARMS], cap)
        if not ok:
            sys.exit(f"cost gate: projected ${projected:.2f} > ${cap:.2f} remaining — "
                     "grid halted")
        print(f"cost gate: projected ${projected:.2f} within ${cap:.2f} remaining — proceeding")
        est = per
        tasks = []
        for sub, (src_rel, context) in SCENARIOS.items():
            src = HERE / src_rel
            if not src.exists():
                sys.exit(f"{sub}: {src_rel} missing — build the scenario bundles first")
            for rep in range(1, REPS + 1):
                for arm in ARMS:
                    tasks.append((sub, src, context, rep, arm))

    # Single-writer lock (ADR 0073 / PR #219 retrospective): the resumable skip in run_cell is
    # read-then-run, so a second concurrent invocation silently double-generates (double-SPENDS)
    # cells. O_EXCL create fails fast instead; released on every exit path below.
    lockfile = out / ".grid.lock"
    try:
        lock_fd = os.open(lockfile, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        sys.exit(f"{lockfile} exists — another grid.py run owns this outputs dir (or died holding "
                 "it); confirm no process is live before removing the lockfile")
    try:
        with ThreadPoolExecutor(max_workers=2 if args.pilot else 4) as pool:
            list(pool.map(lambda t: run_cell(*t, env, out, state, lock, cap, est), tasks))
    finally:
        os.close(lock_fd)
        lockfile.unlink(missing_ok=True)
    if state["halt"]:
        sys.exit(f"backstop: ${state['spent']:.2f} spent, next call would pass ${cap:.2f} — "
                 "halted, resumable")
    print(f"{'pilot' if args.pilot else 'grid'} complete: total ${state['spent']:.2f}")


if __name__ == "__main__":
    main()
