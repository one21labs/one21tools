#!/usr/bin/env python3
"""Per-skill merge verdicts for the issue #55 3-skill re-measure (ADR 0027 bar, generalized).

Inputs (graded/): verdicts.jsonl (grader + prosecutor-on-PASS, final evidence = final judgment's),
prosecute_counts.jsonl (uniform adversarial re-count), arm_map.tsv.
Metric = fraction-met with met_final = min(grader_met, prosecutor_met) per cell (ADR 0025).
Per (skill, eval): mean frac per arm over reps, then d_old = with-old - without,
d_new = with-new - without, diff = d_new - d_old (algebraically with-new minus with-old).
Merge bar per skill (ADR 0027 as amended): PRIMARY mean(diff) > 0 -> MERGE, directional; the
skill-clustered 95% CI on diff is a confidence signal (strong if it excludes 0), never a gate;
mean(diff) <= 0 -> NO MERGE (one valid de-confounded ADR 0024 iteration for that skill).
Writes results.jsonl.
"""
import csv, json, math, os, statistics

BASE = os.path.dirname(os.path.abspath(__file__))
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

frac = {}   # (skill, eval_id, arm) -> [met_final/total per rep]
for bid, m in arm_map.items():
    v, c = verdicts.get(bid), counts.get(bid)
    if v is None or c is None:
        print(f"WARNING: bid {bid} missing {'verdict' if v is None else 'prosecutor count'} — skipped")
        continue
    tot = v.get("total") or 0
    met = min(v.get("met") or 0, c.get("met") or 0)
    frac.setdefault((m["skill"], m["eval_id"], m["arm"]), []).append((met / tot) if tot else 0.0)


def ci95(vals):
    n = len(vals)
    mean = statistics.fmean(vals) if n else 0.0
    sd = statistics.stdev(vals) if n > 1 else 0.0
    se = sd / math.sqrt(n) if n else 0.0
    return mean, mean - 1.96 * se, mean + 1.96 * se


with open(os.path.join(BASE, "treatments", "costs.json"), encoding="utf-8") as fh:
    costs = json.load(fh)

skills = sorted({s for (s, _, _) in frac})
rows, verdict_rows = [], []
for sk in skills:
    evals = sorted({e for (s, e, _) in frac if s == sk}, key=int)
    d_old, d_new, diffs = [], [], []
    for e in evals:
        arm_mean = {a: (statistics.fmean(frac[(sk, e, a)]) if frac.get((sk, e, a)) else float("nan"))
                    for a in ("without", "with-old", "with-new")}
        do = arm_mean["with-old"] - arm_mean["without"]
        dn = arm_mean["with-new"] - arm_mean["without"]
        d_old.append(do); d_new.append(dn); diffs.append(dn - do)
        rows.append({"record": "eval", "skill": sk, "eval_id": e,
                     "without": round(arm_mean["without"], 3), "with_old": round(arm_mean["with-old"], 3),
                     "with_new": round(arm_mean["with-new"], 3), "d_old": round(do, 3),
                     "d_new": round(dn, 3), "diff": round(dn - do, 3)})
    summary = {}
    for name, vals in (("d_old", d_old), ("d_new", d_new), ("diff", diffs)):
        mean, lo, hi = ci95(vals)
        summary[name] = {"mean": round(mean, 3), "ci95": [round(lo, 3), round(hi, 3)]}
    merge = summary["diff"]["mean"] > 0
    confidence = ("strong" if summary["diff"]["ci95"][0] > 0 else "weak") if merge else None
    verdict_rows.append({"record": "verdict", "skill": sk, "evals": len(evals), **summary,
                         "merge": merge, "confidence": confidence,
                         "cost": costs["skills"].get(sk, {})})

with open(os.path.join(BASE, "results.jsonl"), "w", encoding="utf-8", newline="") as fh:
    for r in rows + verdict_rows:
        fh.write(json.dumps(r, separators=(",", ":")) + "\n")

print("=== issue #55 re-measure: fraction-met, met_final=min(grader,prosecutor) ===")
for vr in verdict_rows:
    sk = vr["skill"]
    print(f"\n=== {sk} ===")
    for r in [r for r in rows if r["skill"] == sk]:
        print(f"  eval {r['eval_id']:>2}: without={r['without']:.2f} old={r['with_old']:.2f} "
              f"new={r['with_new']:.2f}  d_old={r['d_old']:+.2f} d_new={r['d_new']:+.2f} diff={r['diff']:+.2f}")
    for name in ("d_old", "d_new", "diff"):
        s = vr[name]
        print(f"  {name}: mean {s['mean']:+.3f} CI [{s['ci95'][0]:+.3f},{s['ci95'][1]:+.3f}]")
    b = vr["cost"].get("body_chars", {})
    print(f"  cost: body {b.get('with-old')}->{b.get('with-new')} chars")
    print(f"  VERDICT: {('MERGE (' + vr['confidence'] + ')') if vr['merge'] else 'NO MERGE'}")
