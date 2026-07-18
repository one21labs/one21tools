#!/usr/bin/env python3
"""ep-partition 4-arm merge read (issue #244).

Inputs (graded/): verdicts.jsonl ({bid,pass,met,total,...} per line, grader+prosecutor-on-PASS),
prosecute_counts.jsonl ({bid,met,total,...} per line, uniform adversarial re-count), arm_map.tsv.
Metric = fraction-met with met_final = min(grader_met, prosecutor_met) per cell (ADR 0025).
Per eval (one clustered observation, ADR 0019): mean frac per arm over reps, then
  d_full        = with-full        - without
  d_operational = with-operational - without
  d_conceptual  = with-conceptual  - without
  contrast_fo   = with-full - with-operational   (full-vs-operational)
  contrast_fc   = with-full - with-conceptual    (full-vs-conceptual)
Headline = eval-clustered mean + 95% CI for each of the 5 series above (n = evals, not cells).
No Option-E escalation (07-09/ADR 0027 mechanism; not part of this design -- issue #244 reads
kill conditions off the CIs directly, see below).

Kill-condition reads (issue #244, pre-registered; a CI "contains 0" = indistinguishable, "excludes
0" = a genuine, directionally-consistent effect at n=6 evals):
  operational_retains      : contrast_fo CI contains 0  AND  d_operational CI excludes 0
                              ("C delta ~ B" -- operational keeps the delta full has)
  conceptual_inert         : d_conceptual CI contains 0
                              ("D delta ~ A" -- conceptual content adds nothing over bare)
  conceptual_activates     : contrast_fc CI contains 0  AND  d_conceptual CI excludes 0
                              ("D delta ~ B" -- activation hypothesis: conceptual alone matches full)
  full_beats_operational   : contrast_fo CI excludes 0  AND  mean(contrast_fo) > 0
                              ("B > C clearly" -- conceptual content carries real signal)
Named per-issue kill conditions are derived compounds of these four reads (see verdict.reads_summary).
Writes results.jsonl (record types: eval, verdict, cost).
"""
import csv, json, math, os, statistics

BASE = os.path.dirname(os.path.abspath(__file__))
G = os.path.join(BASE, "graded")
ARMS = ("without", "with-full", "with-operational", "with-conceptual")


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


def excludes_zero(ci):
    return ci[0] > 0 or ci[1] < 0


def contains_zero(ci):
    return not excludes_zero(ci)


evals = sorted({e for (e, _) in frac}, key=int)
rows = []
series = {k: [] for k in ("d_full", "d_operational", "d_conceptual", "contrast_fo", "contrast_fc")}
for e in evals:
    arm_mean = {a: (statistics.fmean(frac[(e, a)]) if frac.get((e, a)) else float("nan")) for a in ARMS}
    d_full = arm_mean["with-full"] - arm_mean["without"]
    d_op = arm_mean["with-operational"] - arm_mean["without"]
    d_co = arm_mean["with-conceptual"] - arm_mean["without"]
    c_fo = arm_mean["with-full"] - arm_mean["with-operational"]
    c_fc = arm_mean["with-full"] - arm_mean["with-conceptual"]
    series["d_full"].append(d_full); series["d_operational"].append(d_op)
    series["d_conceptual"].append(d_co); series["contrast_fo"].append(c_fo)
    series["contrast_fc"].append(c_fc)
    rows.append({"record": "eval", "eval_id": e,
                 "without": round(arm_mean["without"], 3),
                 "with_full": round(arm_mean["with-full"], 3),
                 "with_operational": round(arm_mean["with-operational"], 3),
                 "with_conceptual": round(arm_mean["with-conceptual"], 3),
                 "d_full": round(d_full, 3), "d_operational": round(d_op, 3),
                 "d_conceptual": round(d_co, 3),
                 "contrast_fo": round(c_fo, 3), "contrast_fc": round(c_fc, 3)})

summary = {}
for name, vals in series.items():
    mean, lo, hi = ci95(vals)
    summary[name] = {"mean": round(mean, 3), "ci95": [round(lo, 3), round(hi, 3)]}

ci_fo = summary["contrast_fo"]["ci95"]
ci_fc = summary["contrast_fc"]["ci95"]
ci_do = summary["d_operational"]["ci95"]
ci_dc = summary["d_conceptual"]["ci95"]
mean_fo = summary["contrast_fo"]["mean"]

operational_retains = contains_zero(ci_fo) and excludes_zero(ci_do)
conceptual_inert = contains_zero(ci_dc)
conceptual_activates = contains_zero(ci_fc) and excludes_zero(ci_dc)
full_beats_operational = excludes_zero(ci_fo) and mean_fo > 0

reads = {
    "operational_retains": {
        "value": operational_retains,
        "evidence": f"contrast_fo (full-vs-operational) CI [{ci_fo[0]:+.3f},{ci_fo[1]:+.3f}] "
                    f"{'contains' if contains_zero(ci_fo) else 'excludes'} 0; "
                    f"d_operational CI [{ci_do[0]:+.3f},{ci_do[1]:+.3f}] "
                    f"{'excludes' if excludes_zero(ci_do) else 'contains'} 0",
    },
    "conceptual_inert": {
        "value": conceptual_inert,
        "evidence": f"d_conceptual CI [{ci_dc[0]:+.3f},{ci_dc[1]:+.3f}] "
                    f"{'contains' if contains_zero(ci_dc) else 'excludes'} 0",
    },
    "conceptual_activates": {
        "value": conceptual_activates,
        "evidence": f"contrast_fc (full-vs-conceptual) CI [{ci_fc[0]:+.3f},{ci_fc[1]:+.3f}] "
                    f"{'contains' if contains_zero(ci_fc) else 'excludes'} 0; "
                    f"d_conceptual CI [{ci_dc[0]:+.3f},{ci_dc[1]:+.3f}] "
                    f"{'excludes' if excludes_zero(ci_dc) else 'contains'} 0",
    },
    "full_beats_operational": {
        "value": full_beats_operational,
        "evidence": f"contrast_fo (full-vs-operational) CI [{ci_fo[0]:+.3f},{ci_fo[1]:+.3f}] "
                    f"{'excludes' if excludes_zero(ci_fo) else 'contains'} 0, mean {mean_fo:+.3f} "
                    f"({'full > operational' if mean_fo > 0 else 'full <= operational'})",
    },
}
reads_summary = {
    "conceptual_content_inert": reads["operational_retains"]["value"] and reads["conceptual_inert"]["value"],
    "activation_hypothesis_wins": reads["conceptual_activates"]["value"],
    "conceptual_content_carries_signal": reads["full_beats_operational"]["value"],
}

verdict = {"record": "verdict", "evals": len(evals), **summary,
           "reads": reads, "reads_summary": reads_summary,
           "kill_conditions_source": "issue #244 pre-registered kill conditions",
           "n_note": "n=6 evals (or fewer if prescreen dropped any); CIs are directional confidence "
                     "signals per ADR 0027-style bar, not a hard gate"}

with open(os.path.join(BASE, "treatments", "costs.json"), encoding="utf-8") as fh:
    costs = json.load(fh)

with open(os.path.join(BASE, "results.jsonl"), "w", encoding="utf-8", newline="") as fh:
    for r in rows:
        fh.write(json.dumps(r) + "\n")
    fh.write(json.dumps(verdict) + "\n")
    fh.write(json.dumps({"record": "cost", **costs}) + "\n")

print("=== ep-partition: fraction-met, met_final=min(grader,prosecutor) ===")
for r in rows:
    print(f"  eval {r['eval_id']:>2}: without={r['without']:.2f} full={r['with_full']:.2f} "
          f"operational={r['with_operational']:.2f} conceptual={r['with_conceptual']:.2f}  "
          f"d_full={r['d_full']:+.2f} d_op={r['d_operational']:+.2f} d_co={r['d_conceptual']:+.2f}  "
          f"fo={r['contrast_fo']:+.2f} fc={r['contrast_fc']:+.2f}")
for name in ("d_full", "d_operational", "d_conceptual", "contrast_fo", "contrast_fc"):
    s = summary[name]
    print(f"  {name}: mean {s['mean']:+.3f} CI [{s['ci95'][0]:+.3f},{s['ci95'][1]:+.3f}]")
print(f"\n=== kill-condition reads (issue #244) ===")
for k, v in reads.items():
    print(f"  {k}: {v['value']}  ({v['evidence']})")
print(f"\n=== derived reads_summary ===")
for k, v in reads_summary.items():
    print(f"  {k}: {v}")
