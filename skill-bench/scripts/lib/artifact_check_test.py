#!/usr/bin/env python3
"""Decision-logic tests for artifact_check.py (#191 item 1)."""
import unittest

from artifact_check import check_artifact, classify_cells


class CheckArtifact(unittest.TestCase):
    def test_empty_and_whitespace_fail(self):
        for text in ("", None, "   \n\t  "):
            ok, reason = check_artifact(text)
            self.assertFalse(ok)
            self.assertIn("under", reason)

    def test_short_fails_long_passes(self):
        ok, _ = check_artifact("x" * 39, min_chars=40)
        self.assertFalse(ok)
        ok, reason = check_artifact("x" * 40, min_chars=40)
        self.assertTrue(ok)
        self.assertEqual(reason, "")

    def test_required_marker(self):
        text = "Decision: adopt the thing because reasons. " * 3
        ok, _ = check_artifact(text, require=("Decision:",))
        self.assertTrue(ok)
        ok, reason = check_artifact(text, require=("## Rationale",))
        self.assertFalse(ok)
        self.assertIn("Rationale", reason)


class ClassifyCells(unittest.TestCase):
    def rec(self, response, error=None):
        return {"summary": {"error": error}, "response": response}

    def test_harness_error_is_error_cell_even_with_text(self):
        good_text = "a plausible decision artifact " * 5
        ok, errors = classify_cells([self.rec(good_text, error="timeout after 900s")],
                                    lambda r: r["response"])
        self.assertEqual(ok, [])
        self.assertEqual(len(errors), 1)
        self.assertIn("harness error", errors[0][1])

    def test_empty_artifact_is_error_never_quality_zero(self):
        records = [self.rec(""), self.rec("a real decision artifact with substance " * 3)]
        ok, errors = classify_cells(records, lambda r: r["response"])
        self.assertEqual(len(ok), 1)
        self.assertEqual(len(errors), 1)
        self.assertIn("under", errors[0][1])

    def test_all_good_records_pass_through_in_order(self):
        records = [self.rec(f"decision artifact number {i} with enough substance to grade")
                   for i in range(3)]
        ok, errors = classify_cells(records, lambda r: r["response"])
        self.assertEqual(ok, records)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
