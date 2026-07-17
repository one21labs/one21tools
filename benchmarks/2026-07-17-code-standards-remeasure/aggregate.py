#!/usr/bin/env python3
"""Aggregate #214: L2 graded cells + L1 trigger reports -> results.jsonl (pre-registered metrics)."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "skill-bench" / "scripts" / "lib"))
import benchstats  # noqa: E402


def frac(met):
    return sum(1 for v in met.values() if v) / len(met) if met else 0.0


def load(jname):
    p = HERE / "graded" / f"cells-{jname}.jsonl"
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l]
    for r in rows:
        r["met"] = {int(k): v for k, v in r["met"].items()}
    return rows


def consistency(cells, arm):
    by_eval = {}
    for c in cells:
        if c["arm"] == arm:
            by_eval.setdefault(c["scenario"], []).append(frac(c["met"]))
    spreads = [max(v) - min(v) for v in by_eval.values() if len(v) > 1]
    worst = min((min(v) for v in by_eval.values()), default=0.0)
    return {"mean_within_eval_spread": round(sum(spreads) / len(spreads), 3) if spreads else None,
            "worst_rep_frac_met": round(worst, 3)}


def durable(report):
    """Per the pre-registered rule: durably fires iff triggers/completed_runs >= 2/3."""
    out = {"TP": [], "TP_lost": [], "FP": []}
    for r in report["results"]:
        comp = r.get("completed_runs") or 0
        fired = comp and (r["triggers"] / comp) >= (2 / 3)
        if r["should_trigger"]:
            (out["TP"] if fired else out["TP_lost"]).append(r["query"])
        elif fired:
            out["FP"].append(r["query"])
    return out


def main():
    out = []
    # L1
    for p in sorted((HERE / "trigger-results").glob("*.json")):
        rep = json.loads(p.read_text(encoding="utf-8"))
        d = durable(rep)
        out.append({"record": "trigger", "variant": p.stem, "description_chars": len(rep["description"]),
                    "durable_tp": len(d["TP"]), "durable_fp": len(d["FP"]),
                    "tp_lost_queries": d["TP_lost"], "fp_queries": d["FP"],
                    "summary": rep["summary"]})
    # L2
    grok = load("grok")
    claude = load("claude")
    for a in sorted({c["arm"] for c in grok}):
        out.append({"record": "arm", "judge": "grok", "arm": a,
                    "mean_frac_met": round(benchstats.arm_mean(grok, a), 3),
                    "all_met_rate": round(sum(1 for c in grok if c["arm"] == a and all(c["met"].values()))
                                          / max(1, sum(1 for c in grok if c["arm"] == a)), 3),
                    **consistency(grok, a)})
    g = benchstats.keep_verdict(benchstats.clustered_delta(grok, "with", "bare"))
    c = benchstats.keep_verdict(benchstats.clustered_delta(claude, "with", "bare"))
    flip = g["verdict"] != c["verdict"]
    out.append({"record": "pair", "pair": "with-bare", "grok": g, "claude": c, "verdict_flip": flip,
                "per_scenario_grok": {k: round(v, 3) for k, v in
                                      benchstats.clustered_delta(grok, "with", "bare")["per_scenario"].items()},
                "status": "EXPLORATORY (judge flip)" if flip else "judge-robust"})
    gm = {(x["bid"], k): v for x in grok for k, v in x["met"].items()}
    cm = {(x["bid"], k): v for x in claude for k, v in x["met"].items()}
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
