#!/usr/bin/env python3
"""Decision-logic tests for config.py precedence (built-in < file < env). Pure/offline."""
import json, os, sys, tempfile, unittest

sys.path.insert(0, os.path.dirname(__file__))
import config  # noqa: E402


class TestConfig(unittest.TestCase):
    def test_builtin_defaults(self):
        c = config.load(env={})
        self.assertEqual(c["judge"], "auto")
        self.assertEqual(c["substrate"], "native")
        self.assertEqual(c["workers"], 8)

    def test_env_overrides_default(self):
        c = config.load(env={"SKILL_BENCH_JUDGE": "claude", "SKILL_BENCH_WORKERS": "3"})
        self.assertEqual(c["judge"], "claude")
        self.assertEqual(c["workers"], 3)  # coerced to int

    def test_config_file_then_env_wins(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"judge": "grok", "substrate": "promptfoo", "ignored": "x"}, f)
            path = f.name
        try:
            c = config.load(env={"SKILL_BENCH_CONFIG": path})
            self.assertEqual(c["judge"], "grok")          # from file
            self.assertEqual(c["substrate"], "promptfoo")  # from file
            self.assertNotIn("ignored", c)                 # unknown keys dropped
            # env beats file
            c2 = config.load(env={"SKILL_BENCH_CONFIG": path, "SKILL_BENCH_JUDGE": "claude"})
            self.assertEqual(c2["judge"], "claude")
        finally:
            os.unlink(path)

    def test_malformed_file_falls_through(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write("{ not json"); path = f.name
        try:
            self.assertEqual(config.load(env={"SKILL_BENCH_CONFIG": path})["judge"], "auto")
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
