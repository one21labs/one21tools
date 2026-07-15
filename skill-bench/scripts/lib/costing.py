#!/usr/bin/env python3
"""Notional (shadow) cost accounting for skill-bench (ADR 0055).

Grok (grok.com subscription) AND Claude (Claude Max) are both MARGINALLY free here — a run adds no
per-call API charge. But every run consumes real usage (quota, rate limits, underlying compute), so
"free" hides a real cost. This module prices any run at PUBLISHED per-token API rates from the token
usage the CLIs report, so the cost is understood regardless of billing mode. Stdlib only.

Rates are per 1,000,000 tokens (USD). Anthropic figures from the claude-api reference (cached
2026-06-24); grok-4.5 from xAI published pricing. Anthropic cache multipliers: cache_read = 0.1x
input, cache_write = 1.25x input (5-minute-TTL model). grok-4.5 cache figures are in the PRICES
table (cache_read 0.25x input; cache_write approximated at the Anthropic 1.25x multiplier).
"""

PRICES = {
    # model: {input, output, cache_read, cache_write}  USD per 1M tokens
    "grok-4.5":         {"input": 2.00, "output": 6.00,  "cache_read": 0.50, "cache_write": 2.50},
    "claude-opus-4-8":  {"input": 5.00, "output": 25.00, "cache_read": 0.50, "cache_write": 6.25},
    "claude-opus-4-7":  {"input": 5.00, "output": 25.00, "cache_read": 0.50, "cache_write": 6.25},
    "claude-sonnet-5":  {"input": 3.00, "output": 15.00, "cache_read": 0.30, "cache_write": 3.75},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00, "cache_read": 0.30, "cache_write": 3.75},
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00,  "cache_read": 0.10, "cache_write": 1.25},
}

# Friendly-name / judge-name aliases -> a PRICES key.
_ALIASES = {
    "grok": "grok-4.5",
    "claude": "claude-opus-4-8",
    "claude-opus": "claude-opus-4-8",
    "opus": "claude-opus-4-8",
    "sonnet": "claude-sonnet-5",
    "haiku": "claude-haiku-4-5",
}


def resolve_model(name):
    if name in PRICES:
        return name
    if name in _ALIASES:
        return _ALIASES[name]
    raise KeyError(f"no price for model {name!r} (known: {sorted(PRICES) + sorted(_ALIASES)})")


def extract_usage(envelope):
    """Pull a normalized usage dict from a grok/claude --output-format json envelope.
    Both put token counts under `usage` with snake_case keys; missing keys -> 0."""
    u = (envelope or {}).get("usage", {}) or {}
    return {
        "input_tokens": int(u.get("input_tokens", 0) or 0),
        "output_tokens": int(u.get("output_tokens", 0) or 0),
        "cache_read_input_tokens": int(u.get("cache_read_input_tokens", 0) or 0),
        "cache_creation_input_tokens": int(u.get("cache_creation_input_tokens", 0) or 0),
    }


def notional_cost(model, usage):
    """USD a run WOULD cost at published API rates. `usage` is an extract_usage() dict (or a superset).
    input_tokens is the uncached remainder; cache reads/writes are priced separately (Anthropic model)."""
    p = PRICES[resolve_model(model)]
    return (
        usage.get("input_tokens", 0) * p["input"]
        + usage.get("output_tokens", 0) * p["output"]
        + usage.get("cache_read_input_tokens", 0) * p["cache_read"]
        + usage.get("cache_creation_input_tokens", 0) * p["cache_write"]
    ) / 1_000_000.0


def add_usage(acc, more):
    """In-place accumulate one usage dict into another (all four token counters)."""
    for k in ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"):
        acc[k] = acc.get(k, 0) + int(more.get(k, 0) or 0)
    return acc
