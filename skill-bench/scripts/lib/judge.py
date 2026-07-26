#!/usr/bin/env python3
"""Pluggable judge backends for skill-bench — the cross-family judge substrate (ADR 0055).

A Judge takes a text prompt + JSON schema and returns a validated object. Swapping the grader
measures self-preference bias directly (the #172 prototype changed the verdict — findings table in
skill-bench/README.md, "The cross-family judge"). Stdlib only; each backend shells its CLI headless
with tools denied so grading is pure-text and hermetic.

DESIGN DIRECTION — repo owner, 26-Jul-2026: "the skill should guide the user to customize to the
user's own environment, so it is general and not environment specific." Whichever judge an adopter
can actually reach is the right judge for them, so this file stays vendor-neutral (a registry plus
a bring-your-own `command` backend) and the SKILL walks them through wiring what they have
(references/judging.md). The backend set and registry mechanics are Claude's implementation of that
direction; the per-call family verification is Claude's own idea rather than a passed-down
requirement (ADR 0085 marks both directions) — it came out of measuring what copilot's router
actually did, not from the brief.

Backends:
  GrokJudge    -> grok -p --json-schema         (default; grok.com subscription = zero marginal cost)
  CopilotJudge -> copilot -p --output-format json (gpt/gemini/kimi via GitHub Copilot's router)
  CommandJudge -> $SKILL_BENCH_JUDGE_CMD        (bring your own: local server, in-house wrapper)
  ClaudeJudge  -> claude -p --output-format json (same-family baseline / A-B judge comparison)

Adding a family is a registry entry, not a new branch in the resolver — see BACKENDS below.
"""
import json, os, re, shutil, subprocess, tempfile
import costing

# Known-good pure-text sandbox. NOTE (grok 0.2.99): longer deny lists or --disable-web-search trip a
# run_terminal_cmd tool-config validation bug — keep this exact set.
GROK_DENY = "Bash,Read,Write,Edit,WebSearch,WebFetch"
CLAUDE_DENY = "Bash,Read,Write,Edit,WebSearch,WebFetch,Glob,Grep,Task"

# The generator's family. A "cross-family" judge is only cross-family if we know WHO answered, and
# a router that picks per call may pick this family: GitHub Copilot's `auto` was measured listing
# claude-haiku-4.5 among its own candidates (26-Jul-2026). A backend that cannot pin a model must
# therefore read back the model that answered and refuse a same-family grade rather than report an
# inflated met-rate as if it were independent.
GENERATOR_FAMILY = "anthropic"

# TWIN: pdca-workflow/scripts/crosscheck.mjs carries this table and parse_copilot_jsonl's logic in
# JS. Neither may import the other (ADR 0050: plugins ship standalone, no content dependencies), so
# the copies are structural — change one, change both. scripts/check-family-parity.test.mjs in the
# source repo fails the build if they drift.
_FAMILY_PATTERNS = ((r"claude|anthropic", "anthropic"), (r"grok|xai", "xai"),
                    (r"gpt|openai", "openai"), (r"gemini", "google"), (r"kimi|moonshot", "moonshot"))


def family_of(model_id):
    """Pure: vendor family for a model id. An id we cannot place is 'unknown' — never assumed
    foreign, because an unplaceable grader cannot evidence a cross-family grade."""
    for pattern, fam in _FAMILY_PATTERNS:
        if model_id and re.search(pattern, model_id, re.I):
            return fam
    return "unknown"


def parse_copilot_jsonl(stdout):
    """Pure: copilot's JSONL event stream -> (answer_text, model_id). The model id is only in the
    event stream (`auto` resolution or the model call), which is why this backend pays for JSONL
    instead of using the cleaner `-s`."""
    model, chunks = None, []
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        d = ev.get("data") or {}
        if d.get("chosenModel"):
            model = d["chosenModel"]
        elif d.get("model") and not model:
            model = d["model"]
        if ev.get("type") == "assistant.message" and isinstance(d.get("content"), str):
            chunks.append(d["content"])
        elif ev.get("type") == "assistant.message_delta" and isinstance(d.get("delta"), str):
            chunks.append(d["delta"])
    return "".join(chunks).strip(), model


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
            try:
                r = subprocess.run(
                    [self.bin, "--prompt-file", pf, "--output-format", "json",
                     "--json-schema", json.dumps(schema), "--disallowed-tools", GROK_DENY],
                    capture_output=True, text=True, timeout=self.timeout)
            except subprocess.TimeoutExpired:
                # Contract consistency: timeout is a JudgeError like every other failure mode —
                # a caller's per-cell handler must be able to catch ONE exception type (a raw
                # TimeoutExpired killed a whole resumable grading pass, PR #219 retrospective).
                raise JudgeError(f"grok timeout after {self.timeout}s")
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
        try:
            r = subprocess.run(
                [self.bin, "-p", p, "--output-format", "json", "--model", self.model,
                 "--disallowedTools", CLAUDE_DENY],
                capture_output=True, text=True, timeout=self.timeout)
        except subprocess.TimeoutExpired:
            raise JudgeError(f"claude timeout after {self.timeout}s")  # same contract as grok
        if r.returncode != 0:
            raise JudgeError(f"claude exit {r.returncode}: {r.stderr[-300:]}")
        env = json.loads(r.stdout)
        self._record(env)
        return json.loads(strip_json_fence(env.get("result", "")))


class CopilotJudge(_CostTracking):
    """GitHub Copilot CLI — the route to gpt/gemini/kimi families without a second subscription.

    Cross-family CONDITIONALLY, and the condition is checked every call. `--model <id>` is
    entitlement-gated: on a plan that does not grant explicit selection it rejects every id the CLI
    itself lists (measured 26-Jul-2026, including `gpt-5-mini` — the very model `auto` then chose).
    So the model cannot be pinned, `auto` routes per call, and its candidate set contains Claude.
    grade() therefore reads back who answered and raises on a same-family landing, rather than
    quietly returning a grade whose independence is the thing being assumed.

    `--available-tools` with no value strips every tool, which is what keeps grading hermetic; it
    also removes the need for `--allow-all-tools` in non-interactive mode.
    """
    name = "copilot-auto"

    def __init__(self, bin=None, model="auto", timeout=300, env=None):
        env = os.environ if env is None else env
        self.bin = bin or env.get("COPILOT_BIN") or shutil.which("copilot") or "copilot"
        self.model = model
        self.timeout = timeout
        self.last_model = None
        self._init_usage()

    def grade(self, prompt, schema):
        p = prompt + "\n\nReturn ONLY valid JSON matching this schema, no prose:\n" + json.dumps(schema)
        try:
            r = subprocess.run(
                [self.bin, "-p", p, "--model", self.model, "--output-format", "json",
                 "--available-tools"],
                capture_output=True, text=True, timeout=self.timeout)
        except subprocess.TimeoutExpired:
            raise JudgeError(f"copilot timeout after {self.timeout}s")  # same contract as grok
        if r.returncode != 0:
            raise JudgeError(f"copilot exit {r.returncode}: {r.stderr[-300:]}")
        text, model = parse_copilot_jsonl(r.stdout)
        self.last_model = model
        fam = family_of(model)
        if fam == GENERATOR_FAMILY:
            raise JudgeError(
                f"copilot routed this grade to {model} ({fam}), the generator's own family — the "
                f"cross-family grade did not happen. `auto` picks per call and its candidates "
                f"include Claude models. Re-run, or use --judge grok, or set $SKILL_BENCH_JUDGE_CMD "
                f"to a judge you can pin.")
        if fam == "unknown":
            raise JudgeError(
                f"copilot named no placeable model ({model or 'none reported'}), so this grade "
                f"cannot be shown to be cross-family. Use --judge grok, or pin one via "
                f"$SKILL_BENCH_JUDGE_CMD.")
        return json.loads(strip_json_fence(text))


class CommandJudge(_CostTracking):
    """Bring-your-own judge: `$SKILL_BENCH_JUDGE_CMD` reads the prompt on stdin and answers on
    stdout. The escape hatch for a family with no backend here — a local model server, an in-house
    wrapper, a vendor CLI this file has never heard of — so an adopter is not blocked on us adding
    code. `$SKILL_BENCH_JUDGE_MODEL` names the model, which is REQUIRED: without it the run cannot
    evidence that grading left the generator's family, and an unevidenced independence claim is the
    confound this whole substrate exists to remove."""
    name = "command"

    def __init__(self, cmd=None, model=None, timeout=300, env=None):
        env = os.environ if env is None else env
        self.cmd = cmd or env.get("SKILL_BENCH_JUDGE_CMD")
        self.model = model or env.get("SKILL_BENCH_JUDGE_MODEL")
        self.timeout = timeout
        self._init_usage()
        if not self.cmd:
            raise JudgeError("--judge command needs $SKILL_BENCH_JUDGE_CMD set to a command that "
                             "reads the prompt on stdin and writes the answer on stdout")
        fam = family_of(self.model)
        if fam in (GENERATOR_FAMILY, "unknown"):
            raise JudgeError(
                f"$SKILL_BENCH_JUDGE_MODEL is {self.model or 'unset'} ({fam}) — set it to the model "
                f"your command actually calls, from a family other than {GENERATOR_FAMILY}, so the "
                f"report can state whose judgement it carries")
        self.name = self.model

    def grade(self, prompt, schema):
        p = prompt + "\n\nReturn ONLY valid JSON matching this schema, no prose:\n" + json.dumps(schema)
        try:
            r = subprocess.run(self.cmd, shell=True, input=p, capture_output=True, text=True,
                               timeout=self.timeout)
        except subprocess.TimeoutExpired:
            raise JudgeError(f"{self.cmd} timeout after {self.timeout}s")
        if r.returncode != 0:
            raise JudgeError(f"judge command exit {r.returncode}: {r.stderr[-300:]}")
        return json.loads(strip_json_fence(r.stdout))


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


# The registry IS the extension point (ADR 0055): a machine we have never seen wires its own family
# through `command` without touching this file, and a new named backend is one entry here rather
# than a new branch in the resolver. `env_bin` names the override for a CLI installed off PATH,
# which is the common case, not the exception.
BACKENDS = {
    "grok":    {"cls": GrokJudge,    "bin": "grok",    "env_bin": "GROK_BIN",    "cross_family": True},
    "copilot": {"cls": CopilotJudge, "bin": "copilot", "env_bin": "COPILOT_BIN", "cross_family": True},
    "command": {"cls": CommandJudge, "bin": None,      "env_bin": None,          "cross_family": True},
    "claude":  {"cls": ClaudeJudge,  "bin": "claude",  "env_bin": None,          "cross_family": False},
}

# Preference order for `auto`. An explicitly configured judge outranks a discovered one — the
# adopter who wired `command` chose it on purpose.
AUTO_ORDER = ("command", "grok", "copilot", "claude")


def cli_available(name, which=None, env=None):
    """Is a judge backend usable on this machine? Pure given `which` + `env` (inject for tests)."""
    which = which or shutil.which
    env = os.environ if env is None else env
    spec = BACKENDS.get(name)
    if not spec:
        return False
    if name == "command":
        return bool(env.get("SKILL_BENCH_JUDGE_CMD"))
    return bool(spec["env_bin"] and env.get(spec["env_bin"])) or which(spec["bin"]) is not None


SAME_FAMILY_NOTE = ("no cross-family judge CLI found — falling back to the claude judge. This is "
                    "SAME-FAMILY grading, so the self-preference caveat applies (absolute rates "
                    "inflate, the verdict can shift). Wire any cross-family judge to restore "
                    "independence: install grok or copilot, or set $SKILL_BENCH_JUDGE_CMD + "
                    "$SKILL_BENCH_JUDGE_MODEL to a command of your own (references/judging.md).")


def resolve_judge(name, which=None, env=None):
    """Return (resolved_backend_name, fallback_note). 'auto' takes the first available backend in
    AUTO_ORDER, so it prefers a cross-family judge and reaches claude only as a caveated last
    resort. An EXPLICIT judge that is unavailable raises with a remedy (respect the explicit
    choice; don't silently substitute)."""
    if name == "auto":
        for candidate in AUTO_ORDER:
            if cli_available(candidate, which, env):
                return candidate, (None if BACKENDS[candidate]["cross_family"] else SAME_FAMILY_NOTE)
        raise JudgeError("no judge available: install one of " + ", ".join(BACKENDS) + ", or set "
                         "$SKILL_BENCH_JUDGE_CMD to your own judge command (references/judging.md)")
    if name in BACKENDS:
        if cli_available(name, which, env):
            return name, (None if BACKENDS[name]["cross_family"] else SAME_FAMILY_NOTE)
        spec = BACKENDS[name]
        remedy = (f"set ${spec['env_bin']} or install {spec['bin']}" if spec["env_bin"]
                  else "set $SKILL_BENCH_JUDGE_CMD" if name == "command"
                  else f"install the {spec['bin']} CLI")
        raise JudgeError(f"--judge {name} requested but it is not available ({remedy}); "
                         f"use --judge auto to fall back gracefully")
    raise JudgeError(f"unknown judge {name!r} (use auto|" + "|".join(BACKENDS) + ")")


def make_judge(name, which=None, env=None):
    resolved, note = resolve_judge(name, which, env)
    j = BACKENDS[resolved]["cls"]()
    j.fallback_note = note
    return j


def met_map(verdict):
    return {e["id"]: bool(e.get("met")) for e in (verdict.get("expectations") or [])}
