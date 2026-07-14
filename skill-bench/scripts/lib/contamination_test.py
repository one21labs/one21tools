#!/usr/bin/env python3
"""Decision-logic tests for contamination sweeps (CLAUDE.md: no gating script without a test).
Offline: temp dirs and synthetic records only."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
import contamination as c  # noqa: E402


class TestSweepRecords(unittest.TestCase):
    def test_outcome_tell_hits_and_clean_pass(self):
        tells = {"B1": [r"2\.94"]}
        dirty = {"cell": "B1-C-r1", "scenario": "B1", "response": "cost blew up 2.94x"}
        clean = {"cell": "B1-A-r1", "scenario": "B1", "response": "adopt only if under 0.7x"}
        self.assertEqual(c.sweep_records([dirty, clean], tells, global_tells=[]),
                         [("B1-C-r1", r"2\.94")])

    def test_global_tells_apply_to_every_scenario(self):
        rec = {"cell": "S1-D-r1", "scenario": "S1",
               "probes": {"p": {"response": "see one21tools-route-i2/docs"}}}
        hits = c.sweep_records([rec], tells={})
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0][0], "S1-D-r1")

    def test_artifacts_are_scanned(self):
        rec = {"cell": "B2-C-r1", "scenario": "B2",
               "response": "", "artifacts": {"d.md": "gate decidable, 216 ran"}}
        self.assertTrue(c.sweep_records([rec], {"B2": [r"\b216\b"]}, global_tells=[]))


class TestSweepTree(unittest.TestCase):
    def test_tree_and_history_hits(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d) / "repo"
            repo.mkdir()
            subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
            (repo / "notes.md").write_text("routine work\n")
            env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                       GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
            subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True, env=env)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm",
                            "add planted defect notes"], check=True, env=env)
            (repo / "notes.md").write_text("clean now\n")
            subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True, env=env)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "tidy"], check=True, env=env)
            hits = c.sweep_tree(d, ["planted defect"])
            self.assertTrue(any("history" in w for w, _ in hits),
                            f"history hit expected, got {hits}")
            self.assertFalse(any(w == "repo/notes.md" for w, _ in hits))
            self.assertEqual(c.sweep_tree(d, ["backstory-drift"]), [])


class TestSanitizedPluginDir(unittest.TestCase):
    def test_doc_surface_stripped_behavior_kept(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "plugin"
            (src / "skills" / "x").mkdir(parents=True)
            (src / "docs").mkdir()
            (src / "skills" / "x" / "SKILL.md").write_text("skill body")
            (src / "README.md").write_text("Measured: the skill showed no edge")
            (src / "docs" / "notes.md").write_text("eval results")
            dst = c.sanitized_plugin_dir(src, Path(d) / "mounted")
            names = {p.name for p in Path(dst).iterdir()}
            self.assertNotIn("README.md", names)
            self.assertNotIn("docs", names)
            self.assertTrue((Path(dst) / "skills" / "x" / "SKILL.md").exists())


if __name__ == "__main__":
    unittest.main()
