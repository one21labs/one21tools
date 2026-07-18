#!/usr/bin/env python3
"""Loader for the benchmarks/lib forwarding shims (issue #229).

benchmarks/lib moved to skill-bench/scripts/lib (ADR 0055 extraction), but frozen dated dirs
committed before the move still `sys.path.insert` this directory (ADR 0026: frozen dirs are
never edited). Each shim module here loads its real counterpart by file path — a plain
`import` would resolve back to the shim itself, since this directory shadows the real one on
the caller's sys.path.
"""
import importlib.util
from pathlib import Path

_REAL_LIB = Path(__file__).resolve().parents[2] / "skill-bench" / "scripts" / "lib"


def load(name, into):
    """Execute skill-bench's `<name>.py` and copy its public names into the shim's globals."""
    spec = importlib.util.spec_from_file_location(f"_skill_bench_{name}", _REAL_LIB / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    into.update({k: v for k, v in vars(mod).items() if not k.startswith("_")})
