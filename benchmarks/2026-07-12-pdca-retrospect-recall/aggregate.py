#!/usr/bin/env python3
"""I1 aggregation (pre-registration: README.md — frozen bar, this script just computes it).

Reads graded/verdicts.jsonl (workflow result persisted per lib/README.md), graded/arm_map.tsv,
graded/audit.jsonl. Computes, exactly as pre-registered:
  - per-cell recall = prosecutor-confirmed found / K (seeded substrates)
  - primary: mean over the 6 seeded clusters of (mean recall_C - mean recall_A), 95% t-CI over
    cluster deltas (df=5, t=2.571 — cluster = substrate per ADR 0019's unit; small-n t in place
    of Wilson because the statistic is a mean delta, not a proportion)
  - verdict word via lib/verdict.py:verdict_of on (mean, lo, hi)
  - FP guard: mean prosecutor-confirmed non-real assertions per cell on C1/C2 by arm;
    guard passes iff mean_FP_C <= mean_FP_A + 1.0; recall-win + guard-fail = INCONCLUSIVE-spray
  - audit: guess-the-arm accuracy on the 8 sampled cells; pre-registered "significantly above
    0.5" operationalized as >=7/8 (one-sided binomial p=0.035 at 8 trials)
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

T_DF5_95 = 2.571
SEEDED = ["T1", "T2", "T3", "T4", "T5", "T6"]
CLEAN = ["C1", "C2"]


def main():
    graded = HERE / "graded"
    cells = {c["bid"]: c for c in bench_io.load_records(str(graded / "verdicts.jsonl"), fmt="jsonl")}
    arm_map = bench_io.load_records(str(graded / "arm_map.tsv"), fmt="tsv")
    audit = bench_io.load_records(str(graded / "audit.jsonl"), fmt="jsonl")

    recall = {}   # (substrate, arm) -> [per-rep recall]
    fp = {}       # (substrate, arm) -> [per-rep FP count]
    for m in arm_map:
        c = cells.get(m["bid"])
        if not c:
            continue
        key = (m["substrate"], m["arm"])
        if m["substrate"] in SEEDED:
            k = len(c["seeds"])
            recall.setdefault(key, []).append(
                sum(1 for s in c["seeds"] if s["found"]) / k if k else 0.0)
        fp.setdefault(key, []).append(
            sum(1 for f in c["nonseed"] if not f["real"]))

    deltas = []
    per_sub = {}
    for sub in SEEDED:
        a = recall.get((sub, "A"), [])
        c = recall.get((sub, "C"), [])
        if not a or not c:
            sys.exit(f"missing cells for {sub} (A={len(a)}, C={len(c)}) — grid incomplete")
        d = statistics.mean(c) - statistics.mean(a)
        per_sub[sub] = {"recall_A": round(statistics.mean(a), 3),
                        "recall_C": round(statistics.mean(c), 3), "delta": round(d, 3)}
        deltas.append(d)
    mean_d = statistics.mean(deltas)
    sd = statistics.stdev(deltas)
    half = T_DF5_95 * sd / (len(deltas) ** 0.5)
    lo, hi = mean_d - half, mean_d + half
    word = verdict_of(mean_d, lo, hi, len(deltas))

    fp_means = {arm: statistics.mean([x for sub in CLEAN for x in fp.get((sub, arm), [0])])
                for arm in ("A", "C")}
    guard_pass = fp_means["C"] <= fp_means["A"] + 1.0

    arm_of = {m["bid"]: m["arm"] for m in arm_map}
    correct = sum(1 for a in audit if a.get("guess") == arm_of.get(a["bid"]))
    blinding_leak = len(audit) >= 8 and correct >= 7

    headline = word
    if mean_d > 0 and not guard_pass:
        headline = "INCONCLUSIVE-spray"
    confidence = "strong" if lo > 0 else "weak"

    results = {
        "primary": {"mean_delta": round(mean_d, 4), "ci95": [round(lo, 4), round(hi, 4)],
                    "clusters": len(deltas), "confidence": confidence},
        "per_substrate": per_sub,
        "fp_guard": {"mean_FP_A": round(fp_means["A"], 3), "mean_FP_C": round(fp_means["C"], 3),
                     "pass": guard_pass},
        "audit": {"n": len(audit), "correct": correct, "blinding_leak": blinding_leak},
        "verdict": headline,
    }
    (HERE / "results.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(json.dumps(results, indent=1))
    if blinding_leak:
        print("WARNING: guess-the-arm audit >=7/8 — blinding leak; ADR 0052 revisit trigger fires")


if __name__ == "__main__":
    main()
