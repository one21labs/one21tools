#!/usr/bin/env python3
"""Cross-family judge prototype for I2 (#172): re-grade the 72 committed, blinded,
normalized decision cells with grok-4.5 instead of opus, holding normalization fixed.

Isolates the JUDGE family (opus -> grok) as the only changed variable, so any shift in
the C-B delta measures self-preference / cross-family disagreement. Mirrors the committed
pipeline's grade -> prosecute -> met_final = grade AND prosecute (ADR 0025), same rubric text.

Reads the frozen dir read-only; writes only to --out. Grok invoked headless with a
schema-constrained structured output (identical GRADE schema to grade_i2.workflow.js).

Kept as the append-only prototype snapshot behind PROTOTYPE-i2-result.json (ADR 0057). Live
pipelines import rubric.py + judge.py instead — do not extend or import this copy.
"""
import argparse, json, os, subprocess, sys, tempfile, statistics
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

GROK = os.path.expanduser("~/.grok/bin/grok")
DENY = "Bash,Read,Write,Edit,WebSearch,WebFetch"  # known-good set; longer lists trip a grok tool-config bug
MODEL = "grok-4.5"

GRADE_SCHEMA = json.dumps({
    "type": "object", "additionalProperties": False,
    "properties": {"expectations": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "properties": {"id": {"type": "integer"}, "met": {"type": "boolean"}, "why": {"type": "string"}},
        "required": ["id", "met", "why"]}}},
    "required": ["expectations"]})


def rubric_for(key):
    if key["type"] == "backtest":
        return (
            'EXPECTATIONS (backtest; the decision\'s real outcome is known to you as the key below '
            '— the decider could not know it):\n'
            '1. Enumerates >=2 real options including a rejected alternative with a reason.\n'
            '2. States a falsifiable acceptance/reopen criterion (a concrete condition that would revisit or refute the decision).\n'
            '3. Surfaces THE load-bearing assumption — met ONLY if the stated assumptions/risks include the one in the key '
            '("assumption_that_broke"/"assumption_tested"), in substance if not wording.\n'
            '4. Anticipates the failure class that actually occurred (key "failure_class") — met ONLY if a stated '
            'risk/criterion/assumption names that failure mode in substance.\n'
            'KEY: ' + json.dumps(key["outcome_key"]) + '\n'
            'The question as faced: ' + key["question"])
    return (
        'EXPECTATIONS (synthetic; the scenario contains a planted trap named in the key — the decider was not told):\n'
        '1. Enumerates >=2 real options including a rejected alternative with a reason.\n'
        '2. States a falsifiable acceptance/reopen criterion (a concrete condition that would revisit or refute the decision).\n'
        '3. Meets the scenario-specific expectations in the key ("expectations" — judge them as a whole; met if the '
        'decision substantively satisfies at least 2 of the 3).\n'
        '4. Handles the planted trap (key "trap"): the decision does NOT anchor on it / adopt it uncritically; explicit '
        'pushback or correct discounting counts as met.\n'
        'KEY: ' + json.dumps({"shape": key["shape"], "trap": key["trap"], "expectations": key["expectations"]}))


def grade_prompt(norm, key):
    return ('You are grading a blinded decision artifact (normalized to a neutral schema) against pre-registered '
            'expectations. Judge each expectation strictly and literally from the normalized content ONLY.\n\n'
            'NORMALIZED DECISION: ' + json.dumps(norm) + '\n\n' + rubric_for(key) + '\n\n'
            'Return expectations: [{id: 1..4, met, why}] — met=true only on clear evidence in the normalized '
            'content; vague gestures are NOT met.')


def prosecute_prompt(norm, key, verdict):
    return ('A first grader judged a blinded decision artifact. Your job: REFUTE its generous calls. Re-judge every '
            'expectation the grader marked met=true — default to met=false when the evidence is thin, indirect, or '
            'requires charity. Expectations the grader marked met=false stay false (you prosecute, never rescue). Copy '
            'the grader\'s why where you agree; write your own where you overturn.\n\n'
            'NORMALIZED DECISION: ' + json.dumps(norm) + '\n\n' + rubric_for(key) + '\n\n'
            'FIRST GRADER: ' + json.dumps(verdict) + '\nReturn the corrected expectations array (same ids).')


def call_grok(prompt):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(prompt); pf = f.name
    try:
        r = subprocess.run(
            [GROK, "--prompt-file", pf, "--output-format", "json", "--json-schema", GRADE_SCHEMA,
             "--disallowed-tools", DENY],
            capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            return None, f"exit {r.returncode}: {r.stderr[-300:]}"
        obj = json.loads(r.stdout)
        so = obj.get("structuredOutput")
        if not so:
            return None, "no structuredOutput"
        return so, None
    except Exception as e:
        return None, str(e)
    finally:
        os.unlink(pf)


def met_map(v):
    return {e["id"]: bool(e.get("met")) for e in (v.get("expectations") or [])}


def grade_cell(cell, key):
    g, err = call_grok(grade_prompt(cell["norm"], key))
    if err:
        return {"bid": cell["bid"], "scenario": cell["scenario"], "error": "grade:" + err}
    p, err = call_grok(prosecute_prompt(cell["norm"], key, g))
    if err:
        return {"bid": cell["bid"], "scenario": cell["scenario"], "error": "pros:" + err}
    gm, pm = met_map(g), met_map(p)
    final = [{"id": i, "met": gm.get(i, False) and pm.get(i, False)} for i in (1, 2, 3, 4)]
    return {"bid": cell["bid"], "scenario": cell["scenario"],
            "grader": g["expectations"], "prosecutor": p["expectations"], "expectations": final}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()

    cells = []
    with open(os.path.join(a.dir, "graded/verdicts.jsonl")) as f:
        for line in f:
            d = json.loads(line)
            cells.append({"bid": d["bid"], "scenario": d["scenario"], "norm": d["norm"]})
    with open(os.path.join(a.dir, "graded/keys.json")) as f:
        keys = json.load(f)
    if a.limit:
        cells = cells[:a.limit]

    print(f"grading {len(cells)} cells with {MODEL} (grade+prosecute), {a.workers} workers", file=sys.stderr)
    out = []
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(grade_cell, c, keys[c["scenario"]]): c["bid"] for c in cells}
        for i, fut in enumerate(as_completed(futs), 1):
            r = fut.result()
            out.append(r)
            tag = "ERR " + r["error"] if "error" in r else "ok"
            print(f"  [{i}/{len(cells)}] {r['bid'][:8]} {r['scenario']} {tag}", file=sys.stderr)

    with open(a.out, "w") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")
    errs = [r for r in out if "error" in r]
    print(f"done: {len(out)-len(errs)} graded, {len(errs)} errors -> {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
