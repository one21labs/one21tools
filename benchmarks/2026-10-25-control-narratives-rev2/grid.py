#!/usr/bin/env python3
"""Grid runner: control-narratives revision 2 x {with, without} x {Opus 5.5, Sonnet 5.5} (metadata.json).

Text tasks; the reply is the graded artifact. Isolation is stricter than the 2026-07 runs, and
identical across arms and models: an empty CLAUDE_CONFIG_DIR, `--tools ""` (no tool exists at
all), `--disable-slash-commands`, `--strict-mcp-config`, plus the shared deny list. Measured
12-Oct-2026 in this environment: without `--tools ""` and `--disable-slash-commands` the bare arm
was offered account-synced copies of the measured skills; with them it reports no tools and no
skills. Arms differ ONLY in --append-system-prompt of a frozen treatment (prep.py).

Modes (resumable; an existing non-error cell is skipped):
  --prescreen  without x every eval x both models x 1 rep  -> prescreen-outputs/
  --pilot      with x first eval x both models x 2 reps    -> pilot-outputs/
  (no flag)    surviving evals (selection.json) x 2 arms x 2 models x REPS -> outputs/
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
# The harness left this repo (ADR 0102): $SKILL_MEASURE_ROOT, else a sibling skill-measure
# checkout. Neither found = exit naming the remedy, never a bare ImportError.
HARNESS = Path(os.environ.get("SKILL_MEASURE_ROOT") or HERE.parents[2] / "skill-measure")
if not (HARNESS / "scripts" / "lib").is_dir():
    sys.exit(f"harness not found at {HARNESS}: git clone https://github.com/"
             "one21labs/skill-measure && export SKILL_MEASURE_ROOT=$PWD/skill-measure")
sys.path.insert(0, str(HARNESS / "scripts" / "lib"))
from cost_gate import (DEFAULT_FAILED_CALL_CHARGE_USD, admit, call_charge_usd, cell_spend,  # noqa: E402
                       gate, spent_so_far)
from hermetic_driver import NEUTRAL_FRAME, build_env, do_call, neutral_cwd, summarize_call  # noqa: E402

SKILLS = ("control-narratives",)
MODELS = {"opus": "claude-opus-5-5", "sonnet": "claude-sonnet-5-5"}
EFFORT = "medium"
REPS = 2
TIMEOUT_S = 600
MAX_OUTPUT_TOKENS = "32000"  # as 2026-10-12; a reply at the cap is scored failed (cap_hit)
FAKE_TOOL_MARKUP = ("<invoke", "<function_calls", "</invoke>")
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


def check_harness():
    """Every run uses the harness commit the freeze recorded (metadata.json harness)."""
    from prep import harness_commit
    frozen = json.loads((HERE / "treatments" / "costs.json").read_text(encoding="utf-8"))["harness_sha"]
    live = harness_commit()
    if live != frozen or live.endswith("-dirty"):
        sys.exit(f"harness is at {live}, the freeze recorded {frozen}: run git -C {HARNESS} "
                 f"checkout {frozen} on a clean tree, or record the deviation in the README")


AUTH_PROBE_MODEL = "claude-nonexistent-0"  # no such model, so the call is never billed


def check_auth(env):
    """$0, before any billed call. The empty config dir holds no credentials, so without a working
    CLAUDE_CODE_OAUTH_TOKEN every call fails and bills a phantom retry (metadata.json auth).
    `claude auth status` reports any non-empty token as signed in, so the token is tested with one
    call to a model that does not exist: the API answers 401 to a bad token and 404 to a good
    one, at $0 either way (measured on CLI 2.1.310, 26-Oct-2026)."""
    r = subprocess.run(["claude", "-p", "--model", AUTH_PROBE_MODEL, "--output-format", "json",
                        "--tools", "", "--disable-slash-commands", "--strict-mcp-config", "x"],
                       env=env, cwd=tempfile.mkdtemp(prefix="auth-check-"), capture_output=True,
                       text=True, timeout=120)
    try:
        status = json.loads(r.stdout).get("api_error_status")
    except ValueError:
        status = None
    if status == 404:
        return
    token = (env.get("CLAUDE_CODE_OAUTH_TOKEN") or "").strip()
    held = ("no CLAUDE_CODE_OAUTH_TOKEN is exported" if not token
            else "the exported CLAUDE_CODE_OAUTH_TOKEN was rejected" if status in (401, 403)
            else f"the check got status {status}, not the 404 a signed-in caller gets")
    sys.exit(f"the hermetic config is not signed in ({held}): run `claude setup-token`, then "
             "export CLAUDE_CODE_OAUTH_TOKEN=<token> (metadata.json auth)")


CAP_HIT_PREFIX = "output hit the "  # hermetic_driver.summarize_call's error for a capped reply


def cap_hit(record):
    """A reply cut off at the output cap: scored failed, never regenerated (metadata.json grid).
    Regenerating until a reply fits would select away a length effect of the treatment."""
    return (record["summary"]["error"] or "").startswith(CAP_HIT_PREFIX)


def run_cell(key, model_key, arm, rep, env, cwd, out, state, lock, cap, est):
    skill, eid = key.split(":")
    cell = f"{skill}-{eid}-{model_key}-{arm}-r{rep}"
    path = out / f"{cell}.json"
    old = json.loads(path.read_text()) if path.exists() else None
    if old and (not old["summary"]["error"] or cap_hit(old)):
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
    summary["charged_usd"] = call_charge_usd(summary, est[model_key])  # a retry bills both attempts
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
    path.write_text(json.dumps(record, indent=1), encoding="utf-8")
    with lock:
        state["reserved"] -= est[model_key]
        state["spent"] += summary["charged_usd"]  # prior attempts are already in the seed
        state["done"] += 1
        print(f"[{state['done']}/{state['n']}] {cell} ${summary['charged_usd']:.3f} "
              f"spent=${state['spent']:.2f} err={record['summary']['error']}", flush=True)


def prior_costs():
    """Derived, never hand-filled (metadata.json pilot): per model, the mean recorded spend of its
    prescreen and pilot cells plus the Opus judge's measured cost per call; and all spend before
    the grid (those cells plus every judge pass over them)."""
    stages = ("prescreen-outputs", "pilot-outputs")
    recs = [json.loads(p.read_text(encoding="utf-8"))
            for d in stages for p in sorted((HERE / d).glob("*.json"))]
    judged = [json.loads(p.read_text(encoding="utf-8")) for d in stages
              for p in sorted((HERE / "graded").glob(f"judge-cost-*-{d}.json"))]
    opus = [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted((HERE / "graded").glob("judge-cost-claude-*-prescreen-outputs.json"))]
    opus = [j for j in opus if j["calls"]]
    if not opus or any(not any(r["model"] == m for r in recs) for m in MODELS.values()):
        sys.exit("cost gate: no measured prescreen and pilot cost yet — run --prescreen, "
                 "grade.py --dirs prescreen-outputs, and --pilot first")
    judge_per_call = opus[0]["billed_usd"] / opus[0]["calls"]
    per = {mk: sum(cell_spend(r) for r in recs if r["model"] == m)
           / sum(1 for r in recs if r["model"] == m) + judge_per_call for mk, m in MODELS.items()}
    prior = sum(spent_so_far(HERE / d) for d in stages) + sum(j["billed_usd"] for j in judged)
    print(f"cost gate: per-cell estimate {per}; spent before the grid ${prior:.2f}")
    return per, prior


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prescreen", action="store_true")
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    meta = json.loads((HERE / "metadata.json").read_text(encoding="utf-8"))
    ceiling = meta["cost"]["ceiling_usd"]
    # No per-cell estimate exists before the pilot: reserve (and charge a failed call) a constant.
    est = dict.fromkeys(MODELS, DEFAULT_FAILED_CALL_CHARGE_USD)
    if args.prescreen:
        out, cap = HERE / "prescreen-outputs", meta["cost"]["prescreen_cap_usd"]
        tasks = [(k, m, "without", 1) for k in EVALS for m in MODELS]
    elif args.pilot:
        out, cap = HERE / "pilot-outputs", meta["cost"]["pilot_cap_usd"]
        first = next(iter(EVALS))
        tasks = [(first, m, "with", r) for m in MODELS for r in (1, 2)]
    else:
        sel = json.loads((HERE / "selection.json").read_text(encoding="utf-8"))
        per, prior = prior_costs()
        out, cap = HERE / "outputs", ceiling - prior
        tasks = [(k, m, a, r) for m in MODELS for k in sel["surviving"][m]
                 for a in ("with", "without") for r in range(1, REPS + 1)]
        costs = [per[t[1]] for t in tasks]
        ok, projected = gate(len(tasks), [sum(costs) / len(costs)], cap)
        if not ok:
            sys.exit(f"cost gate: projected ${projected:.2f} > ${cap:.2f} remaining — grid halted")
        print(f"cost gate: {len(tasks)} cells projected ${projected:.2f} within ${cap:.2f}")
        est = per

    out.mkdir(exist_ok=True)
    env = build_env(EFFORT)
    env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] = MAX_OUTPUT_TOKENS
    env["CLAUDE_CONFIG_DIR"] = tempfile.mkdtemp(prefix="empty-config-")  # outside the checkout
    check_harness()
    check_auth(env)
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
    # admit reserves one estimate, but a call can be charged more (a retry with no envelope is
    # charged two): a pass that ends past the cap is a breach, never "complete".
    if state["halt"] or state["spent"] > cap:
        sys.exit(f"backstop: ${state['spent']:.2f} spent, next call would pass ${cap:.2f} — "
                 "halted, resumable")
    print(f"complete: {out.name}/ total ${state['spent']:.2f}")


if __name__ == "__main__":
    main()
