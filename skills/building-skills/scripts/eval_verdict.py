#!/usr/bin/env python3
"""
eval_verdict.py - cost-per-benefit verdict over a skill-creator benchmark.json (ADR 0013).

Execution is DELEGATED to Anthropic's skill-creator harness (benchmark mode: paired
with_skill/without_skill runs, graded assertions, aggregate_benchmark.py). This script owns
only the thin layer upstream lacks: pairs each eval's runs across the two configurations,
computes the win rate with a Wilson 95% CI, the mean pass-rate delta, and the verdict metric
- mean delta per 1,000 chars of SKILL.md body (does the content EARN its context cost?).

NOT a CI gate (upstream runs are non-deterministic; this only post-processes their output).
Decision logic is pure and unit-tested in eval_verdict_test.py; main() is the IO wrapper.

Usage:
    python eval_verdict.py <benchmark.json> --skill <skill-folder> [--fail-under DELTA]
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path


def strip_frontmatter(text: str) -> str:
    """SKILL.md body - the injected content whose value is being measured."""
    match = re.match(r"^---\n.*?\n---\n?", text, re.DOTALL)
    return text[match.end():].strip() if match else text.strip()


def body_chars(skill_path: Path) -> int:
    """Chars of SKILL.md body - the always-loaded context cost."""
    return len(strip_frontmatter((skill_path / "SKILL.md").read_text(encoding="utf-8")))


def reference_chars(skill_path: Path) -> int:
    """Total chars of the skill's references/*.md - the on-demand surface a with_skill run
    may ALSO load. Uncounted by the body-only denominator, so reference-heavy skills are
    otherwise flattered (ADR 0019). 0 when there is no references/ dir."""
    refs = skill_path / "references"
    if not refs.is_dir():
        return 0
    return sum(len(f.read_text(encoding="utf-8")) for f in sorted(refs.glob("*.md")))


def denominator(skill_path: Path, loaded_chars, include_references):
    """The context cost the delta is charged against (ADR 0019). Precedence: an explicit
    measured --loaded-chars wins; else body + references when --include-references (an UPPER
    bound - assumes every reference loaded); else body-only (the always-on cost). Returns
    (chars, basis-label)."""
    if loaded_chars is not None:
        return loaded_chars, "measured loaded chars"
    if include_references:
        return body_chars(skill_path) + reference_chars(skill_path), "SKILL.md body + references"
    return body_chars(skill_path), "SKILL.md body"


def pairs_by_eval(runs: list) -> dict:
    """Pair benchmark runs by (eval_id, run_number) across the two configurations,
    grouped by eval: {eval_id: [(without_rate, with_rate), ...]}. Replicates of one
    eval are correlated (same task), so eval_id is the clustering unit (ADR 0019).
    Runs missing their twin are dropped."""
    by_key = {}
    for run in runs:
        key = (run["eval_id"], run["run_number"])
        by_key.setdefault(key, {})[run["configuration"]] = run["result"]["pass_rate"]
    grouped = {}
    for (eval_id, _), pair in sorted(by_key.items()):
        if "with_skill" in pair and "without_skill" in pair:
            grouped.setdefault(eval_id, []).append(
                (pair["without_skill"], pair["with_skill"]))
    return grouped


def pair_runs(runs: list) -> list:
    """Flat [(without_rate, with_rate), ...] across all evals (pair-level detail)."""
    return [p for pairs in pairs_by_eval(runs).values() for p in pairs]


def eval_level(by_eval: dict) -> dict:
    """Cluster replicates per eval (ADR 0019): an eval's mean delta > 0 is a win,
    < 0 a loss, 0 a tie. The headline Wilson CI is over non-tied EVALS - replicates
    within an eval are correlated and must not inflate n."""
    wins = losses = ties = 0
    for pairs in by_eval.values():
        mean_delta = sum(wi - wo for wo, wi in pairs) / len(pairs)
        if mean_delta > 0:
            wins += 1
        elif mean_delta < 0:
            losses += 1
        else:
            ties += 1
    return {"evals": len(by_eval), "wins": wins, "losses": losses, "ties": ties,
            "win_ci": wilson_ci(wins, wins + losses)}


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple:
    """Wilson 95% score interval for k successes in n trials. n=0 -> (0.0, 1.0) (no evidence)."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = (z / denom) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, center - margin), min(1.0, center + margin))


def aggregate(pairs: list) -> dict:
    """pairs = [(without_rate, with_rate), ...]. Wins = with_skill strictly better;
    the Wilson CI is over wins among non-ties (ties carry no direction)."""
    wins = sum(1 for wo, wi in pairs if wi > wo)
    losses = sum(1 for wo, wi in pairs if wi < wo)
    ties = len(pairs) - wins - losses
    deltas = [wi - wo for wo, wi in pairs]
    mean_delta = sum(deltas) / len(deltas) if deltas else 0.0
    return {"pairs": len(pairs), "wins": wins, "losses": losses, "ties": ties,
            "mean_delta": mean_delta, "win_ci": wilson_ci(wins, wins + losses)}


def token_cost(run_summary: dict) -> float:
    """Mean token overhead of running WITH the skill (run-time cost, beside the context cost).
    Returns 0.0 when the summary lacks token stats."""
    try:
        return (run_summary["with_skill"]["tokens"]["mean"]
                - run_summary["without_skill"]["tokens"]["mean"])
    except (KeyError, TypeError):
        return 0.0


def fmt_report(agg: dict, evals: dict, content_chars: int, tok_delta: float,
               basis: str = "SKILL.md body") -> str:
    per_1k = (agg["mean_delta"] / content_chars * 1000) if content_chars else 0.0
    lo, hi = evals["win_ci"]
    lines = [
        f"paired runs: {agg['pairs']}  wins: {agg['wins']}  losses: {agg['losses']}  "
        f"ties: {agg['ties']}",
        f"evals: {evals['evals']}  wins: {evals['wins']}  losses: {evals['losses']}  "
        f"ties: {evals['ties']}",
        f"win rate (eval-clustered, excl. ties): {lo:.2f}-{hi:.2f} (Wilson 95% CI)",
        f"mean pass-rate delta: {agg['mean_delta']:+.3f}",
        f"context cost: {content_chars} chars ({basis}); "
        f"mean run-time token delta: {tok_delta:+.0f}",
        f"VERDICT - delta per 1k chars of context: {per_1k:+.4f}",
    ]
    # The headline CI is over non-tied EVALS (replicates are correlated - ADR 0019),
    # so the width guard counts them; 4 matches the authoring floor of 4+ cases.
    if evals["wins"] + evals["losses"] < 4:
        lines.append("[WARN] under 4 non-tied evals - the CI is wide; add evals "
                     "before trusting the verdict")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cost-per-benefit verdict over a skill-creator benchmark.json.")
    parser.add_argument("benchmark_json", type=Path)
    parser.add_argument("--skill", type=Path, required=True,
                        help="skill folder (its SKILL.md body is the default context cost)")
    parser.add_argument("--include-references", action="store_true",
                        help="charge the delta against SKILL.md body + all references/*.md "
                             "(upper bound: assumes every reference loaded) - ADR 0019")
    parser.add_argument("--loaded-chars", type=int, default=None,
                        help="exact measured chars loaded per with_skill run; overrides the "
                             "body/references estimate (ADR 0019)")
    parser.add_argument("--fail-under", type=float, default=None,
                        help="exit 1 if the mean pass-rate delta falls below this")
    args = parser.parse_args()

    benchmark = json.loads(args.benchmark_json.read_text(encoding="utf-8"))
    by_eval = pairs_by_eval(benchmark.get("runs", []))
    pairs = [p for ps in by_eval.values() for p in ps]
    if not pairs:
        print("[FAIL] no paired with_skill/without_skill runs in benchmark.json - "
              "run skill-creator's benchmark mode with both configurations")
        return 1
    chars, basis = denominator(args.skill, args.loaded_chars, args.include_references)
    agg = aggregate(pairs)
    print(fmt_report(agg, eval_level(by_eval), chars,
                     token_cost(benchmark.get("run_summary", {})), basis))
    if args.fail_under is not None and agg["mean_delta"] < args.fail_under:
        print(f"[FAIL] mean delta {agg['mean_delta']:+.3f} < --fail-under {args.fail_under}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
