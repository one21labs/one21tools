#!/usr/bin/env python3
"""Per-skill KEEP/CUT verdict for the hermetic skill benefit-benchmark.

Inputs (graded/): verdicts.json {bid: {pass, met, total, ...}}, arm_map.json {bid: {skill,eval_id,arm}}.
HEADLINE metric = fraction-met (met/total) per cell (ADR 0025): the binary all-or-nothing pass floors
on hard multi-expectation evals and discards a skill's marginal effect, so the continuous met/total
(with the prosecutor applied to counts uniformly, ADR 0025) is the powered measurement. Each eval is one
clustered observation: per-eval delta = mean frac WITH minus WITHOUT; per-skill headline = mean per-eval
delta + 95% CI across the skill's evals (ADR 0019). KEEP if the CI excludes 0 and is positive (ADR 0024).
Binary pass-rate delta is retained as a SECONDARY diagnostic only. Writes results.jsonl; prints both.
"""
import json, math, os, statistics

BASE = os.path.dirname(os.path.abspath(__file__))
G = os.path.join(BASE, "graded")
with open(os.path.join(G, "verdicts.json"), encoding="utf-8") as fh:
    verdicts = json.load(fh)
with open(os.path.join(G, "arm_map.json"), encoding="utf-8") as fh:
    arm_map = json.load(fh)


def verdict_of(mean, lo, hi, n):
    if n and lo > 0:
        return "KEEP"
    if n and hi < 0:
        return "HARMFUL"
    # guards above return unless the CI straddles 0, so lo <= 0 <= hi holds here
    if n and abs(mean) < 0.05:
        return "CUT-CANDIDATE"
    return "INCONCLUSIVE"


# per (skill, eval, arm) -> value lists, for both metrics
frac = {}   # met/total
binr = {}   # 1 if pass else 0
for bid, m in arm_map.items():
    v = verdicts.get(bid)
    if v is None:
        continue
    tot = v.get("total") or 0
    f = ((v.get("met") or 0) / tot) if tot else 0.0
    frac.setdefault((m["skill"], m["eval_id"], m["arm"]), []).append(f)
    binr.setdefault((m["skill"], m["eval_id"], m["arm"]), []).append(1 if v.get("pass") else 0)


def summarize(cellmap):
    """Per-skill: per-eval with-without delta, then mean + 95% CI clustered over evals."""
    skills = sorted({s for (s, _, _) in cellmap})
    rows, summaries, all_d = [], [], []
    for sk in skills:
        evs = sorted({e for (s, e, _) in cellmap if s == sk}, key=lambda x: int(x))
        deltas, w, l, t = [], 0, 0, 0
        for e in evs:
            wi = cellmap.get((sk, e, "with"), []); wo = cellmap.get((sk, e, "without"), [])
            wr = statistics.fmean(wi) if wi else float("nan")
            wor = statistics.fmean(wo) if wo else float("nan")
            d = wr - wor
            deltas.append(d); all_d.append(d)
            cls = "win" if d > 1e-9 else ("loss" if d < -1e-9 else "tie")
            w += cls == "win"; l += cls == "loss"; t += cls == "tie"
            rows.append({"record": "eval", "skill": sk, "eval_id": e, "with": round(wr, 3),
                         "without": round(wor, 3), "delta": round(d, 3), "class": cls})
        n = len(deltas); mean = statistics.fmean(deltas) if n else 0.0
        sd = statistics.stdev(deltas) if n > 1 else 0.0; se = sd / math.sqrt(n) if n else 0.0
        lo, hi = mean - 1.96 * se, mean + 1.96 * se
        summaries.append({"record": "skill", "skill": sk, "evals": n, "mean_delta": round(mean, 3),
                          "delta_ci95": [round(lo, 3), round(hi, 3)], "wins": w, "losses": l, "ties": t,
                          "verdict": verdict_of(mean, lo, hi, n), "ci_halfwidth": round(1.96 * se, 3)})
    N = len(all_d); om = statistics.fmean(all_d) if N else 0.0
    osd = statistics.stdev(all_d) if N > 1 else 0.0; ose = osd / math.sqrt(N) if N else 0.0
    olo, ohi = om - 1.96 * ose, om + 1.96 * ose
    overall = {"record": "overall", "evals": N, "mean_delta": round(om, 3),
               "delta_ci95": [round(olo, 3), round(ohi, 3)], "verdict": verdict_of(om, olo, ohi, N)}
    return rows, summaries, overall


frows, fsum, foverall = summarize(frac)      # PRIMARY: fraction-met
_, bsum, boverall = summarize(binr)           # SECONDARY: binary pass

bmap = {s["skill"]: s for s in bsum}
with open(os.path.join(BASE, "results.jsonl"), "w", encoding="utf-8") as fh:
    for r in frows:
        fh.write(json.dumps(r) + "\n")
    for s in fsum:
        s2 = dict(s); s2["metric"] = "fraction_met"; fh.write(json.dumps(s2) + "\n")
    for s in bsum:
        s2 = dict(s); s2["metric"] = "binary_pass"; fh.write(json.dumps(s2) + "\n")
    fh.write(json.dumps({**foverall, "metric": "fraction_met"}) + "\n")
    fh.write(json.dumps({**boverall, "metric": "binary_pass"}) + "\n")

print("=== PRIMARY: fraction-met (met/total), ADR 0025 ===")
for s in fsum:
    print(f"\n=== {s['skill']} ===")
    for r in [r for r in frows if r["skill"] == s["skill"]]:
        print(f"  eval {r['eval_id']:>2}: with={r['with']:.2f} without={r['without']:.2f} delta={r['delta']:+.2f} [{r['class']}]")
    b = bmap[s["skill"]]
    print(f"  frac  mean {s['mean_delta']:+.3f} CI [{s['delta_ci95'][0]:+.3f},{s['delta_ci95'][1]:+.3f}] -> {s['verdict']}")
    print(f"  (binary secondary: mean {b['mean_delta']:+.3f} CI [{b['delta_ci95'][0]:+.3f},{b['delta_ci95'][1]:+.3f}] -> {b['verdict']})")
print(f"\n=== OVERALL (fraction-met) === mean {foverall['mean_delta']:+.3f} "
      f"CI [{foverall['delta_ci95'][0]:+.3f},{foverall['delta_ci95'][1]:+.3f}] -> {foverall['verdict']}")
print(f"=== OVERALL (binary, secondary) === mean {boverall['mean_delta']:+.3f} "
      f"CI [{boverall['delta_ci95'][0]:+.3f},{boverall['delta_ci95'][1]:+.3f}] -> {boverall['verdict']}")
