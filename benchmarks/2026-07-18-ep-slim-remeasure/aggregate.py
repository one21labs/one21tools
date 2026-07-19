#!/usr/bin/env python3
"""ep-slim-remeasure 3-arm ship read (issue #248).

Sonnet (headline) lane: graded/verdicts.jsonl + graded/prosecute_counts.jsonl,
met_final = min(grader_met, prosecutor_met) per cell (ADR 0025).
Grok lane (ship gate co-judge, if graded/grok_verdicts.jsonl exists): met/total as graded.

Per eval (one clustered observation, ADR 0019): mean frac per arm over reps, then
  d_full      = with-full - without
  d_slim      = with-slim - without
  contrast_sf = with-slim - with-full
Headline = eval-clustered mean + 95% CI (n = evals, not cells).

Pre-registered ship rule (metadata.json, committed before generation) — computed per judge:
  slim_loses            : contrast_sf CI excludes 0 AND mean(contrast_sf) < 0
  slim_retains          : contrast_sf CI contains 0 AND mean(d_slim) > 0
  slim_beats            : contrast_sf CI excludes 0 AND mean(contrast_sf) > 0
  slim_effect_confirmed : d_slim CI excludes 0
  ship_this_judge       : NOT slim_loses AND mean(d_slim) > 0
SHIP (final) = ship_this_judge under BOTH judges. The cost prong is satisfied by construction
(chars_delta_slim_minus_full < 0, asserted here from treatments/costs.json).

Writes results.jsonl (record types: eval, verdict, cost) + graded/grok_summary.json (grok lane).
"""
import csv, json, math, os, statistics

BASE = os.path.dirname(os.path.abspath(__file__))
G = os.path.join(BASE, "graded")
ARMS = ("without", "with-full", "with-slim")


def read_jsonl(path):
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                r = json.loads(line)
                out[r["bid"]] = r
    return out


with open(os.path.join(G, "arm_map.tsv"), encoding="utf-8") as fh:
    arm_map = {r["bid"]: r for r in csv.DictReader(fh, delimiter="\t")}


def fracs_sonnet():
    verdicts = read_jsonl(os.path.join(G, "verdicts.jsonl"))
    counts = read_jsonl(os.path.join(G, "prosecute_counts.jsonl"))
    frac = {}
    for bid, m in arm_map.items():
        v, c = verdicts.get(bid), counts.get(bid)
        if v is None or c is None:
            print(f"WARNING: bid {bid} missing {'verdict' if v is None else 'prosecutor count'} — skipped")
            continue
        tot = v.get("total") or 0
        met = min(v.get("met") or 0, c.get("met") or 0)
        frac.setdefault((m["eval_id"], m["arm"]), []).append((met / tot) if tot else 0.0)
    return frac


def fracs_grok():
    path = os.path.join(G, "grok_verdicts.jsonl")
    if not os.path.exists(path):
        return None
    verdicts = read_jsonl(path)
    frac = {}
    for bid, m in arm_map.items():
        v = verdicts.get(bid)
        if v is None or v.get("met") is None or not v.get("total"):
            print(f"WARNING: grok lane missing/null bid {bid} — skipped")
            continue
        frac.setdefault((m["eval_id"], m["arm"]), []).append(v["met"] / v["total"])
    return frac


def ci95(vals):
    n = len(vals)
    mean = statistics.fmean(vals) if n else 0.0
    sd = statistics.stdev(vals) if n > 1 else 0.0
    se = sd / math.sqrt(n) if n else 0.0
    return mean, mean - 1.96 * se, mean + 1.96 * se


def excludes_zero(ci):
    return ci[0] > 0 or ci[1] < 0


def analyze(frac, judge):
    evals = sorted({e for (e, _) in frac}, key=int)
    rows, series = [], {k: [] for k in ("d_full", "d_slim", "contrast_sf")}
    for e in evals:
        am = {a: (statistics.fmean(frac[(e, a)]) if frac.get((e, a)) else float("nan")) for a in ARMS}
        d_full = am["with-full"] - am["without"]
        d_slim = am["with-slim"] - am["without"]
        c_sf = am["with-slim"] - am["with-full"]
        series["d_full"].append(d_full); series["d_slim"].append(d_slim)
        series["contrast_sf"].append(c_sf)
        rows.append({"record": "eval", "judge": judge, "eval_id": e,
                     "without": round(am["without"], 3), "with_full": round(am["with-full"], 3),
                     "with_slim": round(am["with-slim"], 3), "d_full": round(d_full, 3),
                     "d_slim": round(d_slim, 3), "contrast_sf": round(c_sf, 3)})
    summary = {}
    for name, vals in series.items():
        mean, lo, hi = ci95(vals)
        summary[name] = {"mean": round(mean, 3), "ci95": [round(lo, 3), round(hi, 3)]}
    ci_sf, m_sf = summary["contrast_sf"]["ci95"], summary["contrast_sf"]["mean"]
    ci_ds, m_ds = summary["d_slim"]["ci95"], summary["d_slim"]["mean"]
    reads = {
        "slim_loses": {"value": excludes_zero(ci_sf) and m_sf < 0,
                       "evidence": f"contrast_sf CI [{ci_sf[0]:+.3f},{ci_sf[1]:+.3f}] "
                                   f"{'excludes' if excludes_zero(ci_sf) else 'contains'} 0, mean {m_sf:+.3f}"},
        "slim_retains": {"value": (not excludes_zero(ci_sf)) and m_ds > 0,
                         "evidence": f"contrast_sf CI [{ci_sf[0]:+.3f},{ci_sf[1]:+.3f}] "
                                     f"{'contains' if not excludes_zero(ci_sf) else 'excludes'} 0; "
                                     f"d_slim mean {m_ds:+.3f}"},
        "slim_beats": {"value": excludes_zero(ci_sf) and m_sf > 0,
                       "evidence": f"contrast_sf CI [{ci_sf[0]:+.3f},{ci_sf[1]:+.3f}] "
                                   f"{'excludes' if excludes_zero(ci_sf) else 'contains'} 0, mean {m_sf:+.3f}"},
        "slim_effect_confirmed": {"value": excludes_zero(ci_ds),
                                  "evidence": f"d_slim CI [{ci_ds[0]:+.3f},{ci_ds[1]:+.3f}] "
                                              f"{'excludes' if excludes_zero(ci_ds) else 'contains'} 0"},
    }
    ship = (not reads["slim_loses"]["value"]) and m_ds > 0
    return evals, rows, summary, reads, ship


with open(os.path.join(BASE, "treatments", "costs.json"), encoding="utf-8") as fh:
    costs = json.load(fh)
assert costs["chars_delta_slim_minus_full"] < 0, "cost prong: slim must be a net char cut"

lanes = {"sonnet": fracs_sonnet()}
gf = fracs_grok()
if gf is not None:
    lanes["grok"] = gf

all_rows, judges = [], {}
for judge, frac in lanes.items():
    evals, rows, summary, reads, ship = analyze(frac, judge)
    judges[judge] = {"evals": len(evals), **summary,
                     "reads": {k: v for k, v in reads.items()}, "ship_this_judge": ship}
    all_rows += rows
    print(f"=== {judge}: fraction-met"
          + (" (met_final = min(grader, prosecutor))" if judge == "sonnet" else "") + " ===")
    for r in rows:
        print(f"  eval {r['eval_id']:>2}: without={r['without']:.2f} full={r['with_full']:.2f} "
              f"slim={r['with_slim']:.2f}  d_full={r['d_full']:+.2f} d_slim={r['d_slim']:+.2f} "
              f"sf={r['contrast_sf']:+.2f}")
    for name in ("d_full", "d_slim", "contrast_sf"):
        s = summary[name]
        print(f"  {name}: mean {s['mean']:+.3f} CI [{s['ci95'][0]:+.3f},{s['ci95'][1]:+.3f}]")
    for k, v in reads.items():
        print(f"  {k}: {v['value']}  ({v['evidence']})")
    print(f"  ship_this_judge: {ship}\n")

ship_final = all(j["ship_this_judge"] for j in judges.values()) and "grok" in judges
verdict = {"record": "verdict", "judges": judges, "ship_final": ship_final,
           "rule": "SHIP iff (NOT slim_loses AND mean(d_slim) > 0) under BOTH judges (sonnet "
                   "headline + grok lane); cost prong chars_delta < 0 asserted from costs.json. "
                   "Pre-registered in metadata.json before generation.",
           "n_note": "n=6 evals; CIs are directional confidence signals per ADR 0027-style bar"}
print(f"=== SHIP (final, both judges): {ship_final} ===")

with open(os.path.join(BASE, "results.jsonl"), "w", encoding="utf-8", newline="") as fh:
    for r in all_rows:
        if r["judge"] == "sonnet":
            fh.write(json.dumps(r) + "\n")
    fh.write(json.dumps(verdict) + "\n")
    fh.write(json.dumps({"record": "cost", **costs}) + "\n")
if "grok" in judges:
    with open(os.path.join(G, "grok_summary.json"), "w", encoding="utf-8", newline="") as fh:
        json.dump({"judge": "grok",
                   "rows": [r for r in all_rows if r["judge"] == "grok"],
                   "summary": judges["grok"]}, fh, indent=1)
