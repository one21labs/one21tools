#!/usr/bin/env python3
"""Execution substrate adapters for skill-bench (ADR 0055).

The bench layer (arms, blind grading, prosecutor, cross-family judge, cost gate, pre-registration)
is the in-repo asset. GENERATION — running each prompt under each arm — is rented: promptfoo drives
the matrix + observability + CI regression gating; the models stay ours via `exec` providers. A
native fallback ships for environments without promptfoo. Stdlib only (JSON config, not YAML).

A Substrate.run(prompts, arms) -> list of {"prompt_id","arm","output"}, where an Arm is
  {"name": "C", "cmd": [argv...]}  and the prompt text is fed on stdin.
The bench layer then normalizes + grades those outputs with judge.py / benchstats.py.
"""
import json, os, shlex, stat, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed


def build_promptfoo_config(prompts, providers):
    """Emit a promptfoo config (JSON; promptfoo reads .json configs). `providers` is
    [{"name": label, "exec": <shell command>}] — each becomes an `exec` provider so generation goes
    through our own CLI calls; promptfoo owns the matrix, not the model. prompt_id rides in vars so
    it is echoed back per result row (robust across promptfoo versions). Pure (no fs)."""
    return {
        "description": "skill-bench generation matrix",
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
    Pull provider label, prompt_id (echoed in vars), and response output."""
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
        out.append({"prompt_id": pid, "arm": label, "output": unwrap_cli_output(raw)})
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
        workdir = workdir or tempfile.mkdtemp(prefix="skillbench-pf-")
        providers = [{"name": a["name"], "exec": "bash " + _write_arm_wrapper(workdir, a)} for a in arms]
        cfg = os.path.join(workdir, "promptfooconfig.json")
        out = os.path.join(workdir, "results.json")
        json.dump(build_promptfoo_config(prompts, providers), open(cfg, "w"), indent=1)
        r = subprocess.run(self.argv + ["eval", "-c", cfg, "-o", out, "--no-cache"],
                           capture_output=True, text=True, timeout=1800, cwd=workdir)
        if not os.path.exists(out):
            raise RuntimeError(f"promptfoo produced no output: {r.stderr[-400:]}")
        return parse_promptfoo_output(json.load(open(out)))


class NativeSubstrate:
    """Fallback: shell each (prompt, arm) directly. Hermetic — the arm cmd denies tools itself."""
    name = "native"

    def __init__(self, workers=6, timeout=300):
        self.workers = workers
        self.timeout = timeout

    def _one(self, pid, prompt, arm):
        # prompt passed as final argv element (universal for grok -p / claude -p), unless the arm
        # opts into stdin. Keeps long prompts off the shell (argv, not a shell string).
        if arm.get("stdin"):
            r = subprocess.run(arm["cmd"], input=prompt, capture_output=True, text=True, timeout=self.timeout)
        else:
            r = subprocess.run(arm["cmd"] + [prompt], capture_output=True, text=True, timeout=self.timeout)
        return {"prompt_id": pid, "arm": arm["name"], "output": unwrap_cli_output(r.stdout)}

    def run(self, prompts, arms, workdir=None):
        jobs = [(i, p, a) for i, p in enumerate(prompts) for a in arms]
        res = []
        with ThreadPoolExecutor(max_workers=self.workers) as ex:
            futs = [ex.submit(self._one, i, p, a) for i, p, a in jobs]
            for f in as_completed(futs):
                res.append(f.result())
        return res


def make_substrate(name, **kw):
    return {"promptfoo": PromptfooSubstrate, "native": NativeSubstrate}[name](**kw)
