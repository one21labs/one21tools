#!/usr/bin/env python3
"""Skill-expectation overlap (ADR 0101 decision 1), after the battery is frozen.

N-gram containment of the expectation text (expectations + expected_output) in the frozen
treatment, minus the mean containment in the repo's other skills (controls generic phrasing).
Reported separately for the blind-authored expectations and the one universal expectation
(metadata.json evals.universal_expectation), which was written with the skill in view. Method as
2026-10-12-g8-shortfall/overlap.py, with this batch's one measured skill.

A FLOOR, not the coupling: paraphrased doctrine is invisible to n-grams (#317). Writes overlap.json.
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SKILL = "control-narratives"


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
    universal = json.loads((HERE / "metadata.json").read_text(encoding="utf-8"))["evals"]["universal_expectation"]
    evals = json.loads((HERE / "evals" / f"{SKILL}.json").read_text(encoding="utf-8"))["evals"]
    controls = sorted(p.parent.name for p in (REPO / "skills").glob("*/SKILL.md") if p.parent.name != SKILL)
    texts = {"blind": " ".join(" ".join(x for x in e["expectations"] if x != universal) + " " +
                               e.get("expected_output", "") for e in evals),
             "universal": universal}
    out = {"controls": controls}
    treatment = (HERE / "treatments" / f"{SKILL}.txt").read_text(encoding="utf-8")  # as measured
    for n in (3, 4):
        own = grams(treatment, n)
        ctl = [grams(corpus(c), n) for c in controls]
        for origin, text in texts.items():
            eg = grams(text, n)
            cross = sum(containment(eg, c) for c in ctl) / len(ctl)
            out.setdefault(origin, {})[f"{n}gram"] = {
                "own": round(containment(eg, own), 4), "cross_baseline": round(cross, 4),
                "excess": round(containment(eg, own) - cross, 4)}
    (HERE / "overlap.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    for origin in texts:
        t = out[origin]["3gram"]
        print(f"{origin:10s} trigram own={t['own']:.3f} cross={t['cross_baseline']:.3f} "
              f"excess={t['excess']:+.3f}")


if __name__ == "__main__":
    main()
