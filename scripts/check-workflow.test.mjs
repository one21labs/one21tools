/*
 * check-workflow.test.mjs — proves check-workflow's decision logic (issue #61).
 * Run: node --test scripts/*.test.mjs from the repo root.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { findMissingModel, wrapForCheck } from "./check-workflow.mjs";

// Syntax-check a wrapped source exactly the way check-workflow's IO layer does.
const checks = (wrapped) =>
  spawnSync(process.execPath, ["--check", "-"], { input: wrapped, encoding: "utf8" }).status === 0;

test("flags an agent() call whose options lack model:", () => {
  const src = `const r = await agent("do it", { label: "x", schema: S })\n`;
  const problems = findMissingModel(src, "f");
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

test("flags only the offending call when several are mixed, with line numbers", () => {
  const src = `await agent("a", { model: "sonnet" })
await agent("b", { label: "no-model" })
await agent("c", { model: "haiku" })\n`;
  const problems = findMissingModel(src, "mix");
  assert.equal(problems.length, 1);
  assert.match(problems[0], /^mix:2:/);
});

test("handles nested parens inside the call (template args, ternaries)", () => {
  const src = `await agent(build(a, b), { label: (x ? "y" : "z"), model: "sonnet" })\n`;
  assert.deepEqual(findMissingModel(src), []);
});

test("an agent() call with no options object at all is flagged", () => {
  const src = `await agent("just a prompt")\n`;
  assert.equal(findMissingModel(src).length, 1);
});

test("wrapForCheck makes top-level return/await/export parse as a function body", () => {
  const src = `export const meta = { name: "x", description: "d" };\nconst r = await agent("p", { model: "sonnet" });\nreturn r;\n`;
  const wrapped = wrapForCheck(src);
  assert.ok(wrapped.startsWith("async function __wf("));
  assert.ok(!/^export /m.test(wrapped));
  assert.ok(checks(wrapped), "wrapped workflow source must pass node --check");
  // The same source UNwrapped fails node --check — the reason this script exists.
  assert.ok(!checks(src), "bare workflow source should fail node --check (top-level return)");
});

test("wrapForCheck preserves a genuine syntax error for the checker to catch", () => {
  assert.ok(!checks(wrapForCheck(`const x = { unclosed\n`)));
});
