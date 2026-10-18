#!/usr/bin/env python3
"""Selection (after prescreen) and verdicts (after the grid), per metadata.json.

  python3 aggregate.py --select   first run's selection (ids < NEW_FROM_ID) + graded prescreen of
                                  the held-out ids -> selection.json (per-model surviving evals)
  python3 aggregate.py [--judge J] graded grid -> results-<J>.json + printed table

Verdict per (skill, model) = benchstats.keep_verdict(clustered_delta(with - without)) — the live
interval rule, practical bar 0, eval-clustered (ADR 0019). Below 8 surviving evals a cell is
DIAGNOSTIC ONLY (ADR 0095 decision 4) and is labelled so here, never left to the reader.
Primary: the HELD-OUT verdict per model (ids >= NEW_FROM_ID, authored after revision 1 was
written). Secondary: the TUNED-ON verdict per model (ids < NEW_FROM_ID, the tasks revision 1 was
written against, expected optimistic) and the held-out delta pooled over both models' clusters.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "skill-measure" / "scripts" / "lib"))
import benchstats  # noqa: E402

from grid import EVALS, MODELS, NEW_FROM_ID, PAIRS  # noqa: E402

SATURATED = 0.85
MIN_G = 8
PRIOR = HERE.parent / "2026-10-18-control-narratives-vs-bare" / "selection.json"
SETS = {"held_out": lambda k: eid(k) >= NEW_FROM_ID, "tuned_on": lambda k: eid(k) < NEW_FROM_ID}


def rows(path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l]


def eid(key):
    return int(key.split(":E")[1])


def select(judge):
    graded = rows(HERE / "graded" / f"cells-{judge}-prescreen-outputs.jsonl")
    prior = json.loads(PRIOR.read_text(encoding="utf-8"))
    sel = {"rule": f"drop an eval for a model when its bare prescreen fraction-met >= {SATURATED}; "
                   "0.0 floors flagged, kept. ids < NEW_FROM_ID carry the first run's prescreen "
                   "selection (same judge, instrument and threshold). An eval with no prescreen "
                   "grade is listed in unscreened and KEPT: it was never shown saturated",
           "judge": judge, "surviving": {}, "dropped": {}, "floors": {}, "unscreened": {},
           "per_eval": {}}
    by = {(r["model"], r["scenario"]): benchstats.fraction_met(r["met"]) for r in graded}
    for mk, model in MODELS.items():
        sel["surviving"][mk], sel["dropped"][mk], sel["floors"][mk] = [], [], []
        for key, f in prior["per_eval"].items():
            m, k = key.split(":", 1)
            if m == mk and eid(k) < NEW_FROM_ID:
                by[(model, k)] = f
        for (m, key), f in sorted(by.items(), key=lambda x: (x[0][0], x[0][1].split(":")[0], eid(x[0][1]))):
            if m != model or key.split(":")[0] not in PAIRS[mk]:
                continue
            sel["per_eval"][f"{mk}:{key}"] = round(f, 3)
            (sel["dropped"] if f >= SATURATED else sel["surviving"])[mk].append(key)
            if f == 0.0:
                sel["floors"][mk].append(key)
        sel["unscreened"][mk] = sorted((k for k in EVALS if k.split(":")[0] in PAIRS[mk]
                                        and (model, k) not in by),
                                       key=lambda k: (k.split(":")[0], eid(k)))
        sel["surviving"][mk] += sel["unscreened"][mk]
    sel["g_per_skill"] = {mk: {s: sum(1 for k in sel["surviving"][mk] if k.startswith(s + ":"))
                               for s in PAIRS[mk]} for mk in MODELS}
    (HERE / "selection.json").write_text(json.dumps(sel, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(sel["g_per_skill"], indent=1))
    if any(sel["unscreened"].values()):
        print("UNSCREENED (no prescreen grade; kept):", json.dumps(sel["unscreened"]))


def pooled(graded, keep):
    """Clusters are (model, eval); keys are prefixed with the model so clustered_delta never merges
    two models' cells into one cluster."""
    cells = [{**r, "scenario": f'{r["model"]}|{r["scenario"]}'} for r in graded if keep(r["scenario"])]
    d = benchstats.clustered_delta(cells, "with", "without")
    return {"mean": round(d["mean"], 4), "ci95": [round(x, 4) for x in d["ci95"]],
            "n_clusters": d["n_clusters"],
            "bare": round(benchstats.arm_mean(cells, "without"), 3) if cells else None}


def ungraded_cells(graded):
    """Gradable grid cells (outputs/ minus grade.py's recorded exclusions) with no graded row:
    a judge call that failed twice leaves no row, and without this its cell vanishes silently."""
    recs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((HERE / "outputs").glob("*.json"))]
    errs = HERE / "graded" / "error-cells-outputs.json"
    excluded = {e["cell"] for e in json.loads(errs.read_text(encoding="utf-8"))} if errs.exists() else set()
    done = {r["bid"] for r in graded}
    return [r for r in recs if not r["summary"]["error"] and r["cell"] not in excluded | done]


def verdicts(judge):
    graded = rows(HERE / "graded" / f"cells-{judge}-outputs.jsonl")
    missing = ungraded_cells(graded)
    out = {"judge": judge, "frame": "FRAME-UNCHECKED (generator-family judge, ADR 0093)"
           if judge.startswith("claude-") else "cross-family", "cells": {}, "ungraded": {}}
    for mk, model in MODELS.items():
        s = PAIRS[mk][0]
        for arm in ("with", "without"):
            n = sum(1 for r in missing if (r["model"], r["arm"]) == (model, arm))
            if n:
                out["ungraded"][f"{mk}:{s}:{arm}"] = n
        for set_name, keep in SETS.items():
            cells = [r for r in graded if r["model"] == model and keep(r["scenario"])]
            if not cells:
                continue
            delta = benchstats.clustered_delta(cells, "with", "without")
            v = benchstats.keep_verdict(delta)
            g = delta["n_clusters"]
            v["n_clusters"] = g
            v["arm_means"] = {a: round(x, 3) for a, x in delta["arm_means"].items()}
            v["per_eval"] = {k: round(d, 3) for k, d in delta["per_scenario"].items()}
            v["status"] = "BATCH" if g >= MIN_G else "DIAGNOSTIC-ONLY (G<8, ADR 0095 decision 4)"
            if set_name == "tuned_on":
                v["status"] = "SECONDARY (tuned-on, optimistic) — " + v["status"]
            gap = sum(n for k, n in out["ungraded"].items() if k.startswith(f"{mk}:"))
            if gap:
                v["status"] = (f"INCOMPLETE: {gap} gradable cell(s) have no grade (judge failed; "
                               f"re-run grade.py) — {v['status']}")
            out["cells"][f"{mk}:{set_name}"] = v
            print(f"{mk:6s} {set_name:9s} G={g:2d} bare={v['arm_means']['without']:.3f} "
                  f"with={v['arm_means']['with']:.3f} delta={v.get('mean', float('nan')):+.3f} "
                  f"CI={v.get('ci95')} {v['verdict']} [{v['status'].split(' ')[0]}]")
    if out["ungraded"]:
        print("UNGRADED cells (no verdict row; results incomplete):", json.dumps(out["ungraded"]))
    out["pooled"] = {name: pooled(graded, keep) for name, keep in SETS.items()}
    print("pooled over models:", json.dumps(out["pooled"]))
    # One file per judge: a cross-family re-grade must sit beside the same-family result, never
    # overwrite it (the agreement between the two is what promotes a verdict).
    (HERE / f"results-{judge}.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--select", action="store_true")
    ap.add_argument("--judge", default="claude-opus-5-5")
    a = ap.parse_args()
    select(a.judge) if a.select else verdicts(a.judge)


if __name__ == "__main__":
    main()
