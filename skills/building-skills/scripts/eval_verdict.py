#!/usr/bin/env python3
"""Moved: the real script is one21labs/skill-measure:scripts/eval_verdict.py (ADR 0102).

Two frozen dated dirs cite this path in their reproduce steps
(benchmarks/2026-07-08-claude-md-template-ablation-hermetic/README.md:47,
benchmarks/2026-07-10-ep-loophole-oos-hermetic/README.md:68); frozen dirs are never edited
(ADR 0041), so this stub keeps the citation resolvable (ADR 0089). Nothing imports it, so it
carries no forwarding logic — executing it redirects instead of silently succeeding as a no-op.
"""
import sys

if __name__ == "__main__":
    sys.exit("moved: clone https://github.com/one21labs/skill-measure and run "
             "scripts/eval_verdict.py " + " ".join(sys.argv[1:]))
