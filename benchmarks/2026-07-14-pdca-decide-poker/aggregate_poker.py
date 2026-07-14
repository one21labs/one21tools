#!/usr/bin/env python3
"""Poker-grid aggregation (pre-registration: README.md — frozen bars, this script computes them).

Reads graded/verdicts.jsonl + arm_map.tsv + audit.jsonl + outputs/*.json (cell costs, poker
records). Computes the four pre-registered #185 bars (opus pipeline basis):
  a. hard pair (exps 3+4), cluster mean over all 8 scenarios: mean_P >= mean_C - 0.05
  b. cost: mean cell_cost_P <= 0.7 * mean cell_cost_C (same run; framer amortized in cells)
  c. OUTCOME SPREAD: per-scenario max-min of rep full fraction-met, averaged; P <= C
  d. full fraction-met: cluster mean_P >= mean_C - 0.05
plus P-C / P-A cluster deltas with 95% t-CIs, per-expectation tables, the mechanical herding
metrics (round-2 fire rate; fraction of re-estimates moving toward the round-1 mean),
guess-the-arm audit, and the grok slot (judge disagreement on a bar => bar NOT MET; rerun
with --grok <summary.json> after the re-grade). Writes results.json.
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


def outcome_spread(frac, arm):
    """Per-scenario max-min of rep full fraction-met, averaged over scenarios (ADR 0061 2f)."""
    spreads = {}
    for s in SCENARIOS:
        v = frac.get((s, arm), [])
        spreads[s] = round(max(v) - min(v), 4) if len(v) >= 2 else None
    usable = [x for x in spreads.values() if x is not None]
    return round(statistics.mean(usable), 4) if usable else None, spreads


def herding_metrics(outputs):
    """Mechanical round-2 audit from the poker records (pre-registered, README.md)."""
    p_cells = fired = 0
    toward = away = kept = 0
    per_advisor = {}
    for r in outputs:
        if r["arm"] != "P" or r["summary"]["error"]:
            continue
        p_cells += 1
        poker = r.get("poker") or {}
        divergent = poker.get("divergent") or []
        if not divergent:
            continue
        fired += 1
        r1 = poker.get("round1") or []
        for rec in poker.get("round2") or []:
            k = rec["advisor"]
            for oid, delta in (rec.get("deltas") or {}).items():
                scores = [e[oid]["score"] for e in r1 if oid in e]
                own = r1[k][oid]["score"]
                mean_others = statistics.mean(scores)
                if delta == 0:
                    kept += 1
                elif (own + delta - mean_others) ** 2 < (own - mean_others) ** 2:
                    toward += 1
                else:
                    away += 1
                per_advisor.setdefault(k, []).append(delta)
    moves = toward + away + kept
    return {
        "p_cells": p_cells, "round2_fired_cells": fired,
        "fire_rate": round(fired / p_cells, 3) if p_cells else None,
        "re_estimates": moves, "kept": kept, "toward_mean": toward, "away_from_mean": away,
        "toward_share": round(toward / moves, 3) if moves else None,
        "per_advisor_mean_abs_delta": {k: round(statistics.mean([abs(d) for d in v]), 3)
                                       for k, v in sorted(per_advisor.items())},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grok", help="grok re-grade summary json (bench_verdict output) to fold in")
    args = ap.parse_args()

    graded = HERE / "graded"
    cells = {c["bid"]: c for c in bench_io.load_records(str(graded / "verdicts.jsonl"), fmt="jsonl")}
    arm_map = bench_io.load_records(str(graded / "arm_map.tsv"), fmt="tsv")
    audit = bench_io.load_records(str(graded / "audit.jsonl"), fmt="jsonl")

    frac, hard = {}, {}
    for m in arm_map:
        c = cells.get(m["bid"])
        if not c:
            continue
        s, arm = m["scenario"], m["arm"]
        met = {e["id"]: e["met"] for e in c["expectations"]}
        frac.setdefault((s, arm), []).append(sum(met.values()) / 4.0)
        hard.setdefault((s, arm), []).append((met[3] + met[4]) / 2.0)

    exp_rate = {}
    for m in arm_map:
        c = cells.get(m["bid"])
        if not c:
            continue
        met = {e["id"]: e["met"] for e in c["expectations"]}
        for i in (1, 2, 3, 4):
            exp_rate.setdefault((m["arm"], i, m["scenario"] in BACKTESTS), []).append(
                1.0 if met[i] else 0.0)

    def rate(arm, i, backtest=True):
        v = exp_rate.get((arm, i, backtest), [])
        return round(statistics.mean(v), 3) if v else None

    outputs = [json.loads(p.read_text(encoding="utf-8"))
               for p in sorted((HERE / "outputs").glob("*.json"))]
    costs = {}
    for r in outputs:
        if not r["summary"]["error"]:
            costs.setdefault(r["arm"], []).append(r["summary"].get("cell_cost_usd") or 0.0)
    mean_cost = {a: round(statistics.mean(v), 3) for a, v in costs.items() if v}

    pc_full = cluster_delta(frac, "P", "C")
    pa_full = cluster_delta(frac, "P", "A")
    pc_hard = cluster_delta(hard, "P", "C")
    pa_hard = cluster_delta(hard, "P", "A")
    spread_p, spread_p_per = outcome_spread(frac, "P")
    spread_c, spread_c_per = outcome_spread(frac, "C")

    bars = {
        "a_hard_pair_noninferior": pc_hard[0] >= -0.05,
        "b_cost": ("P" in mean_cost and "C" in mean_cost
                   and mean_cost["P"] <= 0.7 * mean_cost["C"]),
        "c_outcome_spread": (spread_p is not None and spread_c is not None
                             and spread_p <= spread_c),
        "d_full_noninferior": pc_full[0] >= -0.05,
    }

    grok = json.loads(Path(args.grok).read_text(encoding="utf-8")) if args.grok else None

    arm_of = {m["bid"]: m["arm"] for m in arm_map}
    correct = sum(1 for a in audit if a.get("guess") == arm_of.get(a["bid"]))

    results = {
        "bars_opus_basis": bars,
        "h1_survives_opus_basis": all(bars.values()),
        "hard_pair_P_minus_C": {"mean_delta": round(pc_hard[0], 4),
                                "ci95": [round(pc_hard[1], 4), round(pc_hard[2], 4)],
                                "per_scenario": pc_hard[3]},
        "hard_pair_P_minus_A": {"mean_delta": round(pa_hard[0], 4),
                                "ci95": [round(pa_hard[1], 4), round(pa_hard[2], 4)]},
        "full_P_minus_C": {"mean_delta": round(pc_full[0], 4),
                           "ci95": [round(pc_full[1], 4), round(pc_full[2], 4)],
                           "per_scenario": pc_full[3],
                           "confidence": "strong" if pc_full[1] > 0 else "weak"},
        "full_P_minus_A": {"mean_delta": round(pa_full[0], 4),
                           "ci95": [round(pa_full[1], 4), round(pa_full[2], 4)]},
        "outcome_spread": {"P": spread_p, "C": spread_c,
                           "per_scenario_P": spread_p_per, "per_scenario_C": spread_c_per},
        "per_expectation_backtest": {arm: {i: rate(arm, i) for i in (1, 2, 3, 4)}
                                     for arm in ("A", "C", "P")},
        "per_expectation_synthetic": {arm: {i: rate(arm, i, False) for i in (1, 2, 3, 4)}
                                      for arm in ("A", "C", "P")},
        "mean_cell_cost_usd": mean_cost,
        "herding": herding_metrics(outputs),
        "audit": {"n": len(audit), "correct": correct,
                  "blinding_leak": len(audit) >= 9 and correct >= 7},
        "verdict_word_full_PC": verdict_of(pc_full[0], pc_full[1], pc_full[2], 8),
        "grok_second_headline": grok,
        "judge_split": None if grok is None else "fill after comparing bar outcomes across judges",
    }
    (HERE / "results.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(json.dumps(results, indent=1))
    if results["audit"]["blinding_leak"]:
        print("WARNING: guess-the-arm >=7/9 — blinding leak; revisit trigger fires")


if __name__ == "__main__":
    main()
