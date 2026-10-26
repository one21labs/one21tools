"""cap_hit against the message the pinned harness really emits, so a reworded summarize_call
turns this red instead of silently turning capped replies into regenerated ERROR cells."""
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(Path(os.environ.get("SKILL_MEASURE_ROOT") or HERE.parents[2] / "skill-measure")
                       / "scripts" / "lib"))
from hermetic_driver import summarize_call  # noqa: E402

from capped import cap_hit  # noqa: E402


class CapHitTest(unittest.TestCase):
    def record(self, out_tokens):
        call = {"envelope": {"usage": {"output_tokens": out_tokens}}, "max_output_tokens": "32000"}
        return {"summary": summarize_call(call)}

    def test_reply_at_the_cap_is_capped(self):
        self.assertTrue(cap_hit(self.record(32000)))

    def test_short_reply_and_other_errors_are_not(self):
        self.assertFalse(cap_hit(self.record(900)))
        self.assertFalse(cap_hit({"summary": {"error": "timeout"}}))


if __name__ == "__main__":
    unittest.main()
