#!/usr/bin/env python3
"""Execution substrate adapters for skill-measure (ADR 0055).

The bench layer (arms, blind grading, prosecutor, cross-family judge, cost gate, pre-registration)
is the in-repo asset. GENERATION — running each prompt under each arm — is rented: promptfoo drives
the matrix + observability + CI regression gating; the models stay ours via `exec` providers. A
native fallback ships for environments without promptfoo. Stdlib only (JSON config, not YAML).

A Substrate.run(prompts, arms) -> list of {"prompt_id","arm","output"}, where an Arm is
  {"name": "C", "cmd": [argv...]}  and the prompt text is fed on stdin. A native row whose call
  failed (nonzero exit, envelope is_error, timeout, unlaunchable argv) — or a promptfoo row with a
  response error, success false, or no output — also carries "error": it is not an output.
The bench layer then normalizes + grades those outputs with judge.py / benchstats.py.
"""
import json, os, shlex, shutil, stat, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

from hermetic_driver import detached_env, neutral_cwd


def arm_env():
    """The caller's environment minus the parent Claude Code session (an arm run inside one
    inherited its session id — hangs, exit 1 — plus synced skills and reminders), via
    hermetic_driver.detached_env. No hermetic overrides: an arm keeps the caller's PATH and own
    login, including a CLAUDE_CONFIG_DIR the caller set themselves."""
    env = detached_env()
    if "CLAUDE_CONFIG_DIR" in os.environ:
        env["CLAUDE_CONFIG_DIR"] = os.environ["CLAUDE_CONFIG_DIR"]
    return env


def build_promptfoo_config(prompts, providers):
    """Emit a promptfoo config (JSON; promptfoo reads .json configs). `providers` is
    [{"name": label, "exec": <shell command>}] — each becomes an `exec` provider so generation goes
    through our own CLI calls; promptfoo owns the matrix, not the model. prompt_id rides in vars so
    it is echoed back per result row (robust across promptfoo versions). Pure (no fs)."""
    return {
        "description": "skill-measure generation matrix",
        "prompts": ["{{text}}"],
        "providers": [{"id": "exec: " + p["exec"], "label": p["name"]} for p in providers],
        "tests": [{"vars": {"text": t, "prompt_id": i}} for i, t in enumerate(prompts)],
    }


def unwrap_cli_output(s):
    """If a generation arm emitted a CLI --output-format json envelope, return the text field
    (claude=result, grok=text, schema=structuredOutput); else return the string unchanged."""
    s = (s or "").strip()
    try:
        j = json.loads(s)
    except Exception:
        return s
    if not isinstance(j, dict):
        return s
    v = j.get("result") or j.get("text") or j.get("structuredOutput")
    if v is None:
        return s
    return v if isinstance(v, str) else json.dumps(v)


def parse_promptfoo_output(obj):
    """Tolerant parse of `promptfoo eval -o out.json` (rows nest at results.results[] in 0.121).
    Pull provider label, prompt_id (echoed in vars), and response output. A row whose call failed
    (response error, success false, no output) carries "error", so it is excluded, never graded
    as quality 0."""
    res = obj.get("results", obj)
    rows = res.get("results", res) if isinstance(res, dict) else res
    out = []
    for r in rows:
        prov = r.get("provider", {})
        label = (prov.get("label") or prov.get("id")) if isinstance(prov, dict) else str(prov)
        vars_ = r.get("vars", {}) or {}
        meta = (r.get("testCase", {}) or {}).get("metadata", {}) or r.get("metadata", {}) or {}
        pid = vars_.get("prompt_id", meta.get("prompt_id"))
        resp = r.get("response", {})
        raw = resp.get("output") if isinstance(resp, dict) else resp
        row = {"prompt_id": pid, "arm": label, "output": unwrap_cli_output(raw)}
        err = resp.get("error") if isinstance(resp, dict) else None
        if not err and r.get("success") is False:  # no asserts are configured: false = failed call
            err = r.get("error") or "success false"
        if err or raw is None:
            row["error"] = str(err or "no output")[-200:]
        out.append(row)
    return out


def _write_arm_wrapper(workdir, arm):
    """A shim promptfoo's exec provider calls with (prompt, contextJSON) — forward ONLY the prompt
    ($1) to the arm command, so a bare `grok/claude -p` doesn't choke on promptfoo's context arg."""
    path = os.path.join(workdir, f"arm_{arm['name']}.sh")
    with open(path, "w") as f:
        f.write('#!/bin/bash\nexec ' + shlex.join(arm["cmd"]) + ' "$1"\n')
    os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC | stat.S_IRWXU)
    return path


class PromptfooSubstrate:
    name = "promptfoo"
    # Pinned: parse_promptfoo_output is validated against the 0.121 result shape; a benchmark
    # harness must not track a moving head (reproducibility + supply chain — ADR 0058). Bump
    # deliberately: re-validate the parser, then move this constant.
    PIN = "promptfoo@0.121.18"

    def __init__(self, bin=None):
        # explicit arg > $SKILL_BENCH_PROMPTFOO_BIN > `npx promptfoo@<pin>` (fetched on demand)
        bin = bin or os.environ.get("SKILL_BENCH_PROMPTFOO_BIN")
        self.bin = bin
        self.argv = [bin] if bin else ["npx", "--yes", self.PIN]

    def run(self, prompts, arms, workdir=None):
        workdir = workdir or tempfile.mkdtemp(prefix="skillmeasure-pf-")
        providers = [{"name": a["name"], "exec": "bash " + _write_arm_wrapper(workdir, a)} for a in arms]
        cfg = os.path.join(workdir, "promptfooconfig.json")
        out = os.path.join(workdir, "results.json")
        json.dump(build_promptfoo_config(prompts, providers), open(cfg, "w"), indent=1)
        r = subprocess.run(self.argv + ["eval", "-c", cfg, "-o", out, "--no-cache"],
                           capture_output=True, text=True, timeout=1800, cwd=workdir,
                           env=arm_env())
        if not os.path.exists(out):
            raise RuntimeError(f"promptfoo produced no output: {r.stderr[-400:]}")
        return parse_promptfoo_output(json.load(open(out)))


class NativeSubstrate:
    """Fallback: shell each (prompt, arm) directly. Hermetic — the arm cmd denies tools itself."""
    name = "native"

    def __init__(self, workers=6, timeout=300):
        self.workers = workers
        self.timeout = timeout

    def _one(self, pid, prompt, arm, cwd, env):
        # prompt passed as final argv element (universal for grok -p / claude -p), unless the arm
        # opts into stdin. Keeps long prompts off the shell (argv, not a shell string). cwd is a
        # neutral dir outside the caller's project, which blocks PROJECT-scope loading only (its
        # CLAUDE.md, .claude/skills); user-scope plugins and skills still load unless the arm
        # commands disable them. An arm's paths must be absolute (bench_skill refuses relative
        # ones). env drops the parent session (arm_env).
        row = {"prompt_id": pid, "arm": arm["name"]}
        argv, stdin = (arm["cmd"], prompt) if arm.get("stdin") else (arm["cmd"] + [prompt], None)
        try:
            r = subprocess.run(argv, input=stdin, capture_output=True, text=True,
                               timeout=self.timeout, cwd=cwd, env=env)
        except subprocess.TimeoutExpired:
            return {**row, "output": "", "error": f"timeout after {self.timeout}s"}
        except OSError as e:  # unlaunchable argv (e.g. a relative path from the neutral cwd)
            return {**row, "output": "", "error": f"launch failed: {e}"[:200]}
        row["output"] = unwrap_cli_output(r.stdout)
        try:
            is_error = json.loads(r.stdout).get("is_error") is True
        except Exception:
            is_error = False
        if r.returncode != 0 or is_error:
            # a failed or usage-limited call is not a quality result: the caller excludes it
            row["error"] = f"exit {r.returncode}{' is_error' if is_error else ''}: " \
                           f"{(r.stderr.strip() or row['output'])[-200:]}"
        return row

    def run(self, prompts, arms, workdir=None):
        jobs = [(i, p, a) for i, p in enumerate(prompts) for a in arms]
        cwd, env = neutral_cwd("native-substrate"), arm_env()
        res = []
        try:
            with ThreadPoolExecutor(max_workers=self.workers) as ex:
                futs = [ex.submit(self._one, i, p, a, cwd, env) for i, p, a in jobs]
                for f in as_completed(futs):
                    res.append(f.result())
        finally:
            shutil.rmtree(cwd, ignore_errors=True)
        return res


def make_substrate(name, **kw):
    return {"promptfoo": PromptfooSubstrate, "native": NativeSubstrate}[name](**kw)
