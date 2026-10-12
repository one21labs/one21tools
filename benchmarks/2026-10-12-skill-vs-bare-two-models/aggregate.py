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
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "skill-bench" / "scripts" / "lib"))
import benchstats  # noqa: E402

from grid import MODELS, SKILLS  # noqa: E402

SATURATED = 0.85
MIN_G = 8


def rows(path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l]


def select(judge):
    graded = rows(HERE / "graded" / f"cells-{judge}-prescreen-outputs.jsonl")
    sel = {"rule": f"drop an eval for a model when its bare prescreen fraction-met >= {SATURATED}; "
                   "0.0 floors flagged, kept", "judge": judge, "surviving": {}, "dropped": {},
           "floors": {}, "per_eval": {}}
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
    sel["g_per_skill"] = {mk: {s: sum(1 for k in sel["surviving"][mk] if k.startswith(s + ":"))
                               for s in SKILLS} for mk in MODELS}
    (HERE / "selection.json").write_text(json.dumps(sel, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(sel["g_per_skill"], indent=1))


def verdicts(judge):
    graded = rows(HERE / "graded" / f"cells-{judge}-outputs.jsonl")
    out = {"judge": judge, "frame": "FRAME-UNCHECKED (generator-family judge, ADR 0093)"
           if judge.startswith("claude-") else "cross-family", "cells": {}}
    for mk, model in MODELS.items():
        for s in SKILLS:
            cells = [r for r in graded if r["model"] == model and r["skill"] == s]
            delta = benchstats.clustered_delta(cells, "with", "without")
            v = benchstats.keep_verdict(delta)
            g = delta["n_clusters"]
            v["n_clusters"] = g
            v["arm_means"] = {a: round(benchstats.arm_mean(cells, a), 3) for a in ("with", "without")}
            v["per_eval"] = {k: round(d, 3) for k, d in delta["per_scenario"].items()}
            v["status"] = "BATCH" if g >= MIN_G else "DIAGNOSTIC-ONLY (G<8, ADR 0095 decision 4)"
            out["cells"][f"{mk}:{s}"] = v
            print(f"{mk:6s} {s:24s} G={g:2d} bare={v['arm_means']['without']:.3f} "
                  f"with={v['arm_means']['with']:.3f} delta={v.get('mean', float('nan')):+.3f} "
                  f"CI={v.get('ci95')} {v['verdict']} [{v['status'].split(' ')[0]}]")
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
