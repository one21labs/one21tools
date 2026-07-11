/*
 * check-gate-tests.test.mjs — proves check-gate-tests's decision logic (ADR 0047 wave-1).
 * Run: node --test scripts/*.test.mjs from the repo root.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  extractWiredGates,
  extractTestGlobs,
  extractShInvocations,
  globCoversPath,
  extractRegisteredHooks,
  findMissingTests,
} from "./check-gate-tests.mjs";

// hooks.json fixture registering one hook, plugin style.
const hookReg = (name) => ({
  text: JSON.stringify({
    hooks: { PreToolUse: [{ matcher: "Bash", hooks: [{ type: "command", command: `\${CLAUDE_PLUGIN_ROOT}/hooks/${name}.sh` }] }] },
  }),
  pluginRoot: "pdca-workflow",
});

const GATES_YML = [
  "jobs:",
  "  gates:",
  "    steps:",
  "      - run: node --test pdca-workflow/scripts/*.test.mjs scripts/*.test.mjs",
  "      - run: node pdca-workflow/scripts/adr-lint.mjs docs/decisions",
  "      - run: node scripts/check-restatement.mjs",
  "      - run: node scripts/set-version.mjs --dry-run", // NOT wired as a gate step in real gates.yml,
  // kept here only to prove the parser also handles a bare `node x.mjs` line if one existed —
  // this fixture treats it as wired to exercise the "unwired script ignored" case separately below.
].join("\n");

test("extractWiredGates finds every `node <path>.mjs` run line, excluding `node --test` lines", () => {
  const gates = extractWiredGates(GATES_YML);
  assert.deepEqual(gates, [
    "pdca-workflow/scripts/adr-lint.mjs",
    "scripts/check-restatement.mjs",
    "scripts/set-version.mjs",
  ]);
});

test("extractTestGlobs pulls the glob arguments off a `node --test` line", () => {
  assert.deepEqual(extractTestGlobs(GATES_YML), [
    "pdca-workflow/scripts/*.test.mjs",
    "scripts/*.test.mjs",
  ]);
});

test("globCoversPath matches a single-segment wildcard and rejects a different dir/extension", () => {
  assert.ok(globCoversPath("scripts/*.test.mjs", "scripts/check-restatement.test.mjs"));
  assert.ok(!globCoversPath("scripts/*.test.mjs", "scripts/sub/check-restatement.test.mjs"));
  assert.ok(!globCoversPath("scripts/*.test.mjs", "scripts/check-restatement.mjs"));
});

test("gate with a sibling test covered by the node --test glob passes (no finding)", () => {
  const existingFiles = new Set(["scripts/check-restatement.test.mjs"]);
  const gatesYml = [
    "run: node --test scripts/*.test.mjs",
    "run: node scripts/check-restatement.mjs",
  ].join("\n");
  assert.deepEqual(findMissingTests({ gatesYml, hookRegistrations: [], existingFiles }), []);
});

test("gate with no sibling test fails", () => {
  const existingFiles = new Set(); // no *.test.mjs at all
  const gatesYml = [
    "run: node --test scripts/*.test.mjs",
    "run: node scripts/check-restatement.mjs",
  ].join("\n");
  const missing = findMissingTests({ gatesYml, hookRegistrations: [], existingFiles });
  assert.equal(missing.length, 1);
  assert.equal(missing[0].kind, "gate");
  assert.equal(missing[0].path, "scripts/check-restatement.mjs");
  assert.match(missing[0].reason, /no sibling test file/);
});

test("gate whose test file exists but isn't covered by any node --test glob fails", () => {
  // test file lives under a directory the `node --test` step never globs.
  const existingFiles = new Set(["archive/check-restatement.test.mjs"]);
  const gatesYml = [
    "run: node --test scripts/*.test.mjs",
    "run: node archive/check-restatement.mjs",
  ].join("\n");
  const missing = findMissingTests({ gatesYml, hookRegistrations: [], existingFiles });
  assert.equal(missing.length, 1);
  assert.match(missing[0].reason, /not covered by any `node --test` glob/);
});

test("a script never wired into gates.yml (e.g. a manual bump tool) is ignored even with no test", () => {
  const existingFiles = new Set(); // set-version.test.mjs deliberately absent
  const gatesYml = "run: node --test scripts/*.test.mjs\n"; // set-version.mjs never appears in a run: line
  assert.deepEqual(findMissingTests({ gatesYml, hookRegistrations: [], existingFiles }), []);
});

test("extractRegisteredHooks resolves ${CLAUDE_PLUGIN_ROOT} and collects command .sh paths", () => {
  const hooksJson = JSON.stringify({
    hooks: {
      PreToolUse: [{ matcher: "Agent", hooks: [{ type: "command", command: "${CLAUDE_PLUGIN_ROOT}/hooks/explicit-model-guard.sh" }] }],
      PostToolUse: [{ matcher: "Bash", hooks: [{ type: "command", command: "${CLAUDE_PLUGIN_ROOT}/hooks/retrospect-reminder.sh" }] }],
    },
  });
  assert.deepEqual(extractRegisteredHooks(hooksJson, "pdca-workflow"), [
    "pdca-workflow/hooks/explicit-model-guard.sh",
    "pdca-workflow/hooks/retrospect-reminder.sh",
  ]);
});

test("extractRegisteredHooks returns [] for malformed JSON or a hookless settings file", () => {
  assert.deepEqual(extractRegisteredHooks("not json", "pdca-workflow"), []);
  assert.deepEqual(extractRegisteredHooks(JSON.stringify({ outputStyle: "x" }), "."), []);
});

test("hook registered without a CI-visible test fails", () => {
  const hooksJson = JSON.stringify({
    hooks: { PreToolUse: [{ matcher: "Agent", hooks: [{ type: "command", command: "${CLAUDE_PLUGIN_ROOT}/hooks/explicit-model-guard.sh" }] }] },
  });
  const gatesYml = "run: node --test pdca-workflow/scripts/*.test.mjs\n";
  const existingFiles = new Set(); // no explicit-model-guard.test.mjs anywhere
  const missing = findMissingTests({
    gatesYml,
    hookRegistrations: [{ text: hooksJson, pluginRoot: "pdca-workflow" }],
    existingFiles,
  });
  assert.equal(missing.length, 1);
  assert.equal(missing[0].kind, "hook");
  assert.equal(missing[0].path, "pdca-workflow/hooks/explicit-model-guard.sh");
});

test("hook with a CI-visible <basename>.test.mjs in the sibling scripts/ dir passes", () => {
  const hooksJson = JSON.stringify({
    hooks: { PreToolUse: [{ matcher: "Agent", hooks: [{ type: "command", command: "${CLAUDE_PLUGIN_ROOT}/hooks/explicit-model-guard.sh" }] }] },
  });
  const gatesYml = "run: node --test pdca-workflow/scripts/*.test.mjs\n";
  const existingFiles = new Set(["pdca-workflow/scripts/explicit-model-guard.test.mjs"]);
  const missing = findMissingTests({
    gatesYml,
    hookRegistrations: [{ text: hooksJson, pluginRoot: "pdca-workflow" }],
    existingFiles,
  });
  assert.deepEqual(missing, []);
});

test("hook with a test file sitting next to it (not globbed) still fails — must be CI-visible", () => {
  const hooksJson = JSON.stringify({
    hooks: { PreToolUse: [{ matcher: "Agent", hooks: [{ type: "command", command: "${CLAUDE_PLUGIN_ROOT}/hooks/explicit-model-guard.sh" }] }] },
  });
  const gatesYml = "run: node --test pdca-workflow/scripts/*.test.mjs\n"; // does not glob pdca-workflow/hooks/
  const existingFiles = new Set(["pdca-workflow/hooks/explicit-model-guard.test.mjs"]);
  const missing = findMissingTests({
    gatesYml,
    hookRegistrations: [{ text: hooksJson, pluginRoot: "pdca-workflow" }],
    existingFiles,
  });
  assert.equal(missing.length, 1);
  assert.equal(missing[0].kind, "hook");
});

test("extractShInvocations pulls .sh paths and globs off run lines, including a for-loop glob", () => {
  const gatesYml = [
    "      - run: |",
    "          set -e",
    '          for t in pdca-workflow/hooks/test-*.sh; do',
    '            bash "$t"',
    "          done",
    "      - run: bash scripts/one-off-check.sh",
  ].join("\n");
  assert.deepEqual(extractShInvocations(gatesYml), [
    "pdca-workflow/hooks/test-*.sh",
    "scripts/one-off-check.sh",
  ]);
});

test("hook with a gates.yml-invoked test-<basename>.sh sibling passes (hooks-wave convention)", () => {
  const gatesYml = [
    "run: node --test pdca-workflow/scripts/*.test.mjs",
    'run: for t in pdca-workflow/hooks/test-*.sh; do bash "$t"; done',
  ].join("\n");
  const existingFiles = new Set(["pdca-workflow/hooks/test-gate-pipe-guard.sh"]);
  const missing = findMissingTests({
    gatesYml,
    hookRegistrations: [hookReg("gate-pipe-guard")],
    existingFiles,
  });
  assert.deepEqual(missing, []);
});

test("hook whose test-<basename>.sh exists but is invoked by no gates.yml run line fails", () => {
  const gatesYml = "run: node --test pdca-workflow/scripts/*.test.mjs\n"; // no .sh invocation anywhere
  const existingFiles = new Set(["pdca-workflow/hooks/test-gate-pipe-guard.sh"]);
  const missing = findMissingTests({
    gatesYml,
    hookRegistrations: [hookReg("gate-pipe-guard")],
    existingFiles,
  });
  assert.equal(missing.length, 1);
  assert.equal(missing[0].kind, "hook");
  assert.equal(missing[0].path, "pdca-workflow/hooks/gate-pipe-guard.sh");
  assert.match(missing[0].reason, /gates\.yml-invoked test-<basename>\.sh/);
});
