"""The harness left this repo (ADR 0102): $SKILL_MEASURE_ROOT, else a sibling skill-measure
checkout. Importing this puts its scripts/lib on sys.path, or exits naming the remedy, never a
bare ImportError. The one home for the path and the clone remedy; every script here imports it."""
import os
import sys
from pathlib import Path

HARNESS = Path(os.environ.get("SKILL_MEASURE_ROOT") or Path(__file__).resolve().parents[3] / "skill-measure")
CLONE = "git clone https://github.com/one21labs/skill-measure && export SKILL_MEASURE_ROOT=$PWD/skill-measure"
if not (HARNESS / "scripts" / "lib").is_dir():
    sys.exit(f"harness not found at {HARNESS}: {CLONE}")
sys.path.insert(0, str(HARNESS / "scripts" / "lib"))
