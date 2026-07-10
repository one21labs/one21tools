#!/usr/bin/env python3
"""Hermetic claude -p driver for the routing-escalation CHECKER calls (issue #109).

Runs ONE checker variant over the 24 haiku gradient cells in checker_inputs.json -- stdlib only.
Same hermetic pattern as the fullgrid's harness.py (ADR 0023): clean CLAUDE_CONFIG_DIR, full tool
deny list, prompt on stdin, empty scratch cwd outside the repo checkout. Designed to run INSIDE
WSL Debian, invoked from Windows as:

    wsl -d Debian -- python3 /mnt/c/.../checker_harness.py --variant sonnet-judge

The checker sees the ORIGINAL REQUEST + the haiku deliverable ONLY -- no eval expectations
(deployment-realistic; metadata.json:design.checker_variants). Prompt framing mirrors the
fullgrid validate_prompt so the fidelity number is comparable to #41's validator false-accept;
semantics differ: SHIP/ESCALATE, no corrections (routing has no coaching).

Writes checkers/<variant>.<skill>.<eval_id>.r<rep>.json (raw response + envelope; parsing happens
in compose.py) and <variant>.checker-summary.json.
"""
import argparse
import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

WORKERS = 4  # matches the substrate run's fixed parallelism
CALL_TIMEOUT_S = 600
VARIANT_MODEL = {"sonnet-judge": "sonnet", "haiku-judge": "haiku"}

CLAUDE_DENY_TOOLS = [
    "Skill", "Task", "Read", "Grep", "Glob", "Bash", "Edit", "Write",
    "WebFetch", "WebSearch", "NotebookEdit",
]

# Verbatim from the fullgrid harness.py (arm/prompt symmetry with the substrate run).
NEUTRAL_FRAME = (
    "Respond directly from the request text below. Do not read files, search the repository, "
    "run commands, or use any tools -- answer using only the text given in this request."
)


def checker_prompt(prompt, deliverable):
    return (
        f"{NEUTRAL_FRAME}\n\n"
        "You are the release CHECKER in a two-tier routing system. A fast model produced the "
        "deliverable below for the original request, in one attempt. Decide whether to SHIP it "
        "or ESCALATE the whole task to a stronger model, which will redo it from scratch -- "
        "your reason is not passed along, there is no coaching. SHIP only if the deliverable "
        "genuinely satisfies the original request as-is: fully, concretely, and without gaps. "
        "ESCALATE otherwise.\n\n"
        "Respond with STRICT JSON ONLY, matching exactly this shape and nothing else -- no prose "
        'before or after: {"verdict": "<SHIP or ESCALATE>", "reason": "<one sentence>"}\n\n'
        f"Original request:\n{prompt}\n\n"
        f"Deliverable:\n{deliverable}"
    )


def build_env():
    env = dict(os.environ)
    home = os.path.expanduser("~")
    env["PATH"] = os.path.join(home, ".local", "bin") + os.pathsep + env.get("PATH", "")
    env["CLAUDE_CONFIG_DIR"] = os.path.join(home, "issue30", "claude-config")
    env.pop("CLAUDECODE", None)
    env["CLAUDE_EFFORT"] = "medium"
    return env


def _invoke_claude(prompt, model, env, cwd, timeout):
    cmd = ["claude", "-p", "--model", model, "--output-format", "json",
           "--disallowedTools", *CLAUDE_DENY_TOOLS]
    start = time.monotonic()
    try:
        proc = subprocess.run(
            cmd, input=prompt, capture_output=True, text=True, encoding="utf-8",
            env=env, cwd=cwd, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"response": "", "envelope": None, "duration_s": time.monotonic() - start,
                "error": f"timeout after {timeout}s"}
    duration_s = time.monotonic() - start
    if proc.returncode != 0:
        return {"response": "", "envelope": None, "duration_s": duration_s,
                "error": f"nonzero exit {proc.returncode}: {(proc.stderr or '')[-2000:]}"}
    try:
        envelope = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        return {"response": "", "envelope": None, "duration_s": duration_s,
                "error": f"json parse failure: {e}; stdout_tail={proc.stdout[-500:]!r}"}
    result_text = envelope.get("result") if isinstance(envelope, dict) else None
    return {"response": result_text or "", "envelope": envelope, "duration_s": duration_s,
            "error": None}


def do_call(prompt, model, env, cwd, timeout=CALL_TIMEOUT_S):
    """One claude -p call; retries ONCE on timeout or nonzero exit, then gives up."""
    attempt = _invoke_claude(prompt, model, env, cwd, timeout)
    attempt["retried"] = False
    if attempt["error"] is None:
        return attempt
    retry = _invoke_claude(prompt, model, env, cwd, timeout)
    retry["retried"] = True
    return retry


def run_variant(variant, items, outdir):
    model = VARIANT_MODEL[variant]
    checkers_dir = os.path.join(outdir, "checkers")
    os.makedirs(checkers_dir, exist_ok=True)
    cwd = os.path.join(outdir, "cwd")
    os.makedirs(cwd, exist_ok=True)
    env = build_env()

    state = {"done": 0, "failures": 0, "cost": 0.0, "have_cost": False}
    lock = threading.Lock()
    total = len(items)
    arm_start = time.monotonic()

    def worker(item):
        call = do_call(checker_prompt(item["prompt"], item["response"]), model, env, cwd)
        envl = call.get("envelope") or {}
        record = {
            "variant": variant, "model": model,
            "skill": item["skill"], "eval_id": item["eval_id"], "rep": item["rep"],
            "response": call["response"],
            "cost_usd": envl.get("total_cost_usd"),
            "usage": envl.get("usage"),
            "duration_ms_wall": round(call.get("duration_s", 0.0) * 1000, 1),
            "duration_api_ms": envl.get("duration_api_ms"),
            "error": call.get("error"),
            "retried": call.get("retried", False),
        }
        key = f"{variant}.{item['skill']}.{item['eval_id']}.r{item['rep']}"
        with open(os.path.join(checkers_dir, f"{key}.json"), "w", encoding="utf-8") as fh:
            json.dump(record, fh, indent=1)
        with lock:
            state["done"] += 1
            if record["error"]:
                state["failures"] += 1
            if isinstance(record["cost_usd"], (int, float)):
                state["cost"] += record["cost_usd"]
                state["have_cost"] = True
            print(f"{key}  {call.get('duration_s', 0):.1f}s  [{state['done']}/{total}]", flush=True)

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(worker, item) for item in items]
        for f in as_completed(futures):
            exc = f.exception()
            if exc is not None:
                with lock:
                    state["failures"] += 1
                print(f"CHECKER CALL CRASHED: {exc!r}", file=sys.stderr, flush=True)

    summary = {
        "variant": variant, "model": model, "cells": total, "failures": state["failures"],
        "total_cost_usd": round(state["cost"], 6) if state["have_cost"] else None,
        "wall_clock_s": round(time.monotonic() - arm_start, 1),
        "per_call_parallelism": WORKERS,
    }
    with open(os.path.join(outdir, f"{variant}.checker-summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1)
    print(json.dumps(summary))


def main(argv=None):
    base = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(description="checker driver for routing-escalation (#109)")
    parser.add_argument("--variant", required=True, choices=sorted(VARIANT_MODEL))
    parser.add_argument("--inputs", default=os.path.join(base, "checker_inputs.json"))
    parser.add_argument("--outdir", default=os.path.expanduser("~/routing-run"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    with open(args.inputs, encoding="utf-8") as fh:
        items = json.load(fh)
    if not isinstance(items, list) or not items:
        print(f"ERROR: {args.inputs} did not contain a non-empty list", file=sys.stderr)
        return 1
    if args.dry_run:
        for item in items:
            print(f"{args.variant}.{item['skill']}.{item['eval_id']}.r{item['rep']}")
        print(f"[dry-run] {len(items)} checker calls for variant={args.variant}")
        return 0
    os.makedirs(args.outdir, exist_ok=True)
    run_variant(args.variant, items, args.outdir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
