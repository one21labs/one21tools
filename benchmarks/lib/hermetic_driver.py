#!/usr/bin/env python3
"""Forwarding shim: the real module is skill-bench/scripts/lib/hermetic_driver.py (see _forward.py).

Missing from the original shim set (issue #229), which covered bench_io, verdict and
mechanized_checks. Eleven `from hermetic_driver import ...` lines across frozen dated dirs raised
ModuleNotFoundError while their three siblings resolved fine — so the shim layer looked complete
and was not. Frozen dirs are never edited (ADR 0041), so the path end has to survive here.
"""
from _forward import load

load("hermetic_driver", globals())
