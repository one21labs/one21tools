#!/usr/bin/env python3
"""Compose the routing arm and read the verdict off the pre-registered bar (issue #109).

Routing(eval, rep) = haiku-solo(eval, rep) if the checker says SHIP, else sonnet-solo(eval, SAME
rep). Quality is the already-blind-graded frac-met of whichever half ships (met_final =
min(grader, prosecutor), ADR 0025, from the fullgrid substrate); cost is the real per-cell
envelope cost of the shipped path plus the checker call. No new grading -- see metadata.json.

Adoption bar (metadata.json:adoption_bar, pre-registered before any checker call), per variant:
  (1) mean_delta(routing - sonnet-solo) > -0.05 frac-met, eval-clustered over the 8 gradient evals
  (2) median per-cell cost ratio (routing / sonnet-solo) <= 0.6
  (3) false-accept rate over all 24 cells <= 0.15
      (false-accept: SHIP on a cell whose haiku frac_met < eval's sonnet-solo mean - 0.05)
If more than one variant clears, adopt the cheapest (lowest median cost ratio).

Reads checker records from <BASE>/checkers/ (copied back from the WSL outdir) and the mechanized
variant from the fullgrid's graded/mechanized.csv. Writes results.jsonl.
"""
import csv
import json
import math
import os
import statistics

BASE = os.path.dirname(os.path.abspath(__file__))
FULLGRID = os.path.join(BASE, "..", "2026-07-10-tiered-execution-fullgrid")
MODEL_VARIANTS = ("sonnet-judge", "haiku-judge")
VARIANTS = MODEL_VARIANTS + ("mechanized",)
MARGIN = -0.05
COST_RATIO_BAR = 0.6
FALSE_ACCEPT_BAR = 0.15
FA_MARGIN = 0.05
REPS = 3


# ---------------------------------------------------------------- decision logic (tested)

def extract_first_json_object(text):
    if not text:
        return None
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def parse_checker_verdict(text):
    """-> (ship: bool, parse_error: str|None). Fail-safe: anything unparseable ESCALATES."""
    candidate = extract_first_json_object(text or "")
    if candidate is None:
        return False, "no JSON object found in checker output"
    try:
        obj = json.loads(candidate)
    except json.JSONDecodeError as e:
        return False, f"json parse error: {e}"
    verdict = obj.get("verdict") if isinstance(obj, dict) else None
    if not isinstance(verdict, str) or verdict.strip().upper() not in ("SHIP", "ESCALATE"):
        return False, f"missing or unrecognized 'verdict' field: {verdict!r}"
    return verdict.strip().upper() == "SHIP", None


def mechanized_ship(passed_flags):
    """SHIP iff every mechanized check for the eval passed (empty -> ESCALATE, fail-safe)."""
    return bool(passed_flags) and all(passed_flags)


def is_false_accept(shipped, haiku_frac, sonnet_eval_mean, margin=FA_MARGIN):
    """A SHIP is false when shipping loses more than the non-inferiority margin vs escalating."""
    return bool(shipped) and haiku_frac < sonnet_eval_mean - margin


def variant_clears_bar(mean_delta, median_cost_ratio, false_accept_rate):
    return (mean_delta > MARGIN
            and median_cost_ratio <= COST_RATIO_BAR
            and false_accept_rate <= FALSE_ACCEPT_BAR)


def pick_adopted(clearing):
    """clearing: {variant: median_cost_ratio} -> the cheapest clearing variant, or None."""
    return min(clearing, key=clearing.get) if clearing else None


def ci95(vals):
    n = len(vals)
    mean = statistics.fmean(vals) if n else 0.0
    sd = statistics.stdev(vals) if n > 1 else 0.0
    se = sd / math.sqrt(n) if n else 0.0
    return mean, mean - 1.96 * se, mean + 1.96 * se


# ---------------------------------------------------------------- substrate loading

def read_jsonl(path):
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                r = json.loads(line)
                out[r["bid"]] = r
    return out


def load_substrate(gradient):
    """-> frac[(key, arm, rep)], cost[(key, arm, rep)], wall[(key, arm, rep)] for the 2 solo arms."""
    g = os.path.join(FULLGRID, "graded")
    verdicts = read_jsonl(os.path.join(g, "verdicts.jsonl"))
    counts = read_jsonl(os.path.join(g, "prosecute_counts.jsonl"))
    with open(os.path.join(g, "arm_map.tsv"), encoding="utf-8") as fh:
        arm_map = {r["bid"]: r for r in csv.DictReader(fh, delimiter="\t")}

    frac, cost, wall = {}, {}, {}
    for bid, m in arm_map.items():
        if m["key"] not in gradient or m["arm"] not in ("haiku-solo", "sonnet-solo"):
            continue
        v, c = verdicts.get(bid), counts.get(bid)
        if v is None or c is None:
            raise SystemExit(f"ERROR: gradient bid {bid} ({m['key']} {m['arm']} r{m['rep']}) ungraded")
        tot = v.get("total") or 0
        met = min(v.get("met") or 0, c.get("met") or 0)
        k = (m["key"], m["arm"], int(m["rep"]))
        frac[k] = (met / tot) if tot else 0.0
        cell_path = os.path.join(FULLGRID, "outputs", "cells",
                                 f"{m['arm']}.{m['key'].rsplit('.', 1)[0]}."
                                 f"{m['key'].rsplit('.', 1)[1]}.r{m['rep']}.json")
        with open(cell_path, encoding="utf-8") as fh:
            cell = json.load(fh)
        cost[k] = cell["usage"]["cost_usd"]
        wall[k] = cell["duration_ms"]["total_wall_ms"]
    return frac, cost, wall


def load_checker_decisions(gradient):
    """-> decisions[variant][(key, rep)] = {ship, parse_error, cost_usd, wall_ms}"""
    decisions = {v: {} for v in VARIANTS}

    for variant in MODEL_VARIANTS:
        for key in gradient:
            skill, eval_id = key.rsplit(".", 1)
            for rep in range(1, REPS + 1):
                path = os.path.join(BASE, "checkers", f"{variant}.{skill}.{eval_id}.r{rep}.json")
                with open(path, encoding="utf-8") as fh:
                    rec = json.load(fh)
                if rec.get("error"):
                    ship, perr = False, f"checker call error: {rec['error']}"
                else:
                    ship, perr = parse_checker_verdict(rec.get("response"))
                decisions[variant][(key, rep)] = {
                    "ship": ship, "parse_error": perr,
                    "cost_usd": rec.get("cost_usd") or 0.0,
                    "wall_ms": rec.get("duration_ms_wall") or 0.0,
                }

    flags = {}  # (key, rep) -> [passed...]
    with open(os.path.join(FULLGRID, "graded", "mechanized.csv"), encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            key = f"{r['skill']}.{r['eval_id']}"
            if key in gradient and r["arm"] == "haiku-solo":
                flags.setdefault((key, int(r["rep"])), []).append(r["passed"] == "1")
    for key in gradient:
        for rep in range(1, REPS + 1):
            decisions["mechanized"][(key, rep)] = {
                "ship": mechanized_ship(flags.get((key, rep), [])),
                "parse_error": None, "cost_usd": 0.0, "wall_ms": 0.0,
            }
    return decisions


# ---------------------------------------------------------------- main

def main():
    with open(os.path.join(BASE, "metadata.json"), encoding="utf-8") as fh:
        gradient = json.load(fh)["design"]["gradient_evals"]
    frac, cost, wall = load_substrate(set(gradient))
    decisions = load_checker_decisions(gradient)

    sonnet_eval_mean = {key: statistics.fmean(frac[(key, "sonnet-solo", r)] for r in range(1, REPS + 1))
                        for key in gradient}

    rows, verdict_rows, clearing = [], [], {}
    for variant in VARIANTS:
        cells = []
        for key in gradient:
            for rep in range(1, REPS + 1):
                d = decisions[variant][(key, rep)]
                hk, sk = (key, "haiku-solo", rep), (key, "sonnet-solo", rep)
                shipped_frac = frac[hk] if d["ship"] else frac[sk]
                cell_cost = cost[hk] + d["cost_usd"] + (0.0 if d["ship"] else cost[sk])
                cell_wall = wall[hk] + d["wall_ms"] + (0.0 if d["ship"] else wall[sk])
                cells.append({
                    "key": key, "rep": rep, "ship": d["ship"], "parse_error": d["parse_error"],
                    "frac": shipped_frac, "cost": cell_cost, "wall": cell_wall,
                    "cost_ratio": cell_cost / cost[sk],
                    "false_accept": is_false_accept(d["ship"], frac[hk], sonnet_eval_mean[key]),
                })

        deltas = []
        for key in gradient:
            reps = [c for c in cells if c["key"] == key]
            routing_mean = statistics.fmean(c["frac"] for c in reps)
            delta = routing_mean - sonnet_eval_mean[key]
            deltas.append(delta)
            rows.append({"record": "eval", "variant": variant, "eval_key": key,
                         "routing": round(routing_mean, 3),
                         "sonnet_solo": round(sonnet_eval_mean[key], 3),
                         "delta": round(delta, 3),
                         "escalated": sum(1 for c in reps if not c["ship"])})

        mean_delta, lo, hi = ci95(deltas)
        n_ship = sum(1 for c in cells if c["ship"])
        n_fa = sum(1 for c in cells if c["false_accept"])
        median_ratio = statistics.median(c["cost_ratio"] for c in cells)
        total_ratio = (sum(c["cost"] for c in cells)
                       / sum(cost[(c["key"], "sonnet-solo", c["rep"])] for c in cells))
        wall_ratio = (sum(c["wall"] for c in cells)
                      / sum(wall[(c["key"], "sonnet-solo", c["rep"])] for c in cells))
        fa_rate = n_fa / len(cells)
        clears = variant_clears_bar(mean_delta, median_ratio, fa_rate)
        if clears:
            clearing[variant] = median_ratio
        verdict_rows.append({
            "record": "variant", "variant": variant,
            "mean_delta_vs_sonnet_solo": round(mean_delta, 3),
            "ci95": [round(lo, 3), round(hi, 3)],
            "quality_non_inferior": mean_delta > MARGIN,
            "escalation_rate": round(1 - n_ship / len(cells), 3),
            "false_accepts": n_fa, "cells": len(cells),
            "false_accept_rate_cells": round(fa_rate, 3),
            "false_accept_rate_among_accepts": round(n_fa / n_ship, 3) if n_ship else None,
            "checker_fidelity_ok": fa_rate <= FALSE_ACCEPT_BAR,
            "median_cost_ratio_vs_sonnet_solo": round(median_ratio, 3),
            "total_cost_ratio_vs_sonnet_solo": round(total_ratio, 3),
            "sequential_wall_ratio_vs_sonnet_solo": round(wall_ratio, 3),
            "cost_materially_lower": median_ratio <= COST_RATIO_BAR,
            "parse_failures": sum(1 for c in cells if c["parse_error"]),
            "clears_bar": clears,
        })

    adopted = pick_adopted(clearing)
    overall = {
        "record": "verdict", "evals": len(gradient), "cells_per_variant": len(gradient) * REPS,
        "adopt_routing": adopted is not None, "adopted_variant": adopted,
        "adoption_bar": f"mean_delta > {MARGIN} AND median cost ratio <= {COST_RATIO_BAR} AND "
                        f"false-accept(cells) <= {FALSE_ACCEPT_BAR}; cheapest clearing variant wins",
    }

    with open(os.path.join(BASE, "results.jsonl"), "w", encoding="utf-8", newline="") as fh:
        for r in rows + verdict_rows + [overall]:
            fh.write(json.dumps(r) + "\n")

    print("=== routing-escalation (issue #109): frac-met, met_final=min(grader,prosecutor) ===")
    for v in verdict_rows:
        print(f"  {v['variant']:>13}: delta {v['mean_delta_vs_sonnet_solo']:+.3f} "
              f"CI [{v['ci95'][0]:+.3f},{v['ci95'][1]:+.3f}]  E={v['escalation_rate']:.2f}  "
              f"FA={v['false_accepts']}/{v['cells']} ({v['false_accept_rate_cells']:.0%})  "
              f"cost x{v['median_cost_ratio_vs_sonnet_solo']:.2f} (median) "
              f"x{v['total_cost_ratio_vs_sonnet_solo']:.2f} (total)  "
              f"{'CLEARS' if v['clears_bar'] else 'fails'}")
    print(f"\nVERDICT: {'ADOPT routing (' + adopted + ')' if adopted else 'DO NOT ADOPT routing'}"
          f" -- bar: {overall['adoption_bar']}")


if __name__ == "__main__":
    main()
