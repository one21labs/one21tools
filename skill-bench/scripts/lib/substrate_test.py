#!/usr/bin/env python3
"""Decision-logic tests for the substrate adapter's pure functions (config build + output parse).
No promptfoo/network. CLAUDE.md: no script ships without a test of its decision logic."""
import os, sys, unittest

sys.path.insert(0, os.path.dirname(__file__))
import substrate as sub  # noqa: E402


class TestSubstrate(unittest.TestCase):
    def test_config_one_provider_per_spec(self):
        cfg = sub.build_promptfoo_config(["p0", "p1"], [{"name": "A", "exec": "bash a.sh"},
                                                        {"name": "C", "exec": "bash c.sh"}])
        self.assertEqual([p["label"] for p in cfg["providers"]], ["A", "C"])
        self.assertEqual(cfg["providers"][0]["id"], "exec: bash a.sh")
        self.assertEqual(len(cfg["tests"]), 2)
        self.assertEqual(cfg["tests"][1]["vars"]["text"], "p1")
        self.assertEqual(cfg["tests"][1]["vars"]["prompt_id"], 1)  # prompt_id rides in vars

    def test_parse_nested_results_schema(self):
        # promptfoo 0.121 shape: rows at results.results[], prompt_id echoed in vars
        obj = {"results": {"results": [
            {"provider": {"label": "C"}, "vars": {"prompt_id": 0}, "response": {"output": "hi"}},
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

    def test_unwrap_cli_output(self):
        self.assertEqual(sub.unwrap_cli_output('{"text": "hello"}'), "hello")      # grok envelope
        self.assertEqual(sub.unwrap_cli_output('{"result": "hi"}'), "hi")          # claude envelope
        self.assertEqual(sub.unwrap_cli_output("plain text"), "plain text")        # not JSON -> raw
        self.assertEqual(sub.unwrap_cli_output(""), "")                            # empty
        self.assertEqual(sub.unwrap_cli_output(None), "")                          # None -> ""
        self.assertEqual(sub.unwrap_cli_output('{"other": 1}'), '{"other": 1}')    # no text field -> raw

    def test_parse_unwraps_envelope_output(self):
        obj = {"results": {"results": [
            {"provider": {"label": "with"}, "vars": {"prompt_id": 0},
             "response": {"output": '{"text": "the answer"}'}}]}}
        self.assertEqual(sub.parse_promptfoo_output(obj)[0]["output"], "the answer")

    def test_make_substrate_dispatch(self):
        self.assertEqual(sub.make_substrate("native").name, "native")
        self.assertEqual(sub.make_substrate("promptfoo").name, "promptfoo")

    def test_promptfoo_substrate_is_version_pinned(self):
        # ADR 0058: a benchmark harness must not track a moving head (@latest)
        old = os.environ.pop("SKILL_BENCH_PROMPTFOO_BIN", None)
        try:
            s = sub.PromptfooSubstrate()
            self.assertIn(sub.PromptfooSubstrate.PIN, s.argv)
            self.assertNotIn("latest", " ".join(s.argv))
        finally:
            if old is not None:
                os.environ["SKILL_BENCH_PROMPTFOO_BIN"] = old


if __name__ == "__main__":
    unittest.main()
