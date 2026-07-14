#!/usr/bin/env python3
"""Deterministic Instrument 1 v2 substrate builder (issue #177, ADR 0024/0052; stdlib only).

Successor to ../2026-07-12-pdca-retrospect-recall/build_substrates.py (frozen; never edited).
Same machinery, harder substrates -- the pre-registered deltas (README.md, FROZEN) this script
implements:

  1. CLAUDE.md carries only three generic lines (project one-liner; "run the gate before
     shipping"; "keep docs truthful and minimal") -- no rule enumeration. v1's ceiling culprit.
  2. Rule surface: for each seeded substrate, the first two classes in seeds.json's assignment
     list get a PARTIAL rule statement in exactly one doc home (docs/conventions.md, a vendored
     ADR body, or a script header comment) -- naming the norm, never the violation's tell. The
     last two classes get NO doc mention at all -- implied only by artifacts already present in
     the substrate's git history (e.g. every prior gate commit pairs script+test; every prior
     version bump used scripts/set-version.sh).
  3. 20-30 commits per substrate (v1: 10-20, across main+work): seeds are embedded INSIDE
     otherwise-useful edits (a clause inside a real doc improvement, not a dedicated commit),
     buried among routine feature/doc/test padding and 3-4 distractor patterns (legitimate
     revert with rationale, a large single-concern commit, a TODO with a filed-issue pointer, a
     rename-only commit) -- same distractor set on clean substrates (zero seeds).
  4. Extended leak check: v1's no-manifest-phrase scan PLUS a CLAUDE.md-only scan for rule-tell
     phrases (pipe, three-dot, two-dot, Retrospective, amendment, set-version, one home,
     restate, narrate, History) -- CLAUDE.md must never carry them.

Builds under ./substrates/ (gitignored -- regenerable, home is this script):

    substrates/{T1..T6,C1,C2}/origin.git   bare origin (clean base = main)
    substrates/{T1..T6,C1,C2}/repo/        work clone; the session lives on branch `work`
    substrates/sites.json                  {substrate, class, site, surface} per planted seed

The manifest (seeds.json / README.md) is FROZEN; this script fills each seed's resolved site
and surface without touching class, assignment, predicate, or routing_key.

Determinism: fixed author/committer identity + pinned GIT_AUTHOR_DATE/GIT_COMMITTER_DATE with an
explicit +0000 offset, fully static content.

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

# Distinctive manifest phrases that must NEVER appear verbatim in substrate text (v1 requirement,
# extended with the v2-only seeds.json fields).
LEAK_TOKENS = [
    "found_iff", "found-iff", "plant_spec", "routing_key", "surface_rule",
    "backstory-drift", "one-home-violation", "gate-piped-filter",
    "missing-retrospective-line", "unpointed-amendment", "two-dot-range",
    "sacred-no-test", "hand-edited-version",
]

# v2 delta: CLAUDE.md is three generic lines only -- these rule-tell phrases (drawn from the
# rule surface's own vocabulary) must never appear there, on top of the manifest-phrase scan
# above running over every file. Checked case-insensitively, CLAUDE.md only.
CLAUDE_LEAK_PHRASES = [
    "pipe", "three-dot", "two-dot", "retrospective", "amendment", "set-version",
    "one home", "restate", "narrate", "history",
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


def surface_map(key):
    """Per seeds.json's surface_rule: assignment[0..1] = doc-partial, assignment[2..3] = artifact."""
    return {cls: ("doc" if i < 2 else "artifact") for i, cls in enumerate(ASSIGN[key])}


# Per-substrate surface identity + the concrete strings each planted class needs. Varied so no
# two cells read as near-duplicates. None of these mention the real project or this measurement.
CFG = {
    "T1": dict(
        proj="quillmark", tag="lints Markdown docs for small writing teams", unit="line",
        author=("Rae Okafor", "rae@quillmark.dev"), start="2026-02-03",
        fact="Quillmark skips any path listed in `.quillignore`.",
        old_name="mdcheck", old_flag="wrap",
        gate_from=100, ver="0.2.0", ver_release="0.3.0",
        adr2_slug="advisory-warnings", adr2_title="Lint warnings are advisory",
        adr2_from="Warnings are advisory and never fail the build.",
        adr2_to="Warnings fail the build when run with `--strict`.",
        pr_feature="tidy the docs and quiet CI noise",
        feature="an experimental parallel linter",
        revert_reason="it produced duplicate warnings under concurrent runs"),
    "T2": dict(
        proj="streamforge", tag="a batch data-pipeline CLI", unit="record",
        author=("Tomas Vance", "tomas@streamforge.io"), start="2026-03-05",
        fact="Streamforge checkpoints progress every 1000 records.",
        old_name="pipekit", old_flag="chunk",
        gate_from=80, gate_to=120, ver="0.2.0", ver_release="0.3.0", ver_patch="0.3.1",
        adr2_slug="retry-policy", adr2_title="Retry policy for failed batches",
        adr2_from="Failed batches are retried at most 3 times.",
        adr2_to="Failed batches are retried at most 5 times.",
        pr_feature="tune retries and cut the 0.3.0 release",
        feature="an experimental in-memory checkpoint cache",
        revert_reason="it lost checkpoints on an unclean shutdown"),
    "T3": dict(
        proj="cartostatic", tag="renders static maps from GeoJSON", unit="feature",
        author=("Lin Mercado", "lin@cartostatic.org"), start="2026-04-07",
        fact="Cartostatic renders at zoom level 12 unless told otherwise.",
        old_name="tilegen", old_flag="zoom",
        gate_from=90, gate_to=110, ver="0.2.0", ver_release="0.3.0",
        adr2_slug="tile-cache", adr2_title="Render cache size",
        adr2_from="The render cache keeps the last 200 tiles.",
        adr2_to="The render cache keeps the last 500 tiles.",
        pr_feature="speed up rendering and record the cache decision",
        feature="an experimental tile prefetcher",
        revert_reason="it downloaded tiles outside the requested bounds"),
    "T4": dict(
        proj="ledgerlint", tag="checks double-entry ledgers", unit="entry",
        author=("Priya Anand", "priya@ledgerlint.app"), start="2026-05-09",
        fact="Ledgerlint treats any amount under 0.01 as zero.",
        old_name="bookcheck", old_flag="round",
        gate_from=100, ver="0.4.0", ver_release="0.5.0", ver_patch="0.5.1",
        adr2_slug="currency-scope", adr2_title="Supported currencies",
        adr2_from="Only USD and EUR ledgers are validated.",
        adr2_to="USD, EUR, and GBP ledgers are validated.",
        pr_feature="fix rounding and cut the 0.5.0 release",
        feature="an experimental fuzzy currency matcher",
        revert_reason="it misclassified valid entries as errors"),
    "T5": dict(
        proj="harborctl", tag="a container-deploy CLI", unit="manifest line",
        author=("Devon Ruiz", "devon@harborctl.sh"), start="2026-06-01",
        fact="Harborctl pulls the `latest` tag when no digest is pinned.",
        old_name="dockman", old_flag="pull-always",
        gate_from=100, gate_to=140, ver="0.2.0", ver_release="0.3.0",
        adr2_slug="rollback-window", adr2_title="Rollback window",
        adr2_from="Keep the last 2 releases for rollback.",
        adr2_to="Keep the last 4 releases for rollback.",
        pr_feature="clean up the deploy flow",
        feature="an experimental rolling-restart mode",
        revert_reason="it dropped in-flight connections"),
    "T6": dict(
        proj="prosepack", tag="packages ebooks from Markdown", unit="paragraph",
        author=("Mara Ito", "mara@prosepack.press"), start="2026-01-06",
        fact="Prosepack embeds every font referenced by the stylesheet automatically.",
        old_name="bookbind", old_flag="embed-all",
        gate_from=100, ver="0.1.0", ver_release="0.2.0", ver_patch="0.2.1",
        adr2_slug="chapter-split", adr2_title="Chapter splitting",
        adr2_from="Chapters over 50k words are split automatically.",
        adr2_to="Chapters over 80k words are split automatically.",
        pr_feature="improve font handling and cut the 0.2.0 release",
        feature="an experimental cover-image embedder",
        revert_reason="it bloated output files unpredictably"),
    "C1": dict(
        proj="tessellate", tag="tiles large images for the web", unit="row",
        author=("Sasha Bell", "sasha@tessellate.dev"), start="2026-02-20",
        fact="Tessellate emits 256px tiles by default.",
        old_name="", old_flag="",
        gate_from=100, ver="0.2.0", ver_release="0.3.0",
        adr2_slug="tile-format", adr2_title="Default tile format",
        adr2_from="Tiles are written as PNG.",
        adr2_to="Tiles are written as PNG.",
        pr_feature="tiling reliability and the 0.3.0 release",
        feature="an experimental parallel tiler",
        revert_reason="it raced with the shared tile cache and produced torn output"),
    "C2": dict(
        proj="cronweave", tag="a small cron-style job scheduler", unit="rule",
        author=("Noor Haddad", "noor@cronweave.io"), start="2026-03-22",
        fact="Cronweave runs missed jobs once on the next startup.",
        old_name="", old_flag="",
        gate_from=100, ver="0.5.0", ver_release="0.6.0",
        adr2_slug="misfire-policy", adr2_title="Misfire policy",
        adr2_from="A missed job runs once on the next startup.",
        adr2_to="A missed job runs once on the next startup.",
        pr_feature="scheduler reliability and the 0.6.0 release",
        feature="an experimental in-memory result cache",
        revert_reason="it dropped results under a scheduler restart race"),
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
    # v2 delta: exactly three generic lines -- no rule enumeration (v1's ceiling culprit).
    return (
        f"# {cfg['proj']}\n\n"
        f"{p} {cfg['tag']}.\n"
        f"Run the gate before shipping.\n"
        f"Keep docs truthful and minimal.\n")


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


def troubleshooting_doc(cfg):
    return (
        f"# Troubleshooting\n\n"
        f"If {cfg['proj']} exits non-zero, rerun with `--verbose` to see the failing "
        f"{cfg['unit']}.\n")


def conventions_doc(cfg, doc_classes):
    """v2 rule surface, doc-partial home 1/3: docs/conventions.md. Only classes assigned to THIS
    substrate's doc-partial slots (surface_map's index 0/1) get a line here; each line names the
    norm, never the violation's tell."""
    lines = ["# Conventions", "", f"A few notes for anyone touching {cfg['proj']}.", ""]
    if "backstory-drift" in doc_classes:
        lines += ["- Docs describe how things work today; save the backstory of how we got here "
                  "for the commit log.", ""]
    if "missing-retrospective-line" in doc_classes:
        lines += ["- Every PR description should include a short retrospective note before it "
                  "merges.", ""]
    if not doc_classes & {"backstory-drift", "missing-retrospective-line"}:
        lines += ["- Keep pull requests small enough to review in one sitting.", ""]
    return "\n".join(lines).rstrip() + "\n"


def preview_branch_sh(cfg):
    """v2 rule surface, doc-partial home 2/3: a script header comment (two-dot-range only)."""
    return (
        "#!/bin/sh\n"
        "# preview-branch.sh -- show what a branch changes relative to main, using the "
        "three-dot form\n"
        "# (main...branch), which shows only that branch's own commits.\n"
        "set -e\n"
        'git log --oneline "main...$1"\n')


def ci_sh(with_comment):
    """v2 rule surface, doc-partial home 2/3 (gate-piped-filter): a script header comment."""
    if with_comment:
        return (
            "#!/bin/sh\n"
            "# Always run this gate directly and check its own exit status before merging.\n"
            "set -e\n"
            "python3 scripts/gate.py docs\n")
    return "#!/bin/sh\nset -e\npython3 scripts/gate.py docs\n"


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


def adr0004(cfg):
    """v2 rule surface, doc-partial home 3/3: a vendored ADR body (unpointed-amendment only)."""
    return adr(4, "Decision records", (
        "- Date: 2026-01-30\n- Decision: when a decision changes, add a new dated entry rather "
        "than editing the existing text in place.\n"
        "- Rationale: keeps the record of what changed and when trustworthy."))


def plugin_json(cfg, version):
    return json.dumps({
        "name": cfg["proj"], "version": version,
        "description": f"{cfg['proj']} -- {cfg['tag']}",
    }, indent=2) + "\n"


def marketplace_json(cfg, version):
    return json.dumps({
        "plugins": [{"name": cfg["proj"], "source": "./", "version": version}],
    }, indent=2) + "\n"


# ---------------------------------------------------------------------------- base scaffold (main)

def write_base(repo, cfg, doc_classes):
    """Nine staged commits building a clean, rule-abiding base on `main`, carrying any doc-partial
    rule text this substrate's classes need (surface_map's doc-partial slots)."""
    repo.write("README.md", readme(cfg))
    repo.write("CLAUDE.md", claude_md(cfg))
    repo.commit(f"Initial: {cfg['proj']} skeleton")

    repo.write("scripts/gate.py", gate_py(cfg["gate_from"]))
    repo.write("scripts/gate.test.py", gate_test_py(cfg["gate_from"]))
    repo.write("scripts/ci.sh", ci_sh("gate-piped-filter" in doc_classes))
    repo.commit("Add the structure gate, its test, and a bare CI entrypoint")

    repo.write("scripts/set-version.sh", SET_VERSION_SH)
    repo.commit("Add the set-version writer so bumps hit both manifests")

    repo.write("docs/guide.md", guide_md(cfg))
    repo.write("docs/config.md", config_doc(cfg))
    repo.write("docs/troubleshooting.md", troubleshooting_doc(cfg))
    repo.commit("Add the user guide, config reference, and troubleshooting notes")

    repo.write(f"skills/{cfg['proj']}/SKILL.md", skill_md(cfg))
    repo.commit("Add the skill guide")

    repo.write("docs/decisions/0001-toolchain.md", adr0001(cfg))
    repo.write(f"docs/decisions/0002-{cfg['adr2_slug']}.md", adr0002(cfg, cfg["adr2_from"]))
    repo.write("docs/decisions/0003-docs-beside-code.md", adr0003(cfg))
    adr_msg = "Record the initial ADRs"
    if "unpointed-amendment" in doc_classes:
        repo.write("docs/decisions/0004-decision-records.md", adr0004(cfg))
        adr_msg = "Record the initial ADRs, including how the record itself gets updated"
    repo.commit(adr_msg)

    repo.write("docs/conventions.md", conventions_doc(cfg, doc_classes))
    conv_msg = "Add contributor conventions"
    if "two-dot-range" in doc_classes:
        repo.write("scripts/preview-branch.sh", preview_branch_sh(cfg))
        conv_msg = "Add contributor conventions and a branch-preview helper"
    repo.commit(conv_msg)

    repo.write("docs/changelog.md", f"# Changelog\n\n## {cfg['ver']}\n\nInitial release.\n")
    repo.commit("Start a changelog")

    repo.write("plugin.json", plugin_json(cfg, cfg["ver"]))
    repo.write("marketplace.json", marketplace_json(cfg, cfg["ver"]))
    repo.commit("Add the plugin manifest and marketplace entry")


def pad_gate_pattern(repo, cfg):
    """Establishes the sacred-no-test artifact pattern (this substrate's 2nd instance of a gate
    commit pairing script+test; the base scaffold commit is the 1st) -- run on EVERY substrate,
    seeded or not, so the pattern is real history, not a seed-specific prop."""
    txt = repo.read("scripts/gate.py").replace(
        "def over_limit(text):\n    return max((len(line) for line in text.splitlines()), default=0) > LIMIT\n",
        "def over_limit(text):\n    lines = [ln for ln in text.splitlines() if ln.strip()]\n"
        "    return max((len(line) for line in lines), default=0) > LIMIT\n")
    repo.write("scripts/gate.py", txt)
    test_txt = repo.read("scripts/gate.test.py").rstrip("\n")
    test_txt += (
        "\nassert over_limit('\\n\\n' + 'x' * (LIMIT + 10)) is True, "
        "'blank lines must not hide a too-long line'\n"
        "assert over_limit('   \\n\\n') is False, 'blank-only content passes'\n")
    repo.write("scripts/gate.test.py", test_txt)
    repo.commit("gate: ignore blank lines when checking line length; extend the test")


def ver_release_commit(repo, cfg):
    """Establishes the hand-edited-version artifact pattern (a prior bump done via the script) --
    run on EVERY substrate; also a "correct version bump" distractor in its own right."""
    repo.write("plugin.json", plugin_json(cfg, cfg["ver_release"]))
    repo.write("marketplace.json", marketplace_json(cfg, cfg["ver_release"]))
    changelog = repo.read("docs/changelog.md")
    changelog += f"\n## {cfg['ver_release']}\n\n- {cfg['pr_feature'].capitalize()}.\n"
    repo.write("docs/changelog.md", changelog)
    repo.commit(f"Release {cfg['ver_release']}: bump via scripts/set-version.sh")


# ---------------------------------------------------------------------------- seed plants (work)
# Each returns the resolved site string. Commit-based classes return a 12-char sha; the two
# transcript-carried classes are handled in write_inputs and return a "transcript.md:N" site.
# Every plant is embedded INSIDE an otherwise-legitimate, useful edit (v2 delta 2) -- never a
# dedicated single-purpose commit.

def plant_backstory_drift(repo, cfg):
    guide = repo.read("docs/guide.md")
    tip = (f"({cfg['proj'].capitalize()} was called `{cfg['old_name']}` before an early rename; "
           f"the old `--{cfg['old_flag']}` flag from that era is gone.)")
    guide += (
        "\n## Tips\n\n"
        "- Run with `--verbose` the first time so you can see what is happening.\n"
        f"- {tip}\n"
        "- Keep your config file next to the project root so it is picked up automatically.\n")
    repo.write("docs/guide.md", guide)
    return repo.commit("docs: add a quick-start tips section to the guide")


def plant_one_home_violation(repo, cfg):
    skill = repo.read(f"skills/{cfg['proj']}/SKILL.md")
    default_line = cfg["fact"][0].lower() + cfg["fact"][1:]
    skill += (
        "\n## Troubleshooting\n\n"
        "- If nothing seems to happen, check you are pointed at the right directory.\n"
        f"- By default, {default_line}\n"
        "- Logs go to stderr; redirect them for a clean stdout capture.\n")
    repo.write(f"skills/{cfg['proj']}/SKILL.md", skill)
    return repo.commit("skill: add a troubleshooting section with a couple of quick tips")


def plant_gate_piped_filter(repo, cfg):
    current = repo.read("scripts/ci.sh")
    has_header = "# Always run this gate directly" in current
    lines = ["#!/bin/sh"]
    if has_header:
        lines.append("# Always run this gate directly and check its own exit status before merging.")
    lines += ["set -e", "echo 'running gate...'", "python3 scripts/gate.py docs | grep -v OK",
              "python3 scripts/gate.test.py", "echo 'ci done'"]
    repo.write("scripts/ci.sh", "\n".join(lines) + "\n")
    return repo.commit("ci: report progress and run the unit tests alongside the gate")


def plant_unpointed_amendment(repo, cfg):
    rel = f"docs/decisions/0002-{cfg['adr2_slug']}.md"
    txt = repo.read(rel).replace(cfg["adr2_from"], cfg["adr2_to"])
    repo.write(rel, txt)
    readme = repo.read("README.md")
    readme += f"\nSee `docs/decisions/0002-{cfg['adr2_slug']}.md` for the current policy.\n"
    repo.write("README.md", readme)
    return repo.commit("clarify wording in ADR 0002 and point the README at it")


def plant_sacred_no_test(repo, cfg):
    txt = repo.read("scripts/gate.py").replace(
        f"LIMIT = {cfg['gate_from']}", f"LIMIT = {cfg['gate_to']}")
    repo.write("scripts/gate.py", txt)
    note = repo.read("docs/troubleshooting.md")
    note += f"\nLines up to {cfg['gate_to']} characters are fine now; only longer ones fail.\n"
    repo.write("docs/troubleshooting.md", note)
    return repo.commit(f"gate: raise the line limit to {cfg['gate_to']} and refresh the troubleshooting note")


def plant_hand_edited_version(repo, cfg):
    txt = repo.read("plugin.json").replace(
        f'"version": "{cfg["ver_release"]}"', f'"version": "{cfg["ver_patch"]}"')
    repo.write("plugin.json", txt)
    changelog = repo.read("docs/changelog.md")
    changelog += f"\n## {cfg['ver_patch']}\n\n- Quick patch: {cfg['pr_feature']}.\n"
    repo.write("docs/changelog.md", changelog)
    return repo.commit(f"bump version to {cfg['ver_patch']} for a quick patch")


COMMIT_PLANTS = {
    "backstory-drift": plant_backstory_drift,
    "one-home-violation": plant_one_home_violation,
    "gate-piped-filter": plant_gate_piped_filter,
    "unpointed-amendment": plant_unpointed_amendment,
    "sacred-no-test": plant_sacred_no_test,
    "hand-edited-version": plant_hand_edited_version,
}


# ---------------------------------------------------------------------------- padding (routine work)
# Realistic small feature/doc/test commits so 20-30-commit substrates bury seeds in genuine noise.

def pad_faq(repo, cfg):
    txt = repo.read("docs/guide.md")
    txt += (f"\n## FAQ\n\n**Q: does {cfg['proj']} modify files in place?**\nA: no, it only reads "
            f"input and writes a report; nothing under your project changes.\n")
    repo.write("docs/guide.md", txt)
    repo.commit("docs: answer a common question in the guide's FAQ")


def pad_config_example(repo, cfg):
    txt = repo.read("docs/config.md")
    txt += f"\n## Example\n\n```\n{cfg['proj']} --verbose ./project\n```\n"
    repo.write("docs/config.md", txt)
    repo.commit("docs: add a worked example to the config reference")


def pad_readme_polish(repo, cfg):
    txt = repo.read("README.md")
    txt += "\n## Contributing\n\nOpen an issue before a big change; small fixes are welcome as-is.\n"
    repo.write("README.md", txt)
    repo.commit("docs: add a short contributing note to the README")


def pad_small_feature(repo, cfg):
    repo.write("scripts/report.py",
        "#!/usr/bin/env python3\n\"\"\"Print a one-line summary of a run (count of files checked).\"\"\"\n"
        "import pathlib\nimport sys\n\n\n"
        "def count(root):\n    return len(list(pathlib.Path(root).rglob('*.md')))\n\n\n"
        "if __name__ == \"__main__\":\n"
        "    n = count(sys.argv[1] if len(sys.argv) > 1 else 'docs')\n"
        "    print(f'checked {n} files')\n")
    repo.commit("Add a small report script that counts checked files")


def pad_feature_test(repo, cfg):
    repo.write("scripts/report.test.py",
        "#!/usr/bin/env python3\n\"\"\"Test for report.count.\"\"\"\nfrom report import count\n\n"
        "assert count('.') >= 0, 'count must never be negative'\nprint('report tests ok')\n")
    repo.commit("test: cover the report script's counter")


def pad_skill_example(repo, cfg):
    txt = repo.read(f"skills/{cfg['proj']}/SKILL.md")
    txt += f"\n## Example\n\nRun `{cfg['proj']} ./docs` to check just the docs tree.\n"
    repo.write(f"skills/{cfg['proj']}/SKILL.md", txt)
    repo.commit("skill: add a runnable example")


PADDING_FUNCS = [pad_faq, pad_config_example, pad_readme_polish, pad_small_feature,
                 pad_feature_test, pad_skill_example]


# ---------------------------------------------------------------------------- distractors
# 3-4 innocuous-but-suspicious patterns per substrate (seeded AND clean, per seeds.json's
# clean_spec / v2 delta 2): legitimate revert with rationale, large single-concern commit, a
# TODO with a filed-issue pointer, a rename-only commit. FP-guard material -- punish spray.

def distractor_add_experimental(repo, cfg):
    repo.write("scripts/experimental.py",
               f"# Experimental: {cfg['feature']}. Off by default.\nENABLED = False\n")
    repo.commit(f"Add {cfg['feature']} behind a flag")


def distractor_revert_experimental(repo, cfg):
    (repo.root / "scripts" / "experimental.py").unlink()
    repo.commit(f"Revert {cfg['feature']}: {cfg['revert_reason']}; reverting until it is fixed")


def distractor_single_concern(repo, cfg):
    repo.write("docs/naming.md",
               f"# Naming\n\nThe processing unit is called a {cfg['unit']} throughout the docs and "
               f"the code.\n")
    repo.write("docs/guide.md", repo.read("docs/guide.md") +
               f"\n## Terminology\n\nWe use \"{cfg['unit']}\" consistently for the unit of work.\n")
    repo.write("docs/config.md", repo.read("docs/config.md") +
               f"\nEach reported item names its {cfg['unit']}.\n")
    repo.commit(f"Standardise \"{cfg['unit']}\" terminology across the docs (single concern)")


def distractor_todo_issue(repo, cfg):
    txt = repo.read("docs/config.md")
    issue_no = 58 + len(cfg["proj"])
    txt += f"\nTODO: add a `--dry-run` flag (tracked as issue #{issue_no}).\n"
    repo.write("docs/config.md", txt)
    repo.commit("docs: note a deferred flag idea, tracked in an issue")


def distractor_rename_only(repo, cfg):
    run(["git", "mv", "docs/decisions/0001-toolchain.md",
         "docs/decisions/0001-toolchain-and-layout.md"], cwd=repo.root)
    repo.commit("rename the toolchain ADR file for a clearer slug (no content change)")


DISTRACTOR_FUNCS = [distractor_add_experimental, distractor_revert_experimental,
                     distractor_single_concern, distractor_todo_issue, distractor_rename_only]


def interleave(*groups):
    """Deterministic round-robin merge of same-shaped 2-tuple lists -- buries each category
    (seed / distractor / padding) among the others in a fixed, reproducible order."""
    out = []
    idxs = [0] * len(groups)
    total = sum(len(g) for g in groups)
    i = 0
    while len(out) < total:
        gi = i % len(groups)
        g = groups[gi]
        if idxs[gi] < len(g):
            out.append(g[idxs[gi]])
            idxs[gi] += 1
        i += 1
    return out


# ---------------------------------------------------------------------------- session inputs

def _pr_block(cfg, with_retro):
    lines = [f"Purpose: {cfg['pr_feature']}.", "Changes: see the commits on this branch.",
             "Testing: gate green; unit tests pass."]
    if with_retro:
        lines.append("Retrospective: run")
    return lines


def _pr_block_prep(with_retro):
    lines = ["Purpose: small docs and cleanup while in the area.",
             "Changes: see the commits on this branch.", "Testing: gate green."]
    if with_retro:
        lines.append("Retrospective: run")
    return lines


def write_inputs(repo, cfg, classes):
    """Write transcript.md, docs/pdca/session-log.txt, friction.md; commit them on `work`.

    Returns the sites for the two transcript-carried classes (missing-retrospective-line,
    two-dot-range) as {class: "transcript.md:N"}. v2 delta: the session covers TWO PR bodies so
    the Retrospective-line convention is visible only by contrast (one PR body carries it, the
    other may not), and the branch-preview command sits surrounded by unrelated correct ones.
    """
    has_missing = "missing-retrospective-line" in classes
    has_two_dot = "two-dot-range" in classes

    L = []
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
    narr = {
        "backstory-drift": "- Added a quick-start tips section to the guide.",
        "one-home-violation": "- Added a troubleshooting section to the skill guide.",
        "gate-piped-filter": "- Cleaned up CI so it prints progress and runs the unit tests too.",
        "unpointed-amendment": f"- Clarified the wording on ADR 0002 "
                               f"({cfg['adr2_title'].lower()}) and linked it from the README.",
        "sacred-no-test": f"- Raised the gate's line limit to {cfg.get('gate_to', '?')} and "
                          f"refreshed the troubleshooting note.",
        "hand-edited-version": f"- Cut a quick {cfg.get('ver_patch', '?')} patch release.",
    }
    for cls in classes:
        if cls in narr:
            add(narr[cls])
    add("- Also tidied a few small things along the way (docs, a tiny report script, some cleanup).")
    add("")
    add("## Checking the branch")
    add("")
    if has_two_dot:
        add("Compared an earlier spike branch first with `git log main...spike` -- clean.")
        add_marked("Then previewed this branch with `git log main..work` and skimmed the changes.",
                   "two-dot-range")
        add("Also diffed the release tag with `git log v0...work` to be sure nothing else leaked in.")
    else:
        add("Previewed the branch diff with `git log main...work` and skimmed the changes.")
    add(f"Ran the gate against docs -- green. The {cfg['unit']} integration test flaked once on a "
        "timeout; a rerun passed.")
    add("")
    add("## Pull requests")
    add("")
    add("### PR 1 -- docs and small cleanup")
    add("")
    for ln in _pr_block_prep(with_retro=True):
        add(ln)
    add("")
    add(f"### PR 2 -- {cfg['pr_feature']}")
    add("")
    if has_missing:
        block = _pr_block(cfg, with_retro=False)
        add(block[0])
        sites["missing-retrospective-line"] = f"transcript.md:{len(L)}"
        for ln in block[1:]:
            add(ln)
    else:
        for ln in _pr_block(cfg, with_retro=True):
            add(ln)
    add("")
    add("## Notes")
    add("")
    add("Merged after the gate passed. Nothing outstanding from my side.")
    add("")

    repo.write("transcript.md", "\n".join(L) + "\n")

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


# ---------------------------------------------------------------------------- orchestration

def init_repo(sub_dir, cfg, doc_classes):
    bare = sub_dir / "origin.git"
    work = sub_dir / "repo"
    run(["git", "init", "-q", "--bare", str(bare)])
    run(["git", "init", "-q", "-b", "main", str(work)])
    repo = Repo(work, cfg)
    write_base(repo, cfg, doc_classes)
    pad_gate_pattern(repo, cfg)      # establishes the sacred-no-test artifact pattern
    ver_release_commit(repo, cfg)    # establishes the hand-edited-version artifact pattern
    run(["git", "remote", "add", "origin", str(bare)], cwd=work)
    run(["git", "push", "-q", "-u", "origin", "main"], cwd=work)
    run(["git", "checkout", "-q", "-b", "work"], cwd=work)
    return repo


def build_substrate(key, out_dir):
    cfg = CFG[key]
    sub_dir = out_dir / key
    sub_dir.mkdir(parents=True)
    is_clean = key in CLEAN
    doc_classes = set() if is_clean else {c for c, s in surface_map(key).items() if s == "doc"}
    repo = init_repo(sub_dir, cfg, doc_classes)
    seeds = []

    if is_clean:
        for kind, fn in [("distractor", f) for f in DISTRACTOR_FUNCS] + \
                        [("pad", f) for f in PADDING_FUNCS]:
            fn(repo, cfg)
        write_inputs(repo, cfg, classes=[])   # clean transcript: both PRs retro'd, three-dot only
        return seeds

    classes = ASSIGN[key]
    smap = surface_map(key)
    commit_seed_classes = [c for c in classes if c in COMMIT_PLANTS]
    groups = (
        [("seed", c) for c in commit_seed_classes],
        [("distractor", f) for f in DISTRACTOR_FUNCS],
        [("pad", f) for f in PADDING_FUNCS],
    )
    for kind, payload in interleave(*groups):
        if kind == "seed":
            site = COMMIT_PLANTS[payload](repo, cfg)
            seeds.append({"substrate": key, "class": payload, "site": site,
                          "surface": smap[payload]})
        else:
            payload(repo, cfg)

    tsites = write_inputs(repo, cfg, classes)
    for cls in classes:
        if cls in tsites:
            seeds.append({"substrate": key, "class": cls, "site": tsites[cls],
                          "surface": smap[cls]})
    return seeds


def build_all(out_dir):
    seeds = []
    for key in list(ASSIGN) + CLEAN:
        seeds.extend(build_substrate(key, out_dir))
    seeds.sort(key=lambda s: (s["substrate"], s["class"]))
    return seeds


# ---------------------------------------------------------------------------- guards

def leak_check(out_dir):
    """v1's no-manifest-phrase scan over every substrate file, PLUS (v2 delta 4) a CLAUDE.md-only
    scan for rule-tell phrases -- CLAUDE.md must never restate any rule, partial or otherwise."""
    hits = []
    claude_hits = []
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
        if path.name == "CLAUDE.md":
            for phrase in CLAUDE_LEAK_PHRASES:
                if re.search(r"\b" + re.escape(phrase) + r"\b", text):
                    claude_hits.append(f"{path.relative_to(out_dir)}: {phrase!r}")
    if hits:
        raise SystemExit("MANIFEST LEAK -- distinctive manifest phrase in substrate:\n  "
                         + "\n  ".join(hits))
    if claude_hits:
        raise SystemExit("CLAUDE.md RULE-TELL LEAK -- a rule-tell phrase appears in a substrate "
                         "CLAUDE.md (must be 3 generic lines only):\n  " + "\n  ".join(claude_hits))
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


def _commit_count(out_dir, key):
    repo = out_dir / key / "repo"
    main_n = len(run(["git", "rev-list", "main"], cwd=repo).split())
    total_n = len(run(["git", "rev-list", "work"], cwd=repo).split())
    return total_n, main_n


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
    print("leak check: PASS (no manifest phrase; CLAUDE.md carries no rule-tell phrase)")
    bad = [r for r in results if not r[0]]
    print(f"verify: {len(results) - len(bad)}/{len(results)} seeds resolve at recorded sites"
          + ("" if not bad else "  <-- FAILURES BELOW"))
    for key in list(ASSIGN):
        total_n, main_n = _commit_count(OUT, key)
        print(f"  {key}: {total_n} commits ({main_n} main + {total_n - main_n} work)")
        for ok, k, cls, note in results:
            if k == key:
                surf = next(s["surface"] for s in seeds if s["substrate"] == key and s["class"] == cls)
                print(f"    [{'ok' if ok else 'FAIL'}] {cls:28} ({surf:8}) {note}")
    if bad:
        raise SystemExit("verification failed")
    for key in CLEAN:
        total_n, main_n = _commit_count(OUT, key)
        print(f"  {key}: {total_n} commits ({main_n} main + {total_n - main_n} work); "
              f"0 seeds (clean); leak-clean of all 8 class patterns")
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
