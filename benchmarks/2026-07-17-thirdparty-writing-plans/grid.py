#!/usr/bin/env python3
"""Grid runner for the #193 third-party skill benchmark (adapted from skill-bench/templates/grid.py).

Modes (run in pre-registered order; each is resumable — an existing non-error cell is skipped):
  --prescreen   bare x 4 evals x 1 rep      -> prescreen-outputs/   (ADR 0065 saturation screen)
  --pilot       E1 x (wp x2, cek x1)        -> pilot-outputs/       (ADR 0066 cost pilot)
  (no flag)     4 evals x 3 arms x 3 reps   -> outputs/             (gated on metadata cost contract)

Arms differ ONLY in --append-system-prompt skill-body injection (metadata.json:arm_symmetry).
"""
import argparse
import json
import shutil
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "skill-bench" / "scripts" / "lib"))
from cost_gate import gate  # noqa: E402
from hermetic_driver import (build_env, capture_artifacts, do_call,  # noqa: E402
                             fresh_copy, summarize_call)

MODEL = "sonnet"   # pinned — deltas are model-relative
REPS = 3           # ADR 0058
TIMEOUT_S = 1200
ALLOW = ("Read", "Grep", "Glob", "Write", "Edit")  # Task/Agent/Bash stay denied — hermetic
BASE_ARGS = ("--permission-mode", "acceptEdits")

EVALS = {e["id"]: e for e in json.loads((HERE / "evals.json").read_text(encoding="utf-8"))}
FIXTURE = HERE / "fixture"


def body(name):
    """Skill body, frontmatter stripped — the injected loaded surface (ADR 0019: full surface)."""
    text = (HERE / "treatments" / name).read_text(encoding="utf-8")
    if text.startswith("---"):
        text = text.split("---", 2)[2]
    return text.strip()


ARMS = {
    "bare": {"extra_args": BASE_ARGS},
    "wp":   {"extra_args": BASE_ARGS + ("--append-system-prompt", body("writing-plans.SKILL.md"))},
    "cek":  {"extra_args": BASE_ARGS + ("--append-system-prompt", body("plan-task.SKILL.md"))},
}


def run_cell(eval_id, rep, arm, env, out, state, lock, cap):
    cell = f"{eval_id}-{arm}-r{rep}"
    path = out / f"{cell}.json"
    if path.exists() and not json.loads(path.read_text())["summary"]["error"]:
        print(f"[{cell}] exists, skipped", flush=True)
        return
    if state["halt"]:
        return
    workdir = fresh_copy(str(FIXTURE), cell)
    call = do_call(EVALS[eval_id]["task"], MODEL, env, workdir, timeout=TIMEOUT_S,
                   allow=ALLOW, extra_args=ARMS[arm]["extra_args"])
    artifacts = capture_artifacts(workdir, str(FIXTURE))
    shutil.rmtree(workdir, ignore_errors=True)
    summary = summarize_call(call)
    summary["cell_cost_usd"] = summary.get("cost_usd") or 0.0
    record = {"cell": cell, "scenario": eval_id, "arm": arm, "rep": rep, "model": MODEL,
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
    ap.add_argument("--prescreen", action="store_true", help="bare x all evals x 1 rep (ADR 0065)")
    ap.add_argument("--pilot", action="store_true", help="E1 x (wp x2 + cek x1) cost pilot (ADR 0066)")
    args = ap.parse_args()

    meta = json.loads((HERE / "metadata.json").read_text(encoding="utf-8"))
    ceiling = meta["cost"]["ceiling_usd"]
    cap = meta["cost"]["pilot_cap_usd"] if (args.pilot or args.prescreen) else ceiling

    if args.prescreen:
        out = HERE / "prescreen-outputs"
        tasks = [(eid, 1, "bare") for eid in EVALS]
    elif args.pilot:
        out = HERE / "pilot-outputs"
        tasks = [("E1", 1, "wp"), ("E1", 2, "wp"), ("E1", 1, "cek")]
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
    state = {"spent": 0.0, "halt": False}
    lock = threading.Lock()
    with ThreadPoolExecutor(max_workers=2 if (args.pilot or args.prescreen) else 4) as pool:
        list(pool.map(lambda t: run_cell(*t, env, out, state, lock, cap), tasks))
    if state["halt"]:
        sys.exit(f"backstop: ${state['spent']:.2f} > ${cap} — halted, resumable")
    print(f"complete: total ${state['spent']:.2f}")


if __name__ == "__main__":
    main()
