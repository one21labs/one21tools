#!/usr/bin/env python3
"""Forwarding shim: the real module is skill-bench/scripts/lib/mechanized_checks.py (see _forward.py)."""
from _forward import load

load("mechanized_checks", globals())
