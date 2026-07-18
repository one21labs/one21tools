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
import sys
from pathlib import Path


def spent_so_far(out_dir):
    """Cumulative cell_cost_usd of existing NON-ERROR cell records in out_dir.

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
        summary = rec.get("summary") or {}
        if not summary.get("error"):
            total += summary.get("cell_cost_usd") or 0.0
    return total


def project_grid_cost(cells_total, pilot_cell_costs):
    """Projected full-grid cost: mean measured per-cell cost x total cells.

    The mean (not min) is the projection basis — a pilot's cheapest cell understates arm C's
    variance, and the gate exists to stop optimistic overruns.
    """
    if cells_total <= 0:
        raise ValueError("cells_total must be positive")
    if not pilot_cell_costs or any(c < 0 for c in pilot_cell_costs):
        raise ValueError("pilot_cell_costs must be non-empty and non-negative")
    return cells_total * (sum(pilot_cell_costs) / len(pilot_cell_costs))


def gate(cells_total, pilot_cell_costs, ceiling_usd):
    """Returns (ok: bool, projected_usd: float). ok is False when projected > ceiling."""
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
