#!/usr/bin/env node
/*
 * adr-lint.mjs — ARCHITECTURE ROLE: guard the ADR corpus (docs/decisions/). There is NO
 * materialized index — poka-yoke: a mirror you don't keep can't drift, so the ADR files ARE
 * the catalog (skim them via their `summary`/`status` frontmatter). This module only CHECKS.
 *
 * Guards (decision logic in the pure lint() below; exercised by adr-lint.test.mjs):
 *   - every ADR has valid frontmatter (id/title/summary); ids are unique and match the filename;
 *   - no ADR names a release version (version-agnostic — name the cut/feature, not the release);
 *   - every `ADR NNNN` / `[NNNN]` cited inside an ADR resolves to an ADR on disk (the
 *     renumber/fold catcher — a stale cite would pass review otherwise);
 *   - every ADR states a falsifiable criterion (a `[checkable]`/`[checkable-doc]`/`[contradiction]`
 *     assumption bullet, or an `[unverifiable]` paired with a REOPEN-IF) — else UNFALSIFIABLE: the
 *     Plan-phase criterion-minting gate (lint checks PRESENCE/shape; the PM + gate judge substance);
 *   - no ADR exceeds the char budget (char budgets are ungameable by long lines — see ADR 0008 +
 *     char-budget.mjs; no exemptions — every ADR is held to the cap);
 *   - a marketplace plugin entry's metadata matches its plugin's own plugin.json where both state
 *     a field (manifestDrift — the marketplace copy may not silently diverge from the lower home).
 *   main() also char-checks CLAUDE.md (oversizeDocs) + agent prompts (oversizeAgents) and prints each ADR's char count (compute, don't assert).
 *
 * DESIGN CONSTRAINTS:
 * - Zero dependencies. Node is the one runtime every consumer provably has (Claude Code runs on
 *   it), so this stays a plain `.mjs` — runs in CI / a git hook / by hand on any stack incl. Windows.
 * - lint() is PURE (no fs/process) so its decision logic is unit-testable, per "no process-gating
 *   script without a test of its decision logic." main() is the thin IO wrapper.
 * - The char caps + the over-budget predicate are the SSoT in char-budget.mjs — imported, not
 *   redefined here, so they can't drift. This module only applies them.
 * - The frontmatter schema (id/title/status/summary) is pinned in adr-template.md — keep in sync.
 * - Project-specific guards a project may add (a ROADMAP-strike check vs the package version, or
 *   `ADR NNNN` cites in source) are intentionally omitted: a generic consumer may have neither.
 *
 * SEE ALSO: ../skills/decide/references/adr-lint.md (spec), adr-template.md (the rules).
 * TESTING: adr-lint.test.mjs (`node --test pdca-workflow/scripts/*.test.mjs` from the repo root).
 *
 * Usage:
 *   node scripts/adr-lint.mjs [decisionsDir] [--budget=N]
 *   decisionsDir default: docs/decisions   ·   --budget default: ADR_CHAR_BUDGET (char-budget.mjs)
 */
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { overBudget, oversizeDocs, oversizeAgents, ADR_CHAR_BUDGET } from "./char-budget.mjs";

// Repo root (this file lives at <root>/pdca-workflow/scripts/), matching char-budget.mjs.
const ROOT = fileURLToPath(new URL("../../", import.meta.url));

/**
 * Pure decision logic. `files` is [{ name, text }] for each NNNN-*.md; `budget` is the char max
 * (defaults from char-budget.mjs in main(); passed in so the decision logic stays unit-testable).
 * Returns { problems: string[] } — empty = corpus OK.
 */
export function lint({ files, budget = ADR_CHAR_BUDGET }) {
  const problems = [];
  const adrs = [];

  for (const { name, text } of files) {
    const fm = text.match(/^---\n([\s\S]*?)\n---/);
    if (!fm) { problems.push(`${name}: missing YAML frontmatter`); continue; }
    const props = {};
    for (const line of fm[1].split("\n")) {
      const m = line.match(/^(\w+):\s*(.*)$/);
      if (m) props[m[1]] = m[2].trim().replace(/^"(.*)"$/, "$1");
    }
    if (!/^\d{4}$/.test(props.id ?? "")) problems.push(`${name}: bad/missing frontmatter id`);
    else if (props.id !== name.slice(0, 4)) problems.push(`${name}: id ${props.id} != filename`);
    if (!props.title) problems.push(`${name}: missing frontmatter title`);
    if (!props.summary) problems.push(`${name}: missing frontmatter summary`);
    adrs.push({ name, id: name.slice(0, 4), text, chars: text.length });
  }

  // Unique ids (parallel branches grabbing the same int).
  const ids = adrs.map(a => a.id);
  const dupes = [...new Set(ids.filter((id, i) => ids.indexOf(id) !== i))];
  if (dupes.length) problems.push(`Duplicate ADR ids: ${dupes.join(", ")}`);

  const onDisk = new Set(ids);
  for (const a of adrs) {
    // Version-agnostic: no three-part release version anywhere in the ADR.
    const vers = [...new Set([...a.text.matchAll(/\bv?\d+\.\d+\.\d+\b/g)].map(m => m[0]))];
    if (vers.length) problems.push(`${a.name}: names a release version (version-agnostic): ${vers.join(", ")}`);

    // Dangling cite: every `ADR NNNN` / `[NNNN]` / `superseded by NNNN` cited resolves on disk.
    // The status pointer is the headline fold-cite — match it too, or supersession escapes the guard.
    const cited = new Set();
    for (const m of a.text.matchAll(/ADR ?(\d{4})/g)) cited.add(m[1]);
    for (const m of a.text.matchAll(/\[(\d{4})\]/g)) cited.add(m[1]);
    for (const m of a.text.matchAll(/superseded by (\d{4})/gi)) cited.add(m[1]);
    cited.delete(a.id); // self-reference (title/header) is fine
    const dangling = [...cited].filter(id => !onDisk.has(id));
    if (dangling.length) problems.push(`${a.name}: dangling ADR cite(s): ${dangling.join(", ")}`);

    // Falsifiability (Plan-phase criterion-minting gate): an ADR must state at least one criterion
    // the Check can later test — a `- [checkable]`/`- [checkable-doc]`/`- [contradiction]` assumption
    // bullet, OR a `- [unverifiable]` carrying a REOPEN-IF ON THE SAME BULLET (revisitable on a
    // signal — the template's canonical `- [unverifiable] ... — REOPEN-IF: <trigger>` form). None =
    // the decision is UNFALSIFIABLE. The REOPEN-IF must be same-bullet, not merely present somewhere
    // in the file, else a bare `[unverifiable]` + a stray REOPEN-IF (e.g. the `## Revisit triggers`
    // header's idiom) would fail open. PRESENCE only (a real tagged bullet, `-` or `*`, not a prose
    // mention); whether a stated criterion is GENUINELY falsifiable is the PM's/gate's call, not lint's.
    const hasCriterion = /^\s*[-*]\s*\[(?:checkable|checkable-doc|contradiction)\]/m.test(a.text);
    const hasRevisitable = /^\s*[-*]\s*\[unverifiable\][^\n]*REOPEN-IF/im.test(a.text);
    if (!hasCriterion && !hasRevisitable)
      problems.push(`${a.name}: states no falsifiable criterion ([checkable]/[checkable-doc]/[contradiction], or an [unverifiable] with REOPEN-IF) — UNFALSIFIABLE`);

    // Char budget (ungameable by long lines, unlike a line cap — see ADR 0008): an ADR over the cap
    // is a violation. No exemptions — 0008 chose rewrite-under-budget over a grandfather allowlist.
    if (overBudget(a.chars, budget))
      problems.push(`${a.name}: ${a.chars} chars > ${budget}-char budget`);
  }

  return { problems };
}

/**
 * Pure decision logic for the marketplace<->plugin.json metadata mirror (ADR 0011): a field
 * present in BOTH a marketplace plugin entry and that plugin's own plugin.json must be identical —
 * plugin.json is the lower home; the marketplace copy exists only for the pre-install listing.
 * An entry-side omission is NOT drift (derive, don't mirror). `pairs` = [{ name, entry, plugin }].
 */
export function manifestDrift(pairs) {
  const problems = [];
  for (const { name, entry, plugin } of pairs)
    for (const f of ["description", "version"])
      if (entry?.[f] !== undefined && plugin?.[f] !== undefined && entry[f] !== plugin[f])
        problems.push(`${name}: marketplace ${f} drifts from its plugin.json`);
  return problems;
}

// IO wrapper: pair each marketplace plugin entry with its plugin.json where one exists. An ABSENT
// file is tolerated (a consumer repo may ship neither manifest) — ENOENT only, like oversizeAgents;
// invalid JSON throws (the manifests ARE the registry — a broken one must fail the gate loudly).
function manifestPairs() {
  const read = (rel) => {
    try { return JSON.parse(readFileSync(join(ROOT, rel), "utf8")); }
    catch (e) { if (e.code === "ENOENT") return null; throw e; }
  };
  const marketplace = read(".claude-plugin/marketplace.json");
  return (marketplace?.plugins ?? []).flatMap((entry) => {
    const plugin = entry.source && read(join(entry.source, ".claude-plugin", "plugin.json"));
    return plugin ? [{ name: entry.name, entry, plugin }] : [];
  });
}

function main(argv) {
  const args = argv.slice(2);
  const dir = args.find(a => !a.startsWith("--")) ?? "docs/decisions";
  const budgetArg = args.find(a => a.startsWith("--budget="));
  const budget = budgetArg ? Number(budgetArg.split("=")[1]) : ADR_CHAR_BUDGET;

  let files;
  try {
    files = readdirSync(dir)
      .filter(f => /^\d{4}-.*\.md$/.test(f))
      // CRLF-normalize so the char count is checkout-agnostic, matching char-budget.mjs charLen().
      .map(name => ({ name, text: readFileSync(join(dir, name), "utf8").replace(/\r\n/g, "\n") }));
  } catch (e) {
    console.error(`adr-lint: cannot read ${dir}/ (need NNNN-*.md ADR files): ${e.message}`);
    process.exit(2);
  }

  // Poka-yoke: print each ADR's char count (compute the number, never hand-assert it in prose).
  for (const { name, text } of [...files].sort((a, b) => a.name.localeCompare(b.name)))
    console.log(`  ${name}: ${text.length} chars`);

  // ADR corpus + the named-doc self-budgets (CLAUDE.md) + agent prompts share the char-budget.mjs SSoT.
  const { problems } = lint({ files, budget });
  problems.push(...oversizeDocs().map(d => `doc over budget: ${d}`));
  problems.push(...oversizeAgents().map(a => `agent over budget: ${a}`));
  problems.push(...manifestDrift(manifestPairs()));

  if (problems.length) {
    console.error(`adr-lint: ${problems.length} problem(s) in ${dir}/`);
    for (const p of problems) console.error(`  - ${p}`);
    process.exit(1);
  }
  console.log(`adr-lint: ${files.length} ADR(s) in ${dir}/ — corpus OK (ADR budget ${budget} chars).`);
}

// Run main() only when invoked directly, so the test can import lint() cleanly.
if (process.argv[1] === fileURLToPath(import.meta.url)) main(process.argv);
