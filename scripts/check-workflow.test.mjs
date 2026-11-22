/*
 * check-workflow.test.mjs — proves check-workflow's wrap-and-syntax-check logic (the model-key
 * rule is tested with its home, pdca-workflow/scripts/workflow-model.test.mjs).
 * Run: node --test scripts/*.test.mjs from the repo root.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { wrapForCheck } from "./check-workflow.mjs";

// Syntax-check a wrapped source exactly the way check-workflow's IO layer does.
const checks = (wrapped) =>
  spawnSync(process.execPath, ["--check", "-"], { input: wrapped, encoding: "utf8" }).status === 0;

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
