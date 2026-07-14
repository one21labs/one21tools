#!/usr/bin/env python3
"""Contamination sweeps for benchmark runs (owner directive 2026-07-13: eliminate ruthlessly).

Three checks, all mechanical, run BEFORE a verdict is recorded:

1. sweep_records(records, tells) — outcome-tell / path-escape scan over generated cell records.
   `tells` maps scenario -> [regex...] of facts that exist ONLY post-outcome (e.g. the measured
   blowup numbers of the decision being backtested), plus GLOBAL patterns applied to every cell
   (host-repo paths, harness names — a cell citing them escaped its sandbox). A hit means the
   cell KNEW something it could not know: quarantine the cell, find the channel.
2. sweep_tree(root, tells) — bench-tell scan over a substrate tree AND its full git history
   (defect class names, manifest field names, 'planted', 'pre-registration', ...). A substrate
   that names its own seeds grades the control arm's rule-reading, not its defect-finding.
3. sanitized_plugin_dir(src, dst) — copy a plugin for mounting into cells WITHOUT its
   documentation surface (README/docs/CHANGELOG): the live README may carry measurement
   results about the very skills under test. Skills/agents/hooks/manifest are kept —
   behavior identical, knowledge channel closed.

Stdlib only. Pure helpers; callers decide halt-vs-record per their pre-registration.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

GLOBAL_TELLS = [r"one21tools-route-i2", r"one21tools-wt", r"judge-sensitiv",
                r"skill-bench", r"hermetic_driver", r"cost_gate"]
PLUGIN_DOC_SURFACE = ("README.md", "README", "CHANGELOG.md", "docs")


def _record_text(rec):
    return ((rec.get("response") or "")
            + json.dumps(rec.get("artifacts") or {})
            + json.dumps(rec.get("probes") or {}))


def sweep_records(records, tells, global_tells=None):
    """records: iterable of cell dicts (needs 'scenario'; 'cell' names the hit).
    Returns [(cell, pattern), ...] — empty means clean."""
    hits = []
    gt = GLOBAL_TELLS if global_tells is None else global_tells
    for rec in records:
        text = _record_text(rec)
        for pat in list(tells.get(rec.get("scenario"), [])) + list(gt):
            if re.search(pat, text, re.I):
                hits.append((rec.get("cell") or rec.get("bid") or "?", pat))
    return hits


def sweep_tree(root, tells):
    """Scan a directory tree (excluding .git internals) and each contained git repo's
    full history for any of `tells` (plain strings). Returns [(where, tell), ...]."""
    root = Path(root)
    hits = []
    pat = re.compile("|".join(re.escape(t) for t in tells), re.I)
    for p in root.rglob("*"):
        if p.is_dir() or ".git" in p.parts:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        m = pat.search(text)
        if m:
            hits.append((str(p.relative_to(root)), m.group(0)))
    for git in root.rglob(".git"):
        repo = git.parent
        out = subprocess.run(["git", "-C", str(repo), "log", "--all", "-p"],
                             capture_output=True, text=True)
        m = pat.search(out.stdout or "")
        if m:
            hits.append((str(repo.relative_to(root)) + " (history)", m.group(0)))
    return hits


def sanitized_plugin_dir(src, dst):
    """Copy plugin `src` to `dst` minus its documentation surface. Returns dst (str)."""
    src, dst = Path(src), Path(dst)
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*PLUGIN_DOC_SURFACE))
    kept = {p.name for p in dst.iterdir()}
    for banned in PLUGIN_DOC_SURFACE:
        if banned in kept:
            raise RuntimeError(f"sanitize failed: {banned} survived in {dst}")
    return str(dst)
