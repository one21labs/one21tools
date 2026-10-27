"""cap_hit against the message the pinned harness really emits, so a reworded summarize_call
turns this red instead of silently turning capped replies into regenerated ERROR cells."""
import unittest

import _harness  # noqa: F401  (puts the harness on sys.path)
from hermetic_driver import summarize_call  # noqa: E402

from capped import cap_hit, cell_error  # noqa: E402


class CapHitTest(unittest.TestCase):
    def record(self, out_tokens):
        call = {"envelope": {"usage": {"output_tokens": out_tokens}}, "max_output_tokens": "32000"}
        return {"summary": summarize_call(call)}

    def test_reply_at_the_cap_is_capped(self):
        self.assertTrue(cap_hit(self.record(32000)))

    def test_capped_reply_from_a_substituted_model_is_an_error_not_capped(self):
        call = {"envelope": {"usage": {"output_tokens": 32000}, "modelUsage": {"claude-sonnet-5-5": {}}},
                "max_output_tokens": "32000"}
        summary = summarize_call(call, requested_model="claude-opus-5-5")  # as grid.run_cell calls it
        self.assertFalse(cap_hit({"summary": summary}))
        self.assertIn("envelope served", summary["error"])

    def test_short_reply_and_other_errors_are_not(self):
        self.assertFalse(cap_hit(self.record(900)))
        self.assertFalse(cap_hit({"summary": {"error": "timeout"}}))


class CellErrorTest(unittest.TestCase):
    """grid.run_cell writes cell_error(summary, response) as the cell's error."""

    def summary(self, out_tokens, served=("claude-opus-5-5",)):
        call = {"envelope": {"usage": {"output_tokens": out_tokens},
                             "modelUsage": {m: {} for m in served}}, "max_output_tokens": "32000"}
        return summarize_call(call, requested_model="claude-opus-5-5")

    def test_a_capped_envelope_naming_no_model_is_an_error_not_capped(self):
        err = cell_error(self.summary(32000, served=()), "fragment")
        self.assertEqual(err, "envelope names no served model")
        self.assertFalse(cap_hit({"summary": {"error": err}}))

    def test_markup_is_an_error_but_a_capped_reply_keeps_its_cap_verdict(self):
        self.assertIn("markup", cell_error(self.summary(900), "<invoke name=x>"))
        self.assertTrue(cap_hit({"summary": {"error": cell_error(self.summary(32000), "<invoke>")}}))

    def test_a_clean_reply_has_no_error(self):
        self.assertIsNone(cell_error(self.summary(900), "The narrative."))


if __name__ == "__main__":
    unittest.main()
