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


class DocStructureLint(unittest.TestCase):
    """R8 (ADR 0040): duplicate H2 headings, stale intra-doc anchors, and dangling relative
    .md links fail; clean structure, punctuated-heading slugs, and quoted content inside code
    fences pass."""

    def test_duplicate_h2_heading_fails(self):
        with tempfile.TemporaryDirectory() as t:
            body = "## Sources\n\na\n\n## Sources\n\nb\n"
            d = make_skill(Path(t), "dup-h2", body=body)
            r = validate_skill(d)
            self.assertFalse(r.valid)
            self.assertIn("duplicate", r.error)

    def test_stale_anchor_link_fails(self):
        with tempfile.TemporaryDirectory() as t:
            body = "[Gone Section](#gone-section)\n\n## Here\n\nx\n"
            d = make_skill(Path(t), "stale-anchor", body=body)
            r = validate_skill(d)
            self.assertFalse(r.valid)
            self.assertIn("matches no heading", r.error)

    def test_valid_toc_anchor_with_punctuation_passes(self):
        with tempfile.TemporaryDirectory() as t:
            body = "- [Tier 2 — section ablation](#tier-2--section-ablation)\n\n## Tier 2 — section ablation\n\nx\n"
            d = make_skill(Path(t), "punct-anchor", body=body)
            self.assertTrue(validate_skill(d).valid)

    def test_dangling_relative_md_link_fails(self):
        with tempfile.TemporaryDirectory() as t:
            d = make_skill(Path(t), "dangling-link", refs={"r.md": "see [gone](nowhere.md)\n"})
            r = validate_skill(d)
            self.assertFalse(r.valid)
            self.assertIn("does not exist", r.error)

    def test_existing_relative_md_link_passes(self):
        with tempfile.TemporaryDirectory() as t:
            d = make_skill(Path(t), "good-link",
                           refs={"a.md": "see [b](b.md)\n", "b.md": "see [a](a.md)\n"})
            self.assertTrue(validate_skill(d).valid)

    def test_quoted_heading_inside_code_fence_is_not_counted(self):
        with tempfile.TemporaryDirectory() as t:
            body = "## Sources\n\nx\n\n```text\n## Sources\n[x](#gone)\n```\n"
            d = make_skill(Path(t), "fenced-quote", body=body)
            self.assertTrue(validate_skill(d).valid)


class SelfReferentialPathLint(unittest.TestCase):
    """R6.2 (ADR 0044): a runnable fenced command anchored at the skill's OWN folder breaks in
    an installed plugin; cross-skill refs, non-runnable fences, and the two escape hatches
    must not be flagged."""

    def test_own_folder_path_in_bash_fence_fails(self):
        # The fix-building-skills-paths defect (#115), reproduced.
        with tempfile.TemporaryDirectory() as t:
            body = "run:\n```bash\npython skills/self-path/scripts/validate.py x\n```\n"
            d = make_skill(Path(t), "self-path", body=body)
            r = validate_skill(d)
            self.assertFalse(r.valid)
            self.assertIn("installed plugin", r.error)

    def test_own_folder_path_without_skills_prefix_also_fails(self):
        with tempfile.TemporaryDirectory() as t:
            body = "```sh\npython self-path/scripts/run.py\n```\n"
            d = make_skill(Path(t), "self-path", body=body)
            self.assertFalse(validate_skill(d).valid)

    def test_own_folder_path_in_reference_fails(self):
        with tempfile.TemporaryDirectory() as t:
            ref = "```bash\npython skills/self-path/scripts/run.py\n```\n"
            d = make_skill(Path(t), "self-path", refs={"r.md": ref})
            r = validate_skill(d)
            self.assertFalse(r.valid)
            self.assertIn("r.md", r.error)

    def test_cross_skill_reference_passes(self):
        # A DIFFERENT skill's folder is a legitimate cross-skill reference.
        with tempfile.TemporaryDirectory() as t:
            body = "```bash\npython skills/other-skill/scripts/tool.py\n```\n"
            d = make_skill(Path(t), "self-path", body=body)
            self.assertTrue(validate_skill(d).valid)

    def test_bare_relative_scripts_path_passes(self):
        with tempfile.TemporaryDirectory() as t:
            body = "```bash\npython scripts/validate.py x\n```\n"
            d = make_skill(Path(t), "self-path", body=body)
            self.assertTrue(validate_skill(d).valid)

    def test_non_runnable_fence_passes(self):
        # Escape hatch 1: a ```text (or tree-diagram) fence is not a runnable command.
        with tempfile.TemporaryDirectory() as t:
            body = "```text\nWRONG: python skills/self-path/scripts/run.py\n```\n"
            d = make_skill(Path(t), "self-path", body=body)
            self.assertTrue(validate_skill(d).valid)

    def test_inline_allow_marker_passes(self):
        # Escape hatch 2: the inline marker suppresses a deliberate worked example.
        with tempfile.TemporaryDirectory() as t:
            body = ("```bash\npython skills/self-path/scripts/run.py  "
                    "# validate:allow-self-path\n```\n")
            d = make_skill(Path(t), "self-path", body=body)
            self.assertTrue(validate_skill(d).valid)

    def test_prose_mention_outside_fence_passes(self):
        with tempfile.TemporaryDirectory() as t:
            body = "The old skills/self-path/scripts/run.py anchor was the defect.\n"
            d = make_skill(Path(t), "self-path", body=body)
            self.assertTrue(validate_skill(d).valid)


class EvalsJsonGate(unittest.TestCase):
    """R7 (ADR 0013): evals/evals.json, when present, matches skill-creator's schema."""

    EVAL = {"id": 1, "prompt": "Do the thing", "expected_output": "The thing, done",
            "expectations": ["Output includes X"]}

    def write_evals(self, d, data):
        (d / "evals").mkdir()
        import json
        (d / "evals" / "evals.json").write_text(json.dumps(data), encoding="utf-8")

    def test_valid_evals_pass(self):
        with tempfile.TemporaryDirectory() as t:
            d = make_skill(Path(t), "with-evals")
            self.write_evals(d, {"skill_name": "with-evals", "evals": [self.EVAL]})
            self.assertTrue(validate_skill(d).valid)

    def test_skill_name_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as t:
            d = make_skill(Path(t), "with-evals")
            self.write_evals(d, {"skill_name": "other", "evals": [self.EVAL]})
            r = validate_skill(d)
            self.assertFalse(r.valid)
            self.assertIn("skill_name", r.error)

    def test_duplicate_ids_fail(self):
        with tempfile.TemporaryDirectory() as t:
            d = make_skill(Path(t), "with-evals")
            self.write_evals(d, {"skill_name": "with-evals", "evals": [self.EVAL, self.EVAL]})
            r = validate_skill(d)
            self.assertFalse(r.valid)
            self.assertIn("duplicate id", r.error)

    def test_empty_expectations_fail(self):
        with tempfile.TemporaryDirectory() as t:
            d = make_skill(Path(t), "with-evals")
            self.write_evals(d, {"skill_name": "with-evals",
                                 "evals": [{**self.EVAL, "expectations": []}]})
            r = validate_skill(d)
            self.assertFalse(r.valid)
            self.assertIn("expectations", r.error)

    def test_invalid_json_fails(self):
        with tempfile.TemporaryDirectory() as t:
            d = make_skill(Path(t), "with-evals")
            (d / "evals").mkdir()
            (d / "evals" / "evals.json").write_text("{not json", encoding="utf-8")
            r = validate_skill(d)
            self.assertFalse(r.valid)
            self.assertIn("not valid JSON", r.error)


if __name__ == "__main__":
    unittest.main()
