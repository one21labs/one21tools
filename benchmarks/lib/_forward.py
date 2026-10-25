#!/usr/bin/env python3
"""Loader for the benchmarks/lib forwarding shims (issue #229).

benchmarks/lib's helpers now live in the standalone skill-measure repo (ADR 0102), but frozen
dated dirs still `sys.path.insert` this directory (ADR 0041: frozen dirs are never edited).
Each shim module here loads its real counterpart by file path from the checkout named by
$SKILL_MEASURE_ROOT — a plain `import` would resolve back to the shim itself, since this
directory shadows the real one on the caller's sys.path.
"""
import importlib.util
import os
import sys
from pathlib import Path

CLONE_HINT = ("set SKILL_MEASURE_ROOT to a skill-measure checkout: git clone "
              "https://github.com/one21labs/skill-measure && export SKILL_MEASURE_ROOT=$PWD/skill-measure "
              "(to reproduce a dated run exactly, check out one21tools at that run's own commit instead)")


def real_lib():
    """The harness lib dir, or exit naming the remedy — a missing checkout is not a silent no-op."""
    root = os.environ.get("SKILL_MEASURE_ROOT")
    lib = Path(root) / "scripts" / "lib" if root else None
    if lib is None or not lib.is_dir():
        sys.exit(f"benchmarks/lib: harness not found ({root or 'SKILL_MEASURE_ROOT unset'}) — {CLONE_HINT}")
    return lib


def load(name, into):
    """Execute skill-measure's `<name>.py` and copy its public names into the shim's globals."""
    spec = importlib.util.spec_from_file_location(f"_skill_measure_{name}", real_lib() / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    into.update({k: v for k, v in vars(mod).items() if not k.startswith("_")})
