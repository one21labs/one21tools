/*
 * char-budget.test.mjs — decision-logic test for the doc char budgets (ADR 0008/0009; "never ship
 * a process-gating script without a test of its decision logic"). Zero-dependency: node's built-in
 * test runner + assert, run via `node --test pdca-workflow/scripts/*.test.mjs` (repo root). The predicate `overBudget` is
 * unit-tested on synthetic input; the corpus walks run over the real docs/agents AND a synthetic
 * fixture proving positive detection — a walk that always returns [] cannot pass this file.
 * (The ADR-corpus application of the same SSoT is tested in adr-lint.test.mjs.)
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync, readdirSync, rmSync } from "node:fs";
import { join, basename } from "node:path";
import { fileURLToPath } from "node:url";
import { overBudget, oversizeDocs, oversizeAgents, agentNameMismatches, DOC_BUDGETS, AGENT_CHAR_BUDGET } from "./char-budget.mjs";

// The same repo root the module under test resolves against (it joins ROOT + a relative dir).
const ROOT = fileURLToPath(new URL("../../", import.meta.url));

test("overBudget: over the cap fails, at/under passes (decision logic)", () => {
  assert.equal(overBudget(6001, 6000), true);  // over -> violation
  assert.equal(overBudget(6000, 6000), false); // exactly at the cap -> ok
  assert.equal(overBudget(5999, 6000), false); // under -> ok
});

test("budgets CLAUDE.md + the pdca-init template (enforcement isn't silently gutted)", () => {
  assert.deepEqual(Object.keys(DOC_BUDGETS).sort(), [
    "CLAUDE.md",
    "pdca-workflow/skills/pdca-init/references/claude-md-template.md",
  ]);
});

test("no budgeted doc exceeds its char cap", () => {
  assert.deepEqual(oversizeDocs(), []);
});

test("oversizeDocs tolerates a budgeted doc that doesn't exist (ENOENT), like the agent walks", () => {
  DOC_BUDGETS["no-such-doc-xyz.md"] = 10;
  try {
    assert.doesNotThrow(() => oversizeDocs());
    assert.deepEqual(oversizeDocs().filter((d) => d.includes("no-such-doc-xyz")), []);
  } finally {
    delete DOC_BUDGETS["no-such-doc-xyz.md"];
  }
});

test("AGENT_CHAR_BUDGET is a positive char cap (enforcement isn't silently gutted)", () => {
  assert.ok(Number.isInteger(AGENT_CHAR_BUDGET) && AGENT_CHAR_BUDGET > 0);
});

test("agent walk sees the real corpus, and no agent prompt exceeds its char cap", () => {
  // Pin that the default dir resolves and holds prompts — an [] from an unresolvable dir must
  // fail HERE, not pass as "no violations".
  assert.ok(readdirSync(join(ROOT, "pdca-workflow/agents")).some((f) => f.endsWith(".md")));
  assert.deepEqual(oversizeAgents(), []);
});

test("oversizeAgents flags an over-cap prompt (positive detection)", () => {
  const abs = mkdtempSync(join(ROOT, "tmp-agents-fixture-"));
  const dir = basename(abs); // ROOT-relative, as the module expects
  try {
    writeFileSync(join(abs, "big.md"), "x".repeat(AGENT_CHAR_BUDGET + 1));
    writeFileSync(join(abs, "ok.md"), "x".repeat(AGENT_CHAR_BUDGET));
    writeFileSync(join(abs, "notes.txt"), "x".repeat(AGENT_CHAR_BUDGET + 1)); // non-.md ignored
    assert.deepEqual(oversizeAgents(dir), [`${dir}/big.md:${AGENT_CHAR_BUDGET + 1}/${AGENT_CHAR_BUDGET}`]);
  } finally {
    rmSync(abs, { recursive: true, force: true });
  }
});

test("an absent agents dir is tolerated (a consumer may have no agents)", () => {
  assert.deepEqual(oversizeAgents("no-such-agents-dir"), []);
});

test("agentNameMismatches flags name != filename and missing frontmatter (positive detection)", () => {
  const abs = mkdtempSync(join(ROOT, "tmp-agent-name-fixture-"));
  const dir = basename(abs); // ROOT-relative, as the module expects
  try {
    writeFileSync(join(abs, "good.md"), "---\nname: good\ndescription: x\n---\nbody\n");
    writeFileSync(join(abs, "bad.md"), "---\nname: wrong-name\ndescription: x\n---\nbody\n");
    writeFileSync(join(abs, "nofm.md"), "no frontmatter here\n");
    writeFileSync(join(abs, "notes.txt"), "---\nname: nope\n---\n"); // non-.md ignored
    assert.deepEqual(agentNameMismatches(dir).sort(), [
      `${dir}/bad.md: name 'wrong-name' != 'bad'`,
      `${dir}/nofm.md: name '(none)' != 'nofm'`,
    ].sort());
  } finally {
    rmSync(abs, { recursive: true, force: true });
  }
});

test("agentNameMismatches tolerates an absent dir (ENOENT), like the char walk", () => {
  assert.deepEqual(agentNameMismatches("no-such-agents-dir"), []);
});
