#!/usr/bin/env python3
"""Cross-family re-grade lane (issue #244 pre-registration): grok grades every blinded item
independently of the sonnet grader/prosecutor, writing graded/grok_verdicts.jsonl. Blind
discipline identical to grade.workflow.js: the item JSON carries no arm. Robustness read-out
only — the headline metric stays met_final = min(grader, prosecutor) for 07-09 comparability.

Resumable: an item with a line already in graded/grok_verdicts.jsonl is skipped.
Usage: python3 grok_regrade.py [--limit N]
"""
import json, os, re, subprocess, sys

GROK = os.path.expanduser("~/.grok/bin/grok")
ITEMS = "graded/items"
OUT = "graded/grok_verdicts.jsonl"
SCHEMA = json.dumps({"type": "object", "properties": {
    "met": {"type": "integer"}, "total": {"type": "integer"}, "evidence": {"type": "string"}},
    "required": ["met", "total", "evidence"]})

PROMPT = """You are grading one response to a task, against a fixed expectation list. Be strict
and adversarial-neutral: an expectation counts as met only if the response clearly satisfies it;
partial or implied credit is not met. Return JSON: met (count of expectations clearly satisfied),
total (number of expectations), evidence (one terse line per unmet expectation, semicolon-joined,
or "all met").

TASK GIVEN TO THE MODEL:
{prompt}

EXPECTATIONS ({n}):
{expectations}

RESPONSE TO GRADE:
{response}"""


def main():
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    shard, nshards = 0, 1
    if "--shard" in sys.argv:  # --shard i/n : process todo[i::n] (parallel workers)
        shard, nshards = map(int, sys.argv[sys.argv.index("--shard") + 1].split("/"))
    done = set()
    if os.path.exists(OUT):
        with open(OUT) as f:
            for line in f:
                try: done.add(json.loads(line)["bid"])
                except Exception: pass
    bids = sorted(b[:-5] for b in os.listdir(ITEMS) if b.endswith(".json"))
    todo = [b for b in bids if b not in done][shard::nshards]
    if limit: todo = todo[:limit]
    print(f"grok_regrade: {len(done)} done, {len(todo)} to grade")
    for i, bid in enumerate(todo):
        item = json.load(open(f"{ITEMS}/{bid}.json"))
        exps = item["expectations"]
        p = PROMPT.format(prompt=item["prompt"], n=len(exps),
                          expectations="\n".join(f"- {e}" for e in exps),
                          response=item["response"])
        r = subprocess.run([GROK, "--single", p, "--json-schema", SCHEMA],
                           capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            print(f"  ERROR {bid}: rc={r.returncode} {r.stderr[:200]}", file=sys.stderr)
            continue
        # grok --json-schema returns an ENVELOPE object; the schema-constrained JSON is the
        # STRING in its "text" field (verified against a live call, 18-Jul).
        try:
            env = json.loads(r.stdout)
            v = json.loads(env["text"])
        except Exception as e:
            print(f"  ERROR {bid}: envelope/text parse ({e})", file=sys.stderr)
            continue
        rec = {"bid": bid, "met": v.get("met"), "total": v.get("total"),
               "evidence": (v.get("evidence") or "")[:500], "judge": "grok"}
        with open(OUT, "a") as f:
            f.write(json.dumps(rec) + "\n")
        print(f"  [{i+1}/{len(todo)}] {bid} met={rec['met']}/{rec['total']}")
    print("grok_regrade done.")


if __name__ == "__main__":
    main()
