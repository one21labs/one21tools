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
import { overBudget, oversizeDocs, oversizeAgents, agentNameMismatches, DOC_BUDGETS, AGENT_CHAR_BUDGET,
  corpusOverage, charLen, ADR_CORPUS_BUDGET, LITE_ADR_CHAR_BUDGET } from "./char-budget.mjs";

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

// --- Corpus WIP cap (ADR 0092) ---------------------------------------------------------------
// The cap's job is to force a TRADE, not to obstruct: these mirror the four-condition experiment
// run against a copy of the real corpus (baseline pass -> full record fails -> compaction clears
// -> a lite record fits where a full one did not).

test("corpusOverage: under and exactly-at the cap both pass; over fails", () => {
  assert.equal(corpusOverage([100, 200], 400), null);
  assert.equal(corpusOverage([100, 300], 400), null, "at the cap is not over (boundary)");
  const v = corpusOverage([100, 301], 400);
  assert.equal(v.over, 1);
  assert.equal(v.total, 401);
});

test("corpusOverage: an empty corpus never fails", () => {
  assert.equal(corpusOverage([], 400), null);
});

test("corpusOverage: the remedy prices the overage in LITE records and names compaction", () => {
  const cap = LITE_ADR_CHAR_BUDGET * 2 + 100;        // 3,100
  const v = corpusOverage([cap + 2_900], cap);        // over by exactly 2,900
  assert.match(v.remedy, /compact or supersede/);
  assert.match(v.remedy, /2 lite-record equivalents/); // ceil(2900/1500) = 2
  assert.doesNotMatch(v.remedy, /delete the record you are adding/i);
});

test("corpusOverage: a LITE addition fits where a FULL one does not (the incentive gradient)", () => {
  const corpus = [400_000];
  const cap = 405_000;                       // 5,000 headroom
  assert.equal(corpusOverage([...corpus, 9_000], cap).over, 4_000, "a full record overruns");
  assert.equal(corpusOverage([...corpus, 1_500], cap), null, "a lite record fits");
});

test("corpusOverage: compaction clears an overage (forces a trade, not a block)", () => {
  const over = corpusOverage([9_000, 9_000, 9_000], 20_000);
  assert.equal(over.over, 7_000);
  // Collapse one full record to lite: 9,000 -> 1,500 frees 7,500.
  assert.equal(corpusOverage([9_000, 9_000, 1_500], 20_000), null);
});

test("the live corpus is under its own cap — this gate is not vacuously green", () => {
  const dir = "docs/decisions";
  const sizes = readdirSync(dir).filter(f => /^\d{4}-.*\.md$/.test(f)).map(f => charLen(join(dir, f)));
  assert.ok(sizes.length > 50, "the real corpus is being read, not an empty list");
  assert.equal(corpusOverage(sizes, ADR_CORPUS_BUDGET), null);
});
