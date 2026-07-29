#!/usr/bin/env python3
"""Aggregate graded cells -> results.json + a readable report.

Answers the three questions the run was commissioned for, in this order:
  1. QUALITY per model  — what each lane scores, bare and treated.
  2. EFFECT of the skill — per model, and averaged across models, each with the smallest effect
                           that comparison could actually have detected (mde80).
  3. CONSISTENCY        — run-to-run spread per cell, which is a deliverable here, not noise.

Plus the two things that decide whether any of it is believable: whether the two judges agree,
and whether the effect is just verbosity.
"""
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import assaystats as S  # noqa: E402

_CRIT_DOC = json.loads((HERE / "criteria.json").read_text(encoding="utf-8"))
CRITERIA = _CRIT_DOC["criteria"]
SUBSETS = {k: v for k, v in _CRIT_DOC.get("subsets", {}).items() if isinstance(v, list)}
PRACTICAL = json.loads((HERE / "metadata.json").read_text(encoding="utf-8")).get(
    "practical_bar", 0.0)


def subset_effects(rows):
    """Effect on each pre-registered criterion subset.

    The load-bearing comparison: an effect present in the FULL set but absent in the
    content_bearing subset is verbosity or formatting transfer, not better feedback. Reported
    because the headline number alone cannot tell those apart.
    """
    out = {}
    for name, ids in SUBSETS.items():
        scored = [dict(r, score=sum(r["met"][i] for i in ids if i in r["met"]) /
                       max(1, len([i for i in ids if i in r["met"]]))) for r in rows]
        cells = S.cell_table(scored, "score")
        eff = S.arm_main_effect(cells)
        eff["verdict"] = S.verdict(eff, PRACTICAL)
        eff["n_criteria"] = len(ids)
        eff["mean_bare"] = round(statistics.mean(
            [r["score"] for r in scored if r["arm"] == "bare"]), 4)
        eff["mean_wp"] = round(statistics.mean(
            [r["score"] for r in scored if r["arm"] == "wp"]), 4)
        out[name] = eff
    return out


def marker_effects(rows):
    """Judge-independent rival-explanation counters, per arm."""
    if not rows or "markers" not in rows[0]:
        return {}
    out = {}
    for key in ("treatment_markers_distinct", "treatment_markers_per_1k",
                "plan_anchors_distinct", "plan_anchors_per_1k", "findings", "chars"):
        vals = [dict(r, m=r["markers"].get(key) or 0) for r in rows]
        cells = S.cell_table(vals, "m")
        out[key] = {
            "bare": round(statistics.mean([v["m"] for v in vals if v["arm"] == "bare"]), 3),
            "wp": round(statistics.mean([v["m"] for v in vals if v["arm"] == "wp"]), 3),
            "effect": S.arm_main_effect(cells),
        }
    return out


def score_length_correlation(rows):
    """Pre-registered check: if score tracks length above r=0.5, the arm delta is reported
    length-restricted and labeled descriptive (metadata.json:length_confound_rule)."""
    xs = [r["response_chars"] for r in rows]
    ys = [r["score"] for r in rows]
    if len(xs) < 3 or len(set(xs)) < 2 or len(set(ys)) < 2:
        return None
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    return round(num / den, 3) if den else None


def load(judge):
    p = HERE / "graded" / f"cells-{judge}.jsonl"
    if not p.exists():
        return []
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l]
    for r in rows:
        r["met"] = {int(k): v for k, v in r["met"].items()}
    return rows


def per_criterion(rows):
    """Which criteria carry the effect — the mechanism check. A delta concentrated in one or two
    criteria is a specific, citable claim; a delta smeared across all of them usually is not."""
    out = {}
    for c in CRITERIA:
        i = c["id"]
        by_arm = {}
        for arm in ("bare", "wp"):
            vals = [r["met"][i] for r in rows if r["arm"] == arm]
            by_arm[arm] = round(sum(vals) / len(vals), 3) if vals else None
        if by_arm["bare"] is not None and by_arm["wp"] is not None:
            out[i] = {"axis": c["axis"], "bare": by_arm["bare"], "wp": by_arm["wp"],
                      "delta": round(by_arm["wp"] - by_arm["bare"], 3)}
    return out


def judge_agreement(a, b):
    ma = {(r["cell"], k): v for r in a for k, v in r["met"].items()}
    mb = {(r["cell"], k): v for r in b for k, v in r["met"].items()}
    common = set(ma) & set(mb)
    if not common:
        return {"n": 0}
    agree = sum(1 for k in common if ma[k] == mb[k])
    return {"n_criterion_cells": len(common), "agreement": round(agree / len(common), 3),
            "judge_a_stricter": sum(1 for k in common if mb[k] and not ma[k]),
            "judge_b_stricter": sum(1 for k in common if ma[k] and not mb[k])}


def analyse(rows, label):
    cells = S.cell_table(rows, "score")
    chars = S.cell_table(rows, "response_chars")
    s_p, df_w = S.pooled_within(cells)
    per_model = S.per_model_effects(cells)
    main = S.arm_main_effect(cells)
    for v in per_model.values():
        v["verdict"] = S.verdict(v, PRACTICAL)
    main["verdict"] = S.verdict(main, PRACTICAL)
    return {
        "judge": label,
        "n_cells": len(rows),
        "pooled_within_sd": None if s_p != s_p else round(s_p, 4),
        "pooled_df": df_w,
        "consistency": S.consistency(cells),
        "per_model_effect": per_model,
        "arm_main_effect": main,
        "model_x_arm_interaction": S.interaction(cells),
        "model_main_effect": S.model_main_effect(cells),
        "verbosity": {"cells": S.consistency(chars),
                      "arm_main_effect_chars": S.arm_main_effect(chars)},
        "subset_effects": subset_effects(rows),
        "marker_effects": marker_effects(rows),
        "score_length_r": score_length_correlation(rows),
        "per_criterion": per_criterion(rows),
        "answering_models": dict(sorted(
            {m: sum(1 for r in rows if r.get("answering_model") == m)
             for m in {r.get("answering_model") for r in rows}}.items(), key=lambda kv: -kv[1])),
    }


def fmt(v):
    return "n/a" if v is None else f"{v:+.3f}"


def report(res):
    L = []
    j = res["judge"]
    L.append(f"\n{'=' * 78}\nJUDGE: {j}   cells={res['n_cells']}   "
             f"pooled within-cell SD={res['pooled_within_sd']} on df={res['pooled_df']}\n{'=' * 78}")

    L.append("\n-- QUALITY AND CONSISTENCY BY MODEL (fraction of criteria met, 3 runs each) --")
    L.append(f"{'model':<10} {'arm':<5} {'mean':>7} {'sd':>7} {'range':>7}  runs")
    for k, c in res["consistency"].items():
        lane, arm = k.rsplit("-", 1)
        L.append(f"{lane:<10} {arm:<5} {c['mean']:>7.3f} {c['sd']:>7.3f} {c['range']:>7.3f}  "
                 + ", ".join(f"{v:.3f}" for v in c["values"]))

    L.append("\n-- EFFECT OF THE SKILL, PER MODEL (pooled error term, df=%d) --" % res["pooled_df"])
    L.append(f"{'model':<10} {'bare':>7} {'wp':>7} {'delta':>8} {'95% interval':>20} "
             f"{'mde80':>7}  verdict")
    for lane, e in res["per_model_effect"].items():
        ci = (f"[{e['ci95'][0]:+.3f}, {e['ci95'][1]:+.3f}]"
              if e["ci95"][0] is not None else "[undefined]")
        L.append(f"{lane:<10} {e['mean_control']:>7.3f} {e['mean_treatment']:>7.3f} "
                 f"{e['delta']:>+8.3f} {ci:>20} "
                 f"{(e['mde80'] if e['mde80'] is not None else float('nan')):>7.3f}  "
                 f"{e['verdict']['verdict']}")

    m = res["arm_main_effect"]
    L.append(f"\n-- SKILL EFFECT AVERAGED ACROSS ALL 5 MODELS (best-powered comparison) --")
    if m.get("ci95", [None])[0] is not None:
        L.append(f"   delta {m['delta']:+.4f}   95% interval [{m['ci95'][0]:+.4f}, "
                 f"{m['ci95'][1]:+.4f}]   mde80 {m['mde80']:.4f}   p={m['p']}")
    L.append(f"   VERDICT: {m['verdict']['verdict']} — {m['verdict']['why']}")

    i = res["model_x_arm_interaction"]
    L.append(f"\n-- DOES THE EFFECT DIFFER BY MODEL? (model x arm interaction) --")
    if "F" in i:
        L.append(f"   F({i['df1']},{i['df2']}) = {i['F']}   p = {i['p']}   "
                 f"spread of per-model effects = {i['delta_spread']:+.3f}")
        L.append("   " + ("The per-model differences exceed what noise alone produces."
                          if i["p"] < 0.05 else
                          "The per-model differences are within noise — this data does NOT "
                          "support ranking the models against each other."))
    else:
        L.append("   " + i.get("note", "not estimable"))

    mm = res["model_main_effect"]
    L.append(f"\n-- DO THE MODELS DIFFER IN FEEDBACK QUALITY OVERALL? --")
    if "F" in mm:
        L.append(f"   F({mm['df1']},{mm['df2']}) = {mm['F']}   p = {mm['p']}")
        L.append("   means: " + "  ".join(f"{k}={v:.3f}" for k, v in mm["lane_means"].items()))

    L.append(f"\n-- IS THE EFFECT QUALITY, OR STRUCTURE AND VOCABULARY? (pre-registered subsets) --")
    L.append(f"{'subset':<16} {'k':>3} {'bare':>7} {'wp':>7} {'delta':>8} {'mde80':>7}  verdict")
    for name, e in res.get("subset_effects", {}).items():
        mde = e["mde80"] if e.get("mde80") is not None else float("nan")
        L.append(f"{name:<16} {e['n_criteria']:>3} {e['mean_bare']:>7.3f} {e['mean_wp']:>7.3f} "
                 f"{e['delta']:>+8.3f} {mde:>7.3f}  {e['verdict']['verdict']}")
    L.append("   Read: an effect in the full set but NOT in content_bearing is verbosity or")
    L.append("   formatting transfer, not better feedback.")

    vb = res["verbosity"]["arm_main_effect_chars"]
    L.append(f"\n-- RIVAL EXPLANATION: IS IT JUST LENGTH OR VOCABULARY? --")
    if vb.get("ci95", [None])[0] is not None:
        L.append(f"   treatment changes response length by {vb['delta']:+.0f} chars "
                 f"[{vb['ci95'][0]:+.0f}, {vb['ci95'][1]:+.0f}], p={vb['p']}")
    r = res.get("score_length_r")
    if r is not None:
        L.append(f"   correlation(score, length) across all cells = {r}"
                 + ("   ABOVE the pre-registered 0.5 bar — length is a live confound"
                    if abs(r) > 0.5 else "   below the pre-registered 0.5 bar"))
    me = res.get("marker_effects", {})
    if me:
        L.append(f"   {'counter':<28} {'bare':>9} {'wp':>9} {'delta':>9}")
        for k, v in me.items():
            L.append(f"   {k:<28} {v['bare']:>9.2f} {v['wp']:>9.2f} "
                     f"{v['effect'].get('delta', float('nan')):>+9.2f}")

    L.append(f"\n-- WHICH CRITERIA CARRY THE EFFECT --")
    ranked = sorted(res["per_criterion"].items(), key=lambda kv: -abs(kv[1]["delta"]))
    for cid, c in ranked[:8]:
        L.append(f"   C{cid:<3} {c['axis']:<14} bare {c['bare']:.2f} -> wp {c['wp']:.2f}   "
                 f"{c['delta']:+.2f}")

    if res["answering_models"]:
        L.append(f"\n-- ANSWERING MODELS (copilot lane routes per call) --")
        for k, v in res["answering_models"].items():
            L.append(f"   {k}: {v} cells")
    return "\n".join(L)


def main():
    out, texts = {}, []
    loaded = {}
    for j in ("grok", "claude"):
        rows = load(j)
        if rows:
            loaded[j] = rows
            out[j] = analyse(rows, j)
            texts.append(report(out[j]))
    if not loaded:
        sys.exit("no graded cells found — run grade.py first")
    if len(loaded) == 2:
        a, b = loaded["grok"], loaded["claude"]
        out["cross_judge"] = judge_agreement(a, b)
        va = out["grok"]["arm_main_effect"]["verdict"]["verdict"]
        vb = out["claude"]["arm_main_effect"]["verdict"]["verdict"]
        out["cross_judge"]["main_effect_verdict"] = {"grok": va, "claude": vb, "flipped": va != vb}
        texts.append(f"\n{'=' * 78}\nCROSS-JUDGE\n{'=' * 78}\n"
                     f"   agreement {out['cross_judge']['agreement']} over "
                     f"{out['cross_judge']['n_criterion_cells']} criterion-cells\n"
                     f"   main-effect verdict: grok={va}  claude={vb}  "
                     f"{'FLIPPED — exploratory only' if va != vb else 'judge-robust'}")
    (HERE / "results.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    text = "\n".join(texts)
    (HERE / "results.txt").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
