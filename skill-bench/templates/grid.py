#!/usr/bin/env python3
"""Canonical grid-runner TEMPLATE (#170; the shape three dated dirs re-derived by cloning).

COPY this file into a new dated benchmark dir and adapt every `ADAPT` block; never clone a
sibling dated dir (those are frozen measurement records, ADR 0026). The shape you keep:

  - per-cell fresh-copy hermetics: every call runs in its own private copy of the bundle
  - per-arm allow-lists + extra args: arms differ ONLY in the treatment (arm symmetry, ADR 0023)
  - resumable outputs: an existing non-error cell file is skipped on re-run
  - --pilot mode + cost gate + spend backstop: cost-pilot-first, the grid never runs ungated
  - artifact capture for EVERY arm, never pre-existing corpus files (#185 lesson, #191)
  - an infrastructure failure records an ERROR cell (resumable), never a quality 0 (#191)
"""
import argparse
import json
import shutil
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
# ADAPT: path to skill-bench/scripts/lib — repo checkout shown; installed plugin:
# Path(os.environ["CLAUDE_PLUGIN_ROOT"]) / "scripts" / "lib"
sys.path.insert(0, str(HERE.parents[1] / "skill-bench" / "scripts" / "lib"))
from cost_gate import gate  # noqa: E402
from hermetic_driver import (build_env, capture_artifacts, do_call,  # noqa: E402
                             fresh_copy, summarize_call)

MODEL = "sonnet"   # ADAPT and PIN — deltas are model-relative
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


def run_cell(scenario, src, context, rep, arm, env, out, state, lock, cap):
    cell = f"{scenario}-{arm}-r{rep}"
    path = out / f"{cell}.json"
    if path.exists() and not json.loads(path.read_text())["summary"]["error"]:
        print(f"[{cell}] exists, skipped", flush=True)
        return
    if state["halt"]:
        return
    spec = ARMS[arm]
    workdir = fresh_copy(src, cell)
    call = do_call(context + spec["suffix"], MODEL, env, workdir, timeout=TIMEOUT_S,
                   allow=spec["allow"], extra_args=spec["extra_args"])
    artifacts = capture_artifacts(workdir, src)
    shutil.rmtree(workdir, ignore_errors=True)
    summary = summarize_call(call)
    summary["cell_cost_usd"] = summary.get("cost_usd") or 0.0
    record = {"cell": cell, "scenario": scenario, "arm": arm, "rep": rep, "model": MODEL,
              "summary": summary, "response": call["response"], "artifacts": artifacts}
    path.write_text(json.dumps(record, indent=1), encoding="utf-8")
    with lock:
        state["spent"] += summary["cell_cost_usd"]
        if state["spent"] > cap:
            state["halt"] = True
    print(f"[{cell}] cost={summary['cell_cost_usd']:.3f} spent={state['spent']:.2f} "
          f"err={summary['error']}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true",
                    help=f"first scenario x {PILOT_ARM} x {REPS} reps under the pilot cap")
    args = ap.parse_args()

    # metadata.json: {"cost": {"ceiling_usd": .., "pilot_cap_usd": .., "per_arm_estimate_usd":
    # {arm: null-until-piloted}}} — the pre-registered spend contract, written BEFORE any run.
    meta = json.loads((HERE / "metadata.json").read_text(encoding="utf-8"))
    ceiling = meta["cost"]["ceiling_usd"]
    cap = meta["cost"]["pilot_cap_usd"] if args.pilot else ceiling
    out = HERE / ("pilot-outputs" if args.pilot else "outputs")
    out.mkdir(exist_ok=True)
    env = build_env()
    state = {"spent": 0.0, "halt": False}
    lock = threading.Lock()

    if args.pilot:
        sub, (src_rel, context) = next(iter(SCENARIOS.items()))
        tasks = [(sub, HERE / src_rel, context, r, PILOT_ARM) for r in range(1, REPS + 1)]
    else:
        per = meta["cost"]["per_arm_estimate_usd"]
        if any(per[a] is None for a in ARMS):
            sys.exit("cost gate: per_arm_estimate_usd incomplete — run --pilot first")
        n_cells = len(SCENARIOS) * len(ARMS) * REPS
        ok, projected = gate(n_cells, [per[a] for a in ARMS], ceiling)
        if not ok:
            sys.exit(f"cost gate: projected ${projected:.2f} > ${ceiling} — grid halted")
        print(f"cost gate: projected ${projected:.2f} within ${ceiling} — proceeding")
        tasks = []
        for sub, (src_rel, context) in SCENARIOS.items():
            src = HERE / src_rel
            if not src.exists():
                sys.exit(f"{sub}: {src_rel} missing — build the scenario bundles first")
            for rep in range(1, REPS + 1):
                for arm in ARMS:
                    tasks.append((sub, src, context, rep, arm))

    with ThreadPoolExecutor(max_workers=2 if args.pilot else 4) as pool:
        list(pool.map(lambda t: run_cell(*t, env, out, state, lock, cap), tasks))
    if state["halt"]:
        sys.exit(f"backstop: ${state['spent']:.2f} > ${cap} — halted, resumable")
    print(f"{'pilot' if args.pilot else 'grid'} complete: total ${state['spent']:.2f}")


if __name__ == "__main__":
    main()
