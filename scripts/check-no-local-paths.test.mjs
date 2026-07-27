/*
 * check-no-local-paths.test.mjs — THIS REPO IS PUBLIC. No tracked file may carry an absolute path
 * out of somebody's home directory.
 *
 * WHY: such a path publishes the operator's account name and local tree layout to anyone who
 * clones, and it accretes silently — nobody sets out to commit one. This repo had 146 of them
 * across 35 files before anyone looked, in four shapes (`/home/<name>`, `/mnt/c/Users/<name>`,
 * `C:\Users\<name>`, `/Users/<name>`), and the single largest source was a COMMITTED telemetry log
 * that appended one absolute path per gate fire. Two of the offending files were the very scripts
 * that check other files for hardcoded personal paths, using the owner's real username as the
 * fixture.
 *
 * RUNG 1 IS ELSEWHERE, AND THAT IS THE POINT (ADR 0047). The telemetry writer now emits
 * project-relative paths (pdca-workflow/hooks/lib/hook-lib.sh, hook_gate_hit), so the biggest
 * producer cannot emit one at all. This file is the rung-4 backstop for everything a writer does
 * not own: a doc, a benchmark record, a README example someone pastes from their own terminal.
 *
 * IT SCANS THE REAL INDEX, not a fixture: `git ls-files`, every tracked text file. A test that
 * checked a sample would pass while the repo leaked.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const REPO = join(dirname(fileURLToPath(import.meta.url)), "..");
const SELF = "scripts/check-no-local-paths.test.mjs";

// Names that are placeholders or CI-owned, not a person's account. Kept DELIBERATELY SHORT.
// `user`, `me` and `x` were in this list on the first draft and had to come out: they are real
// logins somewhere, and on this very machine the account IS `user` — so allowlisting it made a live
// absolute path permanently invisible to the check that advertises "no home paths". An allowlist
// entry is a blind spot you chose; only earn one for a name that cannot be a person here.
const PLACEHOLDERS = new Set(["USER", "<user>", "${USER}", "$USER", "runner", "youruser",
  "NAME", "<name>"]);

// Built from parts so this file does not match its own pattern and report itself.
const HOME_ROOTS = ["/home/", "/Users/", "/mnt/c/Users/", "C:\\\\Users\\\\", "C:/Users/"];
const NAME = "([A-Za-z_][A-Za-z0-9._-]*)";
// Two shapes, because the second is the one a path-shaped regex cannot see. Claude Code encodes a
// project directory into a flat slug by replacing every `/` with `-`, so `/home/<account>/projects`
// becomes `-home-<account>-projects` — and that string appeared in five committed benchmark files
// AFTER a sweep that believed it had removed every home path. It carries exactly the same account
// name, in a form with no slashes at all. A cross-family review found it; the slash-based pass and
// its author both read straight past it.
// Anchored two ways, because the obvious `-home-<name>-` matches ordinary hyphenated English:
// "one-home-per-fact", "at-home-routing" and "-home-with-" are all in this repo's prose and all
// got reported as leaks on the first attempt. A real slug either keeps the `projects` segment that
// followed the account in the source path, or appears right after a `/` as a directory name.
const SLUG = new RegExp(`(?:-home-${NAME}-projects|/-home-${NAME}-)`, "g");
const RE = new RegExp(`(?:${HOME_ROOTS.join("|")})${NAME}`, "g");

function trackedTextFiles() {
  return execFileSync("git", ["ls-files", "-z"], { cwd: REPO, encoding: "utf8", maxBuffer: 64 << 20 })
    .split("\0").filter(Boolean);
}

export function offendersIn(text) {
  const out = [];
  for (const m of text.matchAll(RE)) if (!PLACEHOLDERS.has(m[1])) out.push(m[0]);
  // Either alternative may be the one that matched, so the account is m[1] ?? m[2].
  for (const m of text.matchAll(SLUG)) { const n = m[1] ?? m[2]; if (!PLACEHOLDERS.has(n)) out.push(m[0]); }
  return out;
}

test("the detector recognises every shape, and does not flag a placeholder", () => {
  // Pinned so a future edit that loosens the regex fails HERE rather than going quiet in the sweep.
  assert.deepEqual(offendersIn("see /home/alice/proj"), ["/home/alice"]);
  assert.deepEqual(offendersIn("/mnt/c/Users/bob/x"), ["/mnt/c/Users/bob"]);
  assert.deepEqual(offendersIn("C:\\Users\\bob\\x"), ["C:\\Users\\bob"]);
  assert.deepEqual(offendersIn("C:/Users/bob/x"), ["C:/Users/bob"]);
  assert.deepEqual(offendersIn("/Users/carol/x"), ["/Users/carol"]);
  assert.deepEqual(offendersIn("/home/USER/x and /home/runner/y and $HOME/z"), []);
  // The slug shape, which has no slashes and which the first draft of this file missed entirely.
  assert.deepEqual(offendersIn("/tmp/claude-1000/-home-alice-projects/uuid"), ["/-home-alice-"]);
  assert.deepEqual(offendersIn('"cwd":"-home-alice-projects-repo"'), ["-home-alice-projects"]);
  assert.deepEqual(offendersIn(".claude/projects/-home-USER-projects/x"), []);
  // Ordinary hyphenated prose is NOT a slug — the first pattern flagged all of these.
  assert.deepEqual(offendersIn("one-home-per-fact, at-home-routing, -home-with-care"), []);
  // And the names that were wrongly allowlisted: on this machine the real account is `user`.
  // COMPOSED FROM PARTS, never written literally. A fixture that spells a real account out is
  // itself a match for the thing being detected, so any repo-wide sanitisation — including the
  // git-history rewrite this repo ran — silently rewrites the FIXTURE, and the test then asserts
  // that a placeholder is an offender and goes red, or worse, asserts nothing. The detector must
  // be the one file whose examples a sweep cannot reach.
  const home = "/home/";
  assert.deepEqual(offendersIn(`${home}user/projects/x`), [`${home}user`]);
  assert.deepEqual(offendersIn(`${home}me/x`), [`${home}me`]);
});

test("no tracked file carries an absolute path out of a real home directory", () => {
  const bad = [];
  for (const rel of trackedTextFiles()) {
    if (rel === SELF) continue;                       // holds the pattern by construction
    let text;
    try { text = readFileSync(join(REPO, rel), "utf8"); }
    catch { continue; }                               // binary, submodule, or removed under us
    if (text.includes("\0")) continue;                // binary
    const hits = [...new Set(offendersIn(text))];
    if (hits.length) bad.push(`${rel}: ${hits.slice(0, 3).join(", ")}`);
  }
  assert.deepEqual(bad, [],
    `this repo is PUBLIC — these tracked files publish a home directory:\n  ${bad.join("\n  ")}\n`
    + `Replace the account name with USER (or make the path project-relative). If a telemetry `
    + `writer produced it, fix the writer: hook_gate_hit in pdca-workflow/hooks/lib/hook-lib.sh `
    + `emits project-relative paths for exactly this reason.`);
});
