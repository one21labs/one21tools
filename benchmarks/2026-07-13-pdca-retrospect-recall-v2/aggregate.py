#!/usr/bin/env python3
"""I1 v2 aggregation (pre-registration: README.md / metadata.json -- frozen bar, this script just
computes it). Successor to ../2026-07-12-pdca-retrospect-recall/aggregate.py (frozen; never
edited).

Reads graded/verdicts.jsonl (the opus judge pipeline's persisted result, per lib/README.md),
graded/arm_map.tsv, graded/audit.jsonl, graded/keys/<sub>.json (now carrying routing_key
alongside found_iff, per blind_cells.py's v2 delta). Input contract for graded/verdicts.jsonl,
per cell: {bid, substrate, seeds: [{class, found, routed, matched_claim, why}, ...] (same order
as the key), nonseed: [{claim, real, why}, ...]} -- "routed" is the v2 addition the grading
workflow's routing-aware successor to v1's grade.workflow.js must emit per ADR 0057 d2 /
README.md item 3; this script does not grade, only aggregates what the pipeline judged.

Computes, exactly as pre-registered (metadata.json:bar):
  - PRIMARY per-cell triage score (seeded substrates): per seed, 1.0 if found AND routed
    (grader-AND-prosecutor per the pipeline's own min-of-two-judges discipline, carried in the
    "found"/"routed" booleans it persists), 0.5 if found only, 0 otherwise; cell triage = mean
    over the substrate's K seeds.
  - primary bar: mean over the 6 seeded clusters of (mean triage_C - mean triage_A), 95% t-CI over
    cluster deltas (df=5, t=2.571 -- cluster = substrate, small-n t in place of Wilson because the
    statistic is a mean delta, not a proportion). bar_pass = mean_delta > 0.
  - verdict word via lib/verdict.py:verdict_of on (mean, lo, hi).
  - FP guard (clean substrates), audit (guess-the-arm) -- both v1's exact rule, unchanged.
  - SECONDARY diagnostics (recorded, never the bar): raw recall = found/K per cell (v1's metric,
    ignoring routing), and per-class found rate by arm.
  - grok_regrade: reserved result slots for the second headline (ADR 0057 d2 / README item 5) --
    "pending" with null fields until graded/verdicts_grok.jsonl exists; once present, the SAME
    triage pipeline runs over it and, if its bar_pass disagrees with the opus pipeline's, the
    verdict is forced to JUDGE-SPLIT (never averaged, never promoted to KEEP) regardless of the
    opus-only word or the FP-guard spray check.
Writes results.json and prints the verdict block.
"""
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "skill-bench" / "scripts" / "lib"))
import bench_io  # noqa: E402
from verdict import verdict_of  # noqa: E402

T_DF5_95 = 2.571
SEEDED = ["T1", "T2", "T3", "T4", "T5", "T6"]
CLEAN = ["C1", "C2"]


def triage_and_raw(seed_judgments, key):
    """(triage_score, raw_recall) for one cell: triage credits routing (1.0/0.5/0), raw recall is
    v1's found/K regardless of routing (secondary diagnostic)."""
    k = len(key)
    if k == 0:
        return 0.0, 0.0
    triage_total = 0.0
    found_n = 0
    for sj in seed_judgments:
        found = bool(sj.get("found"))
        routed = bool(sj.get("routed"))
        if found and routed:
            triage_total += 1.0
        elif found:
            triage_total += 0.5
        if found:
            found_n += 1
    return triage_total / k, found_n / k


def _cluster_ci(deltas):
    mean_d = statistics.mean(deltas)
    sd = statistics.stdev(deltas)
    half = T_DF5_95 * sd / (len(deltas) ** 0.5)
    return mean_d, mean_d - half, mean_d + half


def _primary_block(cells, arm_map, keys):
    """Runs the triage pipeline over one judge's verdicts dict {bid: cell}. Returns
    (results_dict, bar_pass, per_sub, raw_recall_pairs) or None if any seeded substrate is
    missing cells (incomplete grid for that judge)."""
    triage = {}   # (sub, arm) -> [per-cell triage]
    raw = {}      # (sub, arm) -> [per-cell raw recall]
    per_class_found = {}  # (class, arm) -> [bool]

    for m in arm_map:
        c = cells.get(m["bid"])
        if not c or m["substrate"] not in SEEDED:
            continue
        kdef = keys.get(m["substrate"], [])
        seed_judgments = c.get("seeds", [])
        t, r = triage_and_raw(seed_judgments, kdef)
        key = (m["substrate"], m["arm"])
        triage.setdefault(key, []).append(t)
        raw.setdefault(key, []).append(r)
        for kd, sj in zip(kdef, seed_judgments):
            per_class_found.setdefault((kd["class"], m["arm"]), []).append(bool(sj.get("found")))

    deltas = []
    per_sub = {}
    for sub in SEEDED:
        a = triage.get((sub, "A"), [])
        c = triage.get((sub, "C"), [])
        if not a or not c:
            return None
        d = statistics.mean(c) - statistics.mean(a)
        per_sub[sub] = {
            "triage_A": round(statistics.mean(a), 3), "triage_C": round(statistics.mean(c), 3),
            "delta": round(d, 3),
            "raw_recall_A": round(statistics.mean(raw.get((sub, "A"), [0.0])), 3),
            "raw_recall_C": round(statistics.mean(raw.get((sub, "C"), [0.0])), 3),
        }
        deltas.append(d)

    mean_d, lo, hi = _cluster_ci(deltas)
    word = verdict_of(mean_d, lo, hi, len(deltas))
    confidence = "strong" if lo > 0 else "weak"
    bar_pass = mean_d > 0

    per_class_rate = {}
    for (cls, arm), vals in per_class_found.items():
        per_class_rate.setdefault(cls, {})[arm] = round(sum(vals) / len(vals), 3) if vals else 0.0

    primary = {"mean_delta": round(mean_d, 4), "ci95": [round(lo, 4), round(hi, 4)],
               "clusters": len(deltas), "confidence": confidence, "bar_pass": bar_pass}
    return primary, word, per_sub, per_class_rate


def main():
    graded = HERE / "graded"
    cells = {c["bid"]: c for c in bench_io.load_records(str(graded / "verdicts.jsonl"), fmt="jsonl")}
    arm_map = bench_io.load_records(str(graded / "arm_map.tsv"), fmt="tsv")
    audit = bench_io.load_records(str(graded / "audit.jsonl"), fmt="jsonl")
    keys = {}
    for sub in SEEDED:
        p = graded / "keys" / f"{sub}.json"
        if p.exists():
            keys[sub] = json.loads(p.read_text(encoding="utf-8"))

    opus = _primary_block(cells, arm_map, keys)
    if opus is None:
        sys.exit("missing cells for one or more seeded substrates -- grid incomplete")
    primary, word, per_sub, per_class_rate = opus

    fp = {}
    for m in arm_map:
        c = cells.get(m["bid"])
        if not c:
            continue
        key = (m["substrate"], m["arm"])
        fp.setdefault(key, []).append(sum(1 for f in c.get("nonseed", []) if not f.get("real")))
    fp_means = {arm: statistics.mean([x for sub in CLEAN for x in fp.get((sub, arm), [0])])
                for arm in ("A", "C")}
    guard_pass = fp_means["C"] <= fp_means["A"] + 1.0

    arm_of = {m["bid"]: m["arm"] for m in arm_map}
    correct = sum(1 for a in audit if a.get("guess") == arm_of.get(a["bid"]))
    blinding_leak = len(audit) >= 8 and correct >= 7

    headline = word
    if primary["mean_delta"] > 0 and not guard_pass:
        headline = "INCONCLUSIVE-spray"

    # Judge policy (ADR 0057 d2 / README.md item 5): grok-4.5 re-grade is the second headline.
    # Reserved slots, filled once graded/verdicts_grok.jsonl exists.
    grok_path = graded / "verdicts_grok.jsonl"
    grok_block = {"status": "pending", "primary": None, "verdict": None}
    judge_split = None
    if grok_path.exists():
        grok_cells = {c["bid"]: c for c in bench_io.load_records(str(grok_path), fmt="jsonl")}
        grok_result = _primary_block(grok_cells, arm_map, keys)
        if grok_result is not None:
            g_primary, g_word, _, _ = grok_result
            grok_block = {"status": "complete", "primary": g_primary, "verdict": g_word}
            judge_split = primary["bar_pass"] != g_primary["bar_pass"]
            if judge_split:
                headline = "JUDGE-SPLIT"

    results = {
        "primary": primary,
        "per_substrate": per_sub,
        "secondary": {"per_class_found_rate": per_class_rate},
        "fp_guard": {"mean_FP_A": round(fp_means["A"], 3), "mean_FP_C": round(fp_means["C"], 3),
                     "pass": guard_pass},
        "audit": {"n": len(audit), "correct": correct, "blinding_leak": blinding_leak},
        "grok_regrade": grok_block,
        "judge_split": judge_split,
        "verdict": headline,
    }
    (HERE / "results.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(json.dumps(results, indent=1))
    if blinding_leak:
        print("WARNING: guess-the-arm audit >=7/8 -- blinding leak; ADR 0052 revisit trigger fires")
    if judge_split:
        print("WARNING: opus and grok disagree on the primary bar's pass/fail -- JUDGE-SPLIT, "
              "never averaged, never promoted to KEEP")


if __name__ == "__main__":
    main()
