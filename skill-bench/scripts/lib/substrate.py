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
import json, os, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed


def build_promptfoo_config(prompts, arms):
    """Emit a promptfoo config (JSON; promptfoo reads .json configs). Each arm is an `exec` provider
    so generation goes through our own hermetic CLI calls — promptfoo owns the matrix, not the model.
    `exec` passes the rendered prompt to the command; stdout is the response."""
    return {
        "description": "skill-bench generation matrix",
        "prompts": ["{{text}}"],
        "providers": [
            {"id": "exec: " + " ".join(a["cmd"]), "label": a["name"]} for a in arms
        ],
        "tests": [{"vars": {"text": p}, "metadata": {"prompt_id": i}}
                  for i, p in enumerate(prompts)],
    }


def parse_promptfoo_output(obj):
    """Tolerant parse of `promptfoo eval -o out.json`. Schema varies across versions; walk to the
    results list and pull provider label, prompt_id (from vars/metadata), and response output."""
    res = obj.get("results", obj)
    rows = res.get("results", res) if isinstance(res, dict) else res
    out = []
    for r in rows:
        prov = r.get("provider", {})
        label = prov.get("label") or prov.get("id") if isinstance(prov, dict) else str(prov)
        meta = (r.get("testCase", {}) or {}).get("metadata", {}) or r.get("metadata", {}) or {}
        vars_ = r.get("vars", {}) or {}
        pid = meta.get("prompt_id", vars_.get("prompt_id"))
        resp = r.get("response", {})
        output = resp.get("output") if isinstance(resp, dict) else resp
        out.append({"prompt_id": pid, "arm": label, "output": output})
    return out


class PromptfooSubstrate:
    name = "promptfoo"

    def __init__(self, bin=None):
        # prefer a local install, else `npx promptfoo`
        self.bin = bin
        self.argv = [bin] if bin else ["npx", "--yes", "promptfoo@latest"]

    def run(self, prompts, arms, workdir=None):
        workdir = workdir or tempfile.mkdtemp(prefix="skillbench-pf-")
        cfg = os.path.join(workdir, "promptfooconfig.json")
        out = os.path.join(workdir, "results.json")
        json.dump(build_promptfoo_config(prompts, arms), open(cfg, "w"), indent=1)
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
        out = r.stdout.strip()
        try:  # unwrap CLI --output-format json envelopes: claude=result, grok=text, schema=structuredOutput
            j = json.loads(out)
            unwrapped = j.get("result") or j.get("text") or j.get("structuredOutput")
            if unwrapped is not None:
                out = unwrapped if isinstance(unwrapped, str) else json.dumps(unwrapped)
        except Exception:
            pass
        return {"prompt_id": pid, "arm": arm["name"], "output": out}

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
