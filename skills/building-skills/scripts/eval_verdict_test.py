#!/usr/bin/env python3
"""
eval_verdict_test.py -- decision-logic test for eval_verdict.py (ADR 0013; "never ship a
process-gating script without a test of its decision logic"). Zero-dependency: stdlib unittest.
Run: python eval_verdict_test.py  (or: python -m unittest eval_verdict_test) from this dir.

Covers the pure layer only (pairing, Wilson CI, aggregation, token cost, report shape);
main() is a thin IO wrapper over these.
"""
import unittest

import tempfile
from pathlib import Path

import json

from eval_verdict import (
    strip_frontmatter,
    body_chars,
    reference_chars,
    denominator,
    pairs_by_eval,
    eval_level,
    wilson_ci,
    aggregate,
    token_cost,
    fmt_report,
    AuditSampleError,
    load_sample_rule,
    expected_sample,
    check_audit_sample,
    report_audit_sample,
)


def run(eval_id, run_number, configuration, pass_rate):
    """A minimal benchmark.json runs[] entry (schema: skill-creator references/schemas.md)."""
    return {"eval_id": eval_id, "run_number": run_number,
            "configuration": configuration, "result": {"pass_rate": pass_rate}}


class EvalLevel(unittest.TestCase):
    """ADR 0019: replicates within an eval are correlated -> cluster per eval."""

    def test_groups_pairs_by_eval(self):
        grouped = pairs_by_eval([run(1, 1, "without_skill", 0.4), run(1, 1, "with_skill", 0.8),
                                 run(1, 2, "without_skill", 0.5), run(1, 2, "with_skill", 0.9),
                                 run(2, 1, "without_skill", 0.5), run(2, 1, "with_skill", 0.5)])
        self.assertEqual(grouped, {1: [(0.4, 0.8), (0.5, 0.9)], 2: [(0.5, 0.5)]})

    def test_eval_win_is_the_mean_delta_direction(self):
        # eval 1: mean delta +0.2 -> win; eval 2: -0.1 -> loss; eval 3: 0 -> tie.
        ev = eval_level({1: [(0.4, 0.8), (0.6, 0.6)], 2: [(0.5, 0.4)], 3: [(0.7, 0.7)]})
        self.assertEqual((ev["wins"], ev["losses"], ev["ties"]), (1, 1, 1))
        self.assertEqual(ev["evals"], 3)

    def test_headline_ci_is_over_non_tied_evals(self):
        # 12 pairs but only 2 evals (1 win, 1 tie) -> CI over n=1, not n=12.
        ev = eval_level({1: [(0.4, 0.8)] * 6, 2: [(0.5, 0.5)] * 6})
        self.assertEqual(ev["win_ci"], wilson_ci(1, 1))

    def test_replicates_cannot_inflate_the_headline_n(self):
        # One winning eval with 100 replicates is still n=1 evidence.
        many = eval_level({1: [(0.4, 0.8)] * 100})
        few = eval_level({1: [(0.4, 0.8)]})
        self.assertEqual(many["win_ci"], few["win_ci"])


class WilsonCI(unittest.TestCase):
    def test_zero_trials_is_the_ignorant_interval(self):
        self.assertEqual(wilson_ci(0, 0), (0.0, 1.0))

    def test_interval_brackets_the_point_estimate(self):
        lo, hi = wilson_ci(8, 10)
        self.assertLess(lo, 0.8)
        self.assertGreater(hi, 0.8)
        self.assertGreaterEqual(lo, 0.0)
        self.assertLessEqual(hi, 1.0)

    def test_more_trials_narrow_the_interval(self):
        lo_s, hi_s = wilson_ci(8, 10)
        lo_l, hi_l = wilson_ci(80, 100)
        self.assertLess(hi_l - lo_l, hi_s - lo_s)


class Aggregate(unittest.TestCase):
    def test_win_loss_tie_and_mean_delta(self):
        agg = aggregate([(0.4, 0.8), (0.6, 0.5), (0.5, 0.5)])
        self.assertEqual((agg["wins"], agg["losses"], agg["ties"]), (1, 1, 1))
        self.assertAlmostEqual(agg["mean_delta"], (0.4 - 0.1 + 0.0) / 3)

    def test_ties_are_excluded_from_the_win_ci(self):
        # 1 win, 0 losses, 2 ties -> CI over n=1, not n=3.
        agg = aggregate([(0.4, 0.8), (0.5, 0.5), (0.7, 0.7)])
        self.assertEqual(agg["win_ci"], wilson_ci(1, 1))


class TokenCost(unittest.TestCase):
    def test_mean_token_delta(self):
        summary = {"with_skill": {"tokens": {"mean": 3800}},
                   "without_skill": {"tokens": {"mean": 2100}}}
        self.assertEqual(token_cost(summary), 1700)

    def test_missing_token_stats_read_as_zero(self):
        self.assertEqual(token_cost({}), 0.0)
        self.assertEqual(token_cost({"with_skill": {}}), 0.0)


def report_for(by_eval, content_chars=4000, tok_delta=0.0):
    pairs = [p for ps in by_eval.values() for p in ps]
    return fmt_report(aggregate(pairs), eval_level(by_eval), content_chars, tok_delta)


class Report(unittest.TestCase):
    WIN = [(0.4, 0.8)] * 3  # one eval's replicates, clear win

    def test_verdict_is_delta_per_1k_chars(self):
        report = report_for({i: [(0.4, 0.8)] for i in range(10)}, content_chars=4000,
                            tok_delta=1700.0)
        self.assertIn("+0.1000", report)  # 0.4 delta / 4000 chars * 1000
        self.assertIn("Wilson 95% CI", report)

    def test_headline_ci_is_eval_clustered(self):
        # 4 evals x 3 replicates: eval-level CI (n=4), not pair-level (n=12).
        report = report_for({i: self.WIN for i in range(4)})
        lo, hi = eval_level({i: self.WIN for i in range(4)})["win_ci"]
        self.assertIn(f"win rate (eval-clustered, excl. ties): {lo:.2f}-{hi:.2f}", report)

    def test_warning_keys_on_non_tied_evals(self):
        # 3 winning evals (9 pairs) -> under the 4-eval floor -> warn.
        small = report_for({i: self.WIN for i in range(3)})
        self.assertIn("[WARN] under 4 non-tied evals", small)
        # 4 winning evals -> at the floor -> no warning.
        ok = report_for({i: self.WIN for i in range(4)})
        self.assertNotIn("[WARN]", ok)
        # Ties don't count: 4 evals but 3 tie -> warn.
        tied = report_for({1: self.WIN, 2: [(0.5, 0.5)], 3: [(0.5, 0.5)], 4: [(0.5, 0.5)]})
        self.assertIn("[WARN]", tied)

    def test_pair_level_detail_is_kept(self):
        report = report_for({i: self.WIN for i in range(4)})
        self.assertIn("paired runs: 12", report)
        self.assertIn("evals: 4", report)

    def test_zero_content_chars_does_not_divide_by_zero(self):
        report = report_for({1: [(0.4, 0.8)]}, content_chars=0)
        self.assertIn("+0.0000", report)


class StripFrontmatter(unittest.TestCase):
    def test_strips_the_yaml_fence(self):
        self.assertEqual(strip_frontmatter("---\nname: x\n---\nBody here"), "Body here")

    def test_no_frontmatter_returns_the_text(self):
        self.assertEqual(strip_frontmatter("Body only"), "Body only")


class Denominator(unittest.TestCase):
    """ADR 0019: the delta is charged against what a with_skill run actually loads,
    not SKILL.md body alone (reference-heavy skills were otherwise flattered)."""

    def _skill(self, tmp, body="Body text.", refs=None):
        d = Path(tmp)
        (d / "SKILL.md").write_text(f"---\nname: s\n---\n{body}", encoding="utf-8")
        if refs:
            (d / "references").mkdir()
            for name, text in refs.items():
                (d / "references" / name).write_text(text, encoding="utf-8")
        return d

    def test_body_only_is_the_default(self):
        with tempfile.TemporaryDirectory() as t:
            d = self._skill(t, body="12345")
            chars, basis = denominator(d, None, False)
            self.assertEqual((chars, basis), (5, "SKILL.md body"))

    def test_include_references_adds_reference_chars(self):
        with tempfile.TemporaryDirectory() as t:
            d = self._skill(t, body="12345", refs={"a.md": "xxx", "b.md": "yy"})
            self.assertEqual(reference_chars(d), 5)
            chars, basis = denominator(d, None, True)
            self.assertEqual((chars, basis), (10, "SKILL.md body + references"))

    def test_no_references_dir_is_zero(self):
        with tempfile.TemporaryDirectory() as t:
            d = self._skill(t, body="12345")
            self.assertEqual(reference_chars(d), 0)
            self.assertEqual(denominator(d, None, True)[0], 5)

    def test_explicit_loaded_chars_wins(self):
        with tempfile.TemporaryDirectory() as t:
            d = self._skill(t, body="12345", refs={"a.md": "xxxxx"})
            chars, basis = denominator(d, 999, True)
            self.assertEqual((chars, basis), (999, "measured loaded chars"))

    def test_report_labels_the_basis(self):
        report = report_for({i: [(0.4, 0.8)] for i in range(4)}, content_chars=4000)
        self.assertIn("(SKILL.md body)", report)
        ref_report = fmt_report(aggregate([(0.4, 0.8)] * 4),
                                eval_level({i: [(0.4, 0.8)] for i in range(4)}),
                                4000, 0.0, basis="SKILL.md body + references")
        self.assertIn("(SKILL.md body + references)", ref_report)


# ADR 0023: eval_verdict.py re-derives a benchmark dir's audit sample_rule and asserts every
# selected cell's transcript is present - the silent-drop tripwire. Fixtures are hermetic tmp
# dirs (never the real benchmarks/ trees, none of which carry sample_rule yet).
RULE = {
    "per_group": 2,
    "group_by": ["skill", "arm"],
    "population": [
        {"file": "s.1.with.1.txt", "skill": "s", "arm": "with"},
        {"file": "s.1.with.2.txt", "skill": "s", "arm": "with"},
        {"file": "s.1.with.3.txt", "skill": "s", "arm": "with"},
        {"file": "s.1.without.1.txt", "skill": "s", "arm": "without"},
        {"file": "s.1.without.2.txt", "skill": "s", "arm": "without"},
    ],
}


def _benchmark_dir(tmp, sample_rule=None, metadata=None, outputs=(),
                    write_archive=False, write_metadata=True):
    """Build a hermetic benchmark-dir fixture: metadata.json (with sample_rule unless
    write_metadata=False) + outputs/ populated with the given filenames."""
    d = Path(tmp)
    if write_metadata:
        meta = dict(metadata) if metadata is not None else {}
        if sample_rule is not None:
            meta["sample_rule"] = sample_rule
        (d / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
    outdir = d / "outputs"
    outdir.mkdir()
    for name in outputs:
        (outdir / name).write_text("raw transcript text\n", encoding="utf-8")
    if write_archive:
        (outdir / "all.tar.gz").write_bytes(b"")
    return d


class LoadSampleRule(unittest.TestCase):
    """Absence of metadata.json/sample_rule IS the silent-drop condition ADR 0023 guards -
    load_sample_rule must fail loudly, never skip the check."""

    def test_missing_metadata_json_raises(self):
        with tempfile.TemporaryDirectory() as t:
            d = _benchmark_dir(t, write_metadata=False)
            with self.assertRaises(AuditSampleError) as cm:
                load_sample_rule(d)
            self.assertIn("metadata.json", str(cm.exception))

    def test_malformed_json_raises(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            (d / "metadata.json").write_text("{not json", encoding="utf-8")
            (d / "outputs").mkdir()
            with self.assertRaises(AuditSampleError):
                load_sample_rule(d)

    def test_missing_sample_rule_key_raises(self):
        with tempfile.TemporaryDirectory() as t:
            d = _benchmark_dir(t, sample_rule=None, metadata={"date": "2026-07-09"})
            with self.assertRaises(AuditSampleError) as cm:
                load_sample_rule(d)
            self.assertIn("sample_rule", str(cm.exception))

    def test_missing_required_field_raises(self):
        with tempfile.TemporaryDirectory() as t:
            bad = {"group_by": ["skill"], "population": RULE["population"]}
            d = _benchmark_dir(t, sample_rule=bad)
            with self.assertRaises(AuditSampleError) as cm:
                load_sample_rule(d)
            self.assertIn("per_group", str(cm.exception))

    def test_non_positive_per_group_raises(self):
        with tempfile.TemporaryDirectory() as t:
            bad = dict(RULE, per_group=0)
            d = _benchmark_dir(t, sample_rule=bad)
            with self.assertRaises(AuditSampleError):
                load_sample_rule(d)

    def test_empty_group_by_raises(self):
        with tempfile.TemporaryDirectory() as t:
            bad = dict(RULE, group_by=[])
            d = _benchmark_dir(t, sample_rule=bad)
            with self.assertRaises(AuditSampleError):
                load_sample_rule(d)

    def test_population_entry_missing_file_raises(self):
        with tempfile.TemporaryDirectory() as t:
            bad = dict(RULE, population=[{"skill": "s", "arm": "with"}])
            d = _benchmark_dir(t, sample_rule=bad)
            with self.assertRaises(AuditSampleError) as cm:
                load_sample_rule(d)
            self.assertIn("population[0]", str(cm.exception))

    def test_population_entry_missing_group_by_field_raises(self):
        with tempfile.TemporaryDirectory() as t:
            bad = dict(RULE, population=[{"file": "s.1.with.1.txt", "skill": "s"}])
            d = _benchmark_dir(t, sample_rule=bad)
            with self.assertRaises(AuditSampleError) as cm:
                load_sample_rule(d)
            self.assertIn("arm", str(cm.exception))

    def test_valid_rule_loads(self):
        with tempfile.TemporaryDirectory() as t:
            d = _benchmark_dir(t, sample_rule=RULE)
            self.assertEqual(load_sample_rule(d), RULE)


class ExpectedSample(unittest.TestCase):
    """Re-derivation mirrors bench_io.sample_and_archive_raw: sorted-filename order per group,
    first per_group kept - never a random draw (ADR 0023)."""

    def test_keeps_first_per_group_in_sorted_order(self):
        self.assertEqual(
            expected_sample(RULE),
            ["s.1.with.1.txt", "s.1.with.2.txt", "s.1.without.1.txt", "s.1.without.2.txt"])

    def test_per_group_larger_than_group_keeps_all(self):
        rule = dict(RULE, per_group=10)
        self.assertEqual(len(expected_sample(rule)), len(RULE["population"]))


class CheckAuditSample(unittest.TestCase):
    def test_all_expected_transcripts_present(self):
        with tempfile.TemporaryDirectory() as t:
            d = _benchmark_dir(t, sample_rule=RULE, outputs=[
                "s.1.with.1.txt", "s.1.with.2.txt", "s.1.without.1.txt", "s.1.without.2.txt"])
            report = check_audit_sample(d)
            self.assertEqual(report["missing"], [])

    def test_missing_transcript_is_the_silent_drop_tripwire(self):
        with tempfile.TemporaryDirectory() as t:
            # s.1.with.2.txt (part of the expected sample) never landed under outputs/.
            d = _benchmark_dir(t, sample_rule=RULE, outputs=[
                "s.1.with.1.txt", "s.1.without.1.txt", "s.1.without.2.txt"])
            report = check_audit_sample(d)
            self.assertEqual(report["missing"], ["s.1.with.2.txt"])

    def test_absent_metadata_fails_loudly_not_silently(self):
        with tempfile.TemporaryDirectory() as t:
            d = _benchmark_dir(t, write_metadata=False, outputs=["s.1.with.1.txt"])
            with self.assertRaises(AuditSampleError):
                check_audit_sample(d)

    def test_archive_expected_when_population_exceeds_the_sample(self):
        with tempfile.TemporaryDirectory() as t:
            # 3 "with" cells, per_group=2 -> 1 archived away -> the tar is load-bearing.
            d = _benchmark_dir(t, sample_rule=RULE, outputs=[
                "s.1.with.1.txt", "s.1.with.2.txt", "s.1.without.1.txt", "s.1.without.2.txt"],
                write_archive=True)
            report = check_audit_sample(d)
            self.assertTrue(report["archive_expected"])
            self.assertTrue(report["archive_present"])

    def test_archive_not_expected_when_sample_covers_the_population(self):
        with tempfile.TemporaryDirectory() as t:
            rule = dict(RULE, population=[e for e in RULE["population"] if e["arm"] == "without"])
            d = _benchmark_dir(t, sample_rule=rule,
                                outputs=["s.1.without.1.txt", "s.1.without.2.txt"])
            report = check_audit_sample(d)
            self.assertFalse(report["archive_expected"])

    def test_archive_missing_is_flagged(self):
        with tempfile.TemporaryDirectory() as t:
            d = _benchmark_dir(t, sample_rule=RULE, outputs=[
                "s.1.with.1.txt", "s.1.with.2.txt", "s.1.without.1.txt", "s.1.without.2.txt"],
                write_archive=False)
            report = check_audit_sample(d)
            self.assertTrue(report["archive_expected"])
            self.assertFalse(report["archive_present"])


class ReportAuditSample(unittest.TestCase):
    def test_ok_when_nothing_missing_and_no_archive_expected(self):
        report = {"expected": ["a.txt", "b.txt"], "missing": [],
                   "archive_expected": False, "archive_present": False}
        out = report_audit_sample(report)
        self.assertIn("[OK]", out)
        self.assertNotIn("[FAIL]", out)

    def test_fail_lists_each_missing_file(self):
        report = {"expected": ["a.txt", "b.txt"], "missing": ["b.txt"],
                   "archive_expected": False, "archive_present": False}
        out = report_audit_sample(report)
        self.assertIn("[FAIL]", out)
        self.assertIn("b.txt", out)

    def test_missing_archive_is_flagged_even_when_transcripts_are_all_present(self):
        report = {"expected": ["a.txt"], "missing": [],
                   "archive_expected": True, "archive_present": False}
        out = report_audit_sample(report)
        self.assertIn("[OK]", out)  # transcripts fine
        self.assertIn("[FAIL] all.tar.gz missing", out)


if __name__ == "__main__":
    unittest.main()
