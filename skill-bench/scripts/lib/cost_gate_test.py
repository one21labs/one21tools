#!/usr/bin/env python3
"""Decision-logic tests for cost_gate.py (CLAUDE.md Never rule: no gating script without a test
of its decision logic)."""
import json
import tempfile
import unittest
from pathlib import Path

from cost_gate import gate, main, project_grid_cost, spent_so_far


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


class SpentSoFarTest(unittest.TestCase):
    """Resume seeding (#233): the backstop must see cumulative spend, not per-invocation."""

    def _write(self, d, name, cost, error=None):
        (Path(d) / name).write_text(
            json.dumps({"cell": name, "summary": {"error": error, "cell_cost_usd": cost}}),
            encoding="utf-8")

    def test_sums_non_error_cells_only(self):
        with tempfile.TemporaryDirectory() as d:
            self._write(d, "a.json", 0.10)
            self._write(d, "b.json", 0.25)
            self._write(d, "c.json", 0.40, error="timeout")  # error cell re-runs; not spent-credit
            self.assertAlmostEqual(spent_so_far(d), 0.35)

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
