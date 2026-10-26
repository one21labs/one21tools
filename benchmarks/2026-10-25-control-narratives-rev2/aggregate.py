#!/usr/bin/env python3
"""Selection (after prescreen) and verdicts (after the grid), per metadata.json.

  python3 aggregate.py --select   graded prescreen -> selection.json (per-model surviving evals)
  python3 aggregate.py [--judge J] graded grid      -> results-<J>.json + printed table

Verdict per (skill, model) = benchstats.keep_verdict(clustered_delta(with - without)) — the live
interval rule, practical bar 0, eval-clustered (ADR 0019). Below 8 surviving evals a cell is
DIAGNOSTIC ONLY (ADR 0095 decision 4) and is labelled so here, never left to the reader.
"""
import argparse
import json
import os
import statistics
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
# The harness left this repo (ADR 0102): $SKILL_MEASURE_ROOT, else a sibling skill-measure
# checkout. Neither found = exit naming the remedy, never a bare ImportError.
HARNESS = Path(os.environ.get("SKILL_MEASURE_ROOT") or HERE.parents[2] / "skill-measure")
if not (HARNESS / "scripts" / "lib").is_dir():
    sys.exit(f"harness not found at {HARNESS}: git clone https://github.com/one21labs/skill-measure "
             "&& export SKILL_MEASURE_ROOT=$PWD/skill-measure")
sys.path.insert(0, str(HARNESS / "scripts" / "lib"))
import benchstats  # noqa: E402

from grid import EVALS, MODELS, SKILLS, check_harness  # noqa: E402

SATURATED = 0.85
MIN_G = 8


def rows(path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l]


def select(judge):
    graded = rows(HERE / "graded" / f"cells-{judge}-prescreen-outputs.jsonl")
    sel = {"rule": f"drop an eval for a model when its bare prescreen fraction-met >= {SATURATED}; "
                   "0.0 floors flagged, kept. An eval with no prescreen grade (cell errored or "
                   "ungraded) is listed in unscreened and KEPT: it was never shown saturated",
           "judge": judge, "surviving": {}, "dropped": {}, "floors": {}, "unscreened": {},
           "per_eval": {}}
    by = {(r["model"], r["scenario"]): benchstats.fraction_met(r["met"]) for r in graded}
    for mk, model in MODELS.items():
        sel["surviving"][mk], sel["dropped"][mk], sel["floors"][mk] = [], [], []
        for (m, key), f in sorted(by.items()):
            if m != model:
                continue
            sel["per_eval"][f"{mk}:{key}"] = round(f, 3)
            (sel["dropped"] if f >= SATURATED else sel["surviving"])[mk].append(key)
            if f == 0.0:
                sel["floors"][mk].append(key)
        sel["unscreened"][mk] = sorted(k for k in EVALS if (model, k) not in by)
        sel["surviving"][mk] += sel["unscreened"][mk]
    sel["g_per_skill"] = {mk: {s: sum(1 for k in sel["surviving"][mk] if k.startswith(s + ":"))
                               for s in SKILLS} for mk in MODELS}
    (HERE / "selection.json").write_text(json.dumps(sel, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(sel["g_per_skill"], indent=1))
    if any(sel["unscreened"].values()):
        print("UNSCREENED (no prescreen grade; kept):", json.dumps(sel["unscreened"]))


def ungraded_cells(graded):
    """Gradable grid cells with no graded row: a judge call that failed twice, or a cell grid.py
    regenerated or capped after the last grade.py pass, leaves no row, and without this its cell
    vanishes silently. Gradable is decided from outputs/ as it is now (grade.exclusion)."""
    from grade import exclusion
    recs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((HERE / "outputs").glob("*.json"))]
    done = {r["bid"] for r in graded}
    return [r for r in recs if exclusion(r) is None and r["cell"] not in done] + never_run(recs)


def never_run(recs):
    """Planned grid cells with no record at all (a halted or interrupted pass), as stub records
    so they count toward INCOMPLETE like an ungraded cell."""
    from grid import REPS
    sel = json.loads((HERE / "selection.json").read_text(encoding="utf-8"))
    have = {r["cell"] for r in recs}
    return [{"cell": f"{k.replace(':', '-')}-{mk}-{a}-r{rep}", "model": MODELS[mk], "skill": k.split(":")[0],
             "arm": a} for mk in MODELS for k in sel["surviving"][mk] for a in ("with", "without")
            for rep in range(1, REPS + 1) if f"{k.replace(':', '-')}-{mk}-{a}-r{rep}" not in have]


def consistency(cells):
    """Per arm, over evals: mean within-eval rep SD and mean worst-rep score (skill-measure
    pre-registration.md, 'Variance is a primary metric'). Descriptive; no verdict rests on it."""
    reps = defaultdict(list)
    for r in cells:
        reps[(r["arm"], r["scenario"])].append(benchstats.fraction_met(r["met"]))
    out = {}
    for arm in ("with", "without"):
        groups = [v for (a, _), v in reps.items() if a == arm and len(v) > 1]
        if groups:
            out[arm] = {"rep_sd": round(statistics.mean(statistics.stdev(v) for v in groups), 3),
                        "worst_rep": round(statistics.mean(min(v) for v in groups), 3),
                        "evals": len(groups)}
    return out


def verdicts(judge):
    graded = rows(HERE / "graded" / f"cells-{judge}-outputs.jsonl")
    missing = ungraded_cells(graded)
    out = {"judge": judge, "frame": "FRAME-UNCHECKED (generator-family judge, ADR 0093)"
           if judge.startswith("claude-") else "cross-family", "cells": {}, "ungraded": {}}
    for mk, model in MODELS.items():
        for s in SKILLS:
            cells = [r for r in graded if r["model"] == model and r["skill"] == s]
            for arm in ("with", "without"):
                n = sum(1 for r in missing if (r["model"], r["skill"], r["arm"]) == (model, s, arm))
                if n:
                    out["ungraded"][f"{mk}:{s}:{arm}"] = n
            delta = benchstats.clustered_delta(cells, "with", "without")
            v = benchstats.keep_verdict(delta)
            g = delta["n_clusters"]
            v["n_clusters"] = g
            # Matched-scenario means, so the printed with and bare subtract to the delta.
            v["arm_means"] = {a: round(x, 3) for a, x in delta["arm_means"].items()}
            v["consistency"] = consistency(cells)
            v["cap_hits"] = {a: sum(1 for r in cells if r["arm"] == a and r.get("cap_hit"))
                             for a in ("with", "without")}  # scored failed (grade.capped_row)
            v["per_eval"] = {k: round(d, 3) for k, d in delta["per_scenario"].items()}
            v["status"] = "BATCH" if g >= MIN_G else "DIAGNOSTIC-ONLY (G<8, ADR 0095 decision 4)"
            gap = sum(n for k, n in out["ungraded"].items() if k.startswith(f"{mk}:{s}:"))
            if gap:
                v["status"] = (f"INCOMPLETE: {gap} gradable cell(s) have no grade (judge failed or never run; "
                               f"re-run grid.py, then grade.py) — {v['status']}")
            out["cells"][f"{mk}:{s}"] = v
            print(f"{mk:6s} {s:24s} G={g:2d} bare={v['arm_means']['without']:.3f} "
                  f"with={v['arm_means']['with']:.3f} delta={v.get('mean', float('nan')):+.3f} "
                  f"CI={v.get('ci95')} {v['verdict']} [{v['status'].split(' ')[0]}]")
    if out["ungraded"]:
        print("UNGRADED cells (no verdict row; results incomplete):", json.dumps(out["ungraded"]))
    # One file per judge: the cross-family result sits beside the same-family one, never
    # overwrites it (metadata.json judging says which verdict promotes).
    (HERE / f"results-{judge}.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--select", action="store_true")
    ap.add_argument("--judge", default="claude-opus-5-5")
    a = ap.parse_args()
    check_harness()  # a verdict computed by another benchstats is not this run's
    select(a.judge) if a.select else verdicts(a.judge)


if __name__ == "__main__":
    main()
