#!/usr/bin/env python3
"""/bench-skill — paired with/without value benchmark for a skill, cross-family judged (ADR 0055).

Generate each eval task under two arms (skill-loaded vs bare) via the rented substrate, grade each
output against pre-registered expectations with the cross-family judge, and report the with-without
fraction-met delta + KEEP/CUT verdict (ADR 0025 shape). Reuses benchstats for the math.

Eval file: JSON list of {"id","task","expectations":[...]}. Arms: {"with":[argv...],"without":[argv...]}
where the task text is appended as the final CLI arg. Substrate + judge are injected so the
orchestration core (grade_all/aggregate) is unit-testable offline (see bench_skill_test.py).

Explicit-invoke only; prints a cost estimate and requires --yes before any paid generation.
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
import rubric, benchstats  # noqa: E402
from judge import make_judge, met_map  # noqa: E402
from substrate import make_substrate  # noqa: E402


def grade_all(gen_rows, evals_by_id, judge):
    """gen_rows: [{prompt_id, arm, output}] -> cells: [{bid, arm, scenario, met}]."""
    cells = []
    for r in gen_rows:
        ev = evals_by_id[r["prompt_id"]]
        exps = ev["expectations"]
        v = judge.grade(rubric.skill_grade_prompt(ev["task"], r["output"], exps), rubric.GRADE_SCHEMA)
        m = met_map(v)
        # normalize to ids 1..len(exps); missing -> False
        met = {i: bool(m.get(i, False)) for i in range(1, len(exps) + 1)}
        cells.append({"bid": f'{ev["id"]}:{r["arm"]}:r{r.get("rep", 1)}', "arm": r["arm"],
                      "scenario": str(ev["id"]), "met": met})
    return cells


def aggregate(cells, with_arm="with", without_arm="without"):
    delta = benchstats.clustered_delta(cells, with_arm, without_arm)
    return {"arm_means": {a: round(benchstats.arm_mean(cells, a), 3) for a in (with_arm, without_arm)},
            "with_minus_without": benchstats.keep_verdict(delta),
            "per_scenario": {k: round(v, 3) for k, v in delta["per_scenario"].items()}}


def frac_met_generic(met):
    return sum(1 for v in met.values() if v) / len(met) if met else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--evals", required=True, help="JSON list of {id, task, expectations[]}")
    ap.add_argument("--with-cmd", required=True, help="argv (JSON list) for the skill-loaded arm")
    ap.add_argument("--without-cmd", required=True, help="argv (JSON list) for the bare arm")
    ap.add_argument("--judge", choices=["auto", "grok", "claude"], default="auto",
                    help="auto = grok if available else claude (cross-family preferred)")
    ap.add_argument("--substrate", choices=["native", "promptfoo"], default="native")
    ap.add_argument("--reps", type=int, default=3,
                    help="generations per task x arm (a single pass cannot separate reliably-good "
                         "from lucky; ADR 0019/0058 — set 1 only for a smoke run)")
    ap.add_argument("--out", default="-")
    ap.add_argument("--yes", action="store_true", help="confirm paid generation (spend guard)")
    a = ap.parse_args()
    if a.reps < 1:
        sys.exit("--reps must be >= 1")

    evals = json.load(open(a.evals))
    evals_by_id = {e["id"]: e for e in evals}
    arms = [{"name": "with", "cmd": json.loads(a.with_cmd)},
            {"name": "without", "cmd": json.loads(a.without_cmd)}]
    n_gen = len(evals) * 2 * a.reps
    print(f"[cost] {len(evals)} tasks x 2 arms x {a.reps} reps = {n_gen} generations + "
          f"{n_gen} judge calls (judge={a.judge}, substrate={a.substrate})", file=sys.stderr)
    if not a.yes:
        print("Refusing to spend without --yes (spend guard). Re-run with --yes to proceed.", file=sys.stderr)
        sys.exit(2)

    sub = make_substrate(a.substrate)
    judge = make_judge(a.judge)  # 'auto' falls back grok->claude; raises with remedy if none
    if judge.fallback_note:
        print("NOTE: " + judge.fallback_note, file=sys.stderr)
    tasks = [e["task"] for e in evals]
    gen = []
    for rep in range(1, a.reps + 1):
        rows = sub.run(tasks, arms)
        for g in rows:
            g["rep"] = rep
        gen.extend(rows)
    # resolve prompt_id (task index from the substrate) back to the eval id; promptfoo may echo it as
    # a string, native as an int. A non-numeric value is assumed to already be an eval id.
    for g in gen:
        pid = g["prompt_id"]
        if isinstance(pid, int):
            g["prompt_id"] = evals[pid]["id"]
        elif isinstance(pid, str) and pid.isdigit():
            g["prompt_id"] = evals[int(pid)]["id"]
    cells = grade_all(gen, evals_by_id, judge)
    report = {"skill_evals": a.evals, "judge": judge.name, "n_tasks": len(evals),
              "n_reps": a.reps, **aggregate(cells)}
    js = json.dumps(report, indent=1)
    print(js) if a.out == "-" else open(a.out, "w").write(js)


if __name__ == "__main__":
    main()
