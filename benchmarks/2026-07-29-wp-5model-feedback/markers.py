#!/usr/bin/env python3
"""Mechanical, judge-independent counters that separate a real quality effect from an artifact.

Three rival explanations for any positive treatment effect, and the counter that tests each:

  TREATMENT VOCABULARY. The skill supplies a checklist. If the treated arm merely echoes its
  vocabulary, `treatment_markers` rises while feedback quality does not. This is the continuous,
  judge-independent analogue of criterion 6 — it does not depend on a judge noticing.

  GROUNDING. `plan_anchors` counts DISTINCT identifiers from the document under review. Real
  engagement cites the document; generic advice does not. Distinct-counting matters: repeating
  "P1" twelve times is one anchor, not twelve.

  LENGTH. Both counts above rise with output length on their own, so `per_1k` densities are
  reported next to the raw counts. A treated arm that has more markers AND more anchors purely
  because it wrote 3x as much has not given better feedback, and only the density shows that.

Frozen token lists: changing them after seeing results would be picking the measurement to fit
the answer, so they are pre-registered here and not tuned.
"""
import re

# Vocabulary the treatment skill supplies. Frozen 2026-07-29 from
# treatments/writing-plans.SKILL.md before any cell was graded.
TREATMENT_MARKERS = (
    "TDD", "YAGNI", "DRY", "bite-sized", "bite sized", "2-5 minute", "2-5 minutes",
    "Consumes:", "Produces:", "frequent commits", "No Placeholders", "placeholder",
    "Global Constraints", "failing test", "pytest", "git commit", "test-first",
    "writing-plans", "superpowers", "docs/superpowers/plans", "Task Right-Sizing",
    "Self-Review", "checkbox", "Tech Stack:", "Architecture:",
)

# Identifiers belonging to the document under review. Frozen from plan.md.
PLAN_ANCHORS = (
    "P0", "P1", "P2b", "P2", "P3",
    "#303", "#317", "#310", "#302", "#252", "#320", "#321", "#193", "#319", "#318",
    "0024", "0055", "0065", "0066", "0076", "0081", "0089", "0093", "0095", "0096",
    "0097", "0098", "0041", "0052", "0059", "0062",
    "ADOPT", "Inspect AI", "MDE", "G>=8", "G >= 8", "47.9%", "6.6x", "7x-cheaper",
    "10pd", "self-referential spiral", "lever 1", "lever-1", "truth-in-labeling",
    "re-measure", "sweep", "skill-bench", "SkillsBench", "building-skills",
    "optimizing-context", "trigram", "Monte Carlo", "README.md:47", "benchstats.py:186",
)

# The '- [ ]' checkbox literal needs a regex rather than a substring test.
_CHECKBOX = re.compile(r"^\s*[-*]\s*\[\s*[ xX]?\s*\]", re.MULTILINE)
# Top-level list items / numbered headings — the mechanical finding count.
_FINDING = re.compile(r"^\s{0,3}(?:[-*+]\s+|\d+[.)]\s+|#{2,4}\s+)", re.MULTILINE)


def _count_distinct(text, tokens):
    """How many of `tokens` appear at all (DISTINCT), plus total occurrences."""
    lowered = text.lower()
    hits = [t for t in tokens if t.lower() in lowered]
    total = sum(lowered.count(t.lower()) for t in tokens)
    return len(hits), total, hits


def measure(text):
    """All mechanical counters for one response. Pure."""
    text = text or ""
    chars = len(text)
    tm_distinct, tm_total, tm_hits = _count_distinct(text, TREATMENT_MARKERS)
    pa_distinct, pa_total, _ = _count_distinct(text, PLAN_ANCHORS)
    checkboxes = len(_CHECKBOX.findall(text))
    findings = len(_FINDING.findall(text))
    per_1k = (chars / 1000.0) or 1.0
    return {
        "chars": chars,
        "treatment_markers_distinct": tm_distinct,
        "treatment_markers_total": tm_total + checkboxes,
        "treatment_marker_hits": tm_hits,
        "checkboxes": checkboxes,
        "plan_anchors_distinct": pa_distinct,
        "plan_anchors_total": pa_total,
        "findings": findings,
        # Densities: the length-independent versions. A treated arm scoring higher on raw counts
        # but not on these has written more, not better.
        "treatment_markers_per_1k": round((tm_total + checkboxes) / per_1k, 3),
        "plan_anchors_per_1k": round(pa_total / per_1k, 3),
        "chars_per_finding": round(chars / findings, 1) if findings else None,
    }
