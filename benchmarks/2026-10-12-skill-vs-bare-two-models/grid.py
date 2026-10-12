#!/usr/bin/env python3
"""Grid runner: four measured skills x {with, without} x {Opus 5.5, Sonnet 5.5} (metadata.json).

Text tasks; the reply is the graded artifact. Isolation is stricter than the 2026-07 runs, and
identical across arms and models: an empty CLAUDE_CONFIG_DIR, `--tools ""` (no tool exists at
all), `--disable-slash-commands`, `--strict-mcp-config`, plus the shared deny list. Measured
12-Oct-2026 in this environment: without `--tools ""` and `--disable-slash-commands` the bare arm
was offered account-synced copies of these very skills; with them it reports no tools and no
skills. Arms differ ONLY in --append-system-prompt of a frozen treatment (prep.py).

Modes (resumable; an existing non-error cell is skipped):
  --prescreen  without x every eval x both models x 1 rep  -> prescreen-outputs/
  --pilot      with x first eval x both models x 2 reps    -> pilot-outputs/
  (no flag)    surviving evals (selection.json) x 2 arms x 2 models x REPS -> outputs/
"""
import argparse
import json
import os
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "skill-bench" / "scripts" / "lib"))
from cost_gate import gate, spent_so_far  # noqa: E402
from hermetic_driver import build_env, do_call, neutral_cwd, summarize_call  # noqa: E402

SKILLS = ("building-skills", "code-standards", "engineering-principles", "optimizing-context")
MODELS = {"opus": "claude-opus-5-5", "sonnet": "claude-sonnet-5-5"}
EFFORT = "medium"
REPS = 2
TIMEOUT_S = 600
ISOLATION = ("--tools", "", "--disable-slash-commands", "--strict-mcp-config", "--effort", EFFORT)


def load_evals():
    out = {}
    for s in SKILLS:
        raw = json.loads((HERE / "evals" / f"{s}.json").read_text(encoding="utf-8"))
        for e in raw["evals"]:
            out[f'{s}:E{e["id"]}'] = {"skill": s, "task": e["prompt"],
                                      "expectations": e["expectations"]}
    return out


EVALS = load_evals()


def extra_args(skill, arm):
    if arm == "without":
        return ISOLATION
    body = (HERE / "treatments" / f"{skill}.txt").read_text(encoding="utf-8").strip()
    return ISOLATION + ("--append-system-prompt", body)


def run_cell(key, model_key, arm, rep, env, cwd, out, state, lock, cap):
    skill, eid = key.split(":")
    cell = f"{skill}-{eid}-{model_key}-{arm}-r{rep}"
    path = out / f"{cell}.json"
    if path.exists() and not json.loads(path.read_text())["summary"]["error"]:
        return
    if state["halt"]:
        return
    call = do_call(EVALS[key]["task"], MODELS[model_key], env, cwd, timeout=TIMEOUT_S,
                   allow=(), extra_args=extra_args(skill, arm))
    summary = summarize_call(call)
    summary["cell_cost_usd"] = summary.get("cost_usd") or 0.0
    served = sorted(((call.get("envelope") or {}).get("modelUsage") or {}).keys())
    record = {"cell": cell, "skill": skill, "scenario": key, "arm": arm, "rep": rep,
              "model": MODELS[model_key], "served_models": served, "effort": EFFORT,
              "summary": summary, "response": call["response"]}
    if not summary["error"] and MODELS[model_key] not in served:
        record["summary"]["error"] = f"requested {MODELS[model_key]}, envelope served {served}"
    path.write_text(json.dumps(record, indent=1), encoding="utf-8")
    with lock:
        state["spent"] += summary["cell_cost_usd"]
        state["done"] += 1
        if state["spent"] > cap:
            state["halt"] = True
        print(f"[{state['done']}/{state['n']}] {cell} ${summary['cell_cost_usd']:.3f} "
              f"spent=${state['spent']:.2f} err={record['summary']['error']}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prescreen", action="store_true")
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    meta = json.loads((HERE / "metadata.json").read_text(encoding="utf-8"))
    ceiling = meta["cost"]["ceiling_usd"]
    if args.prescreen:
        out, cap = HERE / "prescreen-outputs", meta["cost"]["prescreen_cap_usd"]
        tasks = [(k, m, "without", 1) for k in EVALS for m in MODELS]
    elif args.pilot:
        out, cap = HERE / "pilot-outputs", meta["cost"]["pilot_cap_usd"]
        first = next(iter(EVALS))
        tasks = [(first, m, "with", r) for m in MODELS for r in (1, 2)]
    else:
        sel = json.loads((HERE / "selection.json").read_text(encoding="utf-8"))
        per = meta["cost"]["per_cell_estimate_usd"]
        if any(per.get(m) is None for m in MODELS):
            sys.exit("cost gate: per_cell_estimate_usd incomplete — run --prescreen and --pilot first")
        out, cap = HERE / "outputs", ceiling - meta["cost"]["spent_before_grid_usd"]
        tasks = [(k, m, a, r) for m in MODELS for k in sel["surviving"][m]
                 for a in ("with", "without") for r in range(1, REPS + 1)]
        costs = [per[t[1]] for t in tasks]
        ok, projected = gate(len(tasks), [sum(costs) / len(costs)], cap)
        if not ok:
            sys.exit(f"cost gate: projected ${projected:.2f} > ${cap:.2f} remaining — grid halted")
        print(f"cost gate: {len(tasks)} cells projected ${projected:.2f} within ${cap:.2f}")

    out.mkdir(exist_ok=True)
    env = build_env(EFFORT)
    env["CLAUDE_CONFIG_DIR"] = tempfile.mkdtemp(prefix="empty-config-")  # outside the checkout
    cwd = neutral_cwd(str(out))
    state = {"spent": spent_so_far(out), "halt": False, "done": 0, "n": len(tasks)}
    lock = threading.Lock()
    lockfile = out / ".grid.lock"
    try:
        fd = os.open(lockfile, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        sys.exit(f"{lockfile} exists — another run owns this dir (or died holding it)")
    try:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            list(pool.map(lambda t: run_cell(*t, env, cwd, out, state, lock, cap), tasks))
    finally:
        os.close(fd)
        lockfile.unlink(missing_ok=True)
    if state["halt"]:
        sys.exit(f"backstop: ${state['spent']:.2f} > ${cap:.2f} — halted, resumable")
    print(f"complete: {out.name}/ total ${state['spent']:.2f}")


if __name__ == "__main__":
    main()
