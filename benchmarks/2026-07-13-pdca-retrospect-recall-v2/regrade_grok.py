#!/usr/bin/env python3
"""Grok-4.5 second headline for I1-v2 (pre-registration README item 5, ADR 0057 d2).

Re-judges every SEEDED cell's predicate + routing calls with the cross-family judge, holding
normalization fixed (the committed graded/items findings — the only stage that saw raw output).
Same shape as the opus pipeline: grade -> prosecute -> per-seed min. Writes
graded/verdicts_grok.jsonl in the opus verdicts' schema; aggregate.py then fills the
grok_regrade slot and the judge-split comparison on its next run. Reads frozen inputs only.
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "skill-bench" / "scripts" / "lib"))
from judge import make_judge  # noqa: E402

SEED_ITEM = {"type": "object", "additionalProperties": False,
             "properties": {"class": {"type": "string"}, "found": {"type": "boolean"},
                            "routed": {"type": "boolean"}, "why": {"type": "string"}},
             "required": ["class", "found", "routed", "why"]}
SCHEMA = {"type": "object", "additionalProperties": False,
          "properties": {"seeds": {"type": "array", "items": SEED_ITEM}},
          "required": ["seeds"]}


def grade_prompt(sub, findings, key):
    return (
        "You are grading a blinded review cell against a ground-truth key. NORMALIZED FINDINGS "
        "(the review's claims, neutral wording, each with an optional proposed remedy):\n"
        + json.dumps(findings) + f"\n\nGROUND-TRUTH SEED KEY for substrate {sub} (per seeded "
        "defect: class, plant site, the found-iff predicate defining a match, and the "
        "routing_key describing the correct remedy home):\n" + json.dumps(key) + "\n\n"
        "For EACH seed decide: found=true ONLY if some finding satisfies the found_iff predicate "
        "(cites the right site AND names the defect's substance; vague thematic mention without "
        "the cite does NOT count). routed=true ONLY if found=true AND that finding's remedy (or "
        "claim) names the routing_key's remedy home in substance; generic fixes or wrong homes do "
        "NOT count. Judge strictly and literally. Return seeds in the key's order.")


def prosecute_prompt(sub, findings, key, verdict):
    return (
        "A first grader judged a blinded review cell. REFUTE its generous calls. NORMALIZED "
        "FINDINGS:\n" + json.dumps(findings) + f"\nSEED KEY (substrate {sub}):\n"
        + json.dumps(key) + "\nFIRST GRADER:\n" + json.dumps(verdict) + "\n\n"
        "Re-judge every found=true (does the match REALLY satisfy the predicate, right cite, "
        "right substance? default false when thin) and every routed=true (does the remedy REALLY "
        "name the routing_key's home? default false when generic/wrong). found=false stays false; "
        "routed can never be true where found is false. Return the corrected seeds, same order.")


def main():
    graded = HERE / "graded"
    keys = {p.stem: json.loads(p.read_text()) for p in (graded / "keys").glob("*.json")}
    cells = [json.loads(l) for l in open(graded / "verdicts.jsonl")]
    seeded = [c for c in cells if keys.get(c["substrate"])]
    judge = make_judge("grok")
    print(f"re-grading {len(seeded)} seeded cells with {judge.name}", file=sys.stderr)

    def one(c):
        sub, findings, key = c["substrate"], c["findings"], keys[sub_of(c)]
        g = judge.grade(grade_prompt(sub, findings, key), SCHEMA)
        p = judge.grade(prosecute_prompt(sub, findings, key, g), SCHEMA)
        gs = {s["class"]: s for s in g.get("seeds", [])}
        ps = {s["class"]: s for s in p.get("seeds", [])}
        seeds = []
        for k in key:
            cl = k["class"]
            found = bool(gs.get(cl, {}).get("found")) and bool(ps.get(cl, {}).get("found"))
            routed = found and bool(gs.get(cl, {}).get("routed")) and bool(ps.get(cl, {}).get("routed"))
            seeds.append({"class": cl, "found": found, "routed": routed,
                          "matched_claim": "", "why": (ps.get(cl) or gs.get(cl) or {}).get("why", "")})
        return {"bid": c["bid"], "substrate": sub, "findings": findings,
                "seeds": seeds, "nonseed": c.get("nonseed", [])}

    def sub_of(c):
        return c["substrate"]

    out, errs = [], 0
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(one, c): c["bid"] for c in seeded}
        for i, f in enumerate(as_completed(futs), 1):
            try:
                out.append(f.result())
            except Exception as e:
                errs += 1
                print(f"ERR {futs[f]}: {str(e)[:120]}", file=sys.stderr)
            print(f"  [{i}/{len(seeded)}]", file=sys.stderr)
    with open(graded / "verdicts_grok.jsonl", "w") as fh:
        for c in out:
            fh.write(json.dumps(c) + "\n")
    print(f"wrote {len(out)} grok verdicts, {errs} errors; judge calls {judge.calls}, "
          f"notional ${judge.cost_usd():.2f}", file=sys.stderr)
    if errs:
        sys.exit(1)


if __name__ == "__main__":
    main()
