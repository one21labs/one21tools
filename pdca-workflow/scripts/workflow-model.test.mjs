/*
 * Decision-logic tests for workflow-model.mjs (CI: `node --test pdca-workflow/scripts/*.test.mjs`).
 * Two contracts: findMissingModel flags exactly the agent() calls that choose no model, and the
 * hook path denies those while failing OPEN on anything it cannot read.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { findMissingModel, hookDecision } from "./workflow-model.mjs";

const SCRIPT = fileURLToPath(new URL("./workflow-model.mjs", import.meta.url));
const hook = (stdin) => spawnSync(process.execPath, [SCRIPT, "--hook"], { input: stdin, encoding: "utf8" });

test("flags an agent() call whose options lack model:", () => {
  const problems = findMissingModel(`const r = await agent("do it", { label: "x", schema: S })\n`, "f");
  assert.equal(problems.length, 1);
  assert.match(problems[0], /f:1: agent\(\) call without a model: key/);
});

test("passes an agent() call with model:, including multi-line options", () => {
  const src = `const r = await agent(
  prompt(x),
  { label: \`grade:\${x}\`, phase: "Grade", schema: S, model: "sonnet" }
)\n`;
  assert.deepEqual(findMissingModel(src), []);
});

test("passes a call that names a registered agent — it brings its own model", () => {
  assert.deepEqual(findMissingModel(`await agent("check it", { agentType: "verifier" })\n`), []);
});

test("flags only the offending call when several are mixed, with line numbers", () => {
  const src = `await agent("a", { model: "sonnet" })
await agent("b", { label: "no-model" })
await agent("c", { model: "haiku" })\n`;
  const problems = findMissingModel(src, "mix");
  assert.equal(problems.length, 1);
  assert.match(problems[0], /^mix:2:/);
});

test("handles nested parens inside the call (template args, ternaries)", () => {
  assert.deepEqual(findMissingModel(`await agent(build(a, b), { label: (x ? "y" : "z"), model: "sonnet" })\n`), []);
});

test("an agent() call with no options object at all is flagged", () => {
  assert.equal(findMissingModel(`await agent("just a prompt")\n`).length, 1);
});

test("hook: an inline script with an unmodeled agent() is denied, naming the line", () => {
  const d = hookDecision({ tool_name: "Workflow", tool_input: { script: `await agent("a", { model: "sonnet" })\nawait agent("b")\n` } });
  assert.equal(d.hookSpecificOutput.permissionDecision, "deny");
  assert.match(d.hookSpecificOutput.permissionDecisionReason, /script:2/);
});

test("hook: a fully modeled script passes", () => {
  assert.equal(hookDecision({ tool_input: { script: `await agent("a", { model: "sonnet" })\n` } }), null);
});

test("hook: a scriptPath is read and judged the same way", () => {
  const read = (p) => { assert.equal(p, "/w/x.workflow.js"); return `await agent("b")\n`; };
  assert.equal(hookDecision({ tool_input: { scriptPath: "/w/x.workflow.js" } }, read)
    .hookSpecificOutput.permissionDecision, "deny");
});

test("hook: fails open on a named workflow, an unreadable script file, and no tool_input", () => {
  assert.equal(hookDecision({ tool_input: { name: "saved-workflow" } }), null);
  assert.equal(hookDecision({ tool_input: { scriptPath: "/nope" } }, () => { throw new Error("ENOENT"); }), null);
  assert.equal(hookDecision({}), null);
});

test("hook CLI: prints a deny for an unmodeled script, nothing for garbage, always exit 0", () => {
  const denied = hook(JSON.stringify({ tool_name: "Workflow", tool_input: { script: `await agent("b")` } }));
  assert.equal(JSON.parse(denied.stdout).hookSpecificOutput.permissionDecision, "deny");
  assert.equal(denied.status, 0);
  const garbage = hook("not json {{{");
  assert.equal(garbage.stdout, "");
  assert.equal(garbage.status, 0);
});
