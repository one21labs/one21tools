#!/usr/bin/env python3
"""Decision-logic tests for judge.py pure helpers (no CLI/network)."""
import os, sys, unittest

sys.path.insert(0, os.path.dirname(__file__))
import judge  # noqa: E402


class TestJudge(unittest.TestCase):
    def test_met_map_extracts_bools_by_id(self):
        v = {"expectations": [{"id": 1, "met": True, "why": "x"}, {"id": 2, "met": False, "why": "y"}]}
        self.assertEqual(judge.met_map(v), {1: True, 2: False})

    def test_met_map_empty(self):
        self.assertEqual(judge.met_map({}), {})

    def test_strip_fence_plain_json(self):
        self.assertEqual(judge.strip_json_fence('{"a": 1}'), '{"a": 1}')

    def test_strip_fence_json_block(self):
        s = 'Here you go:\n```json\n{"a": 1}\n```\ndone'
        self.assertEqual(judge.strip_json_fence(s), '{"a": 1}')

    def test_strip_fence_bare_block(self):
        self.assertEqual(judge.strip_json_fence("```\n[1,2]\n```"), "[1,2]")

    def test_make_judge_dispatch_and_names(self):
        self.assertEqual(judge.make_judge("grok").name, "grok-4.5")
        self.assertEqual(judge.make_judge("claude").name, "claude-opus")


if __name__ == "__main__":
    unittest.main()
