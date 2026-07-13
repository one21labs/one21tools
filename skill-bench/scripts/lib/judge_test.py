#!/usr/bin/env python3
"""Decision-logic tests for judge.py pure helpers (no CLI/network)."""
import os, sys, unittest

sys.path.insert(0, os.path.dirname(__file__))
import judge  # noqa: E402


def _which(available):
    """Stub for shutil.which: returns a fake path iff the name is in `available`."""
    return lambda name: ("/usr/bin/" + name) if name in available else None


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
        # inject availability so this passes regardless of which CLIs the CI runner has
        both = _which({"grok", "claude"})
        self.assertEqual(judge.make_judge("grok", which=both).name, "grok-4.5")
        self.assertEqual(judge.make_judge("claude", which=both).name, "claude-opus-4-8")

    def test_auto_prefers_grok_cross_family(self):
        r, note = judge.resolve_judge("auto", which=_which({"grok", "claude"}))
        self.assertEqual(r, "grok")
        self.assertIsNone(note)

    def test_auto_falls_back_to_claude_with_caveat(self):
        r, note = judge.resolve_judge("auto", which=_which({"claude"}))
        self.assertEqual(r, "claude")
        self.assertIn("SAME-FAMILY", note)

    def test_auto_none_available_errors(self):
        with self.assertRaises(judge.JudgeError):
            judge.resolve_judge("auto", which=_which(set()))

    def test_explicit_grok_missing_errors_with_remedy(self):
        with self.assertRaises(judge.JudgeError) as cm:
            judge.resolve_judge("grok", which=_which({"claude"}))
        self.assertIn("GROK_BIN", str(cm.exception))

    def test_make_judge_auto_fallback_sets_note(self):
        j = judge.make_judge("auto", which=_which({"claude"}))
        self.assertEqual(j.name, "claude-opus-4-8")
        self.assertIn("SAME-FAMILY", j.fallback_note)


if __name__ == "__main__":
    unittest.main()
