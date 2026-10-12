#!/usr/bin/env python3
"""Usage-limit guard: pause every paid `claude -p` call at 80% of a subscription window, resume
after the window resets (owner policy 2026-10-12; ADR 0099).

Why: benchmark calls draw on the SAME subscription limits as the operator's own session. Run to
exhaustion, the limit rejects calls with exit 1 and an empty stderr — a mass of ERROR cells that
reads like a harness defect (measured 2026-10-12: 46/80 and then 23/80 prescreen cells), and it
starves the operator's session too. Pausing at a threshold keeps headroom for the operator and
turns a hard failure into a wait.

Signal: `claude -p --output-format stream-json --verbose` emits a `rate_limit_event` whose
`rate_limit_info.unifiedWindows` carries `utilization` (0..1) and `resetsAt` (epoch s) per window
(five_hour, seven_day). decide() is PURE (now injected) so the policy is unit-testable; UsageGate
is the thin thread-safe wrapper every caller in the process shares (GATE).

Threshold: $SKILL_BENCH_PAUSE_AT (default 0.80); 1 disables the early pause but a REJECTED status
still waits for the reset — retrying into a closed window only manufactures ERROR cells.
"""
import json
import os
import subprocess
import sys
import threading
import time

DEFAULT_PAUSE_AT = 0.80
RESUME_BUFFER_S = 60  # a window reported reset at T is not reliably open at exactly T


def pause_at():
    try:
        return float(os.environ.get("SKILL_BENCH_PAUSE_AT", DEFAULT_PAUSE_AT))
    except ValueError:
        return DEFAULT_PAUSE_AT


def decide(info, threshold, now):
    """-> {"pause": bool, "resume_at": epoch|None, "why": str}. Pause when the limit already
    rejected (status other than allowed) or any window's utilization >= threshold; resume after
    the LATEST reset among the windows that triggered (all must reopen)."""
    if not info:
        return {"pause": False, "resume_at": None, "why": "no rate-limit signal"}
    windows = info.get("unifiedWindows") or {}
    hot = {name: w for name, w in windows.items()
           if (w.get("utilization") or 0) >= threshold and (w.get("resetsAt") or 0) > now}
    rejected = info.get("status") not in (None, "allowed", "allowed_warning")
    if rejected and not hot and (info.get("resetsAt") or 0) > now:
        hot = {info.get("rateLimitType") or "limit": {"utilization": 1.0,
                                                      "resetsAt": info["resetsAt"]}}
    if not hot:
        return {"pause": False, "resume_at": None, "why": "below threshold"}
    resume = max(w["resetsAt"] for w in hot.values()) + RESUME_BUFFER_S
    why = ", ".join(f"{n} at {w.get('utilization', 0):.0%}" for n, w in sorted(hot.items()))
    return {"pause": True, "resume_at": resume,
            "why": ("REJECTED: " if rejected else f">= {threshold:.0%}: ") + why}


def parse_stream(stdout):
    """stream-json stdout -> (envelope, rate_limit_info). Also accepts a plain single-object
    --output-format json body, so older callers and test fakes keep working."""
    envelope, info = None, None
    for line in (stdout or "").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(ev, dict):
            continue
        if ev.get("type") == "rate_limit_event":
            info = ev.get("rate_limit_info") or info
        elif ev.get("type") == "result" or ("result" in ev and "type" not in ev):
            envelope = ev
    return envelope, info


def streaming(cmd):
    """Rewrite a `claude -p ... --output-format json ...` argv to stream-json (+ --verbose, which
    stream-json requires in print mode) so the rate-limit event is visible."""
    out = list(cmd)
    if "--output-format" in out:
        i = out.index("--output-format")
        out[i + 1] = "stream-json"
    else:
        i = 2
        out[i:i] = ["--output-format", "stream-json"]
    if "--verbose" not in out:
        out.insert(i + 2, "--verbose")  # beside the format flag: trailing args stay trailing
    return out


class UsageGate:
    """Process-wide: every worker thread waits while any observed window is over threshold."""

    def __init__(self, threshold=None, sleep=time.sleep, now=time.time, log=None):
        self.threshold = pause_at() if threshold is None else threshold
        self.sleep, self.now = sleep, now
        self.log = log or (lambda m: print(m, file=sys.stderr, flush=True))
        self.lock = threading.Lock()
        self.resume_at = None
        self.last = None

    def observe(self, info):
        if not info:
            return None
        d = decide(info, self.threshold, self.now())
        with self.lock:
            self.last = info
            if d["pause"] and (self.resume_at is None or d["resume_at"] > self.resume_at):
                self.resume_at = d["resume_at"]
                self.log(f"usage guard: PAUSING new calls ({d['why']}) until "
                         f"{time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime(self.resume_at))}")
        return d

    def wait(self):
        """Block until no pause is in force. Returns seconds waited."""
        waited = 0.0
        while True:
            with self.lock:
                remaining = (self.resume_at or 0) - self.now()
                if remaining <= 0:
                    if self.resume_at is not None:
                        self.log("usage guard: window reset, RESUMING")
                    self.resume_at = None
                    return waited
            step = min(remaining, 300)
            self.sleep(step)
            waited += step


GATE = UsageGate()
MAX_LIMIT_WAITS = 3


def guarded_run(cmd, timeout, error, gate=None, run=None, **kw):
    """Run a `claude -p ... --output-format json` argv under the gate -> the result envelope.
    Raises `error` on timeout or failure, with the same messages the callers always raised; a
    call the limit REJECTED waits for the reset and is re-issued (up to MAX_LIMIT_WAITS)."""
    gate = gate or GATE
    for _ in range(MAX_LIMIT_WAITS + 1):
        gate.wait()
        try:
            r = (run or subprocess.run)(streaming(cmd), capture_output=True, text=True,
                                        timeout=timeout, **kw)
        except subprocess.TimeoutExpired:
            raise error(f"claude timeout after {timeout}s")
        envelope, info = parse_stream(r.stdout)
        d = gate.observe(info)
        if r.returncode == 0 and envelope is not None:
            return envelope
        if not (d and d["pause"] and "REJECTED" in d["why"]):
            break
    if r.returncode != 0:
        raise error(f"claude exit {r.returncode}: {(r.stderr or '')[-300:]}")
    raise error(f"claude returned no result event: {(r.stdout or '')[-300:]!r}")
