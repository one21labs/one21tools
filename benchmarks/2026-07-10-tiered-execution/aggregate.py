#!/usr/bin/env python3
"""Verdict for the tiered-execution benchmark (issue #41; pre-registered decision rule).

Quality per (task, arm): fraction-met (met/total, prosecutor applied; ADR 0025 powered
headline) and binary all-met pass (the pre-registration's stated metric — reported first,
with the floor caveat if it floors). Arm deltas are clustered per task (each task = one
observation, mean over its reps; ADR 0019): mean delta + 95% CI over the tasks.

Cost per (task, arm, rep): total tokens = input + cache_creation + cache_read + output summed
across ALL calls in the configuration (solo = 1 call; tiered = plan + every implement +
every validate — the tiering tax counts), plus USD cost (CLI-reported) and wall-clock
(duration_ms summed; tiered calls are sequential so the sum IS the chain's wall-clock).

Pre-registered rule: ADOPT tiered iff pass-rate delta (tiered - sonnet) >= -0.05 (CI-checked:
non-inferiority holds when the clustered 95% CI lower bound >= -0.05) AND median tokens
<= 0.7x sonnet-solo (or wall-clock <= 0.7x). Also reports tiered vs opus (quality) + cost
ratio (the "Opus quality at sub-Opus cost" prize) and validator false-accept/false-reject
vs the blind grader. Writes results.jsonl (append-only snapshot rows).
"""
import csv, json, math, os, statistics, glob

BASE = os.path.dirname(os.path.abspath(__file__))
G = os.path.join(BASE, "graded")
with open(os.path.join(G, "verdicts.jsonl"), encoding="utf-8") as fh:
    verdicts = {v["bid"]: v for v in (json.loads(l) for l in fh if l.strip())}
with open(os.path.join(G, "arm_map.csv"), encoding="utf-8", newline="") as fh:
    arm_map = {r["bid"]: r for r in csv.DictReader(fh)}
ARMS = ["haiku", "sonnet", "opus", "tiered"]
NONINF_MARGIN, TOKEN_RATIO = -0.05, 0.7

# ---- quality: per (key, arm) lists over reps ----
frac, binr = {}, {}
for bid, m in arm_map.items():
    v = verdicts.get(bid)
    if v is None:
        continue
    tot = v.get("total") or 0
    frac.setdefault((m["key"], m["arm"]), []).append(((v.get("met") or 0) / tot) if tot else 0.0)
    binr.setdefault((m["key"], m["arm"]), []).append(1 if v.get("pass") else 0)
keys = sorted({k for (k, _) in frac})

# ---- cost: per (key, arm) lists of (tokens, usd, ms) over reps ----
def tok(u):
    return sum(u.get(f) or 0 for f in
               ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"))

cost = {}
for f in glob.glob(os.path.join(BASE, "outputs", "*.json")):
    name = os.path.basename(f)[:-5]
    if name.endswith(".trace"):
        with open(f, encoding="utf-8") as fh:
            t = json.load(fh)
        key, arm = t["key"], "tiered"
        tokens = sum(tok(c["usage"] or {}) for c in t["calls"])
        usd, ms = t["total_cost_usd"], t["total_duration_ms"]
    else:
        parts = name.split(".")
        if len(parts) != 4:
            continue
        key, arm = ".".join(parts[:2]), parts[2]
        with open(f, encoding="utf-8") as fh:
            d = json.load(fh)
        tokens, usd, ms = tok(d.get("usage") or {}), d.get("total_cost_usd") or 0, d.get("duration_ms") or 0
    if key in keys:
        cost.setdefault((key, arm), []).append((tokens, usd, ms))


def delta_ci(cellmap, a, b):
    """Clustered per-task delta a-b: mean + 95% CI over tasks (ADR 0019)."""
    ds = []
    for k in keys:
        va, vb = cellmap.get((k, a)), cellmap.get((k, b))
        if va and vb:
            ds.append(statistics.fmean(va) - statistics.fmean(vb))
    n = len(ds); mean = statistics.fmean(ds) if ds else 0.0
    sd = statistics.stdev(ds) if n > 1 else 0.0; se = sd / math.sqrt(n) if n else 0.0
    return {"n": n, "mean": round(mean, 3), "ci95": [round(mean - 1.96 * se, 3), round(mean + 1.96 * se, 3)]}


rows = []
print("=== per-arm quality (mean over tasks of per-task rep-mean) + median cost per cell ===")
for arm in ARMS:
    fm = [statistics.fmean(frac[(k, arm)]) for k in keys if (k, arm) in frac]
    bm = [statistics.fmean(binr[(k, arm)]) for k in keys if (k, arm) in binr]
    cs = [c for k in keys for c in cost.get((k, arm), [])]
    med = lambda i: statistics.median(c[i] for c in cs) if cs else 0
    row = {"record": "arm", "arm": arm, "tasks": len(fm),
           "frac_met": round(statistics.fmean(fm), 3) if fm else None,
           "pass_rate": round(statistics.fmean(bm), 3) if bm else None,
           "med_tokens": int(med(0)), "med_usd": round(med(1), 4), "med_wall_s": round(med(2) / 1000, 1)}
    rows.append(row)
    print(f"  {arm:>7}: frac={row['frac_met']} pass={row['pass_rate']} "
          f"med_tokens={row['med_tokens']} med_usd=${row['med_usd']} med_wall={row['med_wall_s']}s")

print("\n=== clustered deltas (95% CI over tasks) ===")
for a, b in [("tiered", "sonnet"), ("tiered", "opus"), ("tiered", "haiku"),
             ("opus", "sonnet"), ("sonnet", "haiku")]:
    df, db = delta_ci(frac, a, b), delta_ci(binr, a, b)
    rows.append({"record": "delta", "arms": f"{a}-{b}", "frac_met": df, "binary_pass": db})
    print(f"  {a}-{b}: frac {df['mean']:+.3f} CI [{df['ci95'][0]:+.3f},{df['ci95'][1]:+.3f}] | "
          f"pass {db['mean']:+.3f} CI [{db['ci95'][0]:+.3f},{db['ci95'][1]:+.3f}] (n={df['n']})")

# ---- pre-registered decision rule ----
d_bin, d_frac = delta_ci(binr, "tiered", "sonnet"), delta_ci(frac, "tiered", "sonnet")
med_of = lambda arm, i: statistics.median(c[i] for k in keys for c in cost.get((k, arm), []))
tokr = med_of("tiered", 0) / med_of("sonnet", 0)
wallr = med_of("tiered", 2) / med_of("sonnet", 2)
usdr = med_of("tiered", 1) / med_of("sonnet", 1)
noninf_bin = d_bin["ci95"][0] >= NONINF_MARGIN
noninf_frac = d_frac["ci95"][0] >= NONINF_MARGIN
cheaper = tokr <= TOKEN_RATIO or wallr <= TOKEN_RATIO
adopt = noninf_bin and cheaper
decision = {"record": "decision", "noninferior_pass_ci": noninf_bin, "noninferior_frac_ci": noninf_frac,
            "token_ratio_vs_sonnet": round(tokr, 3), "wall_ratio_vs_sonnet": round(wallr, 3),
            "usd_ratio_vs_sonnet": round(usdr, 3), "adopt_tiered": adopt}
rows.append(decision)
print(f"\n=== decision rule (pre-registered) ===\n  non-inferior (pass CI-LB >= {NONINF_MARGIN}): {noninf_bin}"
      f" | (frac CI-LB): {noninf_frac}\n  tokens ratio {tokr:.2f} | wall ratio {wallr:.2f} | usd ratio {usdr:.2f}"
      f" (need <= {TOKEN_RATIO})\n  ADOPT TIERED: {adopt}")

# ---- validator fidelity (tiered traces vs blind grader) ----
fa = fr = agree = 0
grader_pass = {(m["key"], m["rep"]): bool(verdicts.get(bid, {}).get("pass"))
               for bid, m in arm_map.items() if m["arm"] == "tiered" and bid in verdicts}
for f in glob.glob(os.path.join(BASE, "outputs", "*.trace.json")):
    with open(f, encoding="utf-8") as fh:
        t = json.load(fh)
    gp = grader_pass.get((t["key"], str(t["rep"])))
    if gp is None:
        continue
    ip = t["internal_pass"]
    if ip and not gp: fa += 1
    elif not ip and gp: fr += 1
    else: agree += 1
fid = {"record": "validator_fidelity", "false_accept": fa, "false_reject": fr, "agree": agree}
rows.append(fid)
print(f"\n=== validator vs blind grader (final cycle) === false-accept={fa} false-reject={fr} agree={agree}")

with open(os.path.join(BASE, "results.jsonl"), "w", encoding="utf-8") as fh:
    for r in rows:
        fh.write(json.dumps(r) + "\n")
print("\nresults.jsonl written")
