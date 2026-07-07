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

from eval_verdict import (
    strip_frontmatter,
    body_chars,
    reference_chars,
    denominator,
    pairs_by_eval,
    pair_runs,
    eval_level,
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


if __name__ == "__main__":
    unittest.main()
