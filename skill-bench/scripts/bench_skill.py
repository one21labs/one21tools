#!/usr/bin/env python3
"""/bench-skill — paired with/without value benchmark for a skill, cross-family judged (ADR 0055).

Generate each eval task under two arms (skill-loaded vs bare) via the rented substrate, grade each
output against pre-registered expectations with the cross-family judge, and report the with-without
fraction-met delta + KEEP/CUT verdict (ADR 0025 shape). Reuses benchstats for the math.

Eval file: JSON list of {"id","task","expectations":[...]}. Arms: {"with":[argv...],"without":[argv...]}
where the task text is appended as the final CLI arg. Substrate + judge are injected so the
orchestration core (grade_all/aggregate) is unit-testable offline (see bench_skill_test.py).

Prints a cost estimate and refuses to spend without --yes (the refusal ADR 0016 made the
condition for /bench being model-invocable at all).
"""
import argparse, json, os, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
import rubric, benchstats  # noqa: E402
from judge import make_judge, met_map, JudgeError, BACKENDS  # noqa: E402
from substrate import make_substrate  # noqa: E402
from spend_guard import add_spend_flag, require_yes  # noqa: E402


def grade_all(gen_rows, evals_by_id, judge):
    """gen_rows: [{prompt_id, arm, output[, error]}] -> (cells: [{bid, arm, scenario, met}], errors).
    A generation that failed (row carries "error") or a cell the judge cannot grade is recorded in
    errors and EXCLUDED, never graded: scoring it would charge a CLI or judge failure to the arm,
    and one bad call must not end the run."""
    cells, errs = [], []
    for r in gen_rows:
        ev = evals_by_id[r["prompt_id"]]
        exps = ev["expectations"]
        bid = f'{ev["id"]}:{r["arm"]}:r{r.get("rep", 1)}'
        if r.get("error"):
            errs.append({"bid": bid, "error": "generation: " + r["error"][:200]})
            continue
        try:
            m = met_map(judge.grade(rubric.skill_grade_prompt(ev["task"], r["output"], exps),
                                    rubric.GRADE_SCHEMA), len(exps))
        except (JudgeError, ValueError) as e:  # ValueError: a reply that is not JSON at all
            errs.append({"bid": bid, "error": str(e)[:200]})
            continue
        met = {i: m[i] for i in range(1, len(exps) + 1)}  # strict met_map: exactly these ids
        cells.append({"bid": bid, "arm": r["arm"], "scenario": str(ev["id"]), "met": met})
    return cells, errs


PATH_FLAG = re.compile(r"(dir|file|path|settings|config)$")


def relative_path_args(argv):
    """The args of an arm argv that only resolve from the caller's cwd. Arms run from an empty
    temp dir (NativeSubstrate), where these silently miss (the skill not loaded) or fail to
    launch. argv[0] resolves through PATH, so only a slash makes it cwd-relative. A later arg,
    or the value of `--flag=value`, counts when it exists here and looks like a path: it has a
    slash, starts with `.`, or follows a flag named like a path (`--plugin-dir myplug`); a plain
    option value such as `--model sonnet` never does."""
    out = []
    for i, a in enumerate(argv):
        if i == 0:
            if "/" in a and not os.path.isabs(a):
                out.append(a)
            continue
        flag, val = (a.split("=", 1) if a.startswith("-") and "=" in a else (argv[i - 1], a))
        pathlike = "/" in val or val.startswith(".") or PATH_FLAG.search(flag.lstrip("-"))
        if val and not os.path.isabs(val) and os.path.exists(val) and pathlike:
            out.append(a)
    return out


def aggregate(cells, with_arm="with", without_arm="without", practical=0.0):
    delta = benchstats.clustered_delta(cells, with_arm, without_arm)
    # matched-scenario, scenario-weighted: these subtract to the verdict's mean
    return {"arm_means": {a: round(v, 3) for a, v in delta["arm_means"].items()},
            "with_minus_without": benchstats.keep_verdict(delta, practical),
            "per_scenario": {k: round(v, 3) for k, v in delta["per_scenario"].items()}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--evals", required=True, help="JSON list of {id, task, expectations[]}")
    arm_note = ("; arms run from an empty temp dir, so every path in it must be absolute")
    ap.add_argument("--with-cmd", required=True,
                    help="argv (JSON list) for the skill-loaded arm" + arm_note)
    ap.add_argument("--without-cmd", required=True, help="argv (JSON list) for the bare arm" + arm_note)
    # Derived from judge.BACKENDS, never restated — see the same note in bench_verdict.py.
    ap.add_argument("--judge", choices=["auto", *sorted(BACKENDS)], default="auto",
                    help="auto = the first reachable backend in judge.AUTO_ORDER, preferring "
                         "cross-family")
    ap.add_argument("--substrate", choices=["native", "promptfoo"], default="native")
    ap.add_argument("--reps", type=int, default=3,
                    help="generations per task x arm (a single pass cannot separate reliably-good "
                         "from lucky; ADR 0019/0058 — set 1 only for a smoke run)")
    ap.add_argument("--practical", type=float, default=0.0,
                    help="pre-registered minimum difference worth having; KEEP needs the CI's "
                         "lower bound above it (benchstats.keep_verdict)")
    ap.add_argument("--out", default="-")
    add_spend_flag(ap, "paid generation")
    a = ap.parse_args()
    if a.reps < 1:
        sys.exit("--reps must be >= 1")

    evals = json.load(open(a.evals))
    evals_by_id = {e["id"]: e for e in evals}
    arms = [{"name": "with", "cmd": json.loads(a.with_cmd)},
            {"name": "without", "cmd": json.loads(a.without_cmd)}]
    for arm in arms:
        rel = relative_path_args(arm["cmd"])
        if rel:
            sys.exit(f"--{arm['name']}-cmd: {rel} are relative paths; arms run from an empty temp "
                     f"dir, where they would not resolve — make them absolute")
    n_gen = len(evals) * 2 * a.reps
    require_yes(a.yes, f"{len(evals)} tasks x 2 arms x {a.reps} reps = {n_gen} generations + "
                       f"{n_gen} judge calls (judge={a.judge}, substrate={a.substrate})")

    sub = make_substrate(a.substrate)
    judge = make_judge(a.judge)  # 'auto' resolves per judge.AUTO_ORDER; raises with remedy if none
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
    cells, errs = grade_all(gen, evals_by_id, judge)
    report = {"skill_evals": a.evals, "judge": judge.name, "n_tasks": len(evals),
              "n_reps": a.reps, "errors": errs, **aggregate(cells, practical=a.practical)}
    if judge.fallback_note:  # same-family judge: the caveat travels with the numbers
        report["judge_fallback"] = judge.fallback_note
    js = json.dumps(report, indent=1)
    print(js) if a.out == "-" else open(a.out, "w").write(js)


if __name__ == "__main__":
    main()
