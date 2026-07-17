#!/usr/bin/env python3
"""Aggregate graded cells -> results.jsonl (pre-registered metrics, metadata.json:metrics).

Headline (grok): per-pair eval-clustered fraction-met delta + CI + keep_verdict (wp-bare, cek-bare).
Divergence: the same pairs on claude cells + per-expectation agreement + verdict flips.
Secondary: binary all-met per arm; per-arm consistency (within-eval rep spread, worst-rep score).
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "skill-bench" / "scripts" / "lib"))
import benchstats  # noqa: E402

PAIRS = [("wp", "bare"), ("cek", "bare")]


def load(jname):
    p = HERE / "graded" / f"cells-{jname}.jsonl"
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l]
    for r in rows:
        r["met"] = {int(k): v for k, v in r["met"].items()}
    return rows


def frac(met):
    return sum(1 for v in met.values() if v) / len(met) if met else 0.0


def consistency(cells, arm):
    by_eval = {}
    for c in cells:
        if c["arm"] == arm:
            by_eval.setdefault(c["scenario"], []).append(frac(c["met"]))
    spreads = [max(v) - min(v) for v in by_eval.values() if len(v) > 1]
    worst = min((min(v) for v in by_eval.values()), default=0.0)
    return {"mean_within_eval_spread": round(sum(spreads) / len(spreads), 3) if spreads else None,
            "worst_rep_frac_met": round(worst, 3)}


def pair_verdict(cells, x, y):
    d = benchstats.clustered_delta(cells, x, y)
    v = benchstats.keep_verdict(d)
    return {"pair": f"{x}-{y}", **v, "per_scenario": {k: round(s, 3) for k, s in d["per_scenario"].items()}}


def main():
    grok = load("grok")
    claude = load("claude")
    out = []
    arms = sorted({c["arm"] for c in grok})
    for a in arms:
        out.append({"record": "arm", "judge": "grok", "arm": a,
                    "mean_frac_met": round(benchstats.arm_mean(grok, a), 3),
                    "all_met_rate": round(sum(1 for c in grok if c["arm"] == a and all(c["met"].values()))
                                          / max(1, sum(1 for c in grok if c["arm"] == a)), 3),
                    **consistency(grok, a)})
    verdicts = {}
    for x, y in PAIRS:
        g = pair_verdict(grok, x, y)
        c = pair_verdict(claude, x, y)
        flip = g["verdict"] != c["verdict"]
        verdicts[x] = {"grok": g, "claude": c, "verdict_flip": flip}
        out.append({"record": "pair", "pair": f"{x}-{y}", "grok": g, "claude": c, "verdict_flip": flip,
                    "status": "EXPLORATORY (judge flip — pre-registered kill condition: no KEEP/CUT promotion)"
                              if flip else "judge-robust"})
    # per-expectation cross-judge agreement over identical (bid, expectation) pairs
    gm = {(c["bid"], k): v for c in grok for k, v in c["met"].items()}
    cm = {(c["bid"], k): v for c in claude for k, v in c["met"].items()}
    common = set(gm) & set(cm)
    agree = sum(1 for k in common if gm[k] == cm[k])
    out.append({"record": "divergence", "n_expectation_cells": len(common),
                "agreement": round(agree / len(common), 3) if common else None,
                "grok_stricter_n": sum(1 for k in common if cm[k] and not gm[k]),
                "claude_stricter_n": sum(1 for k in common if gm[k] and not cm[k])})
    (HERE / "results.jsonl").write_text("\n".join(json.dumps(r) for r in out) + "\n", encoding="utf-8")
    print("\n".join(json.dumps(r) for r in out))


if __name__ == "__main__":
    main()
