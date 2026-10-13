#!/usr/bin/env python3
"""Hard pre-grid spend stop (ADR 0052 decision 3, discharging ADR 0042's gate-script trigger):
project a full grid's cost from the cost-pilot's measured cells and EXIT NONZERO when the
projection exceeds the pre-registered ceiling. A gate that can only advise gets spent past
(ADR 0042 records a 216-cell grid run past a ~5-cell decidable gate); this one is a command a
harness runs between pilot and grid, so the grid step cannot start on an over-cap projection
without visibly bypassing it.

CLI: cost_gate.py --cells N --pilot-cost-usd X [X ...] --ceiling-usd C
Exit 0 = projection within ceiling (prints the projection); exit 1 = over ceiling (halt, record
the pilot as the artifact, route to a fresh /decide per ADR 0052's revisit trigger).
"""
import argparse
import json
import math
import sys
from pathlib import Path


# Charged for a failed call (no envelope, so no measured cost) when no pilot estimate exists yet
# (prescreen, pilot). A metadata.json cost block may override it as failed_call_charge_usd.
DEFAULT_FAILED_CALL_CHARGE_USD = 0.15


def charged_usd(cost_usd, estimate_usd):
    """What a finished call is charged: its measured cost, or estimate_usd when the call failed
    and reported none. A timeout or nonzero exit bills real usage with no envelope, so charging
    $0 let a run of failing calls never reach the backstop."""
    return estimate_usd if cost_usd is None else cost_usd


def cell_spend(rec):
    """Spend one cell record accounts for: max(cell_cost_usd, charged_usd) for its own attempt
    plus prior_attempts_usd carried forward from the records it overwrote. ERROR cells count —
    their calls were billed whether or not the cell is regenerated."""
    s = rec.get("summary") or {}
    return (max(s.get("cell_cost_usd") or 0.0, s.get("charged_usd") or 0.0)
            + (s.get("prior_attempts_usd") or 0.0))


def spent_so_far(out_dir):
    """Cumulative cell_spend of every cell record in out_dir.

    Seeds a resumed run's spend counter: a runner that restarts its counter at 0 compares only
    the current invocation's spend against the full ceiling, so a checkpoint/resume sequence
    can silently exceed the pre-registered ceiling (#233 — the #214 resumed grid printed $6.09
    where the true 30-cell total was $7.40). Malformed cells are skipped (they re-run anyway);
    a missing dir is $0.
    """
    total = 0.0
    for p in sorted(Path(out_dir).glob("*.json")):
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        total += cell_spend(rec)
    return total


def admit(spent_usd, reserved_usd, estimate_usd, cap_usd):
    """Pre-launch backstop: True iff one more call at estimate_usd fits under cap_usd beside the
    recorded spend and the estimates reserved by calls still in flight. Checked (and reserved)
    BEFORE each launch: a post-hoc check lets every in-flight call overshoot the cap, and a
    resume re-enters with spend already at the cap."""
    if not (math.isfinite(cap_usd) and math.isfinite(estimate_usd) and estimate_usd > 0):
        raise ValueError("cap must be finite and estimate finite and positive")
    return spent_usd + reserved_usd + estimate_usd <= cap_usd


def project_grid_cost(cells_total, pilot_cell_costs):
    """Projected full-grid cost: mean measured per-cell cost x total cells.

    The mean (not min) is the projection basis — a pilot's cheapest cell understates arm C's
    variance, and the gate exists to stop optimistic overruns. A zero or non-finite cost is a
    broken measurement, not a free cell: it would pass any ceiling.
    """
    if cells_total <= 0:
        raise ValueError("cells_total must be positive")
    if not pilot_cell_costs or not all(math.isfinite(c) and c > 0 for c in pilot_cell_costs):
        raise ValueError("pilot_cell_costs must be non-empty, finite and positive")
    return cells_total * (sum(pilot_cell_costs) / len(pilot_cell_costs))


def gate(cells_total, pilot_cell_costs, ceiling_usd):
    """Returns (ok: bool, projected_usd: float). ok is False when projected > ceiling."""
    if not math.isfinite(ceiling_usd):
        raise ValueError("ceiling_usd must be finite")
    projected = project_grid_cost(cells_total, pilot_cell_costs)
    return projected <= ceiling_usd, projected


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cells", type=int, required=True, help="total cells in the full grid")
    p.add_argument("--pilot-cost-usd", type=float, nargs="+", required=True,
                   help="measured per-cell cost of each pilot cell (claude -p envelope total_cost_usd)")
    p.add_argument("--ceiling-usd", type=float, required=True,
                   help="pre-registered grid ceiling from the benchmark's metadata.json")
    args = p.parse_args(argv)
    ok, projected = gate(args.cells, args.pilot_cost_usd, args.ceiling_usd)
    status = "WITHIN" if ok else "OVER"
    print(f"projected ${projected:.2f} for {args.cells} cells vs ceiling ${args.ceiling_usd:.2f} — {status}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
