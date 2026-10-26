#!/usr/bin/env python3
"""Grade cells against the frozen expectations (rubric.skill_grade_prompt, one call per cell).

Usage: python3 grade.py --dirs prescreen-outputs [--judges claude-opus-5-5 grok]
  -> graded/cells-<judge>-<dirs>.jsonl
Default judge: Claude Opus 5.5, run with the same isolation as generation (no tools, no skills,
empty config, cwd outside the checkout). It is the GENERATOR'S FAMILY: every verdict it backs is
FRAME-UNCHECKED (ADR 0093) until a cross-family judge (`--judges grok`, where grok is installed)
grades the same committed cells. Artifact gate + exclusion-symmetry sweep first (ERROR cells
excluded, never quality 0, except a reply cut off at the output cap, which is scored failed with
no judge call; skew on the per-arm exclusion rate); per-judge resumable jsonl; a
JudgeError (incl. a reply that is not JSON or not a full grade: judge.parse_reply, strict
judge.met_map) is retried once, then recorded as an error row; judge cost is persisted per row.
"""
import argparse
import json
import os
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
# The harness left this repo (ADR 0102): $SKILL_MEASURE_ROOT, else a sibling skill-measure
# checkout. Neither found = exit naming the remedy, never a bare ImportError. judge.parse_reply
# needs skill-measure 38772a6 or later.
HARNESS = Path(os.environ.get("SKILL_MEASURE_ROOT") or HERE.parents[2] / "skill-measure")
if not (HARNESS / "scripts" / "lib").is_dir():
    sys.exit(f"harness not found at {HARNESS}: git clone https://github.com/one21labs/skill-measure "
             "&& export SKILL_MEASURE_ROOT=$PWD/skill-measure")
sys.path.insert(0, str(HARNESS / "scripts" / "lib"))
import rubric  # noqa: E402
import usage_guard  # noqa: E402
from artifact_check import check_artifact  # noqa: E402
from blind import capture_symmetry  # noqa: E402
from hermetic_driver import build_env, neutral_cwd  # noqa: E402
from judge import ClaudeJudge, JudgeError, make_judge, met_map, parse_reply  # noqa: E402

from grid import EVALS, cap_hit, check_auth, check_harness  # noqa: E402

MIN_CHARS = 200


class IsolatedClaudeJudge(ClaudeJudge):
    """ClaudeJudge pinned to an exact model and the generation-side isolation flags."""

    def __init__(self, model):
        super().__init__(model=model)
        self.name = model
        self.config = tempfile.mkdtemp(prefix="judge-config-")
        self.cwd = neutral_cwd("judge")
        self.real_cost_usd = 0.0  # billed envelope cost; cost_usd() is the notional price table

    def grade(self, prompt, schema):
        p = prompt + "\n\nReturn ONLY valid JSON matching this schema, no prose:\n" + json.dumps(schema)
        cmd = [self.bin, "-p", "--output-format", "json", "--model", self.model, "--tools", "",
               "--disable-slash-commands", "--strict-mcp-config", "--effort", "medium"]
        env = usage_guard.guarded_run(cmd, timeout=self.timeout, error=JudgeError, input=p,
                                      cwd=self.cwd,
                                      env={**build_env("medium"), "CLAUDE_CONFIG_DIR": self.config})
        self._record(env)
        self.real_cost_usd += env.get("total_cost_usd") or 0.0
        served = sorted((env.get("modelUsage") or {}).keys())
        if self.model not in served:
            raise JudgeError(f"judge requested {self.model}, envelope served {served}")
        return parse_reply(env.get("result", ""), "claude")


def judge_for(name):
    return IsolatedClaudeJudge(name) if name.startswith("claude-") else make_judge(name)


def grade_one(judge, jname, r):
    """One cell -> {"row": ...} or {"error": ...}; never raises on a bad judge reply."""
    ev = EVALS[r["scenario"]]
    n = len(ev["expectations"])
    prompt = rubric.skill_grade_prompt(ev["task"], r["response"], ev["expectations"])
    for attempt in (1, 2):  # one retry: a malformed reply is a judge hiccup, not a grade
        try:
            v = judge.grade(prompt, rubric.GRADE_SCHEMA)
            met = met_map(v, n)  # strict: a wrong-shape or partial reply is not all-false
            break
        except JudgeError as e:
            if attempt == 2:
                return {"error": {"judge": jname, "bid": r["cell"], "error": str(e)}}
    return {"row": {"bid": r["cell"], "skill": r["skill"], "scenario": r["scenario"],
                    "model": r["model"], "arm": r["arm"], "rep": r["rep"], "met": met,
                    "why": {e["id"]: e.get("why", "") for e in v["expectations"]}}}


def capped_row(r):
    """A reply cut off at the output cap fails every expectation, with no judge call: the
    receiving engineer gets an unusable narrative (owner, 26-Oct-2026; metadata.json grid)."""
    n = len(EVALS[r["scenario"]]["expectations"])
    return {"bid": r["cell"], "skill": r["skill"], "scenario": r["scenario"], "model": r["model"],
            "arm": r["arm"], "rep": r["rep"], "met": dict.fromkeys(range(1, n + 1), False),
            "why": {}, "cap_hit": True}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="+", default=["outputs"])
    ap.add_argument("--judges", nargs="+", default=["claude-opus-5-5"])
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    check_harness()
    if any(j.startswith("claude-") for j in args.judges):  # same empty config as generation
        check_auth({**build_env("medium"), "CLAUDE_CONFIG_DIR": tempfile.mkdtemp()})

    recs = [json.loads(p.read_text(encoding="utf-8"))
            for d in args.dirs for p in sorted((HERE / d).glob("*.json"))]
    (HERE / "graded").mkdir(exist_ok=True)
    tag = "-".join(Path(d).name for d in args.dirs)

    ok_cells, errors, capped = [], [], []
    for r in recs:
        if cap_hit(r):  # graded failed below, so not an exclusion in the symmetry sweep
            capped.append(r)
            continue
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
                for r in capped:
                    if r["cell"] not in done:
                        f.write(json.dumps(capped_row(r)) + "\n")
                f.flush()
                for res in pool.map(lambda r: grade_one(judge, jname, r), todo):
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
