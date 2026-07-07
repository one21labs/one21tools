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


def pair_runs(runs: list) -> list:
    """Pair benchmark runs by (eval_id, run_number) across the two configurations.
    Returns [(without_rate, with_rate), ...]; runs missing their twin are dropped."""
    by_key = {}
    for run in runs:
        key = (run["eval_id"], run["run_number"])
        by_key.setdefault(key, {})[run["configuration"]] = run["result"]["pass_rate"]
    return [(pair["without_skill"], pair["with_skill"])
            for _, pair in sorted(by_key.items())
            if "with_skill" in pair and "without_skill" in pair]


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


def fmt_report(agg: dict, content_chars: int, tok_delta: float) -> str:
    per_1k = (agg["mean_delta"] / content_chars * 1000) if content_chars else 0.0
    lo, hi = agg["win_ci"]
    lines = [
        f"paired runs: {agg['pairs']}  wins: {agg['wins']}  losses: {agg['losses']}  "
        f"ties: {agg['ties']}",
        f"win rate (excl. ties): {lo:.2f}-{hi:.2f} (Wilson 95% CI)",
        f"mean pass-rate delta: {agg['mean_delta']:+.3f}",
        f"skill body: {content_chars} chars; mean run-time token delta: {tok_delta:+.0f}",
        f"VERDICT - delta per 1k chars of context: {per_1k:+.4f}",
    ]
    # The CI is over non-tied pairs (ties carry no direction), so the width guard
    # must count them - 12 pairs with 11 ties is an n=1 interval, not an n=12 one.
    if agg["wins"] + agg["losses"] < 9:
        lines.append("[WARN] under 9 non-tied pairs - the CI is wide; add evals or "
                     "replicates before trusting the verdict")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cost-per-benefit verdict over a skill-creator benchmark.json.")
    parser.add_argument("benchmark_json", type=Path)
    parser.add_argument("--skill", type=Path, required=True,
                        help="skill folder (its SKILL.md body is the measured context cost)")
    parser.add_argument("--fail-under", type=float, default=None,
                        help="exit 1 if the mean pass-rate delta falls below this")
    args = parser.parse_args()

    benchmark = json.loads(args.benchmark_json.read_text(encoding="utf-8"))
    pairs = pair_runs(benchmark.get("runs", []))
    if not pairs:
        print("[FAIL] no paired with_skill/without_skill runs in benchmark.json - "
              "run skill-creator's benchmark mode with both configurations")
        return 1
    body_chars = len(strip_frontmatter(
        (args.skill / "SKILL.md").read_text(encoding="utf-8")))
    agg = aggregate(pairs)
    print(fmt_report(agg, body_chars, token_cost(benchmark.get("run_summary", {}))))
    if args.fail_under is not None and agg["mean_delta"] < args.fail_under:
        print(f"[FAIL] mean delta {agg['mean_delta']:+.3f} < --fail-under {args.fail_under}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
