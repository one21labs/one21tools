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
import json, os, subprocess, tempfile
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
        self.bin = bin or os.path.expanduser("~/.grok/bin/grok")
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


def make_judge(name):
    return {"grok": GrokJudge, "claude": ClaudeJudge}[name]()


def met_map(verdict):
    return {e["id"]: bool(e.get("met")) for e in (verdict.get("expectations") or [])}
