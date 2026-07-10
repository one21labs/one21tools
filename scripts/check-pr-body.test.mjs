/*
 * check-pr-body.test.mjs — proves check-pr-body's decision logic (ADR 0030).
 * Run: node --test scripts/*.test.mjs from the repo root.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { hasRetroLine } from "./check-pr-body.mjs";

test("accepts run / unavailable / skipped-<reason>, and a trailing comment after the value", () => {
  assert.ok(hasRetroLine("Purpose: x\nRetrospective: run\n"));
  assert.ok(hasRetroLine("Retrospective: unavailable"));
  assert.ok(hasRetroLine("Retrospective: skipped-batch:#34"));
  assert.ok(hasRetroLine("Retrospective:  skipped-pressure"));
  assert.ok(hasRetroLine("Retrospective: run (batch retrospect in #40)"));
});

test("rejects a missing line, empty/undefined body, bare `skipped`, and `running`", () => {
  assert.equal(hasRetroLine("Purpose: x\nChanges: y\n"), false);
  assert.equal(hasRetroLine(""), false);
  assert.equal(hasRetroLine(undefined), false);
  assert.equal(hasRetroLine("Retrospective: skipped"), false);
  assert.equal(hasRetroLine("Retrospective: running late"), false);
});

test("rejects a prose mention that is not its own line", () => {
  assert.equal(hasRetroLine("See the Retrospective: run note above."), false);
});
