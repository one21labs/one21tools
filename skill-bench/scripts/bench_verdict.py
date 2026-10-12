#!/usr/bin/env python3
"""/bench-verdict — re-run the verdict math on an existing graded benchmark dir, with a pluggable
judge, and NO new generation spend (ADR 0055). This is the generalized #172 cross-family prototype.

Two modes:
  --judge <backend>     re-grade the committed normalized cells with that judge (grade+prosecute),
                        then compute arm means, the clustered treatment-control delta (KEEP/CUT;
                        pair from --primary, default C,B), per-expectation.
  --judge both          run the chosen judge AND load the committed baseline verdicts, then emit the
                        JUDGE-DIVERGENCE diagnostic (agreement, kappa, stricter-count, verdict flip).

Input dir must contain graded/verdicts.jsonl (bid, scenario, norm, expectations[baseline judge]),
arm_map.tsv (bid arm scenario rep; located by bench_io.load_arm_map), graded/keys.json
(scenario -> rubric key).

Normalization is REUSED from the committed cells (the only stage that sees raw output) so the judge
family is the sole changed variable. Reads the benchmark dir read-only; writes only to --out
(and per-cell regraded verdicts to --cells-out when given).
"""
import argparse, json, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
import rubric, benchstats  # noqa: E402
from bench_io import load_arm_map  # noqa: E402
from judge import (make_judge, met_map, JudgeError, cli_available, CachedJudge,  # noqa: E402
                   BACKENDS, family_of, GENERATOR_FAMILY)


def load_dir(d):
    """-> (cells, baseline, keys, baseline_errors, missing). A committed row that is an error row
    (the grading template records judge failures as {bid, error}) or whose expectations are not
    ids 1..len(EXP_IDS) with boolean met is excluded from the baseline and recorded in
    baseline_errors, never scored 0; an error row is not re-graded either (it has no norm).
    `missing` names every arm_map bid with no verdicts.jsonl row: a cell the grid ran but nobody
    graded is an error, never a silent absence (it can flip a verdict by dropping one arm)."""
    amap = load_arm_map(d)
    cells, baseline, berrs, seen = [], [], [], set()
    with open(os.path.join(d, "graded/verdicts.jsonl")) as f:
        for line in f:
            v = json.loads(line)
            if v.get("bid") not in amap:
                continue
            seen.add(v["bid"])
            if "error" in v:
                berrs.append({"bid": v["bid"], "error": str(v["error"])[:200]})
                continue
            arm, scn = amap[v["bid"]]
            cells.append({"bid": v["bid"], "arm": arm, "scenario": scn, "norm": v["norm"]})
            try:  # a malformed committed verdict is excluded from the baseline, never scored 0
                met = met_map(v, len(benchstats.EXP_IDS))
            except JudgeError as e:
                berrs.append({"bid": v["bid"], "error": str(e)[:200]})
                continue
            baseline.append({"bid": v["bid"], "arm": arm, "scenario": scn, "met": met})
    with open(os.path.join(d, "graded/keys.json")) as f:
        keys = json.load(f)
    missing = [{"bid": b, "error": "no graded/verdicts.jsonl row"} for b in amap if b not in seen]
    return cells, baseline, keys, berrs, missing


def regrade_cell(judge, cell, key):
    g = judge.grade(rubric.grade_prompt(cell["norm"], key), rubric.GRADE_SCHEMA)
    p = judge.grade(rubric.prosecute_prompt(cell["norm"], key, g), rubric.GRADE_SCHEMA)
    n = len(benchstats.EXP_IDS)
    gm, pm = met_map(g, n), met_map(p, n)
    return {"bid": cell["bid"], "arm": cell["arm"], "scenario": cell["scenario"],
            "met": {i: gm.get(i, False) and pm.get(i, False) for i in benchstats.EXP_IDS}}


def cache_judge_name(rows):
    """The judge a --cache file says graded it: the `judge` every row carries, when they all carry
    the same one; otherwise "cached". Never a live backend's name — whatever CLI is reachable now
    did not produce these grades."""
    names = {r.get("judge") for r in rows}
    return names.pop() if len(names) == 1 and isinstance(next(iter(names)), str) else "cached"


def regrade(judge, cells, keys, workers, cache=None):
    out, errs = [], []
    if cache is not None:  # reuse a prior run's per-cell grades (offline)
        rows = {r["bid"]: r for r in cache}
        for c in cells:
            r = rows.get(c["bid"])
            try:  # a missing, error, or malformed row is an error, as a failed live call would be
                if r is None:
                    raise JudgeError("no --cache row")
                if "error" in r:
                    raise JudgeError(str(r["error"]))
                if "expectations" not in r and isinstance(r.get("met"), dict):  # pre-12-Oct shape
                    r = {"expectations": [{"id": int(i), "met": m} for i, m in r["met"].items()]}
                out.append({**c, "met": met_map(r, len(benchstats.EXP_IDS))})
            except JudgeError as e:
                errs.append({"bid": c["bid"], "error": str(e)[:200]})
        return out, errs
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(regrade_cell, judge, c, keys[c["scenario"]]): c["bid"] for c in cells}
        for i, fut in enumerate(as_completed(futs), 1):
            try:
                out.append(fut.result())
            except (JudgeError, Exception) as e:
                errs.append({"bid": futs[fut], "error": str(e)[:200]})
            print(f"  [{i}/{len(cells)}] {'ok' if not errs or errs[-1]['bid']!=futs[fut] else 'ERR'}",
                  file=sys.stderr)
    return out, errs


def summarize(cells, x, y, practical=0.0):
    d_xy = benchstats.clustered_delta(cells, x, y)
    # matched-scenario, scenario-weighted: these subtract to the verdict's mean
    return {"arm_means": {a: round(v, 3) for a, v in d_xy["arm_means"].items()},
            f"{x}_minus_{y}": benchstats.keep_verdict(d_xy, practical),
            "per_expectation": {i: {a: round(v, 2) for a, v in benchstats.per_expectation(cells)[i].items()}
                                for i in benchstats.EXP_IDS},
            # #191 item 3: the delta's largest per-cell contributors; inspect=true means the
            # verdict flips or halves without them — check those cells for infrastructure
            # failure before interpreting the bar.
            "attribution": benchstats.top_cell_attribution(cells, x, y, practical=practical)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    # Choices are DERIVED from judge.BACKENDS, never restated: a registry entry that the CLI
    # cannot name is a backend nobody can reach. Adding `copilot` and `command` to the registry
    # left this list behind, so both were unreachable here until the muda-review caught it.
    ap.add_argument("--judge", choices=["auto", *sorted(BACKENDS), "both"], default="auto",
                    help="auto = the first reachable backend in judge.AUTO_ORDER, preferring "
                         "cross-family; both = chosen judge + committed baseline, with the "
                         "divergence diagnostic")
    ap.add_argument("--out", default="-")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--cache", help="prior regrade jsonl (offline: skip live judge calls)")
    ap.add_argument("--cells-out", help="also write per-cell regraded verdicts (jsonl: bid, arm, "
                                        "scenario, judge, expectations) — readable back as --cache; "
                                        "the substrate for judge-basis bar math")
    ap.add_argument("--primary", default="C,B",
                    help="treatment,control arm pair for the clustered delta (default C,B)")
    ap.add_argument("--practical", type=float, default=0.0,
                    help="pre-registered minimum difference worth having; KEEP needs the CI's "
                         "lower bound above it (benchstats.keep_verdict)")
    a = ap.parse_args()
    try:
        px, py = [s.strip() for s in a.primary.split(",")]
    except ValueError:
        sys.exit(f"--primary must be 'X,Y' (got {a.primary!r})")

    cells, baseline, keys, baseline_errs, missing = load_dir(a.dir)
    if a.limit:
        cells, baseline = cells[:a.limit], baseline[:a.limit]
    cache = [json.loads(line) for line in open(a.cache) if line.strip()] if a.cache else None

    # 'both' needs ONE cross-family judge: the baseline half is read off the committed cells,
    # never re-graded (references/judging.md). Live, that is a reachable cross-family CLI; with
    # --cache it is the cache naming a cross-family judge — a CLI on PATH graded nothing here.
    want_both = a.judge == "both"
    degrade_note = None
    if cache is not None:
        judge = CachedJudge(cache_judge_name(cache))  # offline: no CLI, never a live name
        if want_both and family_of(judge.name) in (GENERATOR_FAMILY, "unknown"):
            want_both = False
            degrade_note = (f"--judge both needs a cross-family judge; the --cache file names "
                            f"{judge.name!r}, not one — reporting a single-judge verdict instead")
    else:
        if want_both and not any(cli_available(n) for n, s in BACKENDS.items() if s["cross_family"]):
            want_both = False
            degrade_note = ("--judge both needs a reachable cross-family judge for the divergence "
                            "diagnostic; none is — reporting a single-judge verdict instead")
        # resolves per judge.AUTO_ORDER; raises with remedy if none
        judge = make_judge("auto" if a.judge in ("auto", "both") else a.judge)
    if judge.fallback_note:
        print("NOTE: " + judge.fallback_note, file=sys.stderr)
    if degrade_note:
        print("NOTE: " + degrade_note, file=sys.stderr)
    print(f"re-grading {len(cells)} cells with judge={judge.name}"
          + (" (from --cache)" if cache is not None else ""), file=sys.stderr)
    regraded, errs = regrade(judge, cells, keys, a.workers, cache=cache)
    errs = missing + errs
    if a.cells_out:  # the --cache row shape, so a --cells-out file reads back with its judge
        with open(a.cells_out, "w") as f:
            for c in regraded:
                f.write(json.dumps({"bid": c["bid"], "arm": c["arm"], "scenario": c["scenario"],
                                    "judge": judge.name, "met": c["met"], "expectations": [
                                        {"id": i, "met": m} for i, m in c["met"].items()]}) + "\n")
        print(f"wrote {len(regraded)} per-cell verdicts to {a.cells_out}", file=sys.stderr)

    report = {"dir": a.dir, "judge": judge.name, "n_cells": len(regraded), "errors": len(errs),
              "error_cells": errs,
              "notional_cost_usd": {
                  "judge_calls": judge.calls, "usd": judge.cost_usd(),
                  "note": "shadow cost at published API rates (deterministic: tokens x rate); "
                          "$0 marginal under subscription; 0 here when --cache (no live calls)"},
              "regraded": summarize(regraded, px, py, a.practical)}
    if judge.fallback_note:
        report["judge_fallback"] = judge.fallback_note
    if degrade_note:
        report["degraded"] = degrade_note
    if want_both:
        report["baseline_judge"] = "committed"
        report["baseline"] = summarize(baseline, px, py, a.practical)
        if baseline_errs:
            report["baseline_errors"] = baseline_errs
        report["divergence"] = benchstats.divergence(baseline, regraded, "baseline", judge.name)
        report["verdict_flip"] = benchstats.verdict_flip(
            benchstats.clustered_delta(baseline, px, py),
            benchstats.clustered_delta(regraded, px, py), a.practical)
    js = json.dumps(report, indent=1)
    if a.out == "-":
        print(js)
    else:
        open(a.out, "w").write(js)
        print(f"wrote {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
