/*
 * explicit-model-guard.test.mjs — decision-logic test for hooks/explicit-model-guard.sh (ADR 0040
 * item 6: deny an Agent/Task call with no explicit `model` that targets an unmodeled surface).
 * Lives in scripts/ so the gates workflow's `node --test pdca-workflow/scripts/*.test.mjs` picks
 * it up (ADR 0012).
 *
 * The contract these cases pin: deny fires ONLY on (model absent AND subagent_type absent or
 * "general-purpose") — the call that silently inherits the parent session model; a named
 * frontmatter agent or fork passes; prose containing the word "model" (or even "model":-looking
 * text, which JSON-escapes to \"model\":) never confuses the key match; malformed/empty stdin
 * fails OPEN — a broken hook must never block every agent launch; exit code is always 0 (the
 * deny signal is the stdout JSON, not the exit code).
 *
 * Invoked exactly as hooks.json invokes it — direct exec of the script path (test-the-surface).
 * Skipped on win32 (spawnSync cannot resolve shebangs there); verified in CI on ubuntu-latest.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const HOOK = fileURLToPath(new URL("../hooks/explicit-model-guard.sh", import.meta.url));
const skip =
  process.platform === "win32"
    ? "direct-exec of shebang scripts unsupported on Windows; verified in CI on ubuntu-latest"
    : false;
const run = (raw) => spawnSync(HOOK, [], { input: raw, encoding: "utf8" });
const runToolInput = (toolInput) =>
  run(JSON.stringify({ tool_name: "Agent", tool_input: toolInput }));
const denies = (toolInput) =>
  runToolInput(toolInput).stdout.includes('"permissionDecision":"deny"');

test("denies: no model, no subagent_type", { skip }, () => {
  assert.ok(denies({ prompt: "do the thing", description: "task" }));
});

test("denies: no model, subagent_type general-purpose", { skip }, () => {
  assert.ok(denies({ prompt: "do the thing", subagent_type: "general-purpose" }));
});

test("passes: model present, no subagent_type", { skip }, () => {
  assert.ok(!denies({ prompt: "do the thing", model: "haiku" }));
});

test("passes: named frontmatter agent without model (carve-out)", { skip }, () => {
  assert.ok(!denies({ prompt: "do the thing", subagent_type: "plugin-adopter" }));
});

test("passes: fork without model (carve-out)", { skip }, () => {
  assert.ok(!denies({ prompt: "continue", subagent_type: "fork" }));
});

test("denies: prose mentioning the word model is not a set key", { skip }, () => {
  assert.ok(denies({ prompt: "pick the best model for this and write a model card" }));
});

test('denies: escaped "model": text inside the prompt is not a set key', { skip }, () => {
  assert.ok(denies({ prompt: 'example config: {"model": "sonnet"}' }));
});

test("passes: real model key alongside prompt prose about models", { skip }, () => {
  assert.ok(
    !denies({ prompt: 'compare each model, e.g. {"model": "x"}', model: "sonnet" })
  );
});

test("fails open on empty stdin", { skip }, () => {
  const r = run("");
  assert.equal(r.stdout, "");
  assert.equal(r.status, 0);
});

test("fails open on garbage stdin without a tool_input marker", { skip }, () => {
  const r = run("not json at all {{{");
  assert.equal(r.stdout, "");
  assert.equal(r.status, 0);
});

test("always exits 0 — deny signal is stdout JSON, not the exit code", { skip }, () => {
  assert.equal(runToolInput({ prompt: "x" }).status, 0); // a deny
  assert.equal(runToolInput({ prompt: "x", model: "haiku" }).status, 0); // an allow
});
