#!/usr/bin/env python3
"""Skill-expectation overlap (ADR 0095 decision 4, issue #317 candidate 2), per eval-set origin.

For each skill: n-gram containment of its expectation text (expectations + expected_output) in
its OWN corpus (SKILL.md + references/), minus the mean containment in the other three skills'
corpora (controls generic domain phrasing). Reported separately for the original evals (ids 1-6,
authored with the skill in view), the 12-Oct blind additions (7-10) and this batch's (11+), so
the leakage the blind process was meant to remove is visible as a number, not asserted.

A FLOOR, not the coupling: paraphrased house doctrine is invisible to n-grams (#317 comment).
Writes overlap.json.
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SKILLS = ("building-skills", "code-standards", "engineering-principles", "optimizing-context")
MEASURED = ("building-skills", "code-standards", "optimizing-context")  # this batch's evals
BLIND_FROM_ID = 7
NEW_FROM_ID = 11


def grams(text, n):
    w = re.findall(r"[a-z0-9]+", text.lower())
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


def corpus(skill):
    d = REPO / "skills" / skill
    files = [d / "SKILL.md", *sorted((d / "references").glob("*.md"))]
    return " ".join(p.read_text(encoding="utf-8") for p in files if p.exists())


def containment(exp_grams, corp_grams):
    return len(exp_grams & corp_grams) / len(exp_grams) if exp_grams else 0.0


def main():
    corp = {s: corpus(s) for s in SKILLS}
    out = {}
    for n in (3, 4):
        cg = {s: grams(corp[s], n) for s in SKILLS}
        for s in MEASURED:
            evals = json.loads((HERE / "evals" / f"{s}.json").read_text(encoding="utf-8"))["evals"]
            for origin, keep in (("original", lambda e: e["id"] < BLIND_FROM_ID),
                                 ("blind_12oct", lambda e: BLIND_FROM_ID <= e["id"] < NEW_FROM_ID),
                                 ("blind_new", lambda e: e["id"] >= NEW_FROM_ID)):
                text = " ".join(" ".join(e["expectations"]) + " " + e.get("expected_output", "")
                                for e in evals if keep(e))
                eg = grams(text, n)
                own = containment(eg, cg[s])
                cross = sum(containment(eg, cg[o]) for o in SKILLS if o != s) / (len(SKILLS) - 1)
                out.setdefault(s, {}).setdefault(origin, {})[f"{n}gram"] = {
                    "own": round(own, 4), "cross_baseline": round(cross, 4),
                    "excess": round(own - cross, 4)}
    (HERE / "overlap.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    for s, by in out.items():
        for origin, v in by.items():
            t = v["3gram"]
            print(f"{s:24s} {origin:8s} trigram own={t['own']:.3f} cross={t['cross_baseline']:.3f} "
                  f"excess={t['excess']:+.3f}")


if __name__ == "__main__":
    main()
