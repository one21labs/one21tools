#!/usr/bin/env python3
"""Cross-judge re-grade of the July 8-10 house-skill battery (issue #224 Stage 1; ADR 0055 iii).

Rebuilds every blinded cell (prompt + expectations + response, arm withheld) from each frozen
source dir's committed outputs/ + meta.json, asserts the rebuilt set bid-for-bid against the
committed arm map, then re-judges each cell with the cross-family grok judge using the ORIGINAL
grader and uniform-prosecutor wording (grade.workflow.js / prosecute_counts.workflow.js),
inlined because grok is tool-denied. met_final = min(grader_met, prosecutor_met) (ADR 0025).

Writes graded/<source>.grok.jsonl (resumable: done bids skipped on rerun). Reads frozen dirs
only; never writes into them (ADR 0026). Hard-stops past metadata.json:cost.ceiling_usd
(ADR 0073).

Usage: python3 regrade.py [--limit N] [--workers N] [--sources d1 d2 ...]
"""
import argparse
import csv
import hashlib
import json
import sys
import tarfile
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent
sys.path.insert(0, str(BENCH.parent / "skill-bench" / "scripts" / "lib"))
from judge import JudgeError, make_judge  # noqa: E402

META = json.loads((HERE / "metadata.json").read_text(encoding="utf-8"))
SOURCES = META["sources"]
CEILING = META["cost"]["ceiling_usd"]
ARMS = ("with", "without", "with-old", "with-new")

GRADE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {"pass": {"type": "boolean"}, "met": {"type": "integer"},
                   "total": {"type": "integer"}, "evidence": {"type": "string"}},
    "required": ["pass", "met", "total", "evidence"]}
PROSECUTE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {"met": {"type": "integer"}, "total": {"type": "integer"},
                   "evidence": {"type": "string"}},
    "required": ["met", "total", "evidence"]}


def cell_json(cell):
    """The blinded payload — same fields the original graders read from graded/items/<bid>.json."""
    return json.dumps({"prompt": cell["prompt"], "response": cell["response"],
                       "expectations": cell["expectations"]})


def grade_prompt(cell):
    # grade.workflow.js wording, verbatim except the file read is inlined (grok is tool-denied).
    return ('Below is a JSON object. It has: "prompt" (a user request), "response" (an AI '
            'assistant\'s reply), and "expectations" (an array of specific requirements the '
            'response must satisfy).\n\n' + cell_json(cell) + '\n\n'
            'Evaluate EACH expectation as MET or NOT MET, strictly and literally, using ONLY '
            'evidence in the response text. Do not give credit for intent, partial effort, or '
            'things the response merely gestures at. If the response is truncated, refused, or '
            'off-task, unmet expectations are NOT MET.\n\n'
            'Return: total = number of expectations; met = how many are MET; pass = true ONLY if '
            'met == total (every expectation satisfied); evidence = the single most decisive '
            'expectation that is NOT MET (quote the response gap), or if all met, the expectation '
            'that was closest to failing and why it still passed.')


def prosecute_prompt(cell):
    # prosecute_counts.workflow.js wording, verbatim except the file read is inlined.
    return ('Below is a JSON object with "prompt" (a user request), "response" (an AI '
            'assistant\'s reply), and "expectations" (an array of specific requirements).\n\n'
            + cell_json(cell) + '\n\n'
            'You are an ADVERSARIAL grader. Go expectation by expectation and count how many are '
            'GENUINELY and FULLY satisfied by the response TEXT alone. Be skeptical: default an '
            'expectation to NOT MET when the evidence is thin, partial, gestured-at, '
            'claimed-but-not-done, or faked. Give NO credit for intent or effort. If the response '
            'is truncated, refused, or off-task, its unmet expectations are NOT MET.\n\n'
            'Return: total = number of expectations; met = your strict count of '
            'genuinely-and-fully satisfied expectations; evidence = the single most decisive '
            'expectation you judged NOT MET and the specific gap (or, if you truly found all '
            'met, why).')


def load_cells(src):
    d = BENCH / src
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    texts = {}
    for p in sorted((d / "outputs").glob("*.txt")):
        texts[p.name[:-4]] = p.read_text(encoding="utf-8", errors="replace")
    tgz = d / "outputs" / "all.tar.gz"
    if tgz.exists():
        with tarfile.open(tgz) as tf:
            for m in tf.getmembers():
                base = Path(m.name).name
                if base.endswith(".txt"):
                    texts.setdefault(base[:-4], tf.extractfile(m).read().decode("utf-8", "replace"))
    cells = []
    for name, text in sorted(texts.items()):
        parts = name.split(".")
        if len(parts) != 4:
            continue
        skill, eval_id, arm, rep = parts
        if arm not in ARMS:
            continue
        m = meta.get(f"{skill}.{eval_id}")
        if not m:
            continue
        cells.append({"bid": hashlib.sha256(name.encode()).hexdigest()[:12], "skill": skill,
                      "eval_id": eval_id, "arm": arm, "rep": rep, "prompt": m["prompt"],
                      "expectations": m["expectations"], "response": text.strip()})
    return cells


def committed_arm_map(src):
    d = BENCH / src / "graded"
    j = d / "arm_map.json"
    if j.exists():
        return json.loads(j.read_text(encoding="utf-8"))
    with open(d / "arm_map.tsv", encoding="utf-8") as fh:
        return {r["bid"]: r for r in csv.DictReader(fh, delimiter="\t")}


def assert_arm_map(src, cells):
    """Rebuilt cells must match the committed blinding bid-for-bid, else the frozen inputs were
    misread — abort before spending a single judge call."""
    committed = committed_arm_map(src)
    mine = {c["bid"]: c for c in cells}
    if set(mine) != set(committed):
        raise SystemExit(f"{src}: rebuilt bids != committed arm map "
                         f"(+{sorted(set(mine) - set(committed))[:5]} "
                         f"-{sorted(set(committed) - set(mine))[:5]})")
    for bid, rec in committed.items():
        c = mine[bid]
        for k in ("skill", "eval_id", "arm"):
            if str(rec[k]) != str(c[k]):
                raise SystemExit(f"{src}/{bid}: {k} mismatch committed={rec[k]} rebuilt={c[k]}")


def grade_cell(judge, cell):
    expected = len(cell["expectations"])
    g = judge.grade(grade_prompt(cell), GRADE_SCHEMA)
    p = judge.grade(prosecute_prompt(cell), PROSECUTE_SCHEMA)
    for tag, v in (("grader", g), ("prosecutor", p)):
        if v.get("total") != expected:
            print(f"WARN {cell['bid']}: {tag} total={v.get('total')} != {expected} expectations",
                  file=sys.stderr)
    gm = max(0, min(int(g.get("met") or 0), expected))
    pm = max(0, min(int(p.get("met") or 0), expected))
    met = min(gm, pm)
    # Persisted evidence reflects whichever judgment produced the final count (#49/#50 rule).
    evidence = p.get("evidence", "") if pm < gm else g.get("evidence", "")
    return {"bid": cell["bid"], "skill": cell["skill"], "eval_id": cell["eval_id"],
            "arm": cell["arm"], "rep": cell["rep"], "total": expected, "grader_met": gm,
            "grader_pass": bool(g.get("pass")), "pros_met": pm, "met": met, "evidence": evidence}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="grade at most N pending cells (pilot)")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--sources", nargs="+", default=SOURCES)
    args = ap.parse_args()

    judge = make_judge("grok")  # explicit: never silently fall back to the same family
    (HERE / "graded").mkdir(exist_ok=True)
    write_lock = threading.Lock()
    budget = args.limit or None
    stop = False

    for src in args.sources:
        cells = load_cells(src)
        assert_arm_map(src, cells)
        out = HERE / "graded" / f"{src}.grok.jsonl"
        done = set()
        if out.exists():
            done = {json.loads(l)["bid"] for l in out.read_text(encoding="utf-8").splitlines() if l}
        pending = [c for c in cells if c["bid"] not in done]
        if budget is not None:
            pending = pending[:budget]
            budget -= len(pending)
        print(f"{src}: {len(cells)} cells, {len(done)} done, grading {len(pending)}", flush=True)
        if not pending:
            continue
        errs = 0
        with out.open("a", encoding="utf-8") as fh, \
                ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(grade_cell, judge, c): c["bid"] for c in pending}
            for i, f in enumerate(as_completed(futs), 1):
                try:
                    row = f.result()
                    with write_lock:
                        fh.write(json.dumps(row) + "\n")
                        fh.flush()
                    print(f"  [{i}/{len(pending)}] {futs[f]} met={row['met']}/{row['total']} "
                          f"(g{row['grader_met']}/p{row['pros_met']}) ${judge.cost_usd():.2f}",
                          flush=True)
                except JudgeError as e:
                    errs += 1
                    print(f"  ERR {futs[f]}: {str(e)[:150]}", file=sys.stderr, flush=True)
                if judge.cost_usd() > CEILING:
                    stop = True
                    for other in futs:
                        other.cancel()
                    break
        if errs:
            print(f"{src}: {errs} errors — rerun to retry those bids", file=sys.stderr)
        if stop:
            raise SystemExit(f"notional cost ${judge.cost_usd():.2f} exceeded ceiling ${CEILING} "
                             f"(ADR 0073) — stopped; re-approval required to continue")
    print(f"done; judge calls {judge.calls}, notional ${judge.cost_usd():.2f}", flush=True)


if __name__ == "__main__":
    main()
