#!/usr/bin/env python3
"""Forwarding shim: the real module is skill-bench/scripts/lib/bench_io.py (see _forward.py)."""
from _forward import load

load("bench_io", globals())
