#!/usr/bin/env python3
"""Tiered-execution orchestrator for ONE benchmark cell (issue #41).

Pattern under test: MAIN model plans -> WORKER model implements -> MAIN validates -> on FAIL,
re-dispatch the worker with the validator's defect list, <= MAX_CYCLES worker attempts. The
final artifact is the LAST worker output (pre-registered cap; no best-of selection). The
validator sees ONLY the task + plan + deliverable — never the eval's grading expectations
(this file never opens meta.json; poka-yoke against teaching to the test).

Invoked per-cell by harness.sh (which owns hermeticity: relocated user memory, empty cwd via
HERMETIC_CWD, and the shared neutral framing). Every call is a fresh hermetic `claude -p`
with the SAME neutral system prompt as the solo arms; role instructions ride the user prompt,
so framing is arm-invariant. Roles via env: MAIN_MODEL (default sonnet), WORKER_MODEL
(default haiku), MAX_CYCLES (default 3).

Writes OUT/<key>.tiered.<rep>.txt (final artifact) and .trace.json (every call's model,
usage, cost, duration, validator verdicts, cycle count) — the honest total-cost record:
the orchestration overhead IS the tax under test.
"""
import json, os, re, subprocess, sys

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("OUT", os.path.join(BASE, "outputs"))
EMPTY = os.environ.get("HERMETIC_CWD", "/tmp/hx_tiered_cwd")
MAIN = os.environ.get("MAIN_MODEL", "sonnet")
WORKER = os.environ.get("WORKER_MODEL", "haiku")
MAX_CYCLES = int(os.environ.get("MAX_CYCLES", "3"))
DENY = ["Skill", "Task", "Read", "Grep", "Glob", "Bash", "Edit", "Write",
        "WebFetch", "WebSearch", "NotebookEdit"]
BASE_SYS = ("You are in a headless session with no file-system or code-execution tools; "
            "you cannot open the user's project or run anything. Respond in plain text.")

PLAN = """You are the tech lead. A worker will implement the task below; you will not implement it yourself.
Write a brief implementation plan for the worker: an explicit requirements checklist derived ONLY from the task's own text, the pitfalls to avoid, and the exact deliverable format expected. Be specific and complete but brief.

TASK:
{task}"""

WORK = """You are the implementer on a team. Produce the COMPLETE deliverable the task asks for, following your tech lead's plan. Output the deliverable itself (full file contents wherever the task asks for a file), not a summary or a description of it.

TASK:
{task}

TECH LEAD'S PLAN:
{plan}"""

REWORK = """Your previous attempt was rejected by the tech lead. Produce a CORRECTED complete deliverable fixing every listed defect while still satisfying the whole task. Output the full corrected deliverable, not a diff.

TASK:
{task}

TECH LEAD'S PLAN:
{plan}

YOUR PREVIOUS ATTEMPT:
{prev}

DEFECTS TO FIX:
{defects}"""

VALIDATE = """You are the tech lead validating a worker's deliverable before accepting it. Judge it strictly and ONLY against the task's own requirements (and your plan) — every requirement must be genuinely, fully satisfied by the deliverable text.
Reply with ONLY a JSON object, no other text: {{"pass": true|false, "defects": ["specific actionable defect", ...]}} — defects empty iff pass is true.

TASK:
{task}

PLAN:
{plan}

DELIVERABLE:
{artifact}"""


def call(model, prompt):
    """One hermetic claude -p call; returns (text, meta-for-trace)."""
    env = dict(os.environ, CLAUDE_EFFORT="medium")
    p = subprocess.run(
        ["claude", "-p", "--model", model, "--output-format", "json",
         "--append-system-prompt", BASE_SYS, "--disallowedTools", *DENY],
        input=prompt, capture_output=True, text=True, cwd=EMPTY, env=env, timeout=900)
    d = json.loads(p.stdout)
    return (d.get("result") or "", {
        "model": model, "duration_ms": d.get("duration_ms"),
        "cost_usd": d.get("total_cost_usd"), "usage": d.get("usage"),
        "model_usage": d.get("modelUsage"),
    })


def parse_verdict(text):
    """Extract {"pass":..,"defects":[..]} from the validator reply; None if unparseable."""
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        v = json.loads(m.group(0))
        return {"pass": bool(v.get("pass")), "defects": [str(x) for x in v.get("defects") or []]}
    except (json.JSONDecodeError, AttributeError):
        return None


def run(key, rep):
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(EMPTY, exist_ok=True)
    with open(os.path.join(BASE, "prompts", key + ".txt"), encoding="utf-8") as fh:
        task = fh.read()
    calls, verdicts = [], []

    plan, m = call(MAIN, PLAN.format(task=task))
    calls.append({"role": "plan", **m})

    artifact, defects = "", []
    for cycle in range(1, MAX_CYCLES + 1):
        prompt = (WORK.format(task=task, plan=plan) if cycle == 1 else
                  REWORK.format(task=task, plan=plan, prev=artifact, defects="\n".join(f"- {d}" for d in defects)))
        artifact, m = call(WORKER, prompt)
        calls.append({"role": f"implement.{cycle}", **m})

        vtext, m = call(MAIN, VALIDATE.format(task=task, plan=plan, artifact=artifact))
        calls.append({"role": f"validate.{cycle}", **m})
        v = parse_verdict(vtext)
        # Unparseable verdict: accept-and-stop, recorded — never a free extra worker cycle.
        verdicts.append({"cycle": cycle, "parsed": v is not None, **(v or {"pass": True, "defects": []})})
        if v is None or v["pass"]:
            break
        defects = v["defects"] or ["deliverable rejected; defects unspecified"]

    stem = os.path.join(OUT, f"{key}.tiered.{rep}")
    with open(stem + ".txt", "w", encoding="utf-8") as fh:
        fh.write(artifact)
    trace = {"key": key, "rep": rep, "main_model": MAIN, "worker_model": WORKER,
             "cycles": verdicts[-1]["cycle"], "internal_pass": verdicts[-1]["pass"],
             "verdicts": verdicts, "calls": calls,
             "total_cost_usd": round(sum(c["cost_usd"] or 0 for c in calls), 6),
             "total_duration_ms": sum(c["duration_ms"] or 0 for c in calls)}
    with open(stem + ".trace.json", "w", encoding="utf-8") as fh:
        json.dump(trace, fh, indent=1)
    print(f"tiered {key}.{rep}: cycles={trace['cycles']} internal_pass={trace['internal_pass']} "
          f"cost=${trace['total_cost_usd']}")


if __name__ == "__main__":
    run(sys.argv[1], int(sys.argv[2]))
