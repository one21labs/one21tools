#!/usr/bin/env python3
"""Decision-logic tests for the substrate adapter's pure functions (config build + output parse).
No promptfoo/network. CLAUDE.md: no script ships without a test of its decision logic."""
import os, sys, unittest

sys.path.insert(0, os.path.dirname(__file__))
import substrate as sub  # noqa: E402


class TestSubstrate(unittest.TestCase):
    def test_config_one_provider_per_arm(self):
        cfg = sub.build_promptfoo_config(["p0", "p1"], [{"name": "A", "cmd": ["grok", "-p"]},
                                                        {"name": "C", "cmd": ["claude", "-p"]}])
        self.assertEqual([p["label"] for p in cfg["providers"]], ["A", "C"])
        self.assertTrue(cfg["providers"][0]["id"].startswith("exec: "))
        self.assertEqual(len(cfg["tests"]), 2)
        self.assertEqual(cfg["tests"][1]["vars"]["text"], "p1")
        self.assertEqual(cfg["tests"][1]["metadata"]["prompt_id"], 1)

    def test_parse_nested_results_schema(self):
        obj = {"results": {"results": [
            {"provider": {"label": "C"}, "metadata": {"prompt_id": 0}, "response": {"output": "hi"}},
            {"provider": {"id": "exec: x"}, "vars": {"prompt_id": 1}, "response": {"output": "yo"}},
        ]}}
        rows = sub.parse_promptfoo_output(obj)
        self.assertEqual(rows[0], {"prompt_id": 0, "arm": "C", "output": "hi"})
        self.assertEqual(rows[1]["arm"], "exec: x")
        self.assertEqual(rows[1]["prompt_id"], 1)

    def test_parse_flat_results_and_string_response(self):
        obj = {"results": [{"provider": "A", "response": "plain"}]}
        rows = sub.parse_promptfoo_output(obj)
        self.assertEqual(rows[0]["arm"], "A")
        self.assertEqual(rows[0]["output"], "plain")

    def test_make_substrate_dispatch(self):
        self.assertEqual(sub.make_substrate("native").name, "native")
        self.assertEqual(sub.make_substrate("promptfoo").name, "promptfoo")


if __name__ == "__main__":
    unittest.main()
