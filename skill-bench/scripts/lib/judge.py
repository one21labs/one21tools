#!/usr/bin/env python3
"""Pluggable judge backends for skill-bench — the cross-family judge substrate (ADR 0055).

A Judge takes a text prompt + JSON schema and returns a validated object. Two families ship so a
grader swap measures self-preference bias directly (the #172 prototype: opus met-rate 0.747 vs
grok 0.552, and the C-B verdict flipped +0.010 -> +0.125). Stdlib only; each backend shells its
CLI headless with tools denied so grading is pure-text and hermetic.

Backends:
  GrokJudge   -> grok -p --json-schema        (default; grok.com subscription = zero marginal cost)
  ClaudeJudge -> claude -p --output-format json (same-family baseline / A-B judge comparison)
"""
import json, os, shutil, subprocess, tempfile
import costing

# Known-good pure-text sandbox. NOTE (grok 0.2.99): longer deny lists or --disable-web-search trip a
# run_terminal_cmd tool-config validation bug — keep this exact set.
GROK_DENY = "Bash,Read,Write,Edit,WebSearch,WebFetch"
CLAUDE_DENY = "Bash,Read,Write,Edit,WebSearch,WebFetch,Glob,Grep,Task"


class JudgeError(RuntimeError):
    pass


def strip_json_fence(s):
    """Pure: strip ```json fences / prose around a JSON blob (claude -p has no schema mode)."""
    s = s.strip()
    if "```" in s:
        # take the content of the first fenced block if present
        parts = s.split("```")
        for seg in parts:
            seg = seg.strip()
            if seg.startswith("json"):
                seg = seg[4:].strip()
            if seg.startswith("{") or seg.startswith("["):
                return seg
    return s


class _CostTracking:
    """Mixin: accumulate token usage across grade() calls and price it notionally."""
    def _init_usage(self):
        self.usage = {}
        self.calls = 0

    def _record(self, envelope):
        self.calls += 1
        costing.add_usage(self.usage, costing.extract_usage(envelope))

    def cost_usd(self):
        """Notional (shadow) cost of all grade() calls at published API rates — real usage priced
        even though the subscription made it marginally free."""
        return round(costing.notional_cost(self.name, self.usage), 4) if self.usage else 0.0


class GrokJudge(_CostTracking):
    name = "grok-4.5"

    def __init__(self, bin=None, model="grok-4.5", timeout=300):
        # Portable resolution: explicit arg, then $GROK_BIN, then PATH, then the default installer
        # location. Works when skill-bench is installed as a plugin on any machine.
        self.bin = (bin or os.environ.get("GROK_BIN") or shutil.which("grok")
                    or os.path.expanduser("~/.grok/bin/grok"))
        self.model = model
        self.timeout = timeout
        self._init_usage()

    def grade(self, prompt, schema):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write(prompt); pf = f.name
        try:
            r = subprocess.run(
                [self.bin, "--prompt-file", pf, "--output-format", "json",
                 "--json-schema", json.dumps(schema), "--disallowed-tools", GROK_DENY],
                capture_output=True, text=True, timeout=self.timeout)
            if r.returncode != 0:
                raise JudgeError(f"grok exit {r.returncode}: {r.stderr[-300:]}")
            env = json.loads(r.stdout)
            self._record(env)
            so = env.get("structuredOutput")
            if not so:
                raise JudgeError("grok returned no structuredOutput")
            return so
        finally:
            os.unlink(pf)


class ClaudeJudge(_CostTracking):
    name = "claude-opus-4-8"

    def __init__(self, bin="claude", model="opus", timeout=300):
        self.bin = bin
        self.model = model
        self.timeout = timeout
        self._init_usage()

    def grade(self, prompt, schema):
        # claude -p has no --json-schema; ask for JSON-only and parse, retrying tolerant of fences.
        p = prompt + "\n\nReturn ONLY valid JSON matching this schema, no prose:\n" + json.dumps(schema)
        r = subprocess.run(
            [self.bin, "-p", p, "--output-format", "json", "--model", self.model,
             "--disallowedTools", CLAUDE_DENY],
            capture_output=True, text=True, timeout=self.timeout)
        if r.returncode != 0:
            raise JudgeError(f"claude exit {r.returncode}: {r.stderr[-300:]}")
        env = json.loads(r.stdout)
        self._record(env)
        return json.loads(strip_json_fence(env.get("result", "")))


class CachedJudge(_CostTracking):
    """Placeholder for offline --cache re-analysis: no live CLI needed, 0 calls, $0 cost. Lets
    bench-verdict recompute a verdict from a prior judge run on a machine with no grok/claude."""
    def __init__(self, name="cached"):
        self.name = name if name in costing.PRICES else "grok-4.5"
        self.display_name = name
        self._init_usage()
        self.fallback_note = None

    def grade(self, prompt, schema):
        raise JudgeError("CachedJudge cannot grade live — use only with --cache")


def cli_available(name, which=None):
    """Is a judge backend's CLI usable on this machine? Pure given `which` (inject for tests)."""
    which = which or shutil.which
    if name == "grok":
        return bool(os.environ.get("GROK_BIN")) or which("grok") is not None
    if name == "claude":
        return which("claude") is not None
    return False


SAME_FAMILY_NOTE = ("grok CLI not found — falling back to the claude judge. This is SAME-FAMILY "
                    "grading, so the self-preference caveat applies (absolute rates inflate, the "
                    "verdict can shift). Install grok or set $GROK_BIN to restore the cross-family judge.")


def resolve_judge(name, which=None):
    """Return (resolved_backend_name, fallback_note). 'auto' prefers grok (cross-family) and falls
    back to claude when grok is absent — not everyone has the grok CLI. An EXPLICIT judge that is
    unavailable raises with a remedy (respect the explicit choice; don't silently substitute)."""
    if name == "auto":
        if cli_available("grok", which):
            return "grok", None
        if cli_available("claude", which):
            return "claude", SAME_FAMILY_NOTE
        raise JudgeError("no judge CLI available: install grok or claude (or set $GROK_BIN)")
    if name in ("grok", "claude"):
        if cli_available(name, which):
            return name, None
        remedy = "set $GROK_BIN or install grok" if name == "grok" else "install the claude CLI"
        raise JudgeError(f"--judge {name} requested but its CLI is not available ({remedy}); "
                         f"use --judge auto to fall back gracefully")
    raise JudgeError(f"unknown judge {name!r} (use auto|grok|claude)")


def make_judge(name, which=None):
    resolved, note = resolve_judge(name, which)
    j = {"grok": GrokJudge, "claude": ClaudeJudge}[resolved]()
    j.fallback_note = note
    return j


def met_map(verdict):
    return {e["id"]: bool(e.get("met")) for e in (verdict.get("expectations") or [])}
