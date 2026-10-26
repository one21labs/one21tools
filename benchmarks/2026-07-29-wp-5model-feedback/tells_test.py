#!/usr/bin/env python3
"""Decision-logic tests for tells.py (house rule: no process-gating script without them).

The gate this protects: if a tell survives into a graded artifact the judge is not blind, so the
load-bearing assertion is `residual_after_strip == 0` on realistic treatment-arm text.
"""
import unittest

from tells import detect_tells, strip_tells, strip_report

# Realistic treatment-arm opening: the skill body mandates exactly this announcement.
TREATMENT = """I'm using the writing-plans skill to create the implementation plan.

Here is my feedback on your plan.

## 1. P1 is the load-bearing decision

The plan states 18 commits since 19-Jul edited measured skills with no re-measure. Option (b)
is right, but the plan does not say who writes the ledger.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to
implement this plan task-by-task.

Save the revised plan to docs/superpowers/plans/2026-07-29-repo-state.md and see
superpowers:executing-plans for the handoff.
"""

BARE = """Here is my feedback on your plan.

## 1. P1 is the load-bearing decision

The plan states 18 commits since 19-Jul edited measured skills with no re-measure. Option (b)
is right, but the plan does not say who writes the ledger.
"""


class TestDetect(unittest.TestCase):
    def test_detects_every_tell_class_in_treatment_text(self):
        found = detect_tells(TREATMENT)
        for expected in ("announcement", "superpowers_ns", "superpowers_path", "required_subskill"):
            self.assertIn(expected, found, f"{expected} not detected")

    def test_bare_text_has_no_tells(self):
        self.assertEqual(detect_tells(BARE), {})

    def test_empty_and_none_are_safe(self):
        self.assertEqual(detect_tells(""), {})
        self.assertEqual(detect_tells(None), {})


class TestStrip(unittest.TestCase):
    def test_no_residual_tell_after_strip(self):
        """THE load-bearing assertion: a stripped artifact must be unidentifiable by arm."""
        clean, counts = strip_tells(TREATMENT)
        self.assertEqual(detect_tells(clean), {}, f"residual tell in: {clean!r}")
        self.assertTrue(counts, "expected strips to be counted")

    def test_strip_preserves_substantive_feedback(self):
        """Conservative-strip contract: markers go, real findings stay."""
        clean, _ = strip_tells(TREATMENT)
        self.assertIn("18 commits since 19-Jul", clean)
        self.assertIn("P1 is the load-bearing decision", clean)
        self.assertIn("does not say who writes the ledger", clean)

    def test_bare_text_is_untouched_apart_from_trimming(self):
        clean, counts = strip_tells(BARE)
        self.assertEqual(counts, {})
        self.assertEqual(clean, BARE.strip())

    def test_case_and_formatting_variants_are_caught(self):
        for variant in (
            "I am using the Writing-Plans skill to create the implementation plan.",
            "I'm using the `writing-plans` skill to create the implementation plan.",
            "Following the **writing-plans** skill, here is the plan.",
            "Per the writing-plans skill, every task needs a test.",
        ):
            clean, _ = strip_tells(variant)
            self.assertEqual(detect_tells(clean), {}, f"variant leaked: {variant!r} -> {clean!r}")

    def test_no_runaway_blank_lines(self):
        clean, _ = strip_tells(TREATMENT)
        self.assertNotIn("\n\n\n", clean)


class TestStripReport(unittest.TestCase):
    def _records(self):
        return [{"arm": "wp", "response": TREATMENT}, {"arm": "wp", "response": TREATMENT},
                {"arm": "bare", "response": BARE}, {"arm": "bare", "response": BARE}]

    def test_reports_per_arm_and_flags_zero_residual(self):
        rep = strip_report(self._records(), lambda r: r["response"])
        self.assertEqual(rep["wp"]["cells_stripped"], 2)
        self.assertEqual(rep["bare"]["cells_stripped"], 0)
        self.assertEqual(rep["wp"]["residual_after_strip"], 0)
        self.assertEqual(rep["bare"]["residual_after_strip"], 0)

    def test_asymmetric_strip_is_visible_not_hidden(self):
        """An asymmetric strip rate is expected here (only the treatment mandates the
        announcement) but must be REPORTED, because it bounds how much text the blinding
        removed from one arm only."""
        rep = strip_report(self._records(), lambda r: r["response"])
        self.assertGreater(rep["wp"]["chars_removed"], 0)
        self.assertEqual(rep["bare"]["chars_removed"], 0)


if __name__ == "__main__":
    unittest.main()
