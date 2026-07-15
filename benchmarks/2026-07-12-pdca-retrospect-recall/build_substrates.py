#!/usr/bin/env python3
"""Deterministic Instrument 1 substrate builder (issue #172, ADR 0052; stdlib only).

Builds the 8 synthetic session repos this grid retrospects, under ./substrates/ (gitignored
-- regenerable, home is this script, per benchmarks/lib/README.md's convention):

    substrates/{T1..T6,C1,C2}/origin.git   bare origin (clean base = main)
    substrates/{T1..T6,C1,C2}/repo/        work clone; the session lives on branch `work`
    substrates/sites.json                  {substrate, class, site} for every planted seed

Each repo is one21tools-shaped but names an UNRELATED toy project (a Markdown linter, a data
pipeline, a static-map generator, ...): a mini CLAUDE.md stating the house rules, docs/, a
gate script + its paired test + a version writer, a mini docs/decisions/, and a
plugin.json/marketplace.json manifest pair. Seeds are planted EXACTLY per seeds.json's
assignment (K=4 per T substrate, each defect class in exactly 3 substrates); C1/C2 carry zero
seeds and 2-3 innocuous-but-suspicious patterns (a rationalised revert, a big single-concern
commit, a version bump done correctly through the script).

The manifest (seeds.json / README.md) is FROZEN; this script fills each seed's resolved site
without touching class, assignment, or predicate. Two build-time guards run automatically:
  * leak check -- no distinctive manifest phrase (class ids, `found_iff`, `plant_spec`) appears
    verbatim in any substrate file; class CONTENT is planted, never manifest vocabulary.
  * verify -- every recorded site resolves (commit in `origin/main..work`, or file:line present
    with the expected shape).
Run with --check to prove determinism: two independent builds yield identical seed sites.

Determinism: fixed author/committer identity + pinned GIT_AUTHOR_DATE/GIT_COMMITTER_DATE with an
explicit +0000 offset (so SHAs do not depend on the host timezone), and fully static content.

    python3 build_substrates.py          # build ./substrates/ + sites.json, then guard+verify
    python3 build_substrates.py --check   # build twice in temp dirs, assert identical sites
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "substrates"

# Distinctive manifest phrases that must NEVER appear verbatim in substrate text (requirement 5).
LEAK_TOKENS = [
    "found_iff", "found-iff", "plant_spec",
    "backstory-drift", "one-home-violation", "gate-piped-filter",
    "missing-retrospective-line", "unpointed-amendment", "two-dot-range",
    "sacred-no-test", "hand-edited-version",
]

# Frozen assignment (seeds.json). Kept here only to iterate; the source of truth is seeds.json.
ASSIGN = {
    "T1": ["backstory-drift", "one-home-violation", "gate-piped-filter", "missing-retrospective-line"],
    "T2": ["unpointed-amendment", "two-dot-range", "sacred-no-test", "hand-edited-version"],
    "T3": ["backstory-drift", "gate-piped-filter", "unpointed-amendment", "sacred-no-test"],
    "T4": ["one-home-violation", "missing-retrospective-line", "two-dot-range", "hand-edited-version"],
    "T5": ["backstory-drift", "missing-retrospective-line", "two-dot-range", "sacred-no-test"],
    "T6": ["one-home-violation", "gate-piped-filter", "unpointed-amendment", "hand-edited-version"],
}
CLEAN = ["C1", "C2"]

# Per-substrate surface identity + the concrete strings each planted class needs. Varied so no
# two cells read as near-duplicates. None of these mention the real project or this measurement.
CFG = {
    "T1": dict(
        proj="quillmark", tag="lints Markdown docs for small writing teams", unit="line",
        author=("Rae Okafor", "rae@quillmark.dev"), start="2026-02-03",
        fact="Quillmark skips any path listed in `.quillignore`.",
        old_name="mdcheck", old_flag="wrap",
        gate_from=100, ver="0.2.0",
        adr2_slug="advisory-warnings", adr2_title="Lint warnings are advisory",
        adr2_from="Warnings are advisory and never fail the build.",
        adr2_to="Warnings fail the build when run with `--strict`.",
        pr_feature="tidy the docs and quiet CI noise"),
    "T2": dict(
        proj="streamforge", tag="a batch data-pipeline CLI", unit="record",
        author=("Tomas Vance", "tomas@streamforge.io"), start="2026-03-05",
        fact="Streamforge checkpoints progress every 1000 records.",
        old_name="pipekit", old_flag="chunk",
        gate_from=80, gate_to=120, ver="0.2.0", ver_to="0.3.0",
        adr2_slug="retry-policy", adr2_title="Retry policy for failed batches",
        adr2_from="Failed batches are retried at most 3 times.",
        adr2_to="Failed batches are retried at most 5 times.",
        pr_feature="tune retries and cut the 0.3.0 release"),
    "T3": dict(
        proj="cartostatic", tag="renders static maps from GeoJSON", unit="feature",
        author=("Lin Mercado", "lin@cartostatic.org"), start="2026-04-07",
        fact="Cartostatic renders at zoom level 12 unless told otherwise.",
        old_name="tilegen", old_flag="zoom",
        gate_from=90, gate_to=110, ver="0.2.0",
        adr2_slug="tile-cache", adr2_title="Render cache size",
        adr2_from="The render cache keeps the last 200 tiles.",
        adr2_to="The render cache keeps the last 500 tiles.",
        pr_feature="speed up rendering and record the cache decision"),
    "T4": dict(
        proj="ledgerlint", tag="checks double-entry ledgers", unit="entry",
        author=("Priya Anand", "priya@ledgerlint.app"), start="2026-05-09",
        fact="Ledgerlint treats any amount under 0.01 as zero.",
        old_name="bookcheck", old_flag="round",
        gate_from=100, ver="0.4.0", ver_to="0.5.0",
        adr2_slug="currency-scope", adr2_title="Supported currencies",
        adr2_from="Only USD and EUR ledgers are validated.",
        adr2_to="USD, EUR, and GBP ledgers are validated.",
        pr_feature="fix rounding and cut the 0.5.0 release"),
    "T5": dict(
        proj="harborctl", tag="a container-deploy CLI", unit="manifest line",
        author=("Devon Ruiz", "devon@harborctl.sh"), start="2026-06-01",
        fact="Harborctl pulls the `latest` tag when no digest is pinned.",
        old_name="dockman", old_flag="pull-always",
        gate_from=100, gate_to=140, ver="0.2.0",
        adr2_slug="rollback-window", adr2_title="Rollback window",
        adr2_from="Keep the last 2 releases for rollback.",
        adr2_to="Keep the last 4 releases for rollback.",
        pr_feature="clean up the deploy flow"),
    "T6": dict(
        proj="prosepack", tag="packages ebooks from Markdown", unit="paragraph",
        author=("Mara Ito", "mara@prosepack.press"), start="2026-01-06",
        fact="Prosepack embeds every font referenced by the stylesheet automatically.",
        old_name="bookbind", old_flag="embed-all",
        gate_from=100, ver="0.1.0", ver_to="0.2.0",
        adr2_slug="chapter-split", adr2_title="Chapter splitting",
        adr2_from="Chapters over 50k words are split automatically.",
        adr2_to="Chapters over 80k words are split automatically.",
        pr_feature="improve font handling and cut the 0.2.0 release"),
    "C1": dict(
        proj="tessellate", tag="tiles large images for the web", unit="row",
        author=("Sasha Bell", "sasha@tessellate.dev"), start="2026-02-20",
        fact="Tessellate emits 256px tiles by default.",
        old_name="", old_flag="",
        gate_from=100, ver="0.2.0", ver_to="0.3.0",
        adr2_slug="tile-format", adr2_title="Default tile format",
        adr2_from="Tiles are written as PNG.",
        adr2_to="Tiles are written as PNG.",
        feature="an experimental parallel tiler",
        revert_reason="it raced with the shared tile cache and produced torn output",
        pr_feature="tiling reliability and the 0.3.0 release"),
    "C2": dict(
        proj="cronweave", tag="a small cron-style job scheduler", unit="rule",
        author=("Noor Haddad", "noor@cronweave.io"), start="2026-03-22",
        fact="Cronweave runs missed jobs once on the next startup.",
        old_name="", old_flag="",
        gate_from=100, ver="0.5.0", ver_to="0.6.0",
        adr2_slug="misfire-policy", adr2_title="Misfire policy",
        adr2_from="A missed job runs once on the next startup.",
        adr2_to="A missed job runs once on the next startup.",
        feature="an in-memory result cache",
        revert_reason="it dropped results under a scheduler restart race",
        pr_feature="scheduler reliability and the 0.6.0 release"),
}

AUTHOR_FALLBACK = ("dev", "dev@example.com")


# ---------------------------------------------------------------------------- git plumbing

def run(args, cwd=None, env=None):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True, env=env).stdout


def date_iter(start_iso):
    d0 = datetime.fromisoformat(start_iso)
    k = 0
    while True:
        yield (d0 + timedelta(days=k)).strftime("%Y-%m-%dT10:00:00 +0000")
        k += 1


class Repo:
    """A work clone whose commits land on `origin/main..work` deterministically."""

    def __init__(self, root, cfg):
        self.root = root
        self.author = cfg["author"]
        self.dates = date_iter(cfg["start"])

    def commit(self, msg):
        date = next(self.dates)
        env = {
            **os.environ,
            "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date,
            "GIT_AUTHOR_NAME": self.author[0], "GIT_AUTHOR_EMAIL": self.author[1],
            "GIT_COMMITTER_NAME": self.author[0], "GIT_COMMITTER_EMAIL": self.author[1],
        }
        run(["git", "add", "-A"], cwd=self.root)
        run(["git", "commit", "-q", "-m", msg], cwd=self.root, env=env)
        return run(["git", "rev-parse", "--short=12", "HEAD"], cwd=self.root).strip()

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def read(self, rel):
        return (self.root / rel).read_text()


# ---------------------------------------------------------------------------- file templates

def claude_md(cfg):
    p = cfg["proj"].capitalize()
    return (
        f"# {cfg['proj']}\n\n"
        f"{p} {cfg['tag']}. House rules -- the gate enforces some, the rest are on the author.\n\n"
        f"- Sacred gate: run `python3 scripts/gate.py docs` bare and read its exit code. Never "
        f"pipe it through a filter -- a pipe reports the filter's status, not the gate's.\n"
        f"- Docs: state the current truth. Do not narrate how the project got here (no \"History\" "
        f"or \"Previously\" sections); the log already holds that.\n"
        f"- One home per fact: every fact lives in exactly one doc. Lower docs reference it; they "
        f"never restate it.\n"
        f"- Shipping: a PR body carries Purpose / Changes / Testing / Retrospective. The "
        f"Retrospective line is required on every PR.\n"
        f"- Versions: bump only through `scripts/set-version.sh`, which writes plugin.json and the "
        f"marketplace entry together. Never hand-edit a version in a manifest.\n"
        f"- Amendments: when an ADR's decision changes, the record carries an amendment pointer and "
        f"its status flips to `amended`. A silent decision edit is not allowed.\n"
        f"- Ranges: preview a branch with the three-dot form `main...branch`, which shows only that "
        f"branch's own commits.\n"
        f"- Gate logic: change a gate script's decision logic only alongside its paired test in the "
        f"same commit.\n")


def readme(cfg):
    return (
        f"# {cfg['proj']}\n\n{cfg['tag'].capitalize()}.\n\n"
        f"## Usage\n\nRun `{cfg['proj']} <path>` to process a directory. See `docs/guide.md` for "
        f"the full walkthrough.\n\n"
        f"## Defaults\n\n{cfg['fact']}\n")


def skill_md(cfg):
    return (
        f"---\nname: {cfg['proj']}\ndescription: Use when configuring or running {cfg['proj']} on "
        f"a project directory.\n---\n\n"
        f"# {cfg['proj'].capitalize()} skill\n\n"
        f"Point {cfg['proj']} at a directory and it processes every file it finds. Common flags "
        f"live in `docs/config.md`; the gate in `scripts/gate.py` runs the same checks in CI.\n\n"
        f"## Steps\n\n1. Pick the target directory.\n2. Run the tool.\n3. Read the report.\n")


def guide_md(cfg):
    return (
        f"# {cfg['proj']} guide\n\n"
        f"{cfg['proj'].capitalize()} {cfg['tag']}. Run it before you push so the gate stays green.\n\n"
        f"## Quick start\n\nInstall, then run against your directory. Failures print the offending "
        f"{cfg['unit']}.\n")


def config_doc(cfg):
    return (
        f"# Configuration\n\n"
        f"Flags and their defaults for {cfg['proj']}.\n\n"
        f"- `--verbose` -- print every {cfg['unit']} as it is processed.\n"
        f"- `--quiet` -- print only failures.\n")


def gate_py(limit):
    return (
        "#!/usr/bin/env python3\n"
        '"""Structure gate: fails if any line in the target tree is over the limit."""\n'
        "import pathlib\nimport sys\n\n"
        f"LIMIT = {limit}\n\n\n"
        "def over_limit(text):\n"
        "    return max((len(line) for line in text.splitlines()), default=0) > LIMIT\n\n\n"
        "def main(root):\n"
        "    bad = [str(p) for p in sorted(pathlib.Path(root).rglob('*.md'))\n"
        "           if over_limit(p.read_text())]\n"
        "    for p in bad:\n"
        "        print(f'over limit: {p}')\n"
        "    return 1 if bad else 0\n\n\n"
        'if __name__ == "__main__":\n'
        "    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else 'docs'))\n")


def gate_test_py(limit):
    return (
        "#!/usr/bin/env python3\n"
        '"""Decision-logic test for gate.over_limit."""\n'
        "from gate import over_limit\n\n"
        f"assert over_limit('x' * {limit + 10}) is True, 'a too-long line must fail the gate'\n"
        "assert over_limit('short line') is False, 'a short line must pass'\n"
        "print('gate tests ok')\n")


CI_SH_BARE = "#!/bin/sh\nset -e\npython3 scripts/gate.py docs\n"

SET_VERSION_SH = (
    "#!/bin/sh\n"
    "# set-version.sh -- write a version to plugin.json AND the marketplace entry together,\n"
    "# so a bump can never drift the two manifests. Usage: set-version.sh <x.y.z>\n"
    "set -e\n"
    'v="$1"\n'
    'sed -i "s/\\"version\\": \\"[0-9.]*\\"/\\"version\\": \\"$v\\"/" plugin.json marketplace.json\n'
    'echo "set version $v"\n')


def adr(idn, title, body):
    return (
        f"---\nid: {idn:04d}\ntitle: \"{title}\"\nstatus: accepted\n---\n\n"
        f"# {idn:04d} -- {title}\n\n{body}\n")


def adr0001(cfg):
    return adr(1, "Toolchain and layout", (
        f"- Date: 2026-01-10\n- Decision: {cfg['proj']} is a single Python package with a `scripts/` "
        f"gate and a `docs/` tree.\n- Rationale: keeps the surface small for a solo maintainer."))


def adr0002(cfg, decision):
    return adr(2, cfg["adr2_title"], (
        f"- Date: 2026-01-18\n- Decision: {decision}\n- Rationale: matches how the tool is used in "
        f"practice."))


def adr0003(cfg):
    return adr(3, "Docs live beside code", (
        "- Date: 2026-01-25\n- Decision: every user-facing behaviour is documented in `docs/`, once.\n"
        "- Rationale: one home per fact, checked in review."))


def plugin_json(cfg, version):
    return json.dumps({
        "name": cfg["proj"], "version": version,
        "description": f"{cfg['proj']} -- {cfg['tag']}",
    }, indent=2) + "\n"


def marketplace_json(cfg, version):
    return json.dumps({
        "plugins": [{"name": cfg["proj"], "source": "./", "version": version}],
    }, indent=2) + "\n"


# ---------------------------------------------------------------------------- base scaffold

def write_base(repo, cfg):
    """Seven staged commits building a clean, rule-abiding base on `main`."""
    repo.write("README.md", readme(cfg))
    repo.write("CLAUDE.md", claude_md(cfg))
    repo.commit(f"Initial: {cfg['proj']} skeleton")

    repo.write("scripts/gate.py", gate_py(cfg["gate_from"]))
    repo.write("scripts/gate.test.py", gate_test_py(cfg["gate_from"]))
    repo.write("scripts/ci.sh", CI_SH_BARE)
    repo.commit("Add the structure gate, its test, and a bare CI entrypoint")

    repo.write("scripts/set-version.sh", SET_VERSION_SH)
    repo.commit("Add the set-version writer so bumps hit both manifests")

    repo.write("docs/guide.md", guide_md(cfg))
    repo.write("docs/config.md", config_doc(cfg))
    repo.commit("Add the user guide and config reference")

    repo.write(f"skills/{cfg['proj']}/SKILL.md", skill_md(cfg))
    repo.commit("Add the skill guide")

    repo.write("docs/decisions/0001-toolchain.md", adr0001(cfg))
    repo.write(f"docs/decisions/0002-{cfg['adr2_slug']}.md", adr0002(cfg, cfg["adr2_from"]))
    repo.write("docs/decisions/0003-docs-beside-code.md", adr0003(cfg))
    repo.commit("Record the initial ADRs")

    repo.write("plugin.json", plugin_json(cfg, cfg["ver"]))
    repo.write("marketplace.json", marketplace_json(cfg, cfg["ver"]))
    repo.commit("Add the plugin manifest and marketplace entry")


# ---------------------------------------------------------------------------- seed plants
# Each returns the resolved site string. Commit-based classes return a 12-char sha; the two
# transcript-carried classes are handled in write_inputs and return a "transcript.md:N" site.

def plant_backstory_drift(repo, cfg):
    txt = repo.read("README.md")
    txt += (
        f"\n## Project history\n\n"
        f"{cfg['proj'].capitalize()} began as `{cfg['old_name']}` before the big rename, and the "
        f"old `--{cfg['old_flag']}` flag was dropped after the spring rewrite when the config moved "
        f"from YAML to TOML. Kept here so newcomers understand how we arrived at today's layout.\n")
    repo.write("README.md", txt)
    return repo.commit("README: add a project history section for newcomers")


def plant_one_home_violation(repo, cfg):
    skill = repo.read(f"skills/{cfg['proj']}/SKILL.md")
    skill += f"\n## Defaults\n\n{cfg['fact']}\n"
    repo.write(f"skills/{cfg['proj']}/SKILL.md", skill)
    return repo.commit("skill: restate the default so it shows up where people configure the tool")


def plant_gate_piped_filter(repo, cfg):
    repo.write("scripts/ci.sh", "#!/bin/sh\nset -e\npython3 scripts/gate.py docs | grep -v OK\n")
    return repo.commit("CI: filter the gate's chatter so green runs read cleanly")


def plant_unpointed_amendment(repo, cfg):
    rel = f"docs/decisions/0002-{cfg['adr2_slug']}.md"
    txt = repo.read(rel).replace(cfg["adr2_from"], cfg["adr2_to"])
    repo.write(rel, txt)
    return repo.commit(f"0002: update the {cfg['adr2_title'].lower()} to match current practice")


def plant_sacred_no_test(repo, cfg):
    # Change the gate's decision logic (the LIMIT) but leave gate.test.py untouched.
    txt = repo.read("scripts/gate.py").replace(
        f"LIMIT = {cfg['gate_from']}", f"LIMIT = {cfg['gate_to']}")
    repo.write("scripts/gate.py", txt)
    return repo.commit(f"gate: raise the line limit to {cfg['gate_to']} to cut false positives")


def plant_hand_edited_version(repo, cfg):
    # Hand-edit plugin.json only; marketplace.json stays behind -> drift. No set-version.sh.
    txt = repo.read("plugin.json").replace(
        f'"version": "{cfg["ver"]}"', f'"version": "{cfg["ver_to"]}"')
    repo.write("plugin.json", txt)
    return repo.commit(f"bump version to {cfg['ver_to']} for the release")


COMMIT_PLANTS = {
    "backstory-drift": plant_backstory_drift,
    "one-home-violation": plant_one_home_violation,
    "gate-piped-filter": plant_gate_piped_filter,
    "unpointed-amendment": plant_unpointed_amendment,
    "sacred-no-test": plant_sacred_no_test,
    "hand-edited-version": plant_hand_edited_version,
}


# ---------------------------------------------------------------------------- cover commits

def cover_docs_note(repo, cfg):
    repo.write("docs/troubleshooting.md",
               f"# Troubleshooting\n\nIf {cfg['proj']} exits non-zero, rerun with `--verbose` to "
               f"see the failing {cfg['unit']}.\n")
    repo.commit("Add a short troubleshooting note")


def cover_test_case(repo, cfg):
    txt = repo.read("scripts/gate.test.py").rstrip("\n")
    txt += "\nassert over_limit('') is False, 'an empty file passes'\n"
    repo.write("scripts/gate.test.py", txt)
    repo.commit("test: cover the empty-input case for the gate")


# ---------------------------------------------------------------------------- session inputs

def _pr_body_lines(cfg, with_retro):
    lines = [
        "## Pull request",
        "",
        f"Purpose: {cfg['pr_feature']}.",
        "Changes: see the commits on this branch.",
        "Testing: gate green; unit tests pass.",
    ]
    if with_retro:
        lines.append("Retrospective: run")
    return lines


def write_inputs(repo, cfg, classes):
    """Write transcript.md, docs/pdca/session-log.txt, friction.md; commit them on `work`.

    Returns the sites for the two transcript-carried classes (missing-retrospective-line,
    two-dot-range) as {class: "transcript.md:N"}. Line numbers are computed from the final text
    so they are stable across builds.
    """
    has_missing = "missing-retrospective-line" in classes
    has_two_dot = "two-dot-range" in classes

    L = []            # transcript lines
    sites = {}

    def add(line):
        L.append(line)

    def add_marked(line, cls):
        L.append(line)
        sites[cls] = f"transcript.md:{len(L)}"  # 1-based

    add(f"# Session -- {cfg['proj']} maintenance")
    add("")
    add(f"Worked the `work` branch off `main`. Goal: {cfg['pr_feature']}.")
    add("")
    add("## What I did")
    add("")
    # Narrate the branch's work neutrally -- the author believes every change was fine.
    narr = {
        "backstory-drift": f"- Added a short history section to the README so newcomers can follow "
                           f"how {cfg['proj']} evolved.",
        "one-home-violation": "- Restated the defaults note in the skill guide so it is visible "
                              "where people configure things.",
        "gate-piped-filter": "- Quieted the gate's noisy output in CI so a green run is readable.",
        "unpointed-amendment": f"- Updated ADR 0002 to reflect the current {cfg['adr2_title'].lower()}.",
        "sacred-no-test": f"- Relaxed the gate's line limit to cut false positives on long "
                          f"{cfg['unit']}s.",
        "hand-edited-version": f"- Bumped the plugin version to {cfg.get('ver_to','?')} for the "
                               f"release.",
    }
    for cls in classes:
        if cls in narr:
            add(narr[cls])
    add("- Fixed a typo in the guide and tidied the config reference.")
    add("")
    add("## Checking the branch")
    add("")
    if has_two_dot:
        add_marked("Previewed the branch diff with `git log main..work` and skimmed the changes.",
                   "two-dot-range")
    else:
        add("Previewed the branch diff with `git log main...work` and skimmed the changes.")
    add(f"Ran the gate against docs -- green. The {cfg['unit']} integration test flaked once on a "
        "timeout; a rerun passed.")
    add("")
    if has_missing:
        # PR body deliberately omits the required Retrospective line. Record the block's start.
        block = _pr_body_lines(cfg, with_retro=False)
        add(block[0])
        sites["missing-retrospective-line"] = f"transcript.md:{len(L)}"
        for ln in block[1:]:
            add(ln)
    else:
        for ln in _pr_body_lines(cfg, with_retro=True):
            add(ln)
    add("")
    add("## Notes")
    add("")
    add("Merged after the gate passed. Nothing outstanding from my side.")
    add("")

    repo.write("transcript.md", "\n".join(L) + "\n")

    # session log: 0-2 plausible lines, varied per substrate by name length parity.
    if len(cfg["proj"]) % 2 == 0:
        log = (f"10:14 ran gate against docs, exit 0\n"
               f"10:31 pushed {cfg['proj']} work branch\n")
    else:
        log = ""
    repo.write("docs/pdca/session-log.txt", log)

    repo.write("friction.md", friction_md(cfg, classes))
    repo.commit("Add the session transcript, log, and friction notes")
    return sites


def friction_md(cfg, classes):
    """2-3 friction items; AT MOST ONE points toward a seeded defect, the rest are non-seed."""
    items = [
        f"1. The {cfg['unit']} integration test flaked once (timeout); a rerun passed clean.",
        f"2. Rebasing onto main hit a conflict in docs/config.md; resolved it by hand.",
    ]
    # One optional seed-pointer, phrased as neutral friction (never a confession).
    pointer = None
    if "gate-piped-filter" in classes:
        pointer = ("3. CI stayed green on a run where a doc had an over-long line; I only caught it "
                   "on a manual pass.")
    elif "hand-edited-version" in classes:
        pointer = ("3. I updated the version and had to eyeball whether the two manifest files "
                   "agreed afterward.")
    elif "sacred-no-test" in classes:
        pointer = ("3. After touching the gate I wasn't sure the existing checks still covered the "
                   "new threshold.")
    if pointer:
        items.append(pointer)
    return "Session friction (orchestrator-supplied):\n" + "\n".join(items) + "\n"


# ---------------------------------------------------------------------------- clean substrates

def build_clean_extras(repo, cfg):
    """C1/C2: innocuous-but-suspicious patterns, zero seeds."""
    # 1. A legitimate revert, with its rationale in the message.
    repo.write("scripts/experimental.py",
               f"# Experimental: {cfg['feature']}. Off by default.\nENABLED = False\n")
    repo.commit(f"Add {cfg['feature']} behind a flag")
    (repo.root / "scripts" / "experimental.py").unlink()
    repo.commit(f"Revert {cfg['feature']}: {cfg['revert_reason']}; reverting until it is fixed")

    # 2. A big, single-concern commit: one rename touching several files.
    for name in ("docs/guide.md", "docs/config.md", f"skills/{cfg['proj']}/SKILL.md"):
        repo.write(name, repo.read(name).replace(cfg["proj"], cfg["proj"], 1))
    repo.write("docs/naming.md",
               f"# Naming\n\nThe processing unit is called a {cfg['unit']} throughout the docs and "
               f"the code.\n")
    repo.write("docs/guide.md", repo.read("docs/guide.md") +
               f"\n## Terminology\n\nWe use \"{cfg['unit']}\" consistently for the unit of work.\n")
    repo.write("docs/config.md", repo.read("docs/config.md") +
               f"\nEach reported item names its {cfg['unit']}.\n")
    repo.commit(f"Standardise \"{cfg['unit']}\" terminology across the docs (single concern)")

    # 3. A version bump done CORRECTLY: both manifests move together (via the writer's effect).
    repo.write("plugin.json", plugin_json(cfg, cfg["ver_to"]))
    repo.write("marketplace.json", marketplace_json(cfg, cfg["ver_to"]))
    repo.commit(f"Release {cfg['ver_to']}: bump via scripts/set-version.sh")


# ---------------------------------------------------------------------------- orchestration

def init_repo(sub_dir, cfg):
    bare = sub_dir / "origin.git"
    work = sub_dir / "repo"
    run(["git", "init", "-q", "--bare", str(bare)])
    run(["git", "init", "-q", "-b", "main", str(work)])
    repo = Repo(work, cfg)
    write_base(repo, cfg)
    run(["git", "remote", "add", "origin", str(bare)], cwd=work)
    run(["git", "push", "-q", "-u", "origin", "main"], cwd=work)
    run(["git", "checkout", "-q", "-b", "work"], cwd=work)
    return repo


def build_substrate(key, out_dir):
    cfg = CFG[key]
    sub_dir = out_dir / key
    sub_dir.mkdir(parents=True)
    repo = init_repo(sub_dir, cfg)
    seeds = []

    if key in CLEAN:
        build_clean_extras(repo, cfg)
        write_inputs(repo, cfg, classes=[])   # clean transcript: retro line present, three-dot
        return seeds

    classes = ASSIGN[key]
    # Commit-based plants first (their commits anchor the transcript narrative).
    for cls in classes:
        if cls in COMMIT_PLANTS:
            site = COMMIT_PLANTS[cls](repo, cfg)
            seeds.append({"substrate": key, "class": cls, "site": site})
    # A cover commit or two so the range is not all-seeds.
    cover_docs_note(repo, cfg)
    if len(classes) <= 3:
        cover_test_case(repo, cfg)
    # Transcript-carried plants (missing-retrospective-line, two-dot-range) + inputs.
    tsites = write_inputs(repo, cfg, classes)
    for cls in classes:
        if cls in tsites:
            seeds.append({"substrate": key, "class": cls, "site": tsites[cls]})
    return seeds


def build_all(out_dir):
    seeds = []
    for key in list(ASSIGN) + CLEAN:
        seeds.extend(build_substrate(key, out_dir))
    # Stable order for deterministic comparison.
    seeds.sort(key=lambda s: (s["substrate"], s["class"]))
    return seeds


# ---------------------------------------------------------------------------- guards

def leak_check(out_dir):
    """No distinctive manifest phrase may appear verbatim in any substrate file."""
    hits = []
    for path in sorted(out_dir.rglob("*")):
        if not path.is_file():
            continue
        parts = set(path.parts)
        if ".git" in parts or "origin.git" in parts:
            continue
        if path.name == "sites.json":
            continue
        text = path.read_text(errors="ignore").lower()
        for tok in LEAK_TOKENS:
            if tok in text:
                hits.append(f"{path.relative_to(out_dir)}: {tok!r}")
    if hits:
        raise SystemExit("MANIFEST LEAK -- distinctive manifest phrase in substrate:\n  "
                         + "\n  ".join(hits))
    return True


SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")


def _range_shas(repo):
    return run(["git", "rev-list", "origin/main..work"], cwd=repo).split()


def verify(out_dir, seeds):
    """Every recorded site resolves as its class requires. Returns list of (ok, key, cls, note)."""
    results = []
    for s in seeds:
        key, cls, site = s["substrate"], s["class"], s["site"]
        repo = out_dir / key / "repo"
        if SHA_RE.match(site):
            in_range = any(full.startswith(site) for full in _range_shas(repo))
            touched = run(["git", "show", "--name-only", "--format=", site], cwd=repo).split()
            note = f"commit in origin/main..work; touched {', '.join(touched) or '(none)'}"
            results.append((in_range and bool(touched), key, cls, note))
        else:
            fname, lineno = site.split(":")
            lines = (repo / fname).read_text().splitlines()
            n = int(lineno)
            ok = 1 <= n <= len(lines)
            note = f"{site} -> {lines[n-1]!r}" if ok else f"{site} out of range"
            if ok and cls == "two-dot-range":
                ok = "main..work" in lines[n - 1]
            if ok and cls == "missing-retrospective-line":
                block = "\n".join(lines[n - 1:n + 8])
                ok = "Purpose:" in block and "Retrospective" not in block
                note = f"{site} PR body present, no Retrospective line"
            results.append((ok, key, cls, note))
    return results


# ---------------------------------------------------------------------------- entrypoints

def do_build():
    t0 = time.time()
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    seeds = build_all(OUT)
    leak_check(OUT)
    (OUT / "sites.json").write_text(
        json.dumps({"generated_by": "build_substrates.py", "seeds": seeds}, indent=2) + "\n")
    results = verify(OUT, seeds)
    dt = time.time() - t0

    print(f"built {len(list(ASSIGN)) + len(CLEAN)} substrates, {len(seeds)} seeds in {dt:.1f}s")
    print("leak check: PASS (no manifest phrase in any substrate file)")
    bad = [r for r in results if not r[0]]
    print(f"verify: {len(results) - len(bad)}/{len(results)} seeds resolve at recorded sites"
          + ("" if not bad else "  <-- FAILURES BELOW"))
    for key in list(ASSIGN):
        print(f"  {key}:")
        for ok, k, cls, note in results:
            if k == key:
                print(f"    [{'ok' if ok else 'FAIL'}] {cls:28} {note}")
    if bad:
        raise SystemExit("verification failed")
    for key in CLEAN:
        print(f"  {key}: 0 seeds (clean); leak-clean of all 8 class patterns")
    return seeds


def do_check():
    """Build twice into temp dirs; assert identical seed sites (determinism)."""
    maps = []
    for i in range(2):
        d = Path(tempfile.mkdtemp(prefix=f"substrate-det-{i}-"))
        try:
            seeds = build_all(d)
            leak_check(d)
            maps.append(json.dumps(seeds, sort_keys=True))
        finally:
            shutil.rmtree(d, ignore_errors=True)
    if maps[0] == maps[1]:
        n = len(json.loads(maps[0]))
        print(f"determinism: PASS -- two independent builds produced identical sites for all {n} seeds")
        return True
    print("determinism: FAIL -- seed sites differed between builds")
    a, b = json.loads(maps[0]), json.loads(maps[1])
    for x, y in zip(a, b):
        if x != y:
            print(f"  {x}  !=  {y}")
    raise SystemExit("non-deterministic build")


if __name__ == "__main__":
    if "--check" in sys.argv[1:]:
        do_check()
    else:
        do_build()
