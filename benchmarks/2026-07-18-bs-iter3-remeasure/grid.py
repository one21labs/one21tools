#!/usr/bin/env python3
"""Grid runner for the building-skills iter-3 re-measure (#224; adapted from the #214 runner +
the #233 cumulative-spend fix).

Text tasks, ALL tools denied, no fixture bundle — the 6 committed evals are self-contained
prompts and the response is the graded artifact. Arms differ ONLY in --append-system-prompt of
a committed treatment body (prep.py writes treatments/; ADR 0027 arm symmetry).

Modes (resumable; an existing non-error cell is skipped):
  --prescreen  without x 6 evals x 1 rep  -> prescreen-outputs/
  --pilot      E1 x with-new x 2 reps     -> pilot-outputs/
  (no flag)    6 x 3 arms x 3 reps        -> outputs/  (gated on metadata cost contract)
"""
import argparse
import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "skill-bench" / "scripts" / "lib"))
from cost_gate import gate, spent_so_far  # noqa: E402
from hermetic_driver import build_env, do_call, neutral_cwd, summarize_call  # noqa: E402

MODEL = "sonnet"
REPS = 3
TIMEOUT_S = 600

_raw = json.loads((REPO / "skills" / "building-skills" / "evals" / "evals.json").read_text(encoding="utf-8"))
DROPPED = {"E3", "E6"}  # saturated in the bare prescreen (1.00 >= 0.85) — metadata.json:prescreen
EVALS = {f'E{e["id"]}': {"task": e["prompt"], "expectations": e["expectations"]}
         for e in _raw["evals"] if f'E{e["id"]}' not in DROPPED}


def treatment(name):
    return (HERE / "treatments" / f"building-skills.{name}.txt").read_text(encoding="utf-8").strip()


ARMS = {
    "without": {"extra_args": ()},
    "with-old": {"extra_args": ("--append-system-prompt", treatment("with-old"))},
    "with-new": {"extra_args": ("--append-system-prompt", treatment("with-new"))},
}


def run_cell(eval_id, rep, arm, env, cwd, out, state, lock, cap):
    cell = f"{eval_id}-{arm}-r{rep}"
    path = out / f"{cell}.json"
    if path.exists() and not json.loads(path.read_text())["summary"]["error"]:
        print(f"[{cell}] exists, skipped", flush=True)
        return
    if state["halt"]:
        return
    call = do_call(EVALS[eval_id]["task"], MODEL, env, cwd, timeout=TIMEOUT_S,
                   allow=(), extra_args=ARMS[arm]["extra_args"])
    summary = summarize_call(call)
    summary["cell_cost_usd"] = summary.get("cost_usd") or 0.0
    record = {"cell": cell, "scenario": eval_id, "arm": arm, "rep": rep, "model": MODEL,
              "summary": summary, "response": call["response"], "artifacts": {}}
    path.write_text(json.dumps(record, indent=1), encoding="utf-8")
    with lock:
        state["spent"] += summary["cell_cost_usd"]
        if state["spent"] > cap:
            state["halt"] = True
    print(f"[{cell}] cost={summary['cell_cost_usd']:.3f} spent={state['spent']:.2f} "
          f"err={summary['error']}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prescreen", action="store_true")
    ap.add_argument("--pilot", action="store_true")
    args = ap.parse_args()

    meta = json.loads((HERE / "metadata.json").read_text(encoding="utf-8"))
    ceiling = meta["cost"]["ceiling_usd"]
    cap = meta["cost"]["pilot_cap_usd"] if (args.pilot or args.prescreen) else ceiling

    if args.prescreen:
        out = HERE / "prescreen-outputs"
        tasks = [(eid, 1, "without") for eid in EVALS]
    elif args.pilot:
        out = HERE / "pilot-outputs"
        first = next(iter(EVALS))
        tasks = [(first, 1, "with-new"), (first, 2, "with-new")]
    else:
        per = meta["cost"]["per_arm_estimate_usd"]
        if any(per[a] is None for a in ARMS):
            sys.exit("cost gate: per_arm_estimate_usd incomplete — run --prescreen and --pilot first")
        out = HERE / "outputs"
        n_cells = len(EVALS) * len(ARMS) * REPS
        ok, projected = gate(n_cells, [per[a] for a in ARMS], ceiling)
        if not ok:
            sys.exit(f"cost gate: projected ${projected:.2f} > ${ceiling} — grid halted")
        print(f"cost gate: projected ${projected:.2f} within ${ceiling} — proceeding")
        tasks = [(eid, rep, arm) for eid in EVALS for rep in range(1, REPS + 1) for arm in ARMS]

    out.mkdir(exist_ok=True)
    env = build_env()
    cwd = neutral_cwd(str(out))
    # Cumulative across checkpoint/resume (#233): seed with committed spend, not zero.
    state = {"spent": spent_so_far(out), "halt": False}
    if state["spent"]:
        print(f"resuming: ${state['spent']:.2f} already spent in {out.name}/", flush=True)
    lock = threading.Lock()

    lockfile = out / ".grid.lock"
    try:
        lock_fd = os.open(lockfile, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        sys.exit(f"{lockfile} exists — another grid.py run owns this outputs dir (or died holding "
                 "it); confirm no process is live before removing the lockfile")
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(lambda t: run_cell(*t, env, cwd, out, state, lock, cap), tasks))
    finally:
        os.close(lock_fd)
        lockfile.unlink(missing_ok=True)
    if state["halt"]:
        sys.exit(f"backstop: ${state['spent']:.2f} > ${cap} — halted, resumable")
    print(f"complete: total ${state['spent']:.2f}")


if __name__ == "__main__":
    main()
