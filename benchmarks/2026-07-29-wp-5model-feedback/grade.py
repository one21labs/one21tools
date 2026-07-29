#!/usr/bin/env python3
"""Blind-grade the generated cells against the pre-registered criteria, with two judges.

Pipeline, in order, because each stage gates the next:
  1. tell-strip every response and AUDIT the result. A single residual tell means the judge could
     identify the treatment arm, so grading HALTS rather than producing a compromised number.
  2. capture-symmetry sweep (skill-bench lib/blind.py): an arm with systematically empty or short
     responses is an infrastructure defect, not a quality signal.
  3. artifact shape gate: a too-short response is an ERROR cell, EXCLUDED — never scored 0, which
     would launder an infrastructure failure into a quality finding.
  4. blind ids, then grade with each judge independently.

Neither judge is fully independent of this generator set (three lanes are Anthropic, one is grok),
so results are written per judge and never merged.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "skill-bench" / "scripts" / "lib"))
sys.path.insert(0, str(HERE))
from artifact_check import check_artifact          # noqa: E402
from blind import assign_bids, capture_symmetry    # noqa: E402
from judge import JudgeError, make_judge, met_map  # noqa: E402
from rubric import GRADE_SCHEMA                    # noqa: E402
from tells import detect_tells, strip_report, strip_tells  # noqa: E402

MIN_CHARS = 400
PLAN = (HERE / "plan.md").read_text(encoding="utf-8")
CRITERIA = json.loads((HERE / "criteria.json").read_text(encoding="utf-8"))["criteria"]


def grade_prompt(feedback):
    """Judge sees the plan and one feedback text. It is told NOTHING about arms, models, or that
    a skill is under test — a judge that can infer the arm is not a blind judge."""
    crits = "\n".join(f"{c['id']}. {c['text']}" for c in CRITERIA)
    return (
        "You are grading the QUALITY OF FEEDBACK that a reviewer gave on a planning document.\n\n"
        "Judge each numbered criterion strictly and literally against the REVIEWER FEEDBACK "
        "only, using the PLANNING DOCUMENT as the reference for what the plan actually says. "
        "Mark a criterion met=true ONLY on clear evidence in the feedback text; vague gestures, "
        "partial satisfaction, and generic advice are NOT met. Where a criterion states a count "
        "(for example 'at least three'), count carefully and do not round up.\n\n"
        "--- PLANNING DOCUMENT ---\n" + PLAN + "\n--- END PLANNING DOCUMENT ---\n\n"
        "--- REVIEWER FEEDBACK ---\n" + feedback + "\n--- END REVIEWER FEEDBACK ---\n\n"
        "CRITERIA:\n" + crits + "\n\n"
        "Return expectations: [{id, met, why}] with exactly one entry per criterion above, "
        "where `why` cites the specific part of the feedback that decided the call."
    )


def load_cells(dirs):
    recs = []
    for d in dirs:
        for p in sorted((HERE / d).glob("*.json")):
            recs.append(json.loads(p.read_text(encoding="utf-8")))
    return recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="+", default=["outputs"])
    ap.add_argument("--judges", nargs="+", default=["grok", "claude"])
    args = ap.parse_args()

    recs = load_cells(args.dirs)
    if not recs:
        sys.exit("no cell records found — run generate.py first")
    (HERE / "graded").mkdir(exist_ok=True)

    # --- 1. tell-strip + audit -------------------------------------------------
    report = strip_report(recs, lambda r: r.get("response", ""))
    for r in recs:
        r["clean"], r["_strips"] = strip_tells(r.get("response", ""))
    residual = [r["cell"] for r in recs if detect_tells(r["clean"])]
    audit = {"per_arm": report, "residual_cells": residual}
    (HERE / "graded" / "blinding-audit.json").write_text(json.dumps(audit, indent=1),
                                                         encoding="utf-8")
    print(json.dumps(report, indent=1))
    if residual:
        sys.exit(f"BLINDING FAILURE — arm tells survive in {residual}. Grading halted: a judge "
                 f"that can identify the arm invalidates the whole measurement. Extend tells.py.")

    # --- 2. capture symmetry ---------------------------------------------------
    sym = capture_symmetry(recs, lambda r: r["clean"])
    (HERE / "graded" / "symmetry.json").write_text(json.dumps(sym, indent=1), encoding="utf-8")
    if sym["skewed"]:
        sys.exit(f"capture symmetry SKEWED — infrastructure defect, fix before grading: {sym}")
    print(f"capture symmetry OK: {json.dumps(sym['arms'])}")

    # --- 3. artifact gate ------------------------------------------------------
    ok_cells, errors = [], []
    for r in recs:
        if r["summary"]["error"]:
            errors.append({"cell": r["cell"], "reason": r["summary"]["error"]})
            continue
        good, reason = check_artifact(r["clean"], min_chars=MIN_CHARS)
        if not good:
            errors.append({"cell": r["cell"], "reason": reason})
            continue
        ok_cells.append(r)
    (HERE / "graded" / "error-cells.json").write_text(json.dumps(errors, indent=1),
                                                      encoding="utf-8")
    if errors:
        print(f"ERROR cells excluded (never scored 0): {errors}", file=sys.stderr)

    # --- 4. blind ids + grade --------------------------------------------------
    bid_of = {r["cell"]: bid for bid, r in assign_bids(ok_cells, lambda r: r["cell"])}
    for jname in args.judges:
        out = HERE / "graded" / f"cells-{jname}.jsonl"
        done = set()
        if out.exists():
            done = {json.loads(l)["bid"] for l in out.read_text(encoding="utf-8").splitlines() if l}
        judge = make_judge(jname)
        if getattr(judge, "fallback_note", None):
            print("NOTE: " + judge.fallback_note, file=sys.stderr)
        with out.open("a", encoding="utf-8") as f:
            for r in ok_cells:
                bid = bid_of[r["cell"]]
                if bid in done:
                    continue
                try:
                    v = judge.grade(grade_prompt(r["clean"]), GRADE_SCHEMA)
                except JudgeError as e:
                    print(f"[{jname}:{r['cell']}] JUDGE ERROR {e}", file=sys.stderr, flush=True)
                    continue
                m = met_map(v)
                met = {c["id"]: bool(m.get(c["id"], False)) for c in CRITERIA}
                row = {"bid": bid, "cell": r["cell"], "lane": r["lane"], "arm": r["arm"],
                       "rep": r["rep"], "answering_model": r["summary"].get("answering_model"),
                       "response_chars": len(r["clean"]),
                       "score": sum(met.values()) / len(met), "met": met,
                       "why": {e["id"]: e.get("why", "") for e in v.get("expectations", [])}}
                f.write(json.dumps(row) + "\n")
                f.flush()
                print(f"[{jname}:{r['cell']}] {sum(met.values())}/{len(met)} = "
                      f"{row['score']:.3f}", flush=True)
        print(f"{jname}: notional judge cost ${judge.cost_usd()} over {judge.calls} calls",
              flush=True)


if __name__ == "__main__":
    main()
