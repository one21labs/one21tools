#!/usr/bin/env python3
"""Arm-tell stripping for the writing-plans feedback assay.

WHY THIS EXISTS: the treatment skill body does not merely advise — it MANDATES a self-identifying
announcement ("Announce at start: 'I'm using the writing-plans skill to create the implementation
plan.'"), prescribes `superpowers:` sub-skill names, a `docs/superpowers/plans/` save path, and a
two-option execution-handoff offer. Any of these surviving into a graded artifact tells the judge
exactly which arm it is grading, and a judge that knows the arm is not a blind judge. The whole
measurement would be worthless.

Stripping is deliberately CONSERVATIVE about content: it removes the self-identifying markers and
nothing else, so it cannot quietly delete substantive feedback and shrink an arm's score. Every
strip is counted and the counts are reported per arm — an asymmetric strip rate is itself a
finding, not something to hide.
"""
import re

# Each entry: (name, compiled pattern, replacement). Patterns are line- or phrase-scoped so a
# strip removes a marker, never a paragraph of real feedback.
_RULES = [
    # The mandated announcement, in any of the phrasings models actually emit.
    ("announcement", re.compile(
        r"^.*\bI(?:'m| am)\s+using\s+the\s+[`*_]*writing-plans[`*_]*\s+skill\b.*$",
        re.IGNORECASE | re.MULTILINE), ""),
    ("announcement_third_person", re.compile(
        r"^.*\b(?:using|applying|invoking|per|following)\s+the\s+[`*_]*writing-plans[`*_]*"
        r"\s+skill\b.*$", re.IGNORECASE | re.MULTILINE), ""),
    # Any residual bare mention of the skill by name.
    ("skill_name", re.compile(r"[`*_]*\bwriting-plans\b[`*_]*", re.IGNORECASE), "the plan guidance"),
    # Plugin-namespaced sub-skill references (superpowers:executing-plans, etc).
    ("superpowers_ns", re.compile(r"\bsuperpowers:[a-z0-9-]+", re.IGNORECASE), "a companion process"),
    # The prescribed save path.
    ("superpowers_path", re.compile(r"docs/superpowers/plans/[^\s`)\]]*", re.IGNORECASE),
     "the plans directory"),
    # Residual bare mentions of the source plugin.
    ("superpowers_word", re.compile(r"\bsuperpowers\b", re.IGNORECASE), "the plugin"),
    # The REQUIRED SUB-SKILL directive block the header template mandates.
    ("required_subskill", re.compile(r"^.*\bREQUIRED SUB-SKILL\b.*$", re.MULTILINE), ""),
    ("for_agentic_workers", re.compile(r"^\s*>\s*\*\*For agentic workers:\*\*.*$", re.MULTILINE), ""),
]


def detect_tells(text):
    """Which tell classes appear, and how many times each. Pure; used for the pre-grading audit."""
    text = text or ""
    return {name: len(pat.findall(text)) for name, pat, _ in _RULES if pat.search(text)}


def strip_tells(text):
    """Return (clean_text, {tell_name: n_removed}). Conservative: markers only.

    The blank-line collapse runs ONLY when something was actually stripped. It exists to close the
    gaps a whole-line strip leaves behind (layout is itself a weak tell), but applied
    unconditionally it would also reflow untouched control-arm text, making `chars_removed` report
    edits to an arm nothing was removed from. Keeping it conditional is what lets a caller treat
    "no tells found" as "byte-identical apart from trailing whitespace".
    """
    text = (text or "").strip()
    counts = {}
    for name, pat, repl in _RULES:
        text, n = pat.subn(repl, text)
        if n:
            counts[name] = n
    if counts:
        text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip(), counts


def strip_report(records, text_fn, arm_key="arm"):
    """Per-arm strip summary for the pre-grading audit.

    An arm whose cells need no stripping and an arm whose cells all do is EXPECTED here (only the
    treatment mandates the announcement). What would be alarming is residual tells AFTER stripping,
    which `residual_after_strip` reports and which must be 0 before grading proceeds.
    """
    out = {}
    for r in records:
        arm = r[arm_key]
        raw = text_fn(r) or ""
        clean, counts = strip_tells(raw)
        slot = out.setdefault(arm, {"n": 0, "cells_stripped": 0, "by_tell": {},
                                    "residual_after_strip": 0, "chars_removed": 0})
        slot["n"] += 1
        if counts:
            slot["cells_stripped"] += 1
            for k, v in counts.items():
                slot["by_tell"][k] = slot["by_tell"].get(k, 0) + v
        # Measured against the trimmed original, so trailing-whitespace normalisation is never
        # reported as removed content.
        slot["chars_removed"] += (len(raw.strip()) - len(clean)) if counts else 0
        if detect_tells(clean):
            slot["residual_after_strip"] += 1
    return out
