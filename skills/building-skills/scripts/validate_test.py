#!/usr/bin/env python3
"""
validate_test.py -- decision-logic test for validate.py's char/TOC gates (ADR 0009; "never ship a
process-gating script without a test of its decision logic"). Zero-dependency: Python's stdlib
unittest. Run: python validate_test.py  (or: python -m unittest validate_test) from this dir.

Each case builds a throwaway skill folder in a temp dir and asserts validate_skill's verdict, so the
decision logic (body char cap, reference char cap, reference TOC threshold) is exercised end to end.
"""
import unittest
import tempfile
from pathlib import Path

from validate import (
    validate_skill,
    BODY_MAX_CHARS,
    REFERENCE_MAX_CHARS,
    REFERENCE_TOC_THRESHOLD,
)

# A minimal valid frontmatter (name FIRST, description SECOND starting with a trigger phrase).
FM = "---\nname: {name}\ndescription: Use when testing the char gate; a third-person trigger phrase.\n---\n\n"


def make_skill(root, name, body="body", refs=None):
    """Write <root>/<name>/SKILL.md (frontmatter + body) plus optional references/*.md; return the dir."""
    d = root / name
    d.mkdir()
    (d / "SKILL.md").write_text(FM.format(name=name) + body, encoding="utf-8")
    if refs:
        (d / "references").mkdir()
        for fname, text in refs.items():
            (d / "references" / fname).write_text(text, encoding="utf-8")
    return d


class SkillBodyCharCap(unittest.TestCase):
    def test_body_at_cap_passes(self):
        with tempfile.TemporaryDirectory() as t:
            d = make_skill(Path(t), "body-at-cap", body="x" * BODY_MAX_CHARS)
            self.assertTrue(validate_skill(d).valid)

    def test_body_over_cap_fails(self):
        with tempfile.TemporaryDirectory() as t:
            d = make_skill(Path(t), "body-over-cap", body="x" * (BODY_MAX_CHARS + 1))
            r = validate_skill(d)
            self.assertFalse(r.valid)
            self.assertIn("chars", r.error)


class ReferenceCaps(unittest.TestCase):
    def test_small_reference_needs_no_toc(self):
        with tempfile.TemporaryDirectory() as t:
            d = make_skill(Path(t), "ref-small", refs={"r.md": "x" * (REFERENCE_TOC_THRESHOLD - 1)})
            self.assertTrue(validate_skill(d).valid)

    def test_reference_over_toc_threshold_without_toc_fails(self):
        with tempfile.TemporaryDirectory() as t:
            d = make_skill(Path(t), "ref-no-toc", refs={"r.md": "x" * (REFERENCE_TOC_THRESHOLD + 1)})
            r = validate_skill(d)
            self.assertFalse(r.valid)
            self.assertIn("Table of Contents", r.error)

    def test_reference_over_toc_threshold_with_toc_passes(self):
        with tempfile.TemporaryDirectory() as t:
            text = "## Table of Contents\n\n" + "x" * (REFERENCE_TOC_THRESHOLD + 1)
            d = make_skill(Path(t), "ref-with-toc", refs={"r.md": text})
            self.assertTrue(validate_skill(d).valid)

    def test_reference_over_max_fails_even_with_toc(self):
        with tempfile.TemporaryDirectory() as t:
            text = "## Table of Contents\n\n" + "x" * (REFERENCE_MAX_CHARS + 1)
            d = make_skill(Path(t), "ref-over-max", refs={"r.md": text})
            r = validate_skill(d)
            self.assertFalse(r.valid)
            self.assertIn("exceeds", r.error)


if __name__ == "__main__":
    unittest.main()
