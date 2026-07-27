#!/usr/bin/env python3
"""Forwarding shim: the real module is skill-bench/scripts/lib/cost_gate.py (see _forward.py).

Missing from the original shim set (issue #229) alongside hermetic_driver. Frozen dirs that
insert `HERE.parent / "lib"` import this name and raised ModuleNotFoundError, while the shims
that did exist resolved — so the layer looked complete. Frozen dirs are never edited (ADR 0041),
so the path end has to survive here.
"""
from _forward import load

load("cost_gate", globals())
