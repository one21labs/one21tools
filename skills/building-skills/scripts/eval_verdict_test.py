#!/usr/bin/env python3
"""
eval_verdict_test.py -- decision-logic test for eval_verdict.py (ADR 0013; "never ship a
process-gating script without a test of its decision logic"). Zero-dependency: stdlib unittest.
Run: python eval_verdict_test.py  (or: python -m unittest eval_verdict_test) from this dir.

Covers the pure layer only (pairing, Wilson CI, aggregation, token cost, report shape);
main() is a thin IO wrapper over these.
"""
import unittest

from eval_verdict import (
    strip_frontmatter,
    pair_runs,
    wilson_ci,
    aggregate,
    token_cost,
    fmt_report,
)


def run(eval_id, run_number, configuration, pass_rate):
    """A minimal benchmark.json runs[] entry (schema: skill-creator references/schemas.md)."""
    return {"eval_id": eval_id, "run_number": run_number,
            "configuration": configuration, "result": {"pass_rate": pass_rate}}


class PairRuns(unittest.TestCase):
    def test_pairs_by_eval_and_run_number(self):
        pairs = pair_runs([run(1, 1, "without_skill", 0.4), run(1, 1, "with_skill", 0.8),
                           run(2, 1, "without_skill", 0.5), run(2, 1, "with_skill", 0.5)])
        self.assertEqual(pairs, [(0.4, 0.8), (0.5, 0.5)])

    def test_run_missing_its_twin_is_dropped(self):
        pairs = pair_runs([run(1, 1, "with_skill", 0.9),
                           run(2, 1, "without_skill", 0.3), run(2, 1, "with_skill", 0.6)])
        self.assertEqual(pairs, [(0.3, 0.6)])

    def test_empty_runs_yield_no_pairs(self):
        self.assertEqual(pair_runs([]), [])


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


class Report(unittest.TestCase):
    def test_verdict_is_delta_per_1k_chars(self):
        agg = aggregate([(0.4, 0.8)] * 10)
        report = fmt_report(agg, content_chars=4000, tok_delta=1700.0)
        self.assertIn("+0.1000", report)  # 0.4 delta / 4000 chars * 1000
        self.assertIn("Wilson 95% CI", report)

    def test_small_sample_carries_a_warning(self):
        report = fmt_report(aggregate([(0.4, 0.8)] * 3), content_chars=4000, tok_delta=0.0)
        self.assertIn("[WARN]", report)
        big = fmt_report(aggregate([(0.4, 0.8)] * 12), content_chars=4000, tok_delta=0.0)
        self.assertNotIn("[WARN]", big)

    def test_warning_counts_non_tied_pairs_not_total(self):
        # 12 pairs but 11 ties -> the CI is over n=1; the guard must fire.
        pairs = [(0.4, 0.8)] + [(0.5, 0.5)] * 11
        report = fmt_report(aggregate(pairs), content_chars=4000, tok_delta=0.0)
        self.assertIn("[WARN]", report)

    def test_zero_content_chars_does_not_divide_by_zero(self):
        report = fmt_report(aggregate([(0.4, 0.8)]), content_chars=0, tok_delta=0.0)
        self.assertIn("+0.0000", report)


class StripFrontmatter(unittest.TestCase):
    def test_strips_the_yaml_fence(self):
        self.assertEqual(strip_frontmatter("---\nname: x\n---\nBody here"), "Body here")

    def test_no_frontmatter_returns_the_text(self):
        self.assertEqual(strip_frontmatter("Body only"), "Body only")


if __name__ == "__main__":
    unittest.main()
