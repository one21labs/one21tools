#!/usr/bin/env python3
"""KEEP/CUT-style verdict for the EP loophole OOS hermetic retest (issue #31 item 5).

Inputs (graded/): verdicts.jsonl ({bid,pass,met,total,...} per line, grader+prosecutor-on-PASS),
prosecute_counts.jsonl ({bid,met,total,...} per line, uniform adversarial re-count), arm_map.tsv.
Metric = fraction-met with met_final = min(grader_met, prosecutor_met) per cell (ADR 0025), same
metric convention as 2026-07-08-skills-hermetic and 2026-07-09-ep-remeasure-hermetic. Each of the
3 OOS evals is one clustered observation (ADR 0019): per-eval delta = mean frac WITH minus
WITHOUT; headline = mean per-eval delta + 95% CI across the 3 evals. Reuses the shared
KEEP/HARMFUL/CUT-CANDIDATE/INCONCLUSIVE rule (benchmarks/lib/verdict.py, ADR 0024/0026) rather
than redefining it — this run's n=3 evals is smaller than the n=6 grid the rule was calibrated
against, so a straddling CI is expected and reported as INCONCLUSIVE (underpowered), not a null.
Writes results.jsonl.
"""
import csv, json, math, os, statistics, sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "..", "lib"))
from verdict import verdict_of  # ADR 0026 shared lib; same rule 2026-07-08-skills-hermetic uses

G = os.path.join(BASE, "graded")


def read_jsonl(path):
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                r = json.loads(line)
                out[r["bid"]] = r
    return out


verdicts = read_jsonl(os.path.join(G, "verdicts.jsonl"))
counts = read_jsonl(os.path.join(G, "prosecute_counts.jsonl"))
with open(os.path.join(G, "arm_map.tsv"), encoding="utf-8") as fh:
    arm_map = {r["bid"]: r for r in csv.DictReader(fh, delimiter="\t")}

frac = {}   # (eval_id, arm) -> [met_final/total per rep]
for bid, m in arm_map.items():
    v, c = verdicts.get(bid), counts.get(bid)
    if v is None or c is None:
        print(f"WARNING: bid {bid} missing {'verdict' if v is None else 'prosecutor count'} — skipped")
        continue
    tot = v.get("total") or 0
    met = min(v.get("met") or 0, c.get("met") or 0)
    frac.setdefault((m["eval_id"], m["arm"]), []).append((met / tot) if tot else 0.0)


def ci95(vals):
    n = len(vals)
    mean = statistics.fmean(vals) if n else 0.0
    sd = statistics.stdev(vals) if n > 1 else 0.0
    se = sd / math.sqrt(n) if n else 0.0
    return mean, mean - 1.96 * se, mean + 1.96 * se


evals = sorted({e for (e, _) in frac}, key=int)
rows, deltas = [], []
for e in evals:
    arm_mean = {a: (statistics.fmean(frac[(e, a)]) if frac.get((e, a)) else float("nan"))
                for a in ("without", "with")}
    d = arm_mean["with"] - arm_mean["without"]
    deltas.append(d)
    rows.append({"record": "eval", "eval_id": e, "without": round(arm_mean["without"], 3),
                 "with": round(arm_mean["with"], 3), "delta": round(d, 3)})

mean, lo, hi = ci95(deltas)
verdict = {"record": "verdict", "evals": len(evals), "mean_delta": round(mean, 3),
           "delta_ci95": [round(lo, 3), round(hi, 3)], "verdict": verdict_of(mean, lo, hi, len(evals)),
           "note": "n=3 evals (vs the n=6 grid verdict_of was calibrated against): a straddling "
                   "CI here is an underpowered measurement, not a clean null (ADR 0024)."}

with open(os.path.join(BASE, "results.jsonl"), "w", encoding="utf-8", newline="") as fh:
    for r in rows:
        fh.write(json.dumps(r) + "\n")
    fh.write(json.dumps(verdict) + "\n")

print("=== EP loophole OOS hermetic retest: fraction-met, met_final=min(grader,prosecutor) ===")
for r in rows:
    print(f"  eval {r['eval_id']:>2}: without={r['without']:.2f} with={r['with']:.2f} delta={r['delta']:+.2f}")
print(f"  mean delta {verdict['mean_delta']:+.3f} CI [{verdict['delta_ci95'][0]:+.3f},{verdict['delta_ci95'][1]:+.3f}] -> {verdict['verdict']}")
