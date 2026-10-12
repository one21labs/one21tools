#!/usr/bin/env python3
"""Grade cells against the frozen expectations (rubric.skill_grade_prompt, one call per cell).

Usage: python3 grade.py --dirs prescreen-outputs [--judges claude-opus-5-5 grok]
  -> graded/cells-<judge>-<dirs>.jsonl
Default judge: Claude Opus 5.5, run with the same isolation as generation (no tools, no skills,
empty config, cwd outside the checkout). It is the GENERATOR'S FAMILY: every verdict it backs is
FRAME-UNCHECKED (ADR 0093) until a cross-family judge (`--judges grok`, where grok is installed)
grades the same committed cells. Artifact gate + exclusion-symmetry sweep first (ERROR cells
excluded, never quality 0; skew on the per-arm exclusion rate); per-judge resumable jsonl; a
JudgeError (incl. a reply that is not a full grade, judge.met_map) is retried once, then recorded.
"""
import argparse
import json
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "skill-bench" / "scripts" / "lib"))
import rubric  # noqa: E402
from artifact_check import check_artifact  # noqa: E402
from blind import capture_symmetry  # noqa: E402
from judge import ClaudeJudge, JudgeError, make_judge, met_map  # noqa: E402

from grid import EVALS  # noqa: E402

MIN_CHARS = 200


def judge_for(name):
    """An exact claude-* id is pinned (ClaudeJudge refuses a call served by another model). Empty
    config dir, as generation (grid.py) and the 12-Oct judge used."""
    return (ClaudeJudge(model=name, config_dir=tempfile.mkdtemp(prefix="judge-config-"))
            if name.startswith("claude-") else make_judge(name))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="+", default=["outputs"])
    ap.add_argument("--judges", nargs="+", default=["claude-opus-5-5"])
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    recs = [json.loads(p.read_text(encoding="utf-8"))
            for d in args.dirs for p in sorted((HERE / d).glob("*.json"))]
    (HERE / "graded").mkdir(exist_ok=True)
    tag = "-".join(Path(d).name for d in args.dirs)

    ok_cells, errors = [], []
    for r in recs:
        if r["summary"]["error"]:
            errors.append({"cell": r["cell"], "reason": r["summary"]["error"]})
            continue
        ok, reason = check_artifact(r.get("response") or "", min_chars=MIN_CHARS)
        if ok:
            ok_cells.append(r)
        else:
            errors.append({"cell": r["cell"], "reason": reason})
    if errors:
        print(f"ERROR cells (excluded, #191): {errors}", file=sys.stderr)
    (HERE / "graded" / f"error-cells-{tag}.json").write_text(json.dumps(errors, indent=1), encoding="utf-8")
    # Skew is on the per-arm EXCLUSION rate, every exclusion reason counted, over ALL cells.
    excluded = {e["cell"] for e in errors}
    sym = capture_symmetry(recs, lambda r: r.get("response") or "",
                           excluded_fn=lambda r: r["cell"] in excluded)
    (HERE / "graded" / f"symmetry-{tag}.json").write_text(json.dumps(sym, indent=1), encoding="utf-8")
    if sym["skewed"]:
        sys.exit(f"capture symmetry SKEWED — infrastructure defect, fix before grading: {sym}")

    for jname in args.judges:
        out = HERE / "graded" / f"cells-{jname}-{tag}.jsonl"  # per dir: prescreen and grid bids collide
        done = set()
        if out.exists():
            done = {json.loads(l)["bid"] for l in out.read_text(encoding="utf-8").splitlines() if l}
        judge = judge_for(jname)
        todo = [r for r in ok_cells if r["cell"] not in done]

        def grade_one(r):
            ev = EVALS[r["scenario"]]
            n = len(ev["expectations"])
            prompt = rubric.skill_grade_prompt(ev["task"], r["response"], ev["expectations"])
            for attempt in (1, 2):  # one retry: a malformed reply is a judge hiccup, not a grade
                try:
                    v = judge.grade(prompt, rubric.GRADE_SCHEMA)
                    met = met_map(v, n)  # strict: an empty or partial reply is not all-false
                    break
                except (JudgeError, json.JSONDecodeError) as e:
                    if attempt == 2:
                        return {"error": {"judge": jname, "bid": r["cell"], "error": str(e)}}
            return {"row": {"bid": r["cell"], "skill": r["skill"], "scenario": r["scenario"],
                            "model": r["model"], "arm": r["arm"], "rep": r["rep"], "met": met,
                            "why": {e["id"]: e.get("why", "") for e in v["expectations"]}}}

        cost_file = HERE / "graded" / f"judge-cost-{jname}-{tag}.json"
        prior = json.loads(cost_file.read_text()) if cost_file.exists() else {"billed_usd": 0.0, "calls": 0}

        def persist_cost():  # after every row and on the way out: an interrupt keeps its spend
            cost_file.write_text(json.dumps(
                {"billed_usd": round(prior["billed_usd"] + getattr(judge, "real_cost_usd", 0.0), 4),
                 "calls": prior["calls"] + judge.calls}, indent=1) + "\n")

        try:
            with out.open("a", encoding="utf-8") as f, \
                    (HERE / "graded" / "judge-errors.jsonl").open("a", encoding="utf-8") as jerr, \
                    ThreadPoolExecutor(max_workers=args.workers) as pool:
                for res in pool.map(grade_one, todo):
                    if "error" in res:
                        jerr.write(json.dumps(res["error"]) + "\n")
                        jerr.flush()
                        print(f"JUDGE ERROR (recorded): {res['error']}", flush=True)
                    else:
                        f.write(json.dumps(res["row"]) + "\n")
                        f.flush()
                    persist_cost()
        finally:
            persist_cost()  # after the pool drains: calls still in flight at an interrupt count
        real = getattr(judge, "real_cost_usd", None)
        print(f"{jname}: {len(todo)} graded over {judge.calls} calls; billed "
              f"${real if real is not None else 'n/a'}", flush=True)


if __name__ == "__main__":
    main()
