"""A reply cut off at the output cap: scored failed, never regenerated (metadata.json grid).

Its own module so a test can check it against the harness's real message without loading the
frozen evals grid.py reads at import (capped_test.py)."""

CAP_HIT_PREFIX = "output hit the "  # hermetic_driver.summarize_call's error for a capped reply


def cap_hit(record):
    """Regenerating until a reply fits would select away a length effect of the treatment."""
    return (record["summary"]["error"] or "").startswith(CAP_HIT_PREFIX)
