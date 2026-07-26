#!/usr/bin/env python3
"""Decision-logic test for the shared spend guard (never ship a process-gating script without
one). Covers the refusal itself, the pass-through, and that the cost line always prints."""
import io
import unittest

from spend_guard import REFUSAL, require_yes


class TestRequireYes(unittest.TestCase):
    def test_refuses_with_exit_2_when_not_confirmed(self):
        out, codes = io.StringIO(), []
        require_yes(False, "3 queries x 2 runs = 6 sessions", out=out, exit_fn=codes.append)
        self.assertEqual(codes, [2])
        self.assertIn(REFUSAL, out.getvalue())

    def test_proceeds_silently_when_confirmed(self):
        out, codes = io.StringIO(), []
        require_yes(True, "6 sessions", out=out, exit_fn=codes.append)
        self.assertEqual(codes, [])
        self.assertNotIn(REFUSAL, out.getvalue())

    def test_cost_line_prints_either_way(self):
        for yes in (True, False):
            out = io.StringIO()
            require_yes(yes, "6 sessions", out=out, exit_fn=lambda c: None)
            self.assertIn("[cost] 6 sessions", out.getvalue())


if __name__ == "__main__":
    unittest.main()
