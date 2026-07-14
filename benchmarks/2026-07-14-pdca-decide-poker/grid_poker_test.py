#!/usr/bin/env python3
"""Decision-logic tests for the frozen poker-cell machinery (parsers, spread, tables)."""
import unittest

import grid_poker as g

OPTS = [{"id": "O1", "label": "Adopt", "summary": "Adopt the thing"},
        {"id": "O2", "label": "Decline", "summary": "Do not adopt"}]


class ParseEstimates(unittest.TestCase):
    def test_fenced_json_parses(self):
        r = g.parse_estimates('```json\n{"estimates":[{"id":"O1","score":4,"crux":"c","dependency":"d"},'
                              '{"id":"O2","score":2,"crux":"c","dependency":"d"}]}\n```', ["O1", "O2"])
        self.assertEqual(r["O1"]["score"], 4)

    def test_score_out_of_range_fails(self):
        self.assertIsNone(g.parse_estimates(
            '{"estimates":[{"id":"O1","score":9,"crux":"c","dependency":"d"}]}', ["O1"]))

    def test_non_integer_score_fails(self):
        self.assertIsNone(g.parse_estimates(
            '{"estimates":[{"id":"O1","score":"4","crux":"c","dependency":"d"}]}', ["O1"]))

    def test_missing_option_coverage_fails(self):
        self.assertIsNone(g.parse_estimates(
            '{"estimates":[{"id":"O1","score":3,"crux":"c","dependency":"d"}]}', ["O1", "O2"]))

    def test_subset_coverage_passes(self):
        r = g.parse_estimates('{"estimates":[{"id":"O1","score":3,"crux":"c","dependency":"d"}]}',
                              ["O1", "O2"], subset=["O1"])
        self.assertIsNotNone(r)

    def test_empty_crux_fails(self):
        self.assertIsNone(g.parse_estimates(
            '{"estimates":[{"id":"O1","score":3,"crux":" ","dependency":"d"}]}', ["O1"]))

    def test_unknown_option_id_ignored(self):
        r = g.parse_estimates('{"estimates":[{"id":"O9","score":3,"crux":"c","dependency":"d"},'
                              '{"id":"O1","score":2,"crux":"c","dependency":"d"}]}', ["O1"])
        self.assertEqual(set(r), {"O1"})


class ParseOptions(unittest.TestCase):
    def test_two_to_four_required(self):
        one = '{"options":[{"id":"O1","label":"A","summary":"s"}]}'
        self.assertIsNone(g.parse_options(one))
        five = '{"options":[' + ",".join(
            f'{{"id":"O{i}","label":"L{i}","summary":"s"}}' for i in range(1, 6)) + "]}"
        self.assertIsNone(g.parse_options(five))
        two = '{"options":[{"id":"O1","label":"A","summary":"s"},{"id":"O2","label":"B","summary":"s"}]}'
        self.assertEqual(len(g.parse_options(two)), 2)


class SpreadAndTables(unittest.TestCase):
    def est(self, *scores):
        return [{f"O{i+1}": {"score": s, "crux": "x", "dependency": "y"}
                 for i, s in enumerate(row)} for row in scores]

    def test_reveal_spread_max_minus_min(self):
        r1u = self.est([5, 3], [2, 3], [4, 4])
        spread = {oid: max(e[oid]["score"] for e in r1u) - min(e[oid]["score"] for e in r1u)
                  for oid in ("O1", "O2")}
        self.assertEqual(spread, {"O1": 3, "O2": 1})

    def test_final_table_marks_round2(self):
        t = g.render_final_table(OPTS, self.est([4, 2], [4, 2]), {"O2"})
        self.assertIn("O2: Decline — Do not adopt (re-estimated in round 2)", t)
        self.assertNotIn("O1: Adopt — Adopt the thing (re-estimated", t)
        self.assertIn("reverses if false: y", t)

    def test_reveal_table_only_divergent(self):
        t = g.render_reveal_table(OPTS, self.est([5, 2], [1, 2]), ["O1"])
        self.assertIn("O1: Adopt", t)
        self.assertNotIn("O2", t)


class PromptFormat(unittest.TestCase):
    def test_frozen_templates_render(self):
        p = "ctx" + g.ADVISOR_SUFFIX.format(options=g.render_options(OPTS))
        self.assertIn('{"estimates"', p)
        p2 = "ctx" + g.ROUND2_SUFFIX.format(own="{}", table="T")
        self.assertIn("Re-estimate ONLY", p2)
        p3 = "ctx" + g.POKER_BLOCK.format(table="T") + g.A_SUFFIX
        self.assertIn("Decide this and record your decision", p3)


if __name__ == "__main__":
    unittest.main()
