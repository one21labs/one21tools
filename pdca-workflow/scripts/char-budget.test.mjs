/*
 * char-budget.test.mjs — decision-logic test for the doc char budgets (ADR 0008; "never ship a
 * process-gating script without a test of its decision logic"). Zero-dependency: node's built-in
 * test runner + assert, run via `node --test "scripts/*.test.mjs"`. The predicate `overBudget` is
 * unit-tested on synthetic input; `oversizeDocs` runs it over the real docs. (The ADR-corpus
 * application of the same SSoT is tested in adr-lint.test.mjs.)
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { overBudget, oversizeDocs, DOC_BUDGETS } from "./char-budget.mjs";

test("overBudget: over the cap fails, at/under passes (decision logic)", () => {
  assert.equal(overBudget(6001, 6000), true);  // over -> violation
  assert.equal(overBudget(6000, 6000), false); // exactly at the cap -> ok
  assert.equal(overBudget(5999, 6000), false); // under -> ok
});

test("budgets CLAUDE.md (enforcement isn't silently gutted)", () => {
  assert.deepEqual(Object.keys(DOC_BUDGETS).sort(), ["CLAUDE.md"]);
});

test("no budgeted doc exceeds its char cap", () => {
  assert.deepEqual(oversizeDocs(), []);
});
