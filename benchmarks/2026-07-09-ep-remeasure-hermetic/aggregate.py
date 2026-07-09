#!/usr/bin/env python3
"""ADR 0027 merge verdict for the 3-arm EP re-measure (issue #52).

Inputs (graded/): verdicts.jsonl ({bid,pass,met,total,...} per line, grader+prosecutor-on-PASS),
prosecute_counts.jsonl ({bid,met,total,...} per line, uniform adversarial re-count), arm_map.tsv.
Metric = fraction-met with met_final = min(grader_met, prosecutor_met) per cell (ADR 0025).
Per eval (one clustered observation, ADR 0019): mean frac per arm over reps, then
  d_old = with-old - without, d_new = with-new - without, diff = d_new - d_old.
Merge bar (ADR 0027 decision 5, as amended post-red-team): PRIMARY mean(diff) > 0 -> MERGE,
directional; the clustered 95% CI on diff is a secondary confidence signal (strong if it
excludes 0, weak if it straddles), never a gate; mean(diff) <= 0 -> NO MERGE. Decision 6:
ANY of evals {1,2,5,6} with d_new <= 1e-9 fires the Option E diagnostic escalation.
Writes results.jsonl.
"""
import csv, json, math, os, statistics

BASE = os.path.dirname(os.path.abspath(__file__))
G = os.path.join(BASE, "graded")
ESCALATION_EVALS = {"1", "2", "5", "6"}


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
rows, d_old, d_new, diffs, escalate = [], [], [], [], []
for e in evals:
    arm_mean = {a: (statistics.fmean(frac[(e, a)]) if frac.get((e, a)) else float("nan"))
                for a in ("without", "with-old", "with-new")}
    do = arm_mean["with-old"] - arm_mean["without"]
    dn = arm_mean["with-new"] - arm_mean["without"]
    d_old.append(do); d_new.append(dn); diffs.append(dn - do)
    if e in ESCALATION_EVALS and dn <= 1e-9:
        escalate.append(e)
    rows.append({"record": "eval", "eval_id": e,
                 "without": round(arm_mean["without"], 3), "with_old": round(arm_mean["with-old"], 3),
                 "with_new": round(arm_mean["with-new"], 3), "d_old": round(do, 3),
                 "d_new": round(dn, 3), "diff": round(dn - do, 3)})

summary = {}
for name, vals in (("d_old", d_old), ("d_new", d_new), ("diff", diffs)):
    mean, lo, hi = ci95(vals)
    summary[name] = {"mean": round(mean, 3), "ci95": [round(lo, 3), round(hi, 3)]}

merge = summary["diff"]["mean"] > 0
confidence = ("strong" if summary["diff"]["ci95"][0] > 0 else "weak") if merge else None
verdict = {"record": "verdict", "evals": len(evals), **summary,
           "merge": merge, "confidence": confidence,
           "merge_bar": "PRIMARY mean(diff)>0 directional; CI secondary confidence signal (ADR 0027 as amended)",
           "option_e_escalation": sorted(escalate, key=int)}

with open(os.path.join(BASE, "treatments", "costs.json"), encoding="utf-8") as fh:
    costs = json.load(fh)

with open(os.path.join(BASE, "results.jsonl"), "w", encoding="utf-8") as fh:
    for r in rows:
        fh.write(json.dumps(r) + "\n")
    fh.write(json.dumps(verdict) + "\n")
    fh.write(json.dumps({"record": "cost", **costs}) + "\n")

print("=== ADR 0027 EP re-measure: fraction-met, met_final=min(grader,prosecutor) ===")
for r in rows:
    print(f"  eval {r['eval_id']:>2}: without={r['without']:.2f} old={r['with_old']:.2f} "
          f"new={r['with_new']:.2f}  d_old={r['d_old']:+.2f} d_new={r['d_new']:+.2f} diff={r['diff']:+.2f}")
for name in ("d_old", "d_new", "diff"):
    s = summary[name]
    print(f"  {name}: mean {s['mean']:+.3f} CI [{s['ci95'][0]:+.3f},{s['ci95'][1]:+.3f}]")
print(f"  cost: body {costs['body_chars']['with-old']}->{costs['body_chars']['with-new']} chars; "
      f"full {costs['full_chars']['with-old']}->{costs['full_chars']['with-new']} chars")
print(f"\nVERDICT: {'MERGE (' + confidence + ' confidence)' if merge else 'NO MERGE'} (bar: {verdict['merge_bar']})")
if escalate:
    print(f"Option E diagnostic escalation fires (ADR 0027 decision 6): d_new flat/negative on evals {verdict['option_e_escalation']}")
