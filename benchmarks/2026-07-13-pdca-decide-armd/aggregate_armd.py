#!/usr/bin/env python3
"""Arm-D aggregation (pre-registration: README.md — frozen bars, this script computes them).

Reads graded/verdicts.jsonl + arm_map.tsv + audit.jsonl + outputs/*.json (cell costs).
Computes the four pre-registered ADOPT bars (opus pipeline basis):
  a. backtest exp-4: mean_D >= mean_C - 0.05
  b. backtest exp-3: mean_D > mean_C
  c. full fraction-met: cluster mean_D >= mean_C - 0.05 (8 clusters)
  d. cost: mean cell_cost_D <= 0.6 * mean cell_cost_C (same run)
plus hard-pair (exps 3+4) and full fraction-met cluster deltas D-C / D-A with 95% t-CIs,
per-expectation met-rate table, guess-the-arm audit, and empty grok slots the re-grade fills
(judge disagreement on a bar => bar NOT MET, recorded by rerunning this after the re-grade
with --grok <summary.json>). Writes results.json.
"""
import argparse
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "skill-bench" / "scripts" / "lib"))
import bench_io  # noqa: E402
from verdict import verdict_of  # noqa: E402

T_DF7_95 = 2.365
SCENARIOS = ["B1", "B2", "B3", "B4", "S1", "S2", "S3", "S4"]
BACKTESTS = {"B1", "B2", "B3", "B4"}


def cluster_delta(frac, hi_arm, lo_arm, scenarios=SCENARIOS):
    deltas, per = [], {}
    for s in scenarios:
        a, b = frac.get((s, hi_arm), []), frac.get((s, lo_arm), [])
        if not a or not b:
            sys.exit(f"missing cells for {s} ({hi_arm}={len(a)}, {lo_arm}={len(b)})")
        d = statistics.mean(a) - statistics.mean(b)
        per[s] = round(d, 3)
        deltas.append(d)
    mean_d = statistics.mean(deltas)
    sd = statistics.stdev(deltas)
    half = T_DF7_95 * sd / (len(deltas) ** 0.5)
    return mean_d, mean_d - half, mean_d + half, per


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grok", help="grok re-grade summary json (bench_verdict output) to fold in")
    args = ap.parse_args()

    graded = HERE / "graded"
    cells = {c["bid"]: c for c in bench_io.load_records(str(graded / "verdicts.jsonl"), fmt="jsonl")}
    arm_map = bench_io.load_records(str(graded / "arm_map.tsv"), fmt="tsv")
    audit = bench_io.load_records(str(graded / "audit.jsonl"), fmt="jsonl")

    frac, hard, exp_rate = {}, {}, {}
    for m in arm_map:
        c = cells.get(m["bid"])
        if not c:
            continue
        s, arm = m["scenario"], m["arm"]
        met = {e["id"]: e["met"] for e in c["expectations"]}
        frac.setdefault((s, arm), []).append(sum(met.values()) / 4.0)
        hard.setdefault((s, arm), []).append((met[3] + met[4]) / 2.0)
        for i in (1, 2, 3, 4):
            exp_rate.setdefault((arm, i, s in BACKTESTS), []).append(1.0 if met[i] else 0.0)

    def rate(arm, i, backtest=True):
        v = exp_rate.get((arm, i, backtest), [])
        return round(statistics.mean(v), 3) if v else None

    # Costs from raw outputs (cell_cost_usd includes probe costs for D).
    costs = {}
    for p in sorted((HERE / "outputs").glob("*.json")):
        r = json.loads(p.read_text(encoding="utf-8"))
        if not r["summary"]["error"]:
            costs.setdefault(r["arm"], []).append(r["summary"].get("cell_cost_usd") or 0.0)
    mean_cost = {a: round(statistics.mean(v), 3) for a, v in costs.items() if v}

    dc_mean, dc_lo, dc_hi, dc_per = cluster_delta(frac, "D", "C")
    da_mean, da_lo, da_hi, _ = cluster_delta(frac, "D", "A")
    hdc = cluster_delta(hard, "D", "C")
    hda = cluster_delta(hard, "D", "A")

    bars = {
        "a_exp4_edge_survives": rate("D", 4) >= rate("C", 4) - 0.05,
        "b_exp3_step_pays": rate("D", 3) > rate("C", 3),
        "c_noninferior_overall": dc_mean >= -0.05,
        "d_cost": ("D" in mean_cost and "C" in mean_cost
                   and mean_cost["D"] <= 0.6 * mean_cost["C"]),
    }

    grok = json.loads(Path(args.grok).read_text(encoding="utf-8")) if args.grok else None

    arm_of = {m["bid"]: m["arm"] for m in arm_map}
    correct = sum(1 for a in audit if a.get("guess") == arm_of.get(a["bid"]))

    results = {
        "bars_opus_basis": bars,
        "adopt": all(bars.values()),
        "hard_pair_D_minus_C": {"mean_delta": round(hdc[0], 4), "ci95": [round(hdc[1], 4), round(hdc[2], 4)],
                                "per_scenario": hdc[3]},
        "hard_pair_D_minus_A": {"mean_delta": round(hda[0], 4), "ci95": [round(hda[1], 4), round(hda[2], 4)]},
        "full_D_minus_C": {"mean_delta": round(dc_mean, 4), "ci95": [round(dc_lo, 4), round(dc_hi, 4)],
                           "per_scenario": dc_per,
                           "confidence": "strong" if dc_lo > 0 else "weak"},
        "full_D_minus_A": {"mean_delta": round(da_mean, 4), "ci95": [round(da_lo, 4), round(da_hi, 4)]},
        "per_expectation_backtest": {arm: {i: rate(arm, i) for i in (1, 2, 3, 4)} for arm in ("A", "C", "D")},
        "per_expectation_synthetic": {arm: {i: rate(arm, i, False) for i in (1, 2, 3, 4)} for arm in ("A", "C", "D")},
        "mean_cell_cost_usd": mean_cost,
        "audit": {"n": len(audit), "correct": correct,
                  "blinding_leak": len(audit) >= 9 and correct >= 7},
        "verdict_word_full_DC": verdict_of(dc_mean, dc_lo, dc_hi, 8),
        "grok_second_headline": grok,
        "judge_split": None if grok is None else "fill after comparing bar outcomes across judges",
    }
    (HERE / "results.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(json.dumps(results, indent=1))
    if results["audit"]["blinding_leak"]:
        print("WARNING: guess-the-arm >=7/9 — blinding leak; revisit trigger fires")


if __name__ == "__main__":
    main()
