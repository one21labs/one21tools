/*
 * Decision-logic tests for check-xfam-review.mjs.
 *
 * The load-bearing property is that coverage() is HARD to satisfy accidentally and cannot be
 * satisfied by the shapes an agent under goal pressure would reach for first: an artifact for a
 * different diff, an artifact naming its own family, an artifact naming a model nobody can place.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { diffHash, artifactModel, coverage, ARTIFACT_DIR } from "./check-xfam-review.mjs";

const art = (hash, model, body = "findings...") =>
  ({ name: `${hash}.md`, text: `xfam-model: ${model}\n\n${body}\n` });

const DIFF = "diff --git a/x b/x\n--- a/x\n+++ b/x\n@@ -1 +1 @@\n-a\n+b\n";

test("a diff is covered only by an artifact filed under ITS OWN hash", () => {
  const h = diffHash(DIFF);
  assert.equal(coverage(DIFF, [art(h, "grok-4.5")]).ok, true);
  // The cheapest evasion: an artifact from an earlier, already-reviewed diff sitting in the dir.
  assert.equal(coverage(DIFF, [art("0000000000000000", "grok-4.5")]).ok, false);
  assert.match(coverage(DIFF, []).reason, new RegExp(`${ARTIFACT_DIR}/${h}\\.md`));
});

test("the artifact must name a model outside the maker's family", () => {
  const h = diffHash(DIFF);
  // Same family: the exact case the whole apparatus exists to refuse. copilot's auto mode routes
  // here on this machine, so this is not hypothetical.
  assert.equal(coverage(DIFF, [art(h, "claude-opus-5")]).ok, false);
  assert.match(coverage(DIFF, [art(h, "claude-opus-5")]).reason, /maker's own family/);
  // Unplaceable is NOT foreign — an id we cannot name is not evidence the lineage was left.
  assert.equal(coverage(DIFF, [art(h, "some-local-model")]).ok, false);
  assert.match(coverage(DIFF, [art(h, "some-local-model")]).reason, /cannot be placed/);
  // And a real foreign one passes.
  for (const m of ["grok-4.5", "gpt-5", "gemini-3-pro"]) {
    assert.equal(coverage(DIFF, [art(h, m)]).ok, true, `${m} must count as foreign`);
  }
});

test("an artifact with no header line does not count, however much text it holds", () => {
  const h = diffHash(DIFF);
  const bodyOnly = { name: `${h}.md`, text: "I reviewed this thoroughly and found nothing.\n" };
  assert.equal(coverage(DIFF, [bodyOnly]).ok, false);
  assert.match(artifactModel(bodyOnly.text).reason, /no `xfam-model:` header/);
});

test("the hash ignores git's index lines, so a rebase does not expire a good review", () => {
  // Without this, every rebase invalidates the artifact and the gate becomes noise people re-run
  // until it passes — which trains exactly the behaviour it exists to stop.
  const withIndex = "diff --git a/x b/x\nindex 1111111..2222222 100644\n--- a/x\n+++ b/x\n@@ -1 +1 @@\n-a\n+b\n";
  const rebased  = "diff --git a/x b/x\nindex 9999999..8888888 100644\n--- a/x\n+++ b/x\n@@ -1 +1 @@\n-a\n+b\n";
  assert.equal(diffHash(withIndex), diffHash(rebased));
  // But a real content change DOES change the hash — otherwise the binding means nothing.
  const changed = "diff --git a/x b/x\n--- a/x\n+++ b/x\n@@ -1 +1 @@\n-a\n+c\n";
  assert.notEqual(diffHash(DIFF), diffHash(changed));
});

test("CRLF and trailing whitespace do not change the hash", () => {
  assert.equal(diffHash(DIFF), diffHash(DIFF.replace(/\n/g, "\r\n")));
  assert.equal(diffHash(DIFF), diffHash(`${DIFF}\n\n`));
});

test("an empty diff is covered — nothing shipped, nothing to review", () => {
  // A branch with no changes must not be blocked; the gate is about SHIPPED content.
  assert.equal(coverage("", []).ok, true);
  assert.equal(coverage("   \n", []).ok, true);
});

test("coverage never throws on absent or malformed input", () => {
  assert.equal(coverage(null, null).ok, true);
  assert.equal(coverage(DIFF, null).ok, false);
  assert.equal(artifactModel(null).foreign, false);
  assert.equal(artifactModel(undefined).foreign, false);
});

test("the artifact directory holds ONLY hash-named artifacts, never free prose", () => {
  // check-restatement skips this directory, because a reviewer quoting our code back at us is
  // evidence rather than a second home for a fact. A cross-family review of that exclusion named
  // its residual: the skip makes the directory a blind spot, so anything parked there -- a living
  // doc, a copy of a README, an ADR draft -- inherits a permanent exemption from the one-home rule.
  // Nothing about the exclusion prevents that; this does. Every entry must be <16-hex>.md, which is
  // exactly what this gate files and nothing a person would write by hand.
  const dir = join(dirname(fileURLToPath(import.meta.url)), "..", ARTIFACT_DIR);
  if (!existsSync(dir)) return;   // no artifacts yet is not a violation
  const stray = readdirSync(dir).filter((f) => !/^[0-9a-f]{16}\.md$/.test(f));
  assert.deepEqual(stray, [],
    `${ARTIFACT_DIR} is skipped by check-restatement, so it must contain ONLY hash-named review `
    + `artifacts — these would sit in a permanent one-home blind spot: ${stray.join(", ")}`);
});
