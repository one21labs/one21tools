#!/usr/bin/env python3
"""Grid runner for revised control-narratives (PAIRS) x {with, without} x both models (metadata.json).

Text tasks; the reply is the graded artifact. Isolation is stricter than the 2026-07 runs, and
identical across arms and models: an empty CLAUDE_CONFIG_DIR, `--tools ""` (no tool exists at
all), `--disable-slash-commands`, `--strict-mcp-config`, plus the shared deny list. Measured
12-Oct-2026 in this environment: without `--tools ""` and `--disable-slash-commands` the bare arm
was offered account-synced copies of these very skills; with them it reports no tools and no
skills. Arms differ ONLY in --append-system-prompt of a frozen treatment (prep.py).

Modes (resumable; an existing non-error cell is skipped). Exit nonzero ONLY for a halt or a
refusal (cost gate, backstop, lock); a pass that leaves ERROR cells exits 0 (run_all re-runs it):
  --prescreen  without x held-out evals (id >= NEW_FROM_ID) x both models x 1 rep -> prescreen-outputs/
               (ids below it carry the first run's prescreen selection: aggregate.py --select)
  No pilot: per-cell estimates come from the first run's grid actuals (metadata.json cost).
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
sys.path.insert(0, str(REPO / "skill-measure" / "scripts" / "lib"))
from cost_gate import (DEFAULT_FAILED_CALL_CHARGE_USD, admit, cell_spend, charged_usd,  # noqa: E402
                       gate, spent_so_far)
from hermetic_driver import NEUTRAL_FRAME, build_env, do_call, neutral_cwd, summarize_call  # noqa: E402

SKILLS = ("control-narratives",)
PAIRS = {"opus": SKILLS, "sonnet": SKILLS}
NEW_FROM_ID = 17  # ids 17+ are the held-out set, authored after revision 1 was written
MODELS = {"opus": "claude-opus-5-5", "sonnet": "claude-sonnet-5-5"}
EFFORT = "medium"
REPS = 2
TIMEOUT_S = 600
MAX_OUTPUT_TOKENS = "64000"  # was 32000: 7 with-arm replies hit it and only their last chunk was
# captured (metadata.json deviations). A reply within 3% of the cap is an ERROR cell, never graded.
CAP_HIT_TOKENS = int(int(MAX_OUTPUT_TOKENS) * 0.97)
FAKE_TOOL_MARKUP = ("<invoke", "<function_calls", "</invoke>")
MIN_REPLY_CHARS = 200
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


def run_cell(key, model_key, arm, rep, env, cwd, out, state, lock, cap, est):
    skill, eid = key.split(":")
    cell = f"{skill}-{eid}-{model_key}-{arm}-r{rep}"
    path = out / f"{cell}.json"
    old = json.loads(path.read_text()) if path.exists() else None
    if old and not old["summary"]["error"]:
        return
    with lock:  # reserve this call's estimate so concurrent workers cannot all pass the check
        if state["halt"] or not admit(state["spent"], state["reserved"], est[model_key], cap):
            state["halt"] = True
            return
        state["reserved"] += est[model_key]
    call = do_call(NEUTRAL_FRAME + "\n\n" + EVALS[key]["task"], MODELS[model_key], env, cwd,
                   timeout=TIMEOUT_S,
                   allow=(), extra_args=extra_args(skill, arm))
    summary = summarize_call(call)
    summary["cell_cost_usd"] = summary.get("cost_usd") or 0.0
    summary["charged_usd"] = charged_usd(summary.get("cost_usd"), est[model_key])
    # The overwritten ERROR cell's calls were billed: carry them forward (spent_so_far sums them).
    summary["prior_attempts_usd"] = cell_spend(old) if old else 0.0
    served = sorted(((call.get("envelope") or {}).get("modelUsage") or {}).keys())
    record = {"cell": cell, "skill": skill, "scenario": key, "arm": arm, "rep": rep,
              "model": MODELS[model_key], "served_models": served, "effort": EFFORT,
              "summary": summary, "response": call["response"]}
    if not summary["error"] and MODELS[model_key] not in served:
        record["summary"]["error"] = f"requested {MODELS[model_key]}, envelope served {served}"
    elif not summary["error"] and any(t in call["response"] for t in FAKE_TOOL_MARKUP):
        # A no-tools cell that writes tool-call markup is acting out an agent loop, not answering:
        # infrastructure, never quality (#191). Recorded as ERROR so the next pass regenerates it.
        record["summary"]["error"] = "fake tool-call markup in a no-tools reply"
    elif not summary["error"] and (summary.get("usage") or {}).get("output_tokens", 0) >= CAP_HIT_TOKENS:
        record["summary"]["error"] = f"hit the {MAX_OUTPUT_TOKENS}-token output cap (partial capture)"
    elif not summary["error"] and len(call["response"]) < MIN_REPLY_CHARS:
        record["summary"]["error"] = f"reply under {MIN_REPLY_CHARS} chars"
    path.write_text(json.dumps(record, indent=1), encoding="utf-8")
    with lock:
        state["reserved"] -= est[model_key]
        state["spent"] += summary["charged_usd"]  # prior attempts are already in the seed
        state["done"] += 1
        print(f"[{state['done']}/{state['n']}] {cell} ${summary['charged_usd']:.3f} "
              f"spent=${state['spent']:.2f} err={record['summary']['error']}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prescreen", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    meta = json.loads((HERE / "metadata.json").read_text(encoding="utf-8"))
    ceiling = meta["cost"]["ceiling_usd"]
    # No per-cell estimate exists before the pilot: reserve and charge a conservative constant.
    fallback = meta["cost"].get("failed_call_charge_usd", DEFAULT_FAILED_CALL_CHARGE_USD)
    est = {m: fallback for m in MODELS}
    if args.prescreen:
        out, cap = HERE / "prescreen-outputs", meta["cost"]["prescreen_cap_usd"]
        tasks = [(k, m, "without", 1) for k in EVALS for m in MODELS
                 if EVALS[k]["skill"] in PAIRS[m] and int(k.split(":E")[1]) >= NEW_FROM_ID]
    else:
        sel = json.loads((HERE / "selection.json").read_text(encoding="utf-8"))
        per = meta["cost"]["per_cell_estimate_usd"]
        result = meta["cost"]["per_cell_basis"]
        if meta["cost"].get("spent_before_grid_usd") is None:
            sys.exit("cost gate: spent_before_grid_usd unset — run --prescreen and select first")
        remaining = ceiling - meta["cost"]["spent_before_grid_usd"]
        # Held-out cells first. Pre-registered fallback: if the full grid does not fit the cap,
        # drop the tuned-on secondary (ids < NEW_FROM_ID) and run the held-out primary alone.
        tasks = [(k, m, a, r) for held in (True, False) for m in MODELS for k in sel["surviving"][m]
                 if (int(k.split(":E")[1]) >= NEW_FROM_ID) == held
                 for a in ("with", "without") for r in range(1, REPS + 1)]
        if meta.get("grid_scope") == "held-out only":  # fallback fired on the first grid pass
            tasks = [t for t in tasks if int(t[0].split(":E")[1]) >= NEW_FROM_ID]
        for scope in ("full", "held-out only"):
            costs = [per[t[1]] for t in tasks]  # generation + judge per cell
            ok, projected = gate(len(tasks), [sum(costs) / len(costs)], remaining)
            if ok:
                break
            print(f"cost gate: {scope} grid projected ${projected:.2f} > ${remaining:.2f}")
            tasks = [t for t in tasks if int(t[0].split(":E")[1]) >= NEW_FROM_ID]
        if not ok:
            sys.exit(f"cost gate: projected ${projected:.2f} > ${remaining:.2f} remaining — "
                     "grid halted")
        print(f"cost gate: {len(tasks)} cells projected ${projected:.2f} within ${remaining:.2f}")
        # The backstop sees generation only, so hold back every cell's judge share up front;
        # reserve and charge the generation estimate (the cap already holds the judge share).
        out = HERE / "outputs"
        cap = remaining - len(tasks) * result["judge_per_cell_usd"]
        est = result["generation_mean_usd"]

    out.mkdir(exist_ok=True)
    env = build_env(EFFORT)
    env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] = MAX_OUTPUT_TOKENS
    env["CLAUDE_CONFIG_DIR"] = tempfile.mkdtemp(prefix="empty-config-")  # outside the checkout
    cwd = neutral_cwd(str(out))
    state = {"spent": spent_so_far(out), "reserved": 0.0, "halt": False, "done": 0,
             "n": len(tasks)}
    lock = threading.Lock()
    lockfile = out / ".grid.lock"
    try:
        fd = os.open(lockfile, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        sys.exit(f"{lockfile} exists — another run owns this dir (or died holding it)")
    try:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            list(pool.map(lambda t: run_cell(*t, env, cwd, out, state, lock, cap, est), tasks))
    finally:
        os.close(fd)
        lockfile.unlink(missing_ok=True)
    if state["halt"]:
        sys.exit(f"backstop: ${state['spent']:.2f} spent, next call would pass ${cap:.2f} — "
                 "halted, resumable")
    print(f"complete: {out.name}/ total ${state['spent']:.2f}")


if __name__ == "__main__":
    main()
