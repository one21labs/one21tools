#!/usr/bin/env python3
"""Shared hermetic `claude -p` driver for benchmark harnesses (ADR 0023, issue #110).

One home for the executor plumbing every hermetic benchmark harness needs -- import this instead
of copying it (issue #110). Stdlib only. The two pre-#110 harnesses
(2026-07-10-tiered-execution-fullgrid/harness.py, 2026-07-10-routing-escalation/checker_harness.py)
are append-only snapshots and keep their copies.

The hermetic pattern (ADR 0023):
  - CLAUDE_CONFIG_DIR -> $HOME/issue30/claude-config (clean config: no plugins, credentials only)
  - --disallowedTools CLAUDE_DENY_TOOLS (real tool denial, not a runner convention)
  - prompt on stdin; NEUTRAL_FRAME as the prompt-level counterpart of the deny list
  - every call run from an empty scratch cwd OUTSIDE the repo checkout (CLAUDE_CONFIG_DIR does
    not stop project-level CLAUDE.md auto-discovery by cwd traversal -- verified empirically,
    see the fullgrid README)

Every call result carries start/end UTC timestamps so pre-registration-precedes-run is readable
off the records themselves, not only off git commit ordering.
"""
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_TIMEOUT_S = 600

# One language-neutral deny-list home (ADR 0041): newline-delimited deny_tools.txt, read here
# for python and via `mapfile -t DENY < .../deny_tools.txt` for bash harnesses. Includes the
# task/collaboration + subagent tools (issue #108) -- without them a nested `claude -p` session
# reads and writes the PARENT session's shared task list (an ADR 0023 hermeticity hole).
CLAUDE_DENY_TOOLS = Path(__file__).with_name("deny_tools.txt").read_text().split()

NEUTRAL_FRAME = (
    "Respond directly from the request text below. Do not read files, search the repository, "
    "run commands, or use any tools -- answer using only the text given in this request."
)


def build_env(effort="medium"):
    """Per-call environment, identical across arms (protocol symmetry)."""
    env = dict(os.environ)
    home = os.path.expanduser("~")
    env["PATH"] = os.path.join(home, ".local", "bin") + os.pathsep + env.get("PATH", "")
    # Clean auth-only config dir. Override with $SKILL_BENCH_CONFIG_DIR when installed elsewhere;
    # the default is this repo's fallback (a consumer must create their own credentials-only dir).
    env["CLAUDE_CONFIG_DIR"] = os.environ.get(
        "SKILL_BENCH_CONFIG_DIR", os.path.join(home, "issue30", "claude-config"))
    env.pop("CLAUDECODE", None)
    env["CLAUDE_EFFORT"] = effort
    return env


def neutral_cwd(outdir):
    """An empty scratch cwd outside the repo checkout (see module docstring)."""
    cwd = os.path.join(outdir, "cwd")
    os.makedirs(cwd, exist_ok=True)
    return cwd


def safe_get(d, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


def _invoke_claude(prompt, model, env, cwd, timeout, run=subprocess.run, allow=(), extra_args=()):
    """One `claude -p` subprocess call. `run` is injectable for tests.

    `allow` is the ADR 0052 carve-out: tools REMOVED from the deny list for a skill/agent arm
    (e.g. Read/Grep/Glob/Bash for a retrospect cell). Every name must exist in the deny list —
    allowing an unknown name is a harness spec error, not a silent no-op. `extra_args` appends
    raw CLI args (e.g. --append-system-prompt, --plugin-dir) after the deny flags.
    """
    unknown = set(allow) - set(CLAUDE_DENY_TOOLS)
    if unknown:
        raise ValueError(f"allow names not in deny list: {sorted(unknown)}")
    deny = [t for t in CLAUDE_DENY_TOOLS if t not in set(allow)]
    cmd = ["claude", "-p", "--model", model, "--output-format", "json",
           "--disallowedTools", *deny, *extra_args]
    started = datetime.now(timezone.utc)
    start = time.monotonic()

    def result(response, envelope, error):
        return {
            "response": response, "envelope": envelope, "error": error,
            "duration_s": time.monotonic() - start,
            "timestamps": {"start": started.isoformat(),
                           "end": datetime.now(timezone.utc).isoformat()},
        }

    try:
        proc = run(cmd, input=prompt, capture_output=True, text=True, encoding="utf-8",
                   env=env, cwd=cwd, timeout=timeout)
    except subprocess.TimeoutExpired:
        return result("", None, f"timeout after {timeout}s")
    if proc.returncode != 0:
        return result("", None, f"nonzero exit {proc.returncode}: {(proc.stderr or '')[-2000:]}")
    try:
        envelope = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        return result("", None, f"json parse failure: {e}; stdout_tail={proc.stdout[-500:]!r}")
    text = envelope.get("result") if isinstance(envelope, dict) else None
    return result(text or "", envelope, None)


def do_call(prompt, model, env, cwd, timeout=DEFAULT_TIMEOUT_S, run=subprocess.run,
            allow=(), extra_args=()):
    """One claude -p call; retries ONCE on timeout or nonzero exit, then gives up."""
    attempt = _invoke_claude(prompt, model, env, cwd, timeout, run=run, allow=allow,
                             extra_args=extra_args)
    attempt["retried"] = False
    if attempt["error"] is None:
        return attempt
    retry = _invoke_claude(prompt, model, env, cwd, timeout, run=run, allow=allow,
                           extra_args=extra_args)
    retry["retried"] = True
    return retry


def summarize_call(call):
    """Per-call record for a cell file: envelope figures + wall-clock + timestamps."""
    env = call.get("envelope")
    return {
        "duration_ms_wall": round(call.get("duration_s", 0.0) * 1000, 1),
        "duration_ms": safe_get(env, "duration_ms"),
        "duration_api_ms": safe_get(env, "duration_api_ms"),
        "cost_usd": safe_get(env, "total_cost_usd"),
        "usage": (env or {}).get("usage") if env else None,
        "stop_reason": safe_get(env, "stop_reason"),
        "timestamps": call.get("timestamps"),
        "error": call.get("error"),
        "retried": call.get("retried", False),
    }
