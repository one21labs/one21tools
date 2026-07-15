#!/usr/bin/env python3
"""Config defaults for skill-bench (ADR 0055 / #170 M2 genericization).

Keeps consumer-tunable defaults out of the code so the plugin isn't one21tools-shaped. Precedence:
explicit CLI arg > $SKILL_BENCH_* env var > $SKILL_BENCH_CONFIG JSON file > built-in default.
Stdlib only; the sole I/O is reading the optional $SKILL_BENCH_CONFIG file — output is
determined by the passed `env` plus that file (inject `env` for tests)."""
import json, os

DEFAULTS = {
    "judge": "auto",          # auto = grok if available else claude (cross-family preferred)
    "substrate": "native",    # native | promptfoo
    "workers": 8,
    "grade_expectations": 4,  # decision-outcome rubric arity; skill evals set their own
}

_ENV = {"judge": "SKILL_BENCH_JUDGE", "substrate": "SKILL_BENCH_SUBSTRATE", "workers": "SKILL_BENCH_WORKERS"}


def load(env=None):
    """Return the merged config dict (built-in <- config file <- env vars)."""
    env = os.environ if env is None else env
    cfg = dict(DEFAULTS)
    path = env.get("SKILL_BENCH_CONFIG")
    if path and os.path.exists(path):
        try:
            cfg.update({k: v for k, v in json.load(open(path)).items() if k in DEFAULTS})
        except Exception:
            pass  # a malformed config file falls through to defaults, never crashes a run
    for key, var in _ENV.items():
        if env.get(var):
            cfg[key] = int(env[var]) if key == "workers" else env[var]
    return cfg


def get(key, env=None):
    return load(env).get(key, DEFAULTS.get(key))
