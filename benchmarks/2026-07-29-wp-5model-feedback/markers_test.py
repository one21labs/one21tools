#!/usr/bin/env python3
"""Decision-logic tests for markers.py — the judge-independent rival-explanation counters."""
import unittest

from markers import measure


class TestTreatmentMarkers(unittest.TestCase):
    def test_neutral_text_scores_zero(self):
        m = measure("The plan is sound but the sequencing is unclear in places.")
        self.assertEqual(m["treatment_markers_distinct"], 0)
        self.assertEqual(m["treatment_markers_total"], 0)

    def test_detects_skill_vocabulary(self):
        m = measure("Apply TDD and YAGNI, keep tasks bite-sized, and use frequent commits.")
        self.assertGreaterEqual(m["treatment_markers_distinct"], 4)
        self.assertIn("TDD", m["treatment_marker_hits"])
        self.assertIn("bite-sized", m["treatment_marker_hits"])

    def test_checkboxes_counted_as_treatment_structure(self):
        m = measure("- [ ] Step 1: write the test\n- [ ] Step 2: run it\n- [x] Step 3: done")
        self.assertEqual(m["checkboxes"], 3)
        self.assertGreaterEqual(m["treatment_markers_total"], 3)

    def test_plain_bullets_are_not_checkboxes(self):
        m = measure("- first point\n- second point\n* third point")
        self.assertEqual(m["checkboxes"], 0)


class TestPlanAnchors(unittest.TestCase):
    def test_counts_distinct_not_repeats(self):
        """Repeating one identifier is one anchor. This is the whole point of distinct-counting:
        otherwise a model that says 'P1' twelve times looks maximally grounded."""
        once = measure("P1 needs a decision.")
        many = measure("P1 P1 P1 P1 P1 P1 P1 P1 P1 P1 P1 P1")
        self.assertEqual(once["plan_anchors_distinct"], many["plan_anchors_distinct"])
        self.assertGreater(many["plan_anchors_total"], once["plan_anchors_total"])

    def test_counts_distinct_identifiers_across_kinds(self):
        m = measure("P1 blocks #252, and ADR 0095 settles the re-measure bar for the ADOPT track.")
        self.assertGreaterEqual(m["plan_anchors_distinct"], 5)

    def test_generic_feedback_has_no_anchors(self):
        m = measure("This plan would benefit from clearer ownership and firmer deadlines.")
        self.assertEqual(m["plan_anchors_distinct"], 0)


class TestDensity(unittest.TestCase):
    def test_density_separates_more_from_better(self):
        """THE load-bearing property: padding a response with neutral prose leaves the raw anchor
        count unchanged but lowers its density, which is how a length artifact is caught."""
        short = measure("P1 blocks #252 and ADR 0095 decides it.")
        padded = measure("P1 blocks #252 and ADR 0095 decides it." + (" filler words here." * 200))
        self.assertEqual(short["plan_anchors_total"], padded["plan_anchors_total"])
        self.assertGreater(short["plan_anchors_per_1k"], padded["plan_anchors_per_1k"])

    def test_findings_counted_from_list_structure(self):
        m = measure("## First\n- one\n- two\n1. three\n2. four")
        self.assertGreaterEqual(m["findings"], 5)
        self.assertIsNotNone(m["chars_per_finding"])

    def test_no_findings_yields_none_not_zero_division(self):
        m = measure("A single flowing paragraph with no list structure at all.")
        self.assertEqual(m["findings"], 0)
        self.assertIsNone(m["chars_per_finding"])

    def test_empty_input_is_safe(self):
        for bad in ("", None):
            m = measure(bad)
            self.assertEqual(m["chars"], 0)
            self.assertEqual(m["findings"], 0)


if __name__ == "__main__":
    unittest.main()
