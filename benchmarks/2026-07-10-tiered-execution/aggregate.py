#!/usr/bin/env python3
"""ADOPTION verdict for the tiered-agent execution benchmark (issue #41; ADR 0019/0024/0025).

Inputs (graded/): verdicts.jsonl (grader + prosecutor-on-PASS per cell), prosecute_counts.jsonl
(uniform adversarial re-count on EVERY cell, ADR 0025), arm_map.tsv (bid -> key/skill/eval_id/arm/
rep). met_final = min(grader_met, prosecutor_met) per cell (ADR 0025 safeguard). Per eval (one
clustered observation, ADR 0019): mean fraction-met per arm over reps; per-arm-pair delta = arm
mean minus sonnet-solo mean. Headline pair: tiered vs sonnet-solo (the ADOPTION gate); haiku-solo
vs sonnet-solo is reported for context (the cost/quality floor), not gating.

Cost/time come from the three <arm>.summary.json files that harness.py's claude -p driver writes
per arm (real per-cell envelope totals, not an estimate) -- see README "Reproduce": harness.py
writes them under its --outdir (~/tiered-run by default, inside WSL); the operator copies the
three files into this benchmark directory before running aggregate.py. Per-arm AGGREGATES, not
per-cell; left null rather than fabricated if a summary file is missing.

Adoption bar -- PRE-REGISTERED in metadata.json BEFORE any run (ADR-0027-style directional bar,
not CI-exclusion: at n=24 clustered evals a subtle non-inferiority margin is not reliably provable
by CI-exclusion, matching ADR 0027's rationale for the EP re-measure merge bar):
  mean_delta(tiered - sonnet-solo) > -0.05         (non-inferior on fraction-met, point estimate)
  AND (tokens_tiered <= 0.6 * tokens_sonnet-solo OR time_tiered <= 0.6 * time_sonnet-solo)
The eval-clustered 95% CI on the delta is reported as a secondary confidence signal (strong if its
lower bound also clears -0.05, weak otherwise) -- never a gate. Writes results.jsonl.
"""
import csv, json, math, os, statistics

BASE = os.path.dirname(os.path.abspath(__file__))
G = os.path.join(BASE, "graded")
ARMS = ("sonnet-solo", "haiku-solo", "tiered")
BASELINE = "sonnet-solo"
MARGIN = -0.05
COST_RATIO_BAR = 0.6


def read_jsonl(path):
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                r = json.loads(line)
                out[r["bid"]] = r
    return out


def colname(arm):
    return arm.replace("-", "_")


verdicts = read_jsonl(os.path.join(G, "verdicts.jsonl"))
counts = read_jsonl(os.path.join(G, "prosecute_counts.jsonl"))
with open(os.path.join(G, "arm_map.tsv"), encoding="utf-8") as fh:
    arm_map = {r["bid"]: r for r in csv.DictReader(fh, delimiter="\t")}

frac = {}   # (eval_key, arm) -> [met_final/total per rep]
for bid, m in arm_map.items():
    v, c = verdicts.get(bid), counts.get(bid)
    if v is None or c is None:
        print(f"WARNING: bid {bid} missing {'verdict' if v is None else 'prosecutor count'} -- skipped")
        continue
    tot = v.get("total") or 0
    met = min(v.get("met") or 0, c.get("met") or 0)
    frac.setdefault((m["key"], m["arm"]), []).append((met / tot) if tot else 0.0)


def ci95(vals):
    n = len(vals)
    mean = statistics.fmean(vals) if n else 0.0
    sd = statistics.stdev(vals) if n > 1 else 0.0
    se = sd / math.sqrt(n) if n else 0.0
    return mean, mean - 1.96 * se, mean + 1.96 * se


evals = sorted({e for (e, _) in frac})
rows = []
pair_deltas = {a: [] for a in ARMS if a != BASELINE}
for e in evals:
    arm_mean = {a: (statistics.fmean(frac[(e, a)]) if frac.get((e, a)) else float("nan")) for a in ARMS}
    row = {"record": "eval", "eval_key": e}
    for a in ARMS:
        row[colname(a)] = round(arm_mean[a], 3)
    for a in ARMS:
        if a == BASELINE:
            continue
        d = arm_mean[a] - arm_mean[BASELINE]
        row[f"delta_{colname(a)}_vs_{colname(BASELINE)}"] = round(d, 3)
        pair_deltas[a].append(d)
    rows.append(row)

summary = {}
for a, deltas in pair_deltas.items():
    mean, lo, hi = ci95(deltas)
    summary[a] = {"mean_delta": round(mean, 3), "ci95": [round(lo, 3), round(hi, 3)], "evals": len(deltas)}

arm_summaries = {}
for a in ARMS:
    path = os.path.join(BASE, f"{a}.summary.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            arm_summaries[a] = json.load(fh)


def total_tokens(s):
    if not s:
        return None
    tin, tout = s.get("total_tokens_in"), s.get("total_tokens_out")
    if not isinstance(tin, (int, float)) or not isinstance(tout, (int, float)):
        return None
    return tin + tout


tiered = summary.get("tiered", {"mean_delta": None, "ci95": None})
quality_ok = tiered["mean_delta"] is not None and tiered["mean_delta"] > MARGIN

sonnet_tok = total_tokens(arm_summaries.get(BASELINE))
tiered_tok = total_tokens(arm_summaries.get("tiered"))
sonnet_time = (arm_summaries.get(BASELINE) or {}).get("wall_clock_s")
tiered_time = (arm_summaries.get("tiered") or {}).get("wall_clock_s")
sonnet_cost = (arm_summaries.get(BASELINE) or {}).get("total_cost_usd")
tiered_cost = (arm_summaries.get("tiered") or {}).get("total_cost_usd")

tok_ratio = time_ratio = cost_ratio = None
cost_ok = False
if isinstance(sonnet_tok, (int, float)) and sonnet_tok and isinstance(tiered_tok, (int, float)):
    tok_ratio = tiered_tok / sonnet_tok
    cost_ok = cost_ok or tok_ratio <= COST_RATIO_BAR
if isinstance(sonnet_time, (int, float)) and sonnet_time and isinstance(tiered_time, (int, float)):
    time_ratio = tiered_time / sonnet_time
    cost_ok = cost_ok or time_ratio <= COST_RATIO_BAR
if isinstance(sonnet_cost, (int, float)) and sonnet_cost and isinstance(tiered_cost, (int, float)):
    cost_ratio = tiered_cost / sonnet_cost  # reported for context only; not part of the pre-registered gate

adopt = bool(quality_ok and cost_ok)
confidence = None
if tiered.get("ci95"):
    confidence = "strong" if tiered["ci95"][0] > MARGIN else "weak"

verdict = {
    "record": "verdict", "evals": len(evals), "pairs": summary,
    "tokens_ratio_tiered_over_sonnet": round(tok_ratio, 3) if tok_ratio is not None else None,
    "time_ratio_tiered_over_sonnet": round(time_ratio, 3) if time_ratio is not None else None,
    "cost_usd_ratio_tiered_over_sonnet": round(cost_ratio, 3) if cost_ratio is not None else None,
    "quality_non_inferior": quality_ok, "cost_or_time_materially_lower": cost_ok,
    "adopt_tiered": adopt, "confidence": confidence,
    "adoption_bar": f"mean_delta(tiered-sonnet-solo) > {MARGIN} AND "
                     f"(tokens <= {COST_RATIO_BAR}x OR time <= {COST_RATIO_BAR}x sonnet-solo)",
}

with open(os.path.join(BASE, "results.jsonl"), "w", encoding="utf-8", newline="") as fh:
    for r in rows:
        fh.write(json.dumps(r) + "\n")
    fh.write(json.dumps(verdict) + "\n")

print("=== tiered-agent execution (issue #41): fraction-met, met_final=min(grader,prosecutor) ===")
for r in rows:
    print(f"  {r['eval_key']:>28}: sonnet={r.get('sonnet_solo', 0):.2f} haiku={r.get('haiku_solo', 0):.2f} "
          f"tiered={r.get('tiered', 0):.2f}  d_tiered={r.get('delta_tiered_vs_sonnet_solo', 0):+.2f} "
          f"d_haiku={r.get('delta_haiku_solo_vs_sonnet_solo', 0):+.2f}")
for a, s in summary.items():
    print(f"  {a} vs {BASELINE}: mean {s['mean_delta']:+.3f} CI [{s['ci95'][0]:+.3f},{s['ci95'][1]:+.3f}] (n={s['evals']} evals)")
print(f"  tokens ratio (tiered/sonnet-solo): {verdict['tokens_ratio_tiered_over_sonnet']}")
print(f"  time ratio (tiered/sonnet-solo): {verdict['time_ratio_tiered_over_sonnet']}")
print(f"  cost $ ratio (tiered/sonnet-solo, reported only, not gating): {verdict['cost_usd_ratio_tiered_over_sonnet']}")
print(f"\nVERDICT: {'ADOPT tiered' if adopt else 'DO NOT ADOPT tiered'} "
      f"(confidence: {confidence or 'n/a'}) -- bar: {verdict['adoption_bar']}")
