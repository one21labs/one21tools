#!/usr/bin/env python3
"""claude -p driver for the tiered-agent-execution benchmark (issue #41).

Runs ONE arm's full grid (24 evals x reps = 72 cells by default) via hermetic `claude -p`
subprocess calls -- stdlib only, no repo Python deps. Designed to run INSIDE WSL Debian, invoked
from Windows as:

    wsl -d Debian -- python3 /mnt/c/Users/ajmcc/projects/one21tools/benchmarks/2026-07-10-tiered-execution-fullgrid/harness.py --arm sonnet-solo

Replaces the prior harness.workflow.js executor (see README "Why claude -p instead of the Workflow
runner"). Reuses harness.workflow.js's NEUTRAL_FRAME and plan/work/validate prompt texts verbatim.

Per-cell environment (identical across arms -- protocol symmetry):
  PATH            = $HOME/.local/bin prepended
  CLAUDE_CONFIG_DIR = $HOME/issue30/claude-config   (clean config: no plugins, credentials only)
  CLAUDECODE      stripped
  CLAUDE_EFFORT   = medium (matches prior benchmarks)
  cwd             = <outdir>/cwd, an empty scratch directory OUTSIDE the repo checkout -- without
                    this, `claude -p` auto-discovers this repo's CLAUDE.md by cwd traversal
                    (CLAUDE_CONFIG_DIR only redirects the global ~/.claude dir, not project-level
                    discovery) and every response opens with unsolicited "I've reviewed the project
                    instructions..." narration. Verified empirically before writing this driver:
                    same prompt from the repo root pulled in ~17K tokens of cached project context
                    and 9.7s; from an empty cwd, clean and 1.7s. See README for the transcript.

Executor command: claude -p --model <model> --output-format json --disallowedTools Skill Task
Read Grep Glob Bash Edit Write WebFetch WebSearch NotebookEdit -- prompt on stdin.

Arms:
  sonnet-solo / haiku-solo -- one call, NEUTRAL_FRAME + request, answered directly.
  tiered -- orchestrator (sonnet) plans -> worker (haiku) implements -> orchestrator (sonnet)
    validates against the ORIGINAL request (STRICT JSON {"ok": bool, "corrections": str}) -> if
    not ok, ONE worker redispatch with corrections (max 2 worker iterations). The final
    deliverable is always the worker's LAST output -- the orchestrator never rewrites it.

Writes one record per cell to <outdir>/cells/<arm>.<skill>.<eval_id>.r<rep>.json and one
<outdir>/<arm>.summary.json at arm end. Streams a progress line per completed cell to stdout.
"""
import argparse
import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

WORKERS = 4  # EXACTLY 4 for every arm -- protocol symmetry (do not make this arm-dependent).
CALL_TIMEOUT_S = 600
DEFAULT_REPS = 3

CLAUDE_DENY_TOOLS = [
    "Skill", "Task", "Read", "Grep", "Glob", "Bash", "Edit", "Write",
    "WebFetch", "WebSearch", "NotebookEdit",
]

# Copied verbatim from harness.workflow.js -- the ONLY between-arm difference is executor
# configuration (model tier / orchestration pattern), never prompt text (ADR 0023 arm symmetry).
NEUTRAL_FRAME = (
    "Respond directly from the request text below. Do not read files, search the repository, "
    "run commands, or use any tools -- answer using only the text given in this request."
)


def plan_prompt(prompt):
    return (
        f"{NEUTRAL_FRAME}\n\n"
        "You are the PLANNING lead for a task a separate implementer will carry out. Read the "
        "request below and write a brief, concrete spec for the implementer: what to produce, "
        "the key constraints, and the shape of the deliverable. Do NOT produce the deliverable "
        "yourself -- write the spec only.\n\n"
        f"Request:\n{prompt}"
    )


def work_prompt(prompt, spec, corrections):
    corrections_block = ""
    if corrections:
        corrections_block = (
            "\n\nA reviewer found problems with your PREVIOUS attempt and asked for these "
            f"corrections -- address them:\n{corrections}"
        )
    return (
        f"{NEUTRAL_FRAME}\n\n"
        "You are the IMPLEMENTER. Follow the spec below to produce the deliverable for the "
        f"original request.{corrections_block}\n\n"
        f"Original request:\n{prompt}\n\n"
        f"Spec:\n{spec}\n\n"
        "Write the deliverable directly (the finished output the requester asked for, not a "
        "plan or commentary about it)."
    )


def validate_prompt(prompt, deliverable):
    return (
        f"{NEUTRAL_FRAME}\n\n"
        "You are the REVIEWING lead. Judge whether the deliverable below actually satisfies the "
        "original request -- fully, concretely, and without gaps. Return ok=true only if it is "
        "genuinely ready to hand back as-is; ok=false with specific, actionable corrections "
        "otherwise.\n\n"
        "Respond with STRICT JSON ONLY, matching exactly this shape and nothing else -- no prose "
        'before or after: {"ok": <true or false>, "corrections": "<string, empty if ok>"}\n\n'
        f"Original request:\n{prompt}\n\n"
        f"Deliverable:\n{deliverable}"
    )


def safe_get(d, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


def sum_optional(values):
    present = [v for v in values if isinstance(v, (int, float))]
    return sum(present) if present else None


def extract_first_json_object(text):
    """Find and return the first balanced {...} substring in text, or None."""
    if not text:
        return None
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def parse_validate_response(text):
    """Returns (parsed_dict_or_None, parse_error_str_or_None)."""
    candidate = extract_first_json_object(text or "")
    if candidate is None:
        return None, "no JSON object found in validator output"
    try:
        obj = json.loads(candidate)
    except json.JSONDecodeError as e:
        return None, f"json parse error: {e}"
    if not isinstance(obj, dict) or "ok" not in obj:
        return None, "parsed JSON missing required 'ok' field"
    return obj, None


def build_env():
    env = dict(os.environ)
    home = os.path.expanduser("~")
    local_bin = os.path.join(home, ".local", "bin")
    env["PATH"] = local_bin + os.pathsep + env.get("PATH", "")
    env["CLAUDE_CONFIG_DIR"] = os.path.join(home, "issue30", "claude-config")
    env.pop("CLAUDECODE", None)
    env["CLAUDE_EFFORT"] = "medium"
    return env


def neutral_cwd(outdir):
    cwd = os.path.join(outdir, "cwd")
    os.makedirs(cwd, exist_ok=True)
    return cwd


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
        stderr_tail = (proc.stderr or "")[-2000:]
        return {"response": "", "envelope": None, "duration_s": duration_s,
                "error": f"nonzero exit {proc.returncode}: {stderr_tail}"}
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


def summarize_call(call):
    env = call.get("envelope")
    return {
        "duration_ms_wall": round(call.get("duration_s", 0.0) * 1000, 1),
        "duration_ms": safe_get(env, "duration_ms"),
        "duration_api_ms": safe_get(env, "duration_api_ms"),
        "cost_usd": safe_get(env, "total_cost_usd"),
        "usage": (env or {}).get("usage") if env else None,
        "stop_reason": safe_get(env, "stop_reason"),
        "error": call.get("error"),
        "retried": call.get("retried", False),
    }


def base_record(item, arm, rep, response, calls, started, ended):
    ins = sum_optional([
        (c.get("usage") or {}).get("input_tokens") for c in calls.values()
    ])
    outs = sum_optional([
        (c.get("usage") or {}).get("output_tokens") for c in calls.values()
    ])
    costs = sum_optional([c.get("cost_usd") for c in calls.values()])
    api_total = sum_optional([c.get("duration_api_ms") for c in calls.values()])
    wall_total = sum(c.get("duration_ms_wall", 0.0) for c in calls.values())

    usage = {"input_tokens": ins, "output_tokens": outs}
    if costs is not None:
        usage["cost_usd"] = costs

    record = {
        "skill": item["skill"],
        "eval_id": item["eval_id"],
        "arm": arm,
        "rep": rep,
        "response": response,
        "usage": usage,
        "duration_ms": {
            "per_call": {name: c.get("duration_ms_wall") for name, c in calls.items()},
            "total_wall_ms": round(wall_total, 1),
            "total_api_ms": api_total,
        },
        "timestamps": {"start": started.isoformat(), "end": ended.isoformat()},
        "calls": calls,
    }
    errors = [f"{name}: {c['error']}" for name, c in calls.items() if c.get("error")]
    if errors:
        record["error"] = "; ".join(errors)
    return record


def process_solo_cell(item, rep, arm, model, env, cwd):
    started = datetime.now(timezone.utc)
    prompt = f"{NEUTRAL_FRAME}\n\nRequest:\n{item['prompt']}"
    call = do_call(prompt, model, env, cwd)
    ended = datetime.now(timezone.utc)
    calls = {"exec": summarize_call(call)}
    return base_record(item, arm, rep, call["response"], calls, started, ended)


def process_tiered_cell(item, rep, env, cwd):
    started = datetime.now(timezone.utc)
    prompt = item["prompt"]

    plan_call = do_call(plan_prompt(prompt), "sonnet", env, cwd)
    spec = plan_call["response"]

    worker1_call = do_call(work_prompt(prompt, spec, None), "haiku", env, cwd)
    worker1 = worker1_call["response"]

    validate_call = do_call(validate_prompt(prompt, worker1), "sonnet", env, cwd)
    validate_parsed, validate_parse_err = parse_validate_response(validate_call["response"])

    calls = {
        "plan": summarize_call(plan_call),
        "worker1": summarize_call(worker1_call),
        "validate1": summarize_call(validate_call),
    }

    worker2 = None
    if validate_parsed is not None and validate_parsed.get("ok") is True:
        final_response = worker1
        iterations = 1
    else:
        if validate_parse_err:
            corrections = "validator output unparseable; follow the spec strictly"
        else:
            corrections = (validate_parsed or {}).get("corrections") or \
                "no specific corrections returned; try again from the spec."
        worker2_call = do_call(work_prompt(prompt, spec, corrections), "haiku", env, cwd)
        worker2 = worker2_call["response"]
        calls["worker2"] = summarize_call(worker2_call)
        final_response = worker2 or worker1
        iterations = 2

    ended = datetime.now(timezone.utc)
    record = base_record(item, "tiered", rep, final_response, calls, started, ended)
    record["plan"] = spec
    record["worker1"] = worker1
    record["validate1"] = {
        "raw": validate_call["response"],
        "parsed": validate_parsed,
        "parse_error": validate_parse_err,
    }
    record["worker2"] = worker2
    record["iterations"] = iterations
    return record


def run_arm(arm, evals, outdir, reps, dry_run=False):
    items = [(e, rep) for e in evals for rep in range(1, reps + 1)]
    total = len(items)

    if dry_run:
        for e, rep in items:
            print(f"{arm}.{e['skill']}.{e['eval_id']}.r{rep}")
        print(f"[dry-run] {total} cells for arm={arm} (no claude calls made)")
        return None

    cells_dir = os.path.join(outdir, "cells")
    os.makedirs(cells_dir, exist_ok=True)
    env = build_env()
    cwd = neutral_cwd(outdir)
    model_for = {"sonnet-solo": "sonnet", "haiku-solo": "haiku"}

    arm_start = time.monotonic()
    state = {"done": 0, "failures": 0, "tokens_in": 0.0, "tokens_out": 0.0,
             "cost": 0.0, "have_cost": False}
    lock = threading.Lock()

    def worker(e, rep):
        cell_start = time.monotonic()
        try:
            if arm == "tiered":
                record = process_tiered_cell(e, rep, env, cwd)
            else:
                record = process_solo_cell(e, rep, arm, model_for[arm], env, cwd)
        except Exception as exc:  # never crash the whole arm on one cell
            record = {
                "skill": e["skill"], "eval_id": e["eval_id"], "arm": arm, "rep": rep,
                "response": "", "usage": {"input_tokens": None, "output_tokens": None},
                "timestamps": {"start": None, "end": None},
                "error": f"cell crashed: {exc!r}",
            }
        cell_elapsed = time.monotonic() - cell_start
        key = f"{arm}.{e['skill']}.{e['eval_id']}.r{rep}"
        path = os.path.join(cells_dir, f"{key}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(record, fh, indent=1)

        with lock:
            state["done"] += 1
            if record.get("error"):
                state["failures"] += 1
            u = record.get("usage") or {}
            if isinstance(u.get("input_tokens"), (int, float)):
                state["tokens_in"] += u["input_tokens"]
            if isinstance(u.get("output_tokens"), (int, float)):
                state["tokens_out"] += u["output_tokens"]
            if isinstance(u.get("cost_usd"), (int, float)):
                state["cost"] += u["cost_usd"]
                state["have_cost"] = True
            print(f"{key}  {cell_elapsed:.1f}s  [{state['done']}/{total}]", flush=True)

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(worker, e, rep) for e, rep in items]
        for f in as_completed(futures):
            exc = f.exception()
            if exc is not None:
                with lock:
                    state["failures"] += 1
                print(f"CELL CRASHED (uncaught in pool): {exc!r}", file=sys.stderr, flush=True)

    wall = time.monotonic() - arm_start
    summary = {
        "arm": arm,
        "cells": total,
        "failures": state["failures"],
        "total_tokens_in": int(state["tokens_in"]),
        "total_tokens_out": int(state["tokens_out"]),
        "total_cost_usd": round(state["cost"], 6) if state["have_cost"] else None,
        "wall_clock_s": round(wall, 1),
        "per_call_parallelism": WORKERS,
    }
    with open(os.path.join(outdir, f"{arm}.summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1)
    print(json.dumps(summary))
    return summary


def main(argv=None):
    default_evals = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evals_args.json")
    parser = argparse.ArgumentParser(
        description="claude -p driver for the tiered-agent-execution benchmark (issue #41). "
                     "Run once per arm inside WSL Debian.",
    )
    parser.add_argument("--arm", required=True, choices=["sonnet-solo", "haiku-solo", "tiered"],
                         help="which arm's 24 evals x reps grid to execute")
    parser.add_argument("--outdir", default=os.path.expanduser("~/tiered-run"),
                         help="output directory (default: ~/tiered-run, expanded in WSL)")
    parser.add_argument("--evals-json", default=default_evals,
                         help="path to evals_args.json (default: alongside this script)")
    parser.add_argument("--reps", type=int, default=DEFAULT_REPS,
                         help=f"reps per eval (default: {DEFAULT_REPS})")
    parser.add_argument("--dry-run", action="store_true",
                         help="list the cells for this arm without calling claude")
    args = parser.parse_args(argv)

    with open(args.evals_json, encoding="utf-8") as fh:
        evals = json.load(fh)
    if not isinstance(evals, list) or not evals:
        print(f"ERROR: {args.evals_json} did not contain a non-empty list", file=sys.stderr)
        return 1

    if not args.dry_run:
        os.makedirs(args.outdir, exist_ok=True)

    run_arm(args.arm, evals, args.outdir, args.reps, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
