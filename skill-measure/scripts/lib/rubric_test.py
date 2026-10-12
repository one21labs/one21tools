#!/usr/bin/env python3
"""Decision-logic tests for rubric.py: the grading prompt must embed the key and stay stable so a
judge swap (opus<->grok) is a clean measurement, not a prompt difference."""
import os, sys, unittest

sys.path.insert(0, os.path.dirname(__file__))
import rubric  # noqa: E402

BACKTEST = {"type": "backtest", "question": "adopt X?",
            "outcome_key": {"assumption_that_broke": "A held", "failure_class": "cost blowup"}}
SYNTH = {"type": "synthetic", "shape": "set a limit", "trap": "sunk-cost bait",
         "expectations": ["e1", "e2", "e3"]}
NORM = {"decision": "d", "options": ["o1", "REJECTED: o2 — r"], "criterion": "c",
        "risks": ["cost blowup"], "assumptions": ["A held"]}


class TestRubric(unittest.TestCase):
    def test_backtest_rubric_embeds_outcome_key(self):
        r = rubric.rubric_for(BACKTEST)
        self.assertIn("backtest", r)
        self.assertIn("cost blowup", r)          # failure_class present
        self.assertIn("A held", r)               # assumption present
        self.assertIn("adopt X?", r)             # question present

    def test_synthetic_rubric_embeds_trap(self):
        r = rubric.rubric_for(SYNTH)
        self.assertIn("synthetic", r)
        self.assertIn("sunk-cost bait", r)
        self.assertIn("planted trap", r)

    def test_grade_prompt_contains_norm_and_schema_instruction(self):
        p = rubric.grade_prompt(NORM, BACKTEST)
        self.assertIn('"decision": "d"', p)
        self.assertIn("expectations:", p)
        self.assertIn("met=true only on clear evidence", p)

    def test_prosecute_prompt_is_adversarial_and_carries_prior(self):
        prior = {"expectations": [{"id": 1, "met": True, "why": "w"}]}
        p = rubric.prosecute_prompt(NORM, SYNTH, prior)
        self.assertIn("REFUTE", p)
        self.assertIn("FIRST GRADER", p)
        self.assertIn('"met": true', p)

    def test_grade_schema_shape(self):
        s = rubric.GRADE_SCHEMA
        self.assertEqual(s["type"], "object")
        self.assertIn("expectations", s["properties"])


if __name__ == "__main__":
    unittest.main()
