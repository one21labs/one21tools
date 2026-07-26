#!/usr/bin/env python3
"""Moved: the real script is skill-bench/scripts/eval_verdict.py (skill-bench extraction, 535b996).

Two frozen dated dirs cite this path in their reproduce steps
(benchmarks/2026-07-08-claude-md-template-ablation-hermetic/README.md:47,
benchmarks/2026-07-10-ep-loophole-oos-hermetic/README.md:68); frozen dirs are never edited
(ADR 0041), so this stub keeps the citation resolvable (ADR 0089). Nothing imports it, so it
carries no forwarding logic — executing it redirects instead of silently succeeding as a no-op.
"""
import sys

if __name__ == "__main__":
    sys.exit("moved: run skill-bench/scripts/eval_verdict.py " + " ".join(sys.argv[1:]))
