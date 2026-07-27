/*
 * gate-exit-codes.test.mjs — one invariant, asked of EVERY gate script at once: a gate that cannot
 * read what it was pointed at must exit NON-ZERO.
 *
 * WHY THIS FILE EXISTS, rather than a case in each script's own test. The defect it pins has now
 * shipped three times in this repo, each time in a different file, each time fixed only where it
 * was found:
 *   - check-relocated-paths reported green on a shallow clone (it could not see the history it
 *     was judging);
 *   - the commit that fixed that added prescriptive ENOENT handling to check-workflow and
 *     check-restatement with `return 2` — but both entry points are a bare `main(process.argv)`
 *     that DISCARDS the return value, so both printed a careful diagnostic and then exited 0.
 * A per-script test cannot catch this class, because the author writing that test is the author who
 * just made the assumption. So the question gets asked of the whole SET, from outside: enumerate
 * the gates, point each at a directory that does not exist, and demand a refusal. A new gate added
 * without this behaviour fails here on its first CI run.
 *
 * WHAT IT DELIBERATELY DOES NOT PIN: the exit VALUE (2 for "could not run" vs 1 for "found
 * something") is per-script convention and check-gate-tests legitimately answers 1 for a missing
 * gates.yml. Pinning the exact number would force churn on a distinction this invariant does not
 * care about. Zero is the only wrong answer, because zero is the one an operator and a CI job both
 * read as "checked, and clean".
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { readdirSync, readFileSync } from "node:fs";

const REPO = join(dirname(fileURLToPath(import.meta.url)), "..");

// DERIVED, never restated: every check-*.mjs in scripts/ plus the plugin's own linter. A hand-kept
// list is a list that stops including new gates, which is exactly how a coverage gap goes silent
// (ADR 0086). scorecard is included too — it reads the same ADR corpus and answers with an exit
// code CI consumes.
const GATES = [
  ...readdirSync(join(REPO, "scripts"))
    // `.test.mjs` must be excluded EXPLICITLY: `check-.*\.mjs` is greedy and happily matches
    // `check-workflow.test.mjs`, which then gets spawned as if it were a gate. Caught by this file
    // on its first run — the suite ran as a test runner, exited 0, and was reported as a gate that
    // fails to refuse.
    .filter((f) => !f.endsWith(".test.mjs") && /^(check-.*|scorecard)\.mjs$/.test(f))
    .map((f) => `scripts/${f}`),
  // The PLUGIN half, derived the same way. This was the literal string
  // "pdca-workflow/scripts/adr-lint.mjs" -- one hand-listed entry, in the file whose own comment
  // says a hand-kept list "stops including new gates, which is exactly how a coverage gap goes
  // silent". Every other CLI in the directory that SHIPS TO ADOPTERS was structurally invisible to
  // this test: crosscheck, issue-hygiene and sweep-state were never asked the question. A
  // cross-family round found it.
  // A main guard, not a filename pattern, is what makes a file a CLI here -- and it is matched in
  // all THREE spellings the directory actually uses (`process.argv[1] === fileURLToPath(...)`,
  // `import.meta.url === \`file://${process.argv[1]}\``, and the process.exit-wrapped variant),
  // because keying on one spelling would silently drop the others. Libraries (char-budget,
  // cli-flags) have no main guard and are correctly skipped without needing to be named.
  ...readdirSync(join(REPO, "pdca-workflow", "scripts"))
    .filter((f) => f.endsWith(".mjs") && !f.endsWith(".test.mjs")
      && /process\.argv\[1\]/.test(readFileSync(join(REPO, "pdca-workflow", "scripts", f), "utf8")))
    .map((f) => `pdca-workflow/scripts/${f}`),
].sort();

test("the gate set is discovered, not hand-listed, and is not empty", () => {
  assert.ok(GATES.length >= 7, `expected the repo's gates, found ${GATES.length}: ${GATES}`);
  assert.ok(GATES.includes("scripts/check-workflow.mjs"));
  assert.ok(GATES.includes("scripts/check-restatement.mjs"));
  // The plugin half must be discovered too -- these ship to adopters and were invisible before.
  for (const g of ["adr-lint", "crosscheck", "issue-hygiene", "sweep-state"]) {
    assert.ok(GATES.includes(`pdca-workflow/scripts/${g}.mjs`), `plugin CLI not discovered: ${g}`);
  }
});

// "Nothing usable" has to be expressed in whatever each gate READS, or the probe misses gates that
// take their input another way. Rather than hand-map gate -> input shape (a map that stops
// including new gates, the very failure this file exists to catch), starve every channel at once:
// an argv root that does not exist, AND the PR_* environment scrubbed. A gate that reads a path
// ignores the env; a gate that reads the env ignores argv. Both end up with nothing.
// check-pr-body was found this way — it takes no path at all, and reported green on empty env.
const STARVED_ENV = { ...process.env };
delete STARVED_ENV.PR_TITLE;
delete STARVED_ENV.PR_BODY;

for (const gate of GATES) {
  test(`${gate} refuses input it cannot read, instead of reporting green`, () => {
    const r = spawnSync(process.execPath, [join(REPO, gate), "/no/such/dir-xyz"],
      { cwd: REPO, encoding: "utf8", timeout: 60_000, env: STARVED_ENV });
    assert.equal(r.error, undefined, `spawn failed: ${r.error?.message}`);
    assert.notEqual(r.status, 0,
      `${gate} exited 0 having read nothing — CI and an operator both take that as "checked, and `
      + `clean". stdout: ${String(r.stdout).slice(0, 300)}`);
    // A refusal nobody can act on is only half the rung: say WHAT was unreadable, so the operator
    // fixes the wiring instead of re-running the gate.
    const said = `${r.stdout}${r.stderr}`;
    // `is required` belongs here: crosscheck takes its input via --claim-file, so "that flag is
    // required and takes a value" IS this gate naming what it could not read. The first version of
    // this pattern only knew filesystem wordings and reported a correctly-refusing gate as broken.
    // `bad revision` is git's own wording for an unreadable ref, which is exactly this assertion's
    // subject. check-xfam-review was auto-enrolled by the discovery above and failed here on its
    // first run purely because the pattern had not met git's phrasing yet.
    assert.match(said, /ENOENT|no such file|not found|Invalid path|empty or unset|is required|bad revision/i,
      `${gate} refused without naming the unreadable input: ${said.slice(0, 300)}`);
  });
}
