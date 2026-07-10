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

Also carries an opt-in ADR 0023 check: --check-audit-sample re-derives a benchmark dir's
metadata.json sample_rule and asserts every selected cell's transcript is present (the
silent-drop tripwire) - independent of the verdict computation above.

Usage:
    python eval_verdict.py <benchmark.json> --skill <skill-folder> [--fail-under DELTA]
    python eval_verdict.py --check-audit-sample <benchmark-dir>
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


class AuditSampleError(Exception):
    """metadata.json / sample_rule is missing or malformed. Raised, never swallowed: that
    absence IS the silent-drop condition ADR 0023's completeness check exists to catch."""


def load_sample_rule(benchmark_dir: Path) -> dict:
    """Read and validate metadata.json's sample_rule (ADR 0023 minimal schema):
        {"sample_rule": {"per_group": int, "group_by": [str, ...],
                          "population": [{"file": str, <group_by field>: str, ...}, ...]}}
    `population` lists every raw-output cell that existed before sampling (skill/eval harnesses
    know this population; bench_io.sample_and_archive_raw only sees what sampling left behind).
    Raises AuditSampleError naming exactly what's missing/malformed."""
    meta_path = benchmark_dir / "metadata.json"
    if not meta_path.is_file():
        raise AuditSampleError(
            f"{meta_path} not found - ADR 0023 requires a metadata.json with a machine-readable "
            "sample_rule to audit the raw sample")
    try:
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise AuditSampleError(f"{meta_path} is not valid JSON: {e}") from e
    rule = metadata.get("sample_rule")
    if rule is None:
        raise AuditSampleError(
            f"{meta_path} has no \"sample_rule\" key - ADR 0023 requires one to re-derive and "
            "audit the raw sample")
    for field in ("per_group", "group_by", "population"):
        if field not in rule:
            raise AuditSampleError(f"{meta_path} sample_rule missing required field {field!r}")
    if not isinstance(rule["per_group"], int) or rule["per_group"] < 1:
        raise AuditSampleError(
            f"{meta_path} sample_rule.per_group must be a positive int, got {rule['per_group']!r}")
    if not isinstance(rule["group_by"], list) or not rule["group_by"]:
        raise AuditSampleError(
            f"{meta_path} sample_rule.group_by must be a non-empty list, got {rule['group_by']!r}")
    if not isinstance(rule["population"], list) or not rule["population"]:
        raise AuditSampleError(
            f"{meta_path} sample_rule.population must be a non-empty list, "
            f"got {rule['population']!r}")
    for i, entry in enumerate(rule["population"]):
        if not isinstance(entry, dict) or "file" not in entry:
            raise AuditSampleError(
                f"{meta_path} sample_rule.population[{i}] missing \"file\": {entry!r}")
        for key in rule["group_by"]:
            if key not in entry:
                raise AuditSampleError(
                    f"{meta_path} sample_rule.population[{i}] missing group_by field {key!r}")
    return rule


def expected_sample(rule: dict) -> list:
    """Re-derive which filenames the deterministic sample should have kept: population entries
    sorted by filename, grouped by group_by field values, first per_group kept per group - this
    mirrors bench_io.sample_and_archive_raw's actual algorithm (sorted-filename order, never
    random - ADR 0023), so it re-derives rather than trusts whatever happens to be on disk."""
    groups = {}
    for entry in sorted(rule["population"], key=lambda e: e["file"]):
        key = tuple(entry[k] for k in rule["group_by"])
        groups.setdefault(key, []).append(entry["file"])
    kept = []
    for key in sorted(groups):
        kept.extend(groups[key][:rule["per_group"]])
    return kept


def check_audit_sample(benchmark_dir: Path, outputs_subdir: str = "outputs") -> dict:
    """ADR 0023 silent-drop tripwire: re-derive the expected sample from metadata.json's
    sample_rule and check every selected cell's transcript is present under
    benchmark_dir/outputs_subdir. Raises AuditSampleError if metadata.json/sample_rule is
    missing or malformed (fail loudly - that absence is the silent-drop condition itself).
    Presence gaps are returned, not raised, so a caller can report the full list.

    Returns {"expected": [filenames the rule says must be present],
             "missing": [expected filenames absent from outputs_subdir],
             "archive_expected": bool (population has archived-away cells beyond the sample),
             "archive_present": bool (outputs_subdir/all.tar.gz exists)}."""
    rule = load_sample_rule(benchmark_dir)
    expected = expected_sample(rule)
    outputs_dir = benchmark_dir / outputs_subdir
    missing = [f for f in expected if not (outputs_dir / f).is_file()]
    return {
        "expected": expected,
        "missing": missing,
        "archive_expected": len(rule["population"]) > len(expected),
        "archive_present": (outputs_dir / "all.tar.gz").is_file(),
    }


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


def report_audit_sample(report: dict) -> str:
    """Render a check_audit_sample() report as CLI output text (pure - testable without IO)."""
    lines = []
    if report["missing"]:
        lines.append(
            f"[FAIL] {len(report['missing'])}/{len(report['expected'])} sampled transcripts "
            "missing - silent-drop tripwire triggered (ADR 0023):")
        lines.extend(f"  {f}" for f in report["missing"])
    else:
        lines.append(f"[OK] {len(report['expected'])} sampled transcripts present")
    if report["archive_expected"]:
        if report["archive_present"]:
            lines.append("[OK] all.tar.gz present")
        else:
            lines.append("[FAIL] all.tar.gz missing - archived-away cells are unrecoverable")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cost-per-benefit verdict over a skill-creator benchmark.json.")
    parser.add_argument("benchmark_json", type=Path, nargs="?",
                        help="skill-creator benchmark.json (omit with --check-audit-sample)")
    parser.add_argument("--skill", type=Path, default=None,
                        help="skill folder (its SKILL.md body is the default context cost); "
                             "required unless --check-audit-sample")
    parser.add_argument("--include-references", action="store_true",
                        help="charge the delta against SKILL.md body + all references/*.md "
                             "(upper bound: assumes every reference loaded) - ADR 0019")
    parser.add_argument("--loaded-chars", type=int, default=None,
                        help="exact measured chars loaded per with_skill run; overrides the "
                             "body/references estimate (ADR 0019)")
    parser.add_argument("--fail-under", type=float, default=None,
                        help="exit 1 if the mean pass-rate delta falls below this")
    parser.add_argument("--check-audit-sample", type=Path, default=None, metavar="BENCHMARK_DIR",
                        help="ADR 0023 silent-drop tripwire: re-derive BENCHMARK_DIR/metadata.json's "
                             "sample_rule and assert every selected cell's transcript is present "
                             "under BENCHMARK_DIR/outputs; prints a report and exits, skipping the "
                             "verdict computation")
    args = parser.parse_args()

    if args.check_audit_sample is not None:
        try:
            report = check_audit_sample(args.check_audit_sample)
        except AuditSampleError as e:
            print(f"[FAIL] {e}")
            return 1
        print(report_audit_sample(report))
        return 1 if report["missing"] or (report["archive_expected"]
                                           and not report["archive_present"]) else 0

    if args.benchmark_json is None or args.skill is None:
        parser.error("benchmark_json and --skill are required unless --check-audit-sample is given")

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
