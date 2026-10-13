"""Decision-logic tests for mechanized_checks.py (lib convention: test-per-module).

Every registered check must return True on its positive example and False on its
negative example; the registries must stay key-complete and callable-only.
"""
import unittest

import mechanized_checks as mc


class Registries(unittest.TestCase):
    def test_keys_match(self):
        self.assertEqual(set(mc.CHECKS.keys()), set(mc.TESTS.keys()))

    def test_shapes(self):
        for key, fn in mc.CHECKS.items():
            self.assertTrue(callable(fn), key)
            skill, eval_id, idx = key
            self.assertIsInstance(skill, str)
            self.assertIsInstance(eval_id, int)
            self.assertIsInstance(idx, int)


class CheckDecisions(unittest.TestCase):
    def test_positive_examples_pass(self):
        for key, fn in sorted(mc.CHECKS.items()):
            pos, _ = mc.TESTS[key]
            self.assertIs(fn(pos), True, f"{key} {fn.__name__}: positive example")

    def test_negative_examples_fail(self):
        for key, fn in sorted(mc.CHECKS.items()):
            _, neg = mc.TESTS[key]
            self.assertIs(fn(neg), False, f"{key} {fn.__name__}: negative example")

    def test_empty_text_returns_bool(self):
        # Absence-style checks legitimately pass empty text; the invariant is
        # only that every check total-functions to a strict bool on it.
        for key, fn in sorted(mc.CHECKS.items()):
            self.assertIsInstance(fn(""), bool, f"{key} {fn.__name__}: empty text")


if __name__ == "__main__":
    unittest.main()
