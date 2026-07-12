/*
 * check-pr-body.test.mjs — proves check-pr-body's decision logic (ADR 0030, ADR 0054).
 * Run: node --test scripts/*.test.mjs from the repo root.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { hasRetroLine, titleClosesDeclaredPartial } from "./check-pr-body.mjs";

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

test("denies only the title-closes / body-declares-partial contradiction (ADR 0054)", () => {
  assert.deepEqual(titleClosesDeclaredPartial("Fix #164 finding 1: trim", "Partial: #164"), ["164"]);
  assert.deepEqual(titleClosesDeclaredPartial("Fix #164 finding 1: trim", "Purpose: x"), []);
  assert.deepEqual(titleClosesDeclaredPartial("Add feature", "Partial: #164"), []);
  assert.deepEqual(titleClosesDeclaredPartial("Fixes #164", "Partial: #165"), []);
});

test("matches the full closing grammar, case-insensitive, and multiple Partial lines", () => {
  assert.deepEqual(titleClosesDeclaredPartial("Closes #7 and RESOLVED #9", "Partial: #7\nPartial: #9"), ["7", "9"]);
  assert.deepEqual(titleClosesDeclaredPartial("closed #12: cleanup", "notes\nPartial: #12"), ["12"]);
});

test("ignores a prose Partial mention not on its own line, and empty/undefined inputs", () => {
  assert.deepEqual(titleClosesDeclaredPartial("Fix #8", "this is a Partial: #8 fix"), []);
  assert.deepEqual(titleClosesDeclaredPartial(undefined, undefined), []);
  assert.deepEqual(titleClosesDeclaredPartial("Fix #8", ""), []);
});

test("accepts GitHub's optional-colon closing forms; no separator does not close (ADR 0054 B1)", () => {
  assert.deepEqual(titleClosesDeclaredPartial("Fixes: #164", "Partial: #164"), ["164"]);
  assert.deepEqual(titleClosesDeclaredPartial("Closes:#10", "Partial: #10"), ["10"]);
  assert.deepEqual(titleClosesDeclaredPartial("Fixes#164", "Partial: #164"), []);
});

test("Partial parsing tolerates comma lists, lowercase, and trailing punctuation (ADR 0054 B3)", () => {
  assert.deepEqual(
    titleClosesDeclaredPartial("Fixes #164, closes #165", "Partial: #164, #165"),
    ["164", "165"],
  );
  assert.deepEqual(titleClosesDeclaredPartial("Fix #164", "partial: #164"), ["164"]);
  assert.deepEqual(titleClosesDeclaredPartial("Fix #164", "Partial: #164."), ["164"]);
});

test("a Partial line inside a code fence or HTML comment does not declare (ADR 0054 B4)", () => {
  assert.deepEqual(titleClosesDeclaredPartial("Fix #164", "```\nPartial: #164\n```"), []);
  assert.deepEqual(titleClosesDeclaredPartial("Fix #164", "<!-- Partial: #164 -->"), []);
});
