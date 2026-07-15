#!/usr/bin/env python3
"""I2 aggregation (pre-registration: README.md — frozen bar, this script computes it).

Reads graded/verdicts.jsonl + arm_map.tsv + audit.jsonl. Computes:
  - fraction_met per cell (met/4, met_final = min(grader, prosecutor) folded upstream)
  - PRIMARY (KEEP condition): mean over 8 scenario clusters of
    (mean frac_C - mean frac_B), 95% t-CI over cluster deltas (df=7, t=2.365)
  - context: C - A the same way (never the KEEP basis)
  - verdict via lib/verdict.py:verdict_of on the C-B delta
  - audit: 3-way guess-the-arm on 9 cells; pre-registered "significantly above 0.5"
    operationalized as >=7/9 correct (>=7/9 vs chance 1/3: p~0.001; vs 0.5: p~0.09 —
    the pre-registered 0.5 reference is respected as the leak bar)
Writes results.json and prints the verdict block.
"""
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lib"))
import bench_io  # noqa: E402
from verdict import verdict_of  # noqa: E402

T_DF7_95 = 2.365
SCENARIOS = ["B1", "B2", "B3", "B4", "S1", "S2", "S3", "S4"]


def cluster_delta(frac, hi_arm, lo_arm):
    deltas = []
    per = {}
    for s in SCENARIOS:
        a = frac.get((s, hi_arm), [])
        b = frac.get((s, lo_arm), [])
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
    graded = HERE / "graded"
    cells = {c["bid"]: c for c in bench_io.load_records(str(graded / "verdicts.jsonl"), fmt="jsonl")}
    arm_map = bench_io.load_records(str(graded / "arm_map.tsv"), fmt="tsv")
    audit = bench_io.load_records(str(graded / "audit.jsonl"), fmt="jsonl")

    frac = {}
    for m in arm_map:
        c = cells.get(m["bid"])
        if not c:
            continue
        met = sum(1 for e in c["expectations"] if e["met"])
        frac.setdefault((m["scenario"], m["arm"]), []).append(met / 4.0)

    cb_mean, cb_lo, cb_hi, cb_per = cluster_delta(frac, "C", "B")
    ca_mean, ca_lo, ca_hi, _ = cluster_delta(frac, "C", "A")
    word = verdict_of(cb_mean, cb_lo, cb_hi, 8)

    arm_means = {arm: round(statistics.mean([x for (s, a), v in frac.items() if a == arm for x in v]), 3)
                 for arm in ("A", "B", "C")}

    arm_of = {m["bid"]: m["arm"] for m in arm_map}
    correct = sum(1 for a in audit if a.get("guess") == arm_of.get(a["bid"]))
    blinding_leak = len(audit) >= 9 and correct >= 7

    results = {
        "primary_C_minus_B": {"mean_delta": round(cb_mean, 4),
                              "ci95": [round(cb_lo, 4), round(cb_hi, 4)],
                              "per_scenario": cb_per,
                              "confidence": "strong" if cb_lo > 0 else "weak"},
        "context_C_minus_A": {"mean_delta": round(ca_mean, 4),
                              "ci95": [round(ca_lo, 4), round(ca_hi, 4)]},
        "arm_means_fraction_met": arm_means,
        "audit": {"n": len(audit), "correct": correct, "blinding_leak": blinding_leak},
        "verdict": word,
        "keep_condition_met": cb_mean > 0,
    }
    (HERE / "results.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(json.dumps(results, indent=1))
    if blinding_leak:
        print("WARNING: guess-the-arm >=7/9 — blinding leak; ADR 0052 revisit trigger fires")


if __name__ == "__main__":
    main()
