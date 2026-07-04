/*
 * retrospect-reminder.test.mjs — decision-logic test for hooks/retrospect-reminder.sh's command
 * matching (the PR-create -> /retrospect reminder). Lives in scripts/ (not beside the hook) so the
 * gates workflow's `node --test pdca-workflow/scripts/*.test.mjs` picks it up (ADR 0012).
 *
 * Why it exists: the hook's matching produced two bugs in its first two edits (an anchored match
 * that missed every prefixed `gh pr create`, then the isolate-then-match rewrite). These cases pin
 * the contract: fire on a real `gh pr create` wherever it sits in the command; never fire on a
 * command merely QUOTING the phrase; the documented early-quote limitation stays a silent miss —
 * never a false fire, never a wider regression.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const HOOK = fileURLToPath(new URL("../hooks/retrospect-reminder.sh", import.meta.url));
const run = (command) =>
  spawnSync("bash", [HOOK], { input: JSON.stringify({ tool_input: { command } }), encoding: "utf8" });
const fires = (command) => run(command).stdout.includes("hookSpecificOutput");

test("fires on a bare gh pr create", () => {
  assert.ok(fires("gh pr create --fill"));
});

test("fires on a prefixed/chained invocation (the PR-13-era miss)", () => {
  assert.ok(fires("cd repo && gh pr create --fill"));
});

test("fires when quotes follow the phrase (--title)", () => {
  assert.ok(fires('gh pr create --title "my title"'));
});

test("does not fire on a command merely quoting the phrase", () => {
  assert.ok(!fires('echo "gh pr create"'));
});

test("does not fire on an unrelated command", () => {
  assert.ok(!fires("git push"));
});

test("documented limitation: a quote before the phrase is a miss, never a false fire", () => {
  assert.ok(!fires('git commit -m "x" && gh pr create'));
});

test("always exits 0 (non-blocking hook)", () => {
  assert.equal(run("git push").status, 0);
  assert.equal(run("gh pr create").status, 0);
});
