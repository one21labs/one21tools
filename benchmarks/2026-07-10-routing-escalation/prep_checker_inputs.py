#!/usr/bin/env python3
"""Extract the 24 haiku gradient cells (8 evals x 3 reps) from the fullgrid substrate into
checker_inputs.json: [{skill, eval_id, rep, prompt, response}]. Offline, no claude calls.

Gradient evals are read from metadata.json (the pre-registration), the task prompts from the
fullgrid's evals_args.json, and the haiku responses from its outputs/cells/*.json.
"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
FULLGRID = os.path.join(BASE, "..", "2026-07-10-tiered-execution-fullgrid")
REPS = 3


def main():
    with open(os.path.join(BASE, "metadata.json"), encoding="utf-8") as fh:
        gradient = json.load(fh)["design"]["gradient_evals"]
    with open(os.path.join(FULLGRID, "evals_args.json"), encoding="utf-8") as fh:
        prompts = {f"{e['skill']}.{e['eval_id']}": e["prompt"] for e in json.load(fh)}

    items = []
    for key in gradient:
        skill, eval_id = key.rsplit(".", 1)
        for rep in range(1, REPS + 1):
            cell_path = os.path.join(FULLGRID, "outputs", "cells",
                                     f"haiku-solo.{skill}.{eval_id}.r{rep}.json")
            with open(cell_path, encoding="utf-8") as fh:
                cell = json.load(fh)
            if not cell.get("response"):
                raise SystemExit(f"ERROR: empty haiku response in {cell_path}")
            items.append({"skill": skill, "eval_id": eval_id, "rep": rep,
                          "prompt": prompts[key], "response": cell["response"]})

    out = os.path.join(BASE, "checker_inputs.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(items, fh, indent=1)
    print(f"wrote {len(items)} checker inputs -> {out}")


if __name__ == "__main__":
    main()
