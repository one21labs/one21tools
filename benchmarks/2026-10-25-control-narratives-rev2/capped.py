"""A reply cut off at the output cap: scored failed, never regenerated (metadata.json grid). And
the cell's final error, which decides between that and a regenerated ERROR cell.

Its own module so a test can check both against the harness's real messages without loading the
frozen evals grid.py reads at import (capped_test.py)."""

CAP_HIT_PREFIX = "output hit the "  # hermetic_driver.summarize_call's error for a capped reply
FAKE_TOOL_MARKUP = ("<invoke", "<function_calls", "</invoke>")


def cap_hit(record):
    """Regenerating until a reply fits would select away a length effect of the treatment."""
    return (record["summary"]["error"] or "").startswith(CAP_HIT_PREFIX)


def cell_error(summary, response):
    """summarize_call's error, overridden where the harness cannot decide. An envelope naming no
    model cannot be shown to be the requested one, so it is an ERROR even past the cap. Tool-call
    markup in a no-tools reply is acting out an agent loop: infrastructure, never quality (#191),
    though a capped reply keeps its cap verdict."""
    error = summary["error"]
    if not summary["served_models"] and (not error or error.startswith(CAP_HIT_PREFIX)):
        return "envelope names no served model"
    if not error and any(t in response for t in FAKE_TOOL_MARKUP):
        return "fake tool-call markup in a no-tools reply"
    return error
