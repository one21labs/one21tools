#!/usr/bin/env python3
"""Decision-logic tests for cost_gate.py (CLAUDE.md Never rule: no gating script without a test
of its decision logic)."""
import json
import tempfile
import unittest
from pathlib import Path

from cost_gate import (admit, cell_spend, charged_usd, gate, main, project_grid_cost,
                       spent_so_far)


class ProjectionTest(unittest.TestCase):
    def test_projection_is_mean_times_cells(self):
        self.assertAlmostEqual(project_grid_cost(90, [0.10, 0.20, 0.30]), 18.0)

    def test_single_pilot_cell(self):
        self.assertAlmostEqual(project_grid_cost(36, [0.05]), 1.8)

    def test_rejects_nonpositive_cells(self):
        with self.assertRaises(ValueError):
            project_grid_cost(0, [0.1])

    def test_rejects_empty_and_negative_pilot(self):
        with self.assertRaises(ValueError):
            project_grid_cost(10, [])
        with self.assertRaises(ValueError):
            project_grid_cost(10, [0.1, -0.2])

    def test_rejects_zero_and_nonfinite_costs(self):
        # A $0 or inf/nan measured cost is a broken pilot, not a free cell: it passes any ceiling.
        for bad in ([0.0], [0.1, 0.0], [float("inf")], [float("nan")]):
            with self.assertRaises(ValueError, msg=bad):
                project_grid_cost(10, bad)


class GateTest(unittest.TestCase):
    def test_under_ceiling_passes(self):
        ok, projected = gate(90, [0.30], 40.0)
        self.assertTrue(ok)
        self.assertAlmostEqual(projected, 27.0)

    def test_at_ceiling_passes(self):
        ok, _ = gate(100, [0.40], 40.0)
        self.assertTrue(ok)

    def test_over_ceiling_fails(self):
        ok, projected = gate(90, [0.50], 40.0)
        self.assertFalse(ok)
        self.assertAlmostEqual(projected, 45.0)

    def test_mean_not_min_governs(self):
        # One cheap cell must not rescue an expensive arm: mean(0.1, 0.9)=0.5 -> 45 > 40.
        ok, _ = gate(90, [0.1, 0.9], 40.0)
        self.assertFalse(ok)

    def test_rejects_nonfinite_ceiling(self):
        for bad in (float("inf"), float("nan")):
            with self.assertRaises(ValueError):
                gate(90, [0.3], bad)


class AdmitTest(unittest.TestCase):
    """Pre-launch backstop: never launch a call that could carry spend past the cap."""

    def test_fits_and_at_cap(self):
        self.assertTrue(admit(1.0, 0.0, 0.5, 2.0))
        self.assertTrue(admit(1.5, 0.0, 0.5, 2.0))

    def test_refuses_over_cap(self):
        self.assertFalse(admit(1.6, 0.0, 0.5, 2.0))

    def test_resume_at_cap_refuses(self):
        # A re-invocation seeded with spend already at the cap launches nothing.
        self.assertFalse(admit(2.0, 0.0, 0.01, 2.0))

    def test_in_flight_reservations_count(self):
        # Three calls in flight at 0.5 each: a fourth would overshoot even though spent is 0.
        self.assertFalse(admit(0.0, 1.5, 0.5, 1.9))
        self.assertTrue(admit(0.0, 1.0, 0.5, 1.9))

    def test_rejects_zero_or_nonfinite(self):
        for args in ((0, 0, 0.0, 2.0), (0, 0, float("inf"), 2.0), (0, 0, 0.5, float("inf"))):
            with self.assertRaises(ValueError, msg=args):
                admit(*args)


class ChargeTest(unittest.TestCase):
    def test_measured_cost_wins(self):
        self.assertEqual(charged_usd(0.07, 0.15), 0.07)
        self.assertEqual(charged_usd(0.0, 0.15), 0.0)

    def test_failed_call_charged_estimate(self):
        self.assertEqual(charged_usd(None, 0.15), 0.15)

    def test_cell_spend_is_max_plus_prior(self):
        self.assertAlmostEqual(cell_spend({"summary": {"cell_cost_usd": 0.0, "charged_usd": 0.15,
                                                       "prior_attempts_usd": 0.3}}), 0.45)
        self.assertAlmostEqual(cell_spend({"summary": {"cell_cost_usd": 0.2}}), 0.2)
        self.assertEqual(cell_spend({}), 0.0)


class SpentSoFarTest(unittest.TestCase):
    """Resume seeding (#233): the backstop must see cumulative spend, not per-invocation."""

    def _write(self, d, name, cost, error=None, **extra):
        (Path(d) / name).write_text(
            json.dumps({"cell": name, "summary": {"error": error, "cell_cost_usd": cost, **extra}}),
            encoding="utf-8")

    def test_error_cells_count(self):
        # An ERROR cell's call was billed; dropping it understated spend past the cap.
        with tempfile.TemporaryDirectory() as d:
            self._write(d, "a.json", 0.10)
            self._write(d, "b.json", 0.25)
            self._write(d, "c.json", 0.40, error="fake tool-call markup")
            self.assertAlmostEqual(spent_so_far(d), 0.75)

    def test_failed_charge_and_prior_attempts_count(self):
        with tempfile.TemporaryDirectory() as d:
            self._write(d, "a.json", 0.0, error="timeout after 600s", charged_usd=0.15)
            self._write(d, "b.json", 0.20, charged_usd=0.20, prior_attempts_usd=0.15)
            self.assertAlmostEqual(spent_so_far(d), 0.50)

    def test_malformed_and_missing_tolerated(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "bad.json").write_text("{not json", encoding="utf-8")
            self._write(d, "ok.json", 0.5)
            self.assertAlmostEqual(spent_so_far(d), 0.5)
            self.assertEqual(spent_so_far(Path(d) / "nonexistent"), 0.0)

    def test_empty_dir_is_zero(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(spent_so_far(d), 0.0)


class CliTest(unittest.TestCase):
    def test_exit_zero_within(self):
        rc = main(["--cells", "90", "--pilot-cost-usd", "0.3", "--ceiling-usd", "40"])
        self.assertEqual(rc, 0)

    def test_exit_nonzero_over(self):
        rc = main(["--cells", "90", "--pilot-cost-usd", "0.5", "--ceiling-usd", "40"])
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
