#!/usr/bin/env python3
"""Decision-logic tests for costing.py — deterministic notional cost math (no model, no network)."""
import os, sys, unittest

sys.path.insert(0, os.path.dirname(__file__))
import costing  # noqa: E402


class TestCosting(unittest.TestCase):
    def test_resolve_aliases(self):
        self.assertEqual(costing.resolve_model("grok"), "grok-4.5")
        self.assertEqual(costing.resolve_model("opus"), "claude-opus-4-8")
        self.assertEqual(costing.resolve_model("claude-opus-4-8"), "claude-opus-4-8")
        with self.assertRaises(KeyError):
            costing.resolve_model("gpt-4")

    def test_extract_usage_from_envelope(self):
        env = {"usage": {"input_tokens": 100, "output_tokens": 50,
                         "cache_read_input_tokens": 20}, "text": "..."}
        u = costing.extract_usage(env)
        self.assertEqual(u["input_tokens"], 100)
        self.assertEqual(u["output_tokens"], 50)
        self.assertEqual(u["cache_read_input_tokens"], 20)
        self.assertEqual(u["cache_creation_input_tokens"], 0)  # missing -> 0

    def test_notional_cost_is_exact_arithmetic(self):
        # 1M input + 1M output on grok-4.5 = $2 + $6 = $8, exactly.
        usage = {"input_tokens": 1_000_000, "output_tokens": 1_000_000}
        self.assertEqual(costing.notional_cost("grok-4.5", usage), 8.00)
        # opus: 1M in + 1M out = $5 + $25 = $30
        self.assertEqual(costing.notional_cost("claude-opus-4-8", usage), 30.00)

    def test_cache_tokens_priced_separately(self):
        # 1M cache-read on opus = 0.1x input = $0.50; 1M cache-write = 1.25x = $6.25
        self.assertAlmostEqual(
            costing.notional_cost("claude-opus-4-8", {"cache_read_input_tokens": 1_000_000}), 0.50)
        self.assertAlmostEqual(
            costing.notional_cost("claude-opus-4-8", {"cache_creation_input_tokens": 1_000_000}), 6.25)

    def test_deterministic_repeatable(self):
        usage = {"input_tokens": 14762, "output_tokens": 173, "cache_read_input_tokens": 6016}
        a = costing.notional_cost("grok-4.5", usage)
        b = costing.notional_cost("grok-4.5", usage)
        self.assertEqual(a, b)  # same input -> identical output, always

    def test_add_usage_accumulates(self):
        acc = {}
        costing.add_usage(acc, {"input_tokens": 10, "output_tokens": 5})
        costing.add_usage(acc, {"input_tokens": 3, "cache_read_input_tokens": 7})
        self.assertEqual(acc["input_tokens"], 13)
        self.assertEqual(acc["output_tokens"], 5)
        self.assertEqual(acc["cache_read_input_tokens"], 7)


if __name__ == "__main__":
    unittest.main()
