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
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import usage_guard

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


# Variables that make a child `claude -p` part of the PARENT Claude Code session, when the harness
# itself runs inside one. Measured 2026-10-12 in a cloud session: inherited, they gave the child the
# parent's session id (concurrent cells then hung or exited 1 with empty stderr), synced the
# account's skills, and injected the parent's attribution + user-email reminders into a "bare" arm.
# Auth variables survive (a credential is not session state), and so does the CLI's stream
# watchdog: without it a stalled response hung a cell for the full timeout (measured 2026-10-12).
PARENT_SESSION_PREFIXES = ("CLAUDE_CODE_", "CLAUDE_", "CCR_")
PARENT_SESSION_NAMES = ("CLAUDECODE", "SESSION_INGRESS_URL", "AI_AGENT")
KEEP = ("CLAUDE_CODE_OAUTH_TOKEN", "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX",
        "CLAUDE_CODE_USE_FOUNDRY", "CLAUDE_CODE_SKIP_BEDROCK_AUTH",
        "CLAUDE_CODE_SKIP_VERTEX_AUTH", "CLAUDE_CODE_SKIP_FOUNDRY_AUTH",
        "CLAUDE_ENABLE_STREAM_WATCHDOG")


def detached_env():
    """The caller's environment minus any parent Claude Code session (PARENT_SESSION_* above);
    auth/provider keys in KEEP survive. The one home of that filter."""
    return {k: v for k, v in os.environ.items()
            if k in KEEP or not (k in PARENT_SESSION_NAMES
                                      or k.startswith(PARENT_SESSION_PREFIXES))}


def build_env(effort="medium"):
    """Per-call environment, identical across arms (protocol symmetry): detached_env() plus the
    hermetic overrides below."""
    env = detached_env()
    home = os.path.expanduser("~")
    env["PATH"] = os.path.join(home, ".local", "bin") + os.pathsep + env.get("PATH", "")
    # Clean auth-only config dir. Override with $SKILL_BENCH_CONFIG_DIR when installed elsewhere;
    # the default is this repo's fallback (a consumer must create their own credentials-only dir).
    env["CLAUDE_CONFIG_DIR"] = os.environ.get(
        "SKILL_BENCH_CONFIG_DIR", os.path.join(home, "issue30", "claude-config"))
    env["CLAUDE_EFFORT"] = effort
    return env


def neutral_cwd(outdir):
    """An empty scratch cwd OUTSIDE the repo checkout (see module docstring), named after outdir.

    Built under the system temp dir, never under outdir: every caller passes its outputs dir,
    which lives inside the checkout, so the old `<outdir>/cwd` auto-discovered this repo's
    CLAUDE.md into every arm (measured 2026-10-12: a bare call under benchmarks/ quoted its
    heading). The precondition is enforced here rather than trusted to each caller."""
    cwd = tempfile.mkdtemp(prefix=f"neutral-cwd-{Path(outdir).name}-")
    return cwd


def fresh_copy(src, tag=None):
    """A private temp copy of a scenario bundle for ONE call — per-cell fresh-copy hermetics:
    no cell ever sees another cell's writes. Caller removes it (shutil.rmtree) after capture.

    The dir name is neutral: a cell tag in it (cell-S1-C-r1-...) told a subject with a cwd
    which arm it was in. `tag` is ignored, kept only so frozen benchmark callers still run."""
    workdir = tempfile.mkdtemp(prefix="cell-")
    shutil.rmtree(workdir)
    shutil.copytree(src, workdir, symlinks=True)
    return workdir


def capture_artifacts(workdir, src, pattern="*.md", limit=20000):
    """Every file matching pattern that the CELL created (absent from the source bundle).
    The #185 armd lesson: capture for EVERY arm, and never sweep pre-existing corpus files —
    an arm-skewed capture grades as quality when it is infrastructure (#191)."""
    out = {}
    for p in Path(workdir).rglob(pattern):
        rel = str(p.relative_to(workdir))
        if not (Path(src) / rel).exists():
            out[rel] = p.read_text(encoding="utf-8", errors="replace")[:limit]
    return out


def safe_get(d, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


def _invoke_claude(prompt, model, env, cwd, timeout, run=subprocess.run, allow=(), extra_args=(),
                   gate=None):
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
            "max_output_tokens": env.get("CLAUDE_CODE_MAX_OUTPUT_TOKENS"),
            "duration_s": time.monotonic() - start,
            "timestamps": {"start": started.isoformat(),
                           "end": datetime.now(timezone.utc).isoformat()},
        }

    try:
        proc = run(usage_guard.streaming(cmd), input=prompt, capture_output=True, text=True,
                   encoding="utf-8", env=env, cwd=cwd, timeout=timeout)
    except subprocess.TimeoutExpired:
        return result("", None, f"timeout after {timeout}s")
    envelope, info = usage_guard.parse_stream(proc.stdout)
    verdict = (gate or usage_guard.GATE).observe(info)
    if proc.returncode != 0 or envelope is None:
        out = result("", None, f"nonzero exit {proc.returncode}: {(proc.stderr or '')[-2000:]}"
                     if proc.returncode != 0 else
                     f"json parse failure: no result event; stdout_tail={(proc.stdout or '')[-500:]!r}")
        out["usage_limited"] = bool(verdict and verdict["pause"] and "REJECTED" in verdict["why"])
        return out
    text = envelope.get("result") if isinstance(envelope, dict) else None
    return result(text or "", envelope, None)


def do_call(prompt, model, env, cwd, timeout=DEFAULT_TIMEOUT_S, run=subprocess.run,
            allow=(), extra_args=(), gate=None):
    """One claude -p call; retries ONCE on timeout or nonzero exit, then gives up.

    Usage-limit policy (usage_guard, ADR 0099): every attempt first waits out any pause the gate
    holds (a window at >= 80%), and an attempt the limit REJECTED waits for the reset and is
    re-issued without spending the one retry — a closed window is not a cell failure."""
    gate = gate or usage_guard.GATE

    def attempt():
        for _ in range(usage_guard.MAX_LIMIT_WAITS + 1):
            gate.wait()
            a = _invoke_claude(prompt, model, env, cwd, timeout, run=run, allow=allow,
                               extra_args=extra_args, gate=gate)
            if not a.get("usage_limited"):
                return a
        return a

    first = attempt()
    first["retried"] = False
    if first["error"] is None:
        return first
    retry = attempt()
    retry["retried"] = True
    return retry


CAP_HIT_FRACTION = 0.97


def summarize_call(call, requested_model=None):
    """Per-call record for a cell file: envelope figures + wall-clock + timestamps. With an exact
    `claude-*` requested_model, a call the envelope says another model served is an ERROR cell: a
    silently substituted model would measure the wrong arm (an alias cannot be checked).

    A reply whose output tokens reach CAP_HIT_FRACTION of the call's CLAUDE_CODE_MAX_OUTPUT_TOKENS
    is an ERROR cell too: past the cap the CLI returns only the reply's LAST chunk, so a grader
    scores a fragment (measured 2026-10-18: 7 with-arm cells, all graded as quality)."""
    env = call.get("envelope")
    served = sorted(((env or {}).get("modelUsage") or {}).keys())
    error = call.get("error")
    if (not error and served and requested_model and requested_model.startswith("claude-")
            and requested_model not in served):
        error = f"requested {requested_model}, envelope served {served}"
    cap = call.get("max_output_tokens")
    out_tokens = safe_get(env, "usage", "output_tokens") or 0
    if not error and cap and out_tokens >= int(cap) * CAP_HIT_FRACTION:
        error = f"output hit the {cap}-token cap ({out_tokens}): partial capture"
    return {
        "duration_ms_wall": round(call.get("duration_s", 0.0) * 1000, 1),
        "duration_ms": safe_get(env, "duration_ms"),
        "duration_api_ms": safe_get(env, "duration_api_ms"),
        "cost_usd": safe_get(env, "total_cost_usd"),
        "usage": (env or {}).get("usage") if env else None,
        "stop_reason": safe_get(env, "stop_reason"),
        "timestamps": call.get("timestamps"),
        "error": error,
        "served_models": served,
        "retried": call.get("retried", False),
    }
