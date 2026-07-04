#!/usr/bin/env python3
"""
validate_test.py -- decision-logic test for validate.py's char/TOC gates (ADR 0009; "never ship a
process-gating script without a test of its decision logic"). Zero-dependency: Python's stdlib
unittest. Run: python validate_test.py  (or: python -m unittest validate_test) from this dir.

Each case builds a throwaway skill folder in a temp dir and asserts validate_skill's verdict, so the
decision logic (name rules, body char cap, reference char cap, reference TOC threshold) is
exercised end to end.
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

# A minimal valid frontmatter opening (name FIRST, description SECOND starting with a trigger
# phrase); make_skill closes it with ---, injecting any extra frontmatter lines before the fence.
FM_OPEN = "---\nname: {name}\ndescription: Use when testing the char gate; a third-person trigger phrase.\n"


def make_skill(root, name, body="body", refs=None, extra_fm="", fm_name=None):
    """Write <root>/<name>/SKILL.md (frontmatter [+ extra_fm lines] + body) plus optional
    references/*.md; return the dir. extra_fm, when given, must end with a newline.
    fm_name overrides the frontmatter name: (defaults to the folder name) to probe name rules
    with values a filesystem path can't carry (empty, XML chars)."""
    d = root / name
    d.mkdir()
    (d / "SKILL.md").write_text(FM_OPEN.format(name=name if fm_name is None else fm_name)
                                + extra_fm + "---\n\n" + body,
                                encoding="utf-8")
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

    def test_extra_frontmatter_counts_toward_body_cap(self):
        # A `details: |` block scalar can't smuggle prose past the body cap.
        with tempfile.TemporaryDirectory() as t:
            block = "\n".join("  filler " + "x" * 60 for _ in range(120))  # ~8k of indented block scalar
            d = make_skill(Path(t), "fm-evasion", extra_fm=f"details: |\n{block}\n")
            r = validate_skill(d)
            self.assertFalse(r.valid)
            self.assertIn("chars", r.error)

    def test_duplicate_description_key_counts_toward_body_cap(self):
        # Nor can a DUPLICATED name:/description: key — only the first two frontmatter lines
        # (which carry their own caps) are exempt from the body budget.
        with tempfile.TemporaryDirectory() as t:
            d = make_skill(Path(t), "dup-key",
                           extra_fm="description: " + "y" * (BODY_MAX_CHARS + 1) + "\n")
            r = validate_skill(d)
            self.assertFalse(r.valid)
            self.assertIn("chars", r.error)


class SkillNameRules(unittest.TestCase):
    """R2.2-R2.8 name-rule decision logic (ADR 0010: one shared home, imported by init.py).
    Each invalid frontmatter name must fail on ITS rule — all run before the folder-match check,
    so a valid folder with a bad frontmatter name isolates the rule under test."""

    def assert_name_fails(self, fm_name, error_fragment):
        with tempfile.TemporaryDirectory() as t:
            d = make_skill(Path(t), "name-probe", fm_name=fm_name)
            r = validate_skill(d)
            self.assertFalse(r.valid)
            self.assertIn(error_fragment, r.error)

    def test_empty_name_fails(self):
        self.assert_name_fails("", "empty")

    def test_xml_chars_fail(self):
        self.assert_name_fails("bad<name", "XML")

    def test_over_max_length_fails(self):
        self.assert_name_fails("a" * 65, "exceeds 64")

    def test_uppercase_fails(self):
        self.assert_name_fails("BadName", "kebab-case")

    def test_leading_hyphen_fails(self):
        self.assert_name_fails("-bad", "start with hyphen")

    def test_trailing_hyphen_fails(self):
        self.assert_name_fails("bad-", "end with hyphen")

    def test_consecutive_hyphens_fail(self):
        self.assert_name_fails("bad--name", "consecutive")

    def test_reserved_word_fails(self):
        self.assert_name_fails("claude", "reserved")


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

    def test_quoted_toc_marker_does_not_satisfy_the_gate(self):
        # The TOC check demands a real heading at line start — prose merely quoting the marker
        # string ("## Table of Contents") must not pass.
        with tempfile.TemporaryDirectory() as t:
            text = "must have '## Table of Contents' somewhere " + "x" * (REFERENCE_TOC_THRESHOLD + 1)
            d = make_skill(Path(t), "ref-quoted-toc", refs={"r.md": text})
            r = validate_skill(d)
            self.assertFalse(r.valid)
            self.assertIn("Table of Contents", r.error)

    def test_reference_over_max_fails_even_with_toc(self):
        with tempfile.TemporaryDirectory() as t:
            text = "## Table of Contents\n\n" + "x" * (REFERENCE_MAX_CHARS + 1)
            d = make_skill(Path(t), "ref-over-max", refs={"r.md": text})
            r = validate_skill(d)
            self.assertFalse(r.valid)
            self.assertIn("exceeds", r.error)

    def test_reference_with_emoji_fails(self):
        # References are skill content — emoji forbidden.
        with tempfile.TemporaryDirectory() as t:
            d = make_skill(Path(t), "ref-emoji", refs={"r.md": "a checkmark " + chr(0x2713) + " here"})
            r = validate_skill(d)
            self.assertFalse(r.valid)
            self.assertIn("emoji", r.error)


if __name__ == "__main__":
    unittest.main()
