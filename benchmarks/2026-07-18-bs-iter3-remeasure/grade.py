#!/usr/bin/env python3
"""Grade iter-3 cells against the committed expectations, both judge families (#224; #214 pattern).

Usage: python3 grade.py [--dirs outputs] [--judges grok claude]
Graded artifact = response text. Capture-symmetry sweep + artifact shape gate (ERROR cells
excluded, never quality 0); per-judge resumable jsonl; a JudgeError records and continues.
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
from judge import JudgeError, make_judge, met_map  # noqa: E402

MIN_CHARS = 200
_raw = json.loads((HERE.parents[1] / "skills" / "building-skills" / "evals" / "evals.json").read_text(encoding="utf-8"))
EVALS = {f'E{e["id"]}': {"task": e["prompt"], "expectations": e["expectations"]} for e in _raw["evals"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="+", default=["outputs"])
    ap.add_argument("--judges", nargs="+", default=["grok", "claude"])
    args = ap.parse_args()

    recs = []
    for d in args.dirs:
        for p in sorted((HERE / d).glob("*.json")):
            recs.append(json.loads(p.read_text(encoding="utf-8")))
    (HERE / "graded").mkdir(exist_ok=True)

    sym = capture_symmetry(recs, lambda r: r.get("response") or "")
    (HERE / "graded" / "symmetry.json").write_text(json.dumps(sym, indent=1), encoding="utf-8")
    if sym["skewed"]:
        sys.exit(f"capture symmetry SKEWED — infrastructure defect, fix before grading: {sym}")

    ok_cells, errors = [], []
    for r in recs:
        if r["summary"]["error"]:
            errors.append({"cell": r["cell"], "reason": r["summary"]["error"]})
            continue
        ok, reason = check_artifact(r.get("response") or "", min_chars=MIN_CHARS)
        (ok_cells if ok else errors).append((r, None) if ok else {"cell": r["cell"], "reason": reason})
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
        jerr = (HERE / "graded" / "judge-errors.jsonl").open("a", encoding="utf-8")
        with out.open("a", encoding="utf-8") as f:
            for r, _ in ok_cells:
                bid = r["cell"]
                if bid in done:
                    continue
                ev = EVALS[r["scenario"]]
                exps = ev["expectations"]
                try:
                    v = judge.grade(rubric.skill_grade_prompt(ev["task"], r["response"], exps),
                                    rubric.GRADE_SCHEMA)
                except JudgeError as e:
                    jerr.write(json.dumps({"judge": jname, "bid": bid, "error": str(e)}) + "\n")
                    jerr.flush()
                    print(f"[{jname}:{bid}] JUDGE ERROR (recorded, continuing): {e}", flush=True)
                    continue
                m = met_map(v)
                met = {i: bool(m.get(i, False)) for i in range(1, len(exps) + 1)}
                row = {"bid": bid, "arm": r["arm"], "scenario": r["scenario"], "rep": r["rep"],
                       "met": met, "why": {e["id"]: e.get("why", "") for e in v.get("expectations", [])}}
                f.write(json.dumps(row) + "\n")
                f.flush()
                print(f"[{jname}:{bid}] met={sum(met.values())}/{len(met)}", flush=True)
        jerr.close()
        print(f"{jname}: judge cost ${judge.cost_usd()} over {judge.calls} calls", flush=True)


if __name__ == "__main__":
    main()
