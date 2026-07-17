#!/usr/bin/env python3
"""Grade generated cells against the pre-registered expectations, both judge families.

Usage: python3 grade.py [--dirs outputs] [--judges grok claude]
Reads <dir>/*.json cell records, applies the metadata graded_artifact_rule, runs the #191
capture-symmetry sweep and the artifact shape gate (ERROR cells excluded, never quality 0),
then grades every OK cell with each judge. Writes graded/cells-<judge>.jsonl (resumable per
judge file) and graded/symmetry.json.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "skill-bench" / "scripts" / "lib"))
import rubric  # noqa: E402
from artifact_check import check_artifact  # noqa: E402
from blind import capture_symmetry  # noqa: E402
from judge import make_judge, met_map  # noqa: E402

MIN_CHARS = 400  # metadata.json:graded_artifact_rule
EVALS = {e["id"]: e for e in json.loads((HERE / "evals.json").read_text(encoding="utf-8"))}


def graded_artifact(rec):
    """metadata.json:graded_artifact_rule — new *.md files if any, else the response text."""
    arts = rec.get("artifacts") or {}
    if arts:
        return "\n\n".join(f"# FILE: {k}\n{v}" for k, v in sorted(arts.items()))
    return rec.get("response") or ""


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
    (HERE / "graded").mkdir(exist_ok=True)

    sym = capture_symmetry(recs, graded_artifact)
    (HERE / "graded" / "symmetry.json").write_text(json.dumps(sym, indent=1), encoding="utf-8")
    if sym["skewed"]:
        sys.exit(f"capture symmetry SKEWED — infrastructure defect, fix before grading: {sym}")

    ok_cells, errors = [], []
    for r in recs:
        if r["summary"]["error"]:
            errors.append({"cell": r["cell"], "reason": r["summary"]["error"]})
            continue
        art = graded_artifact(r)
        ok, reason = check_artifact(art, min_chars=MIN_CHARS)
        if not ok:
            errors.append({"cell": r["cell"], "reason": reason})
            continue
        ok_cells.append((r, art))
    if errors:
        print(f"ERROR cells (excluded, #191): {errors}", file=sys.stderr)
    (HERE / "graded" / "error-cells.json").write_text(json.dumps(errors, indent=1), encoding="utf-8")

    for jname in args.judges:
        out = HERE / "graded" / f"cells-{jname}.jsonl"
        done = set()
        if out.exists():
            done = {json.loads(l)["bid"] for l in out.read_text(encoding="utf-8").splitlines() if l}
        judge = make_judge(jname)
        if judge.fallback_note:
            print("NOTE: " + judge.fallback_note, file=sys.stderr)
        with out.open("a", encoding="utf-8") as f:
            for r, art in ok_cells:
                bid = r["cell"]
                if bid in done:
                    continue
                ev = EVALS[r["scenario"]]
                exps = ev["expectations"]
                v = judge.grade(rubric.skill_grade_prompt(ev["task"], art, exps), rubric.GRADE_SCHEMA)
                m = met_map(v)
                met = {i: bool(m.get(i, False)) for i in range(1, len(exps) + 1)}
                row = {"bid": bid, "arm": r["arm"], "scenario": r["scenario"], "rep": r["rep"],
                       "met": met, "why": {e["id"]: e.get("why", "") for e in v.get("expectations", [])}}
                f.write(json.dumps(row) + "\n")
                f.flush()
                print(f"[{jname}:{bid}] met={sum(met.values())}/{len(met)}", flush=True)
        print(f"{jname}: judge cost ${judge.cost_usd()} over {judge.calls} calls", flush=True)


if __name__ == "__main__":
    main()
