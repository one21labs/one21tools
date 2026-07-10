#!/usr/bin/env python3
"""Decision-logic tests for compose.py (repo rule: no gating script without a test)."""
import unittest

from compose import (is_false_accept, mechanized_ship, parse_checker_verdict,
                     pick_adopted, variant_clears_bar)


class ParseCheckerVerdict(unittest.TestCase):
    def test_strict_ship(self):
        self.assertEqual(parse_checker_verdict('{"verdict": "SHIP", "reason": "fine"}'),
                         (True, None))

    def test_strict_escalate(self):
        self.assertEqual(parse_checker_verdict('{"verdict": "ESCALATE", "reason": "gaps"}'),
                         (False, None))

    def test_prose_wrapped_json_still_parses(self):
        ship, err = parse_checker_verdict('Here is my verdict: {"verdict": "ship"} done')
        self.assertTrue(ship)
        self.assertIsNone(err)

    def test_garbage_escalates_failsafe(self):
        ship, err = parse_checker_verdict("looks good to me!")
        self.assertFalse(ship)
        self.assertIsNotNone(err)

    def test_unrecognized_verdict_escalates_failsafe(self):
        ship, err = parse_checker_verdict('{"verdict": "MAYBE"}')
        self.assertFalse(ship)
        self.assertIsNotNone(err)

    def test_empty_escalates_failsafe(self):
        ship, err = parse_checker_verdict("")
        self.assertFalse(ship)
        self.assertIsNotNone(err)


class MechanizedShip(unittest.TestCase):
    def test_all_pass_ships(self):
        self.assertTrue(mechanized_ship([True, True, True]))

    def test_any_fail_escalates(self):
        self.assertFalse(mechanized_ship([True, False, True]))

    def test_no_checks_escalates_failsafe(self):
        self.assertFalse(mechanized_ship([]))


class FalseAccept(unittest.TestCase):
    def test_ship_well_below_sonnet_is_false(self):
        self.assertTrue(is_false_accept(True, haiku_frac=0.2, sonnet_eval_mean=0.6))

    def test_ship_within_margin_is_true_accept(self):
        self.assertFalse(is_false_accept(True, haiku_frac=0.56, sonnet_eval_mean=0.6))

    def test_boundary_exactly_margin_is_true_accept(self):
        # haiku 0.55 vs sonnet 0.60: not strictly below mean - 0.05
        self.assertFalse(is_false_accept(True, haiku_frac=0.55, sonnet_eval_mean=0.6))

    def test_escalate_is_never_false_accept(self):
        self.assertFalse(is_false_accept(False, haiku_frac=0.0, sonnet_eval_mean=1.0))


class Bar(unittest.TestCase):
    def test_all_three_gates_required(self):
        self.assertTrue(variant_clears_bar(0.0, 0.5, 0.10))
        self.assertFalse(variant_clears_bar(-0.06, 0.5, 0.10))   # quality fails
        self.assertFalse(variant_clears_bar(0.0, 0.61, 0.10))    # cost fails
        self.assertFalse(variant_clears_bar(0.0, 0.5, 0.16))     # fidelity fails

    def test_boundaries(self):
        self.assertFalse(variant_clears_bar(-0.05, 0.5, 0.10))   # quality strictly >
        self.assertTrue(variant_clears_bar(0.0, 0.6, 0.15))      # cost/fidelity inclusive

    def test_cheapest_clearing_variant_wins(self):
        self.assertEqual(pick_adopted({"sonnet-judge": 0.5, "mechanized": 0.3}), "mechanized")

    def test_no_clearing_variant(self):
        self.assertIsNone(pick_adopted({}))


if __name__ == "__main__":
    unittest.main()
