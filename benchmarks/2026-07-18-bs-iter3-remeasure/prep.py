#!/usr/bin/env python3
"""Write the two treatment bodies (ADR 0027 arm construction; derive, don't duplicate).

with-old = building-skills SKILL.md body at the pinned main SHA (metadata.json:arms);
with-new = the iter-3 draft body from the working tree. Frontmatter stripped from both.
Asserts the two differ and records codepoint counts (the merge bar's cost prong).
"""
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PIN = "78e6a0c06f65f83092009b2f69290887803ace5d"


def strip_front(text):
    return text.split("---", 2)[2].strip() if text.startswith("---") else text.strip()


def main():
    old = strip_front(subprocess.run(
        ["git", "show", f"{PIN}:skills/building-skills/SKILL.md"],
        capture_output=True, text=True, check=True, cwd=REPO).stdout)
    new = strip_front((REPO / "skills" / "building-skills" / "SKILL.md").read_text(encoding="utf-8"))
    assert old != new, "treatments identical — wrong branch or unapplied draft"
    t = HERE / "treatments"
    t.mkdir(exist_ok=True)
    (t / "building-skills.with-old.txt").write_text(old, encoding="utf-8")
    (t / "building-skills.with-new.txt").write_text(new, encoding="utf-8")
    costs = {"body_chars": {"with-old": len(old), "with-new": len(new)},
             "chars_delta": len(new) - len(old), "pin": PIN}
    (t / "costs.json").write_text(json.dumps(costs, indent=1) + "\n", encoding="utf-8")
    print(f"treatments written; body codepoints old={len(old)} new={len(new)} "
          f"delta={len(new) - len(old):+d}")


if __name__ == "__main__":
    main()
