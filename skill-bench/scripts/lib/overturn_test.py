#!/usr/bin/env python3
"""Decision-logic tests for overturn.py (#191 item 5)."""
import unittest

from overturn import decision_signature, overturn_candidates

PATTERN = r"\b\d+\s*/\s*day\b"


def cell(bid, arm, scenario="S1", **met):
    return {"bid": bid, "arm": arm, "scenario": scenario,
            "met": {int(k.lstrip("e")): v for k, v in met.items()}}


class DecisionSignature(unittest.TestCase):
    def test_extracts_first_match(self):
        self.assertEqual(decision_signature("cap at 300/day with review", PATTERN), "300/day")

    def test_no_match_is_none(self):
        self.assertIsNone(decision_signature("cap at three hundred daily", PATTERN))
        self.assertIsNone(decision_signature(None, PATTERN))


class OverturnCandidates(unittest.TestCase):
    def test_cross_arm_same_decision_split_is_flagged(self):
        cells = [cell("b1", "C", e2=True), cell("b2", "P", e2=False)]
        norms = {"b1": "limit 300/day", "b2": "limit 300/day"}
        found = overturn_candidates(cells, norms, PATTERN)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["signature"], "300/day")
        self.assertEqual(found[0]["exp"], 2)
        self.assertEqual(found[0]["passed"], [("C", "b1")])
        self.assertEqual(found[0]["failed"], [("P", "b2")])

    def test_same_arm_split_is_rep_noise_not_flagged(self):
        cells = [cell("b1", "C", e2=True), cell("b2", "C", e2=False)]
        norms = {"b1": "limit 300/day", "b2": "limit 300/day"}
        self.assertEqual(overturn_candidates(cells, norms, PATTERN), [])

    def test_different_decisions_not_flagged(self):
        cells = [cell("b1", "C", e2=True), cell("b2", "P", e2=False)]
        norms = {"b1": "limit 300/day", "b2": "limit 500/day"}
        self.assertEqual(overturn_candidates(cells, norms, PATTERN), [])

    def test_agreeing_verdicts_not_flagged(self):
        cells = [cell("b1", "C", e2=True), cell("b2", "P", e2=True)]
        norms = {"b1": "limit 300/day", "b2": "limit 300/day"}
        self.assertEqual(overturn_candidates(cells, norms, PATTERN), [])

    def test_different_scenarios_never_grouped(self):
        cells = [cell("b1", "C", "S1", e2=True), cell("b2", "P", "S2", e2=False)]
        norms = {"b1": "limit 300/day", "b2": "limit 300/day"}
        self.assertEqual(overturn_candidates(cells, norms, PATTERN), [])

    def test_unmatched_cells_excluded(self):
        cells = [cell("b1", "C", e2=True), cell("b2", "P", e2=False)]
        norms = {"b1": "limit 300/day", "b2": "no numeric limit stated"}
        self.assertEqual(overturn_candidates(cells, norms, PATTERN), [])

    def test_mixed_arms_flag_only_cross_arm_disagreement(self):
        # C passes, P fails, and a second P cell passes: still a cross-arm split (C-pass vs P-fail).
        cells = [cell("b1", "C", e2=True), cell("b2", "P", e2=False), cell("b3", "P", e2=True)]
        norms = {b: "limit 300/day" for b in ("b1", "b2", "b3")}
        found = overturn_candidates(cells, norms, PATTERN)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["failed"], [("P", "b2")])


if __name__ == "__main__":
    unittest.main()
