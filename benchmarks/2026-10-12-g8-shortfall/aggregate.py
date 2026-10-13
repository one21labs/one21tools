#!/usr/bin/env python3
"""Selection (after prescreen) and verdicts (after the grid), per metadata.json.

  python3 aggregate.py --select   12-Oct selection (ids < NEW_FROM_ID) + graded prescreen of the
                                  new ids -> selection.json (per-model surviving evals, PAIRS only)
  python3 aggregate.py [--judge J] graded grid -> results-<J>.json + printed table

Verdict per (skill, model) = benchstats.keep_verdict(clustered_delta(with - without)) — the live
interval rule, practical bar 0, eval-clustered (ADR 0019). Below 8 surviving evals a cell is
DIAGNOSTIC ONLY (ADR 0095 decision 4) and is labelled so here, never left to the reader.
Secondary (ADR 0101): the delta split by eval provenance (original ids < BLIND_FROM_ID vs blind),
pooled over every in-scope (model, eval) cluster.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "skill-bench" / "scripts" / "lib"))
import benchstats  # noqa: E402

from grid import EVALS, MODELS, NEW_FROM_ID, PAIRS  # noqa: E402

SATURATED = 0.85
MIN_G = 8
BLIND_FROM_ID = 7  # ids 7+ were authored blind (12-Oct metadata.json evals.diff_vs_baseline)
PRIOR = HERE.parent / "2026-10-12-skill-vs-bare-two-models" / "selection.json"


def rows(path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l]


def eid(key):
    return int(key.split(":E")[1])


def select(judge):
    graded = rows(HERE / "graded" / f"cells-{judge}-prescreen-outputs.jsonl")
    prior = json.loads(PRIOR.read_text(encoding="utf-8"))
    sel = {"rule": f"drop an eval for a model when its bare prescreen fraction-met >= {SATURATED}; "
                   "0.0 floors flagged, kept. ids < NEW_FROM_ID carry the 12-Oct prescreen "
                   "selection (same judge, same instrument); new ids are prescreened here. An "
                   "eval with no prescreen grade (cell errored or ungraded, here or on 12-Oct) is "
                   "listed in unscreened and KEPT: it was never shown saturated",
           "judge": judge, "surviving": {}, "dropped": {}, "floors": {}, "unscreened": {},
           "per_eval": {}}
    by = {(r["model"], r["scenario"]): benchstats.fraction_met(r["met"]) for r in graded}
    for mk, model in MODELS.items():
        sel["surviving"][mk], sel["dropped"][mk], sel["floors"][mk] = [], [], []
        for key, f in sorted(prior["per_eval"].items()):
            m, k = key.split(":", 1)
            if m == mk and k.split(":")[0] in PAIRS[mk] and eid(k) < NEW_FROM_ID:
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


def provenance_split(graded):
    """ADR 0101 secondary: clusters are (model, eval); scenario keys are prefixed with the model so
    clustered_delta never merges two models' cells into one cluster."""
    out = {}
    for origin, keep in (("original", lambda k: eid(k) < BLIND_FROM_ID),
                         ("blind_12oct", lambda k: BLIND_FROM_ID <= eid(k) < NEW_FROM_ID),
                         ("blind_new", lambda k: eid(k) >= NEW_FROM_ID)):
        cells = [{**r, "scenario": f'{r["model"]}|{r["scenario"]}'} for r in graded
                 if keep(r["scenario"]) and r["skill"] in PAIRS["opus" if "opus" in r["model"] else "sonnet"]]
        d = benchstats.clustered_delta(cells, "with", "without")
        out[origin] = {"mean": round(d["mean"], 4), "ci95": [round(x, 4) for x in d["ci95"]],
                       "n_clusters": d["n_clusters"],
                       "bare": round(benchstats.arm_mean(cells, "without"), 3) if cells else None}
    # Confirmatory subset = blind_new only: ids 7-10 produced the post-hoc lead (ADR 0101), so
    # they cannot also confirm it.
    o, b = out["original"], out["blind_new"]
    out["reopen_0101_fires"] = (bool(b["ci95"][1] < o["mean"] or b["ci95"][0] > o["mean"])
                                if b["n_clusters"] > 1 else None)
    out["reading"] = ("ADR 0101 reopen-if: the blind_new 95% CI excludes the original point "
                      "estimate. Difficulty and provenance stay confounded (bare levels shown).")
    return out


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
        for s in PAIRS[mk]:
            cells = [r for r in graded if r["model"] == model and r["skill"] == s]
            for arm in ("with", "without"):
                n = sum(1 for r in missing if (r["model"], r["skill"], r["arm"]) == (model, s, arm))
                if n:
                    out["ungraded"][f"{mk}:{s}:{arm}"] = n
            delta = benchstats.clustered_delta(cells, "with", "without")
            v = benchstats.keep_verdict(delta)
            g = delta["n_clusters"]
            v["n_clusters"] = g
            # scenario-weighted over matched scenarios, so with - without equals the delta
            v["arm_means"] = {a: round(x, 3) for a, x in delta["arm_means"].items()}
            v["per_eval"] = {k: round(d, 3) for k, d in delta["per_scenario"].items()}
            v["status"] = "BATCH" if g >= MIN_G else "DIAGNOSTIC-ONLY (G<8, ADR 0095 decision 4)"
            gap = sum(n for k, n in out["ungraded"].items() if k.startswith(f"{mk}:{s}:"))
            if gap:
                v["status"] = (f"INCOMPLETE: {gap} gradable cell(s) have no grade (judge failed; "
                               f"re-run grade.py) — {v['status']}")
            out["cells"][f"{mk}:{s}"] = v
            print(f"{mk:6s} {s:24s} G={g:2d} bare={v['arm_means']['without']:.3f} "
                  f"with={v['arm_means']['with']:.3f} delta={v.get('mean', float('nan')):+.3f} "
                  f"CI={v.get('ci95')} {v['verdict']} [{v['status'].split(' ')[0]}]")
    if out["ungraded"]:
        print("UNGRADED cells (no verdict row; results incomplete):", json.dumps(out["ungraded"]))
    out["provenance_split"] = provenance_split(graded)
    print("provenance split:", json.dumps(out["provenance_split"]))
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
