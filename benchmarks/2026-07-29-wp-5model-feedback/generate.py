#!/usr/bin/env python3
"""Generation harness: 5 model lanes x 2 arms x 3 reps on ONE feedback task.

Design invariants this file enforces (metadata.json is the pre-registration of record):

  1. IDENTICAL PROMPT BYTES. The prompt for a given arm is built ONCE and asserted
     byte-identical across every lane and every rep. The only intended sources of variation
     are (a) the model and (b) the presence of the writing-plans body.
  2. UNIFORM INJECTION. The skill body is PREPENDED to the user prompt on every lane, rather
     than using each CLI's native system-prompt flag. Claude has --append-system-prompt and grok
     has --rules, but copilot has no equivalent; a per-lane mechanism would confound the
     cross-model effect-size comparison, which is the primary question. Labeled limitation.
  3. NO TOOLS ANYWHERE. Every lane runs with its tools stripped, so no cell can explore, and
     context cannot vary by what a CLI happened to read.
  4. HERMETIC ENV. This process runs under Claude Code with CLAUDE_EFFORT=xhigh and a pile of
     CLAUDE_CODE_* vars set. Inherited unchanged they would silently raise the reasoning effort
     of the three Claude lanes. clean_env() strips them and pins effort explicitly.
  5. NEUTRAL CWD. Every cell runs from an empty scratch dir outside the repo checkout, because
     CLAUDE_CONFIG_DIR does not stop project CLAUDE.md / AGENTS.md discovery by cwd traversal.

Resumable: an existing cell file with no error is skipped.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "skill-bench" / "scripts" / "lib"))
from judge import parse_copilot_jsonl  # noqa: E402  (reuse the proven copilot event parser)

REPS = 3
TIMEOUT_S = 900
CLAUDE_DENY = (HERE.parents[1] / "skill-bench" / "scripts" / "lib" / "deny_tools.txt"
               ).read_text().split()
# Grok takes an ALLOW-list, and its tool vocabulary is lowercase snake_case (read_file, list_dir,
# grep, run_terminal_command, ...). MEASURED 29-Jul-2026: `--disallowed-tools` is a NO-OP here — a
# cell run with `--disallowed-tools read_file,...` still read a planted file and returned its
# contents, and so did a cell run with the CamelCase names skill-bench/scripts/lib/judge.py uses.
# The allow-list DOES hold: the same probe under `--tools todo_write` answered "CANNOT READ".
# todo_write is an internal no-op with no filesystem or network reach. (`--sandbox` would be
# stronger but needs bubblewrap, which is not installed here.)
GROK_ALLOW = "todo_write"

# Copilot's tool vocabulary, read back from the CLI itself 29-Jul-2026. MEASURED: the bare
# `--available-tools` flag that skill-bench/scripts/lib/judge.py relies on does NOT strip tools
# (a probe cell read a planted file through it), and `--available-tools=none` merely pushed the
# model onto `curl file://`. The full `--excluded-tools` list below DOES hold: the same probe
# returned no planted value and the event stream shows no tool invocation.
COPILOT_EXCLUDE = ("bash,read_bash,stop_bash,list_bash,view,create,edit,web_fetch,"
                   "fetch_copilot_cli_documentation,skill,sql,session_store_sql,read_agent,"
                   "list_agents,write_agent,grep,glob,task,git,curl")


def count_copilot_tool_calls(stdout):
    """Tool INVOCATION events in copilot's JSONL stream (config events do not count).

    Hermeticity here is enforced by a flag whose behaviour is version-dependent, so every cell
    records whether the flag actually held rather than assuming it did.
    """
    n = 0
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        t = (ev.get("type") or "").lower()
        if "tool" in t and "updated" not in t and "status" not in t:
            n += 1
    return n
GROK_BIN = os.environ.get("GROK_BIN") or os.path.expanduser("~/.grok/bin/grok")
COPILOT_BIN = (os.environ.get("COPILOT_BIN") or shutil.which("copilot") or os.path.expanduser(
    "~/.vscode-server/data/User/globalStorage/github.copilot-chat/copilotCli/copilot"))

# ---------------------------------------------------------------- prompt construction

PLAN = (HERE / "plan.md").read_text(encoding="utf-8")


def skill_body():
    """writing-plans body with YAML frontmatter stripped — the injected surface."""
    text = (HERE / "treatments" / "writing-plans.SKILL.md").read_text(encoding="utf-8")
    if text.startswith("---"):
        text = text.split("---", 2)[2]
    return text.strip()


# Neutral task framing. Deliberately says NOTHING about what good feedback contains: naming
# desirable properties here would leak the rubric into the prompt and inflate every arm equally
# while destroying the instrument's ability to discriminate.
TASK = (
    "The following is a planning document.\n\n"
    "--- BEGIN PLANNING DOCUMENT ---\n"
    + PLAN +
    "\n--- END PLANNING DOCUMENT ---\n\n"
    "Give the author your feedback on this plan."
)

PROMPTS = {
    "bare": TASK,
    "wp": skill_body() + "\n\n---\n\n" + TASK,
}

# ---------------------------------------------------------------- environment hygiene


def clean_env():
    """Strip this session's Claude Code environment so it cannot leak into a cell.

    CLAUDE_EFFORT in particular is live at xhigh in the parent process; inherited, it would give
    the three Claude lanes a reasoning budget the grok and copilot lanes never get.
    """
    env = {k: v for k, v in os.environ.items()
           if not k.startswith("CLAUDE_CODE_") and k not in
           ("CLAUDECODE", "CLAUDE_EFFORT", "CLAUDE_PID", "AI_AGENT", "CLAUDE_CONFIG_DIR")}
    home = os.path.expanduser("~")
    env["PATH"] = os.path.join(home, ".local", "bin") + os.pathsep + env.get("PATH", "")
    env["CLAUDE_CONFIG_DIR"] = os.environ.get(
        "SKILL_BENCH_CONFIG_DIR", os.path.join(home, "issue30", "claude-config"))
    env["CLAUDE_EFFORT"] = "medium"   # pinned, identical for every Claude cell
    return env


# ---------------------------------------------------------------- lane runners
# Each returns (text, meta_dict). meta carries cost/usage/answering-model where the CLI reports it.


def run_claude(prompt, model, env, cwd, timeout):
    cmd = ["claude", "-p", "--model", model, "--output-format", "json",
           "--disallowedTools", *CLAUDE_DENY]
    r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, encoding="utf-8",
                       env=env, cwd=cwd, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"claude exit {r.returncode}: {(r.stderr or '')[-600:]}")
    env_obj = json.loads(r.stdout)
    return env_obj.get("result") or "", {
        "cost_usd": env_obj.get("total_cost_usd"),
        "usage": env_obj.get("usage"),
        "stop_reason": env_obj.get("stop_reason"),
        "answering_model": model,
        # num_turns > 1 means the model took extra turns; with every tool denied that is
        # reasoning, not tool use, but it is recorded so the claim is checkable per cell.
        "num_turns": env_obj.get("num_turns"),
    }


def run_grok(prompt, model, env, cwd, timeout):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(prompt)
        pf = f.name
    try:
        cmd = [GROK_BIN, "--prompt-file", pf, "-m", model, "--output-format", "json",
               "--tools", GROK_ALLOW, "--no-memory", "--disable-web-search"]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           env=env, cwd=cwd, timeout=timeout)
        if r.returncode != 0:
            raise RuntimeError(f"grok exit {r.returncode}: {(r.stderr or '')[-600:]}")
        env_obj = json.loads(r.stdout)
        answered = sorted((env_obj.get("modelUsage") or {}).keys()) or [model]
        return env_obj.get("text") or "", {
            "cost_usd": env_obj.get("total_cost_usd"),
            "usage": env_obj.get("usage"),
            "stop_reason": env_obj.get("stopReason"),
            "answering_model": answered[0],
        }
    finally:
        os.unlink(pf)


def run_copilot(prompt, model, env, cwd, timeout):
    """Copilot's --model is entitlement-gated on this account and rejects every explicit id, so
    the lane runs `auto`. The answering model is read back per cell from the event stream and
    recorded — owner direction, 29-Jul: 'copilot with auto is fine. Just note what model it is
    using for each run.'"""
    cmd = [COPILOT_BIN, "-p", prompt, "--model", model, "--output-format", "json",
           f"--excluded-tools={COPILOT_EXCLUDE}", "--no-custom-instructions",
           "--disable-builtin-mcps", "--no-remote", "--no-remote-export", "--log-level", "none"]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       env=env, cwd=cwd, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"copilot exit {r.returncode}: {(r.stderr or '')[-600:]}")
    text, answered = parse_copilot_jsonl(r.stdout)
    if not text:
        raise RuntimeError(f"copilot produced no assistant text; stdout_tail={r.stdout[-400:]!r}")
    return text, {"cost_usd": None, "usage": None, "stop_reason": None,
                  "answering_model": answered,
                  "tool_calls": count_copilot_tool_calls(r.stdout)}


LANES = {
    "fable5":  {"runner": run_claude,  "model": "claude-fable-5",             "family": "anthropic"},
    "opus5":   {"runner": run_claude,  "model": "claude-opus-5",              "family": "anthropic"},
    "haiku45": {"runner": run_claude,  "model": "claude-haiku-4-5-20251001",  "family": "anthropic"},
    "grok":    {"runner": run_grok,    "model": "grok-4.5",                   "family": "xai"},
    "copilot": {"runner": run_copilot, "model": "auto",                       "family": "router"},
}
ARMS = ("bare", "wp")

# ---------------------------------------------------------------- cell execution


def run_cell(lane, arm, rep, out, state, lock, cap):
    cell = f"{lane}-{arm}-r{rep}"
    path = out / f"{cell}.json"
    if path.exists():
        try:
            if not json.loads(path.read_text(encoding="utf-8"))["summary"]["error"]:
                print(f"[{cell}] exists, skipped", flush=True)
                return
        except Exception:
            pass
    with lock:
        if state["halt"]:
            return
    spec = LANES[lane]
    env = clean_env()
    cwd = tempfile.mkdtemp(prefix=f"wpcell-{cell}-")
    started = datetime.now(timezone.utc)
    t0 = time.monotonic()
    text, meta, err, retried = "", {}, None, False
    for attempt in (1, 2):
        try:
            text, meta = spec["runner"](PROMPTS[arm], spec["model"], env, cwd, TIMEOUT_S)
            err = None
            break
        except Exception as e:                      # noqa: BLE001 - record every failure mode
            err = f"{type(e).__name__}: {e}"[:900]
            retried = attempt == 1
            if attempt == 1:
                time.sleep(5)
    shutil.rmtree(cwd, ignore_errors=True)
    summary = {
        "error": err,
        "retried": retried,
        "duration_s": round(time.monotonic() - t0, 1),
        "cost_usd": meta.get("cost_usd"),
        "usage": meta.get("usage"),
        "stop_reason": meta.get("stop_reason"),
        "answering_model": meta.get("answering_model"),
        "tool_calls": meta.get("tool_calls"),      # copilot lane: measured, not assumed
        "num_turns": meta.get("num_turns"),        # claude lanes
        "response_chars": len(text or ""),
        "timestamps": {"start": started.isoformat(),
                       "end": datetime.now(timezone.utc).isoformat()},
    }
    record = {"cell": cell, "lane": lane, "requested_model": spec["model"],
              "family": spec["family"], "arm": arm, "rep": rep,
              "prompt_sha256_prefix": PROMPT_IDS[arm], "summary": summary, "response": text}
    path.write_text(json.dumps(record, indent=1), encoding="utf-8")
    with lock:
        state["spent"] += summary["cost_usd"] or 0.0
        if cap is not None and state["spent"] > cap:
            state["halt"] = True
    print(f"[{cell}] model={summary['answering_model']} chars={summary['response_chars']} "
          f"cost={summary['cost_usd']} spent=${state['spent']:.2f} err={err}", flush=True)


import hashlib  # noqa: E402
PROMPT_IDS = {a: hashlib.sha256(p.encode("utf-8")).hexdigest()[:16] for a, p in PROMPTS.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true",
                    help="one bare cell per lane -> pilot-outputs/ (ADR 0066 cost pilot)")
    ap.add_argument("--lanes", nargs="+", default=sorted(LANES))
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    meta = json.loads((HERE / "metadata.json").read_text(encoding="utf-8"))
    if args.pilot:
        out, cap = HERE / "pilot-outputs", meta["cost"]["pilot_cap_usd"]
        tasks = [(ln, "bare", 1) for ln in args.lanes]
    else:
        out, cap = HERE / "outputs", meta["cost"]["ceiling_usd"]
        tasks = [(ln, arm, rep) for ln in args.lanes for arm in ARMS
                 for rep in range(1, REPS + 1)]
    out.mkdir(exist_ok=True)

    print(f"prompt ids: {PROMPT_IDS}  (bare {len(PROMPTS['bare'])} chars, "
          f"wp {len(PROMPTS['wp'])} chars)", flush=True)
    print(f"{len(tasks)} cells -> {out.name}/ , cap ${cap}", flush=True)

    state, lock = {"spent": 0.0, "halt": False}, threading.Lock()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(lambda t: run_cell(*t, out, state, lock, cap), tasks))
    if state["halt"]:
        sys.exit(f"backstop: ${state['spent']:.2f} > ${cap} — halted, resumable")
    print(f"complete: measured spend ${state['spent']:.2f} "
          f"(grok/copilot are subscription-billed and report $0 or None)")


if __name__ == "__main__":
    main()
