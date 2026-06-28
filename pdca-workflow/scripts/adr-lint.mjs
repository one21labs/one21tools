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
 *   - no ADR exceeds the line budget (a missed lower home — relocate, keep the crux).
 *
 * DESIGN CONSTRAINTS:
 * - Zero dependencies. Node is the one runtime every consumer provably has (Claude Code runs on
 *   it), so this stays a plain `.mjs` — runs in CI / a git hook / by hand on any stack incl. Windows.
 * - lint() is PURE (no fs/process) so its decision logic is unit-testable, per "no process-gating
 *   script without a test of its decision logic." main() is the thin IO wrapper.
 * - The frontmatter schema (id/title/status/summary) is pinned in adr-template.md — keep in sync.
 * - Project-specific guards LTconfig also runs (ROADMAP-strike vs package.json version, `ADR NNNN`
 *   cites in src/) are intentionally omitted: a generic consumer may have neither. Add them locally.
 *
 * SEE ALSO: ../skills/roadmap-review/references/adr-lint.md (spec), adr-template.md (the rules).
 * TESTING: adr-lint.test.mjs (`node --test "scripts/*.test.mjs"`).
 *
 * Usage:
 *   node scripts/adr-lint.mjs [decisionsDir] [--budget=N]
 *   decisionsDir default: docs/decisions   ·   --budget default: 70
 */
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

/**
 * Pure decision logic. `files` is [{ name, text }] for each NNNN-*.md; `budget` is the line max.
 * Returns { problems: string[] } — empty = corpus OK.
 */
export function lint({ files, budget }) {
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
    adrs.push({ name, id: name.slice(0, 4), text, lines: text.split("\n").length });
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

    // Dangling cross-ADR cite: every `ADR NNNN` / `[NNNN]` cited resolves to a file on disk.
    const cited = new Set();
    for (const m of a.text.matchAll(/ADR ?(\d{4})/g)) cited.add(m[1]);
    for (const m of a.text.matchAll(/\[(\d{4})\]/g)) cited.add(m[1]);
    cited.delete(a.id); // self-reference (title/header) is fine
    const dangling = [...cited].filter(id => !onDisk.has(id));
    if (dangling.length) problems.push(`${a.name}: dangling ADR cite(s): ${dangling.join(", ")}`);

    // Line budget.
    if (a.lines > budget) problems.push(`${a.name}: ${a.lines} lines > ${budget}-line budget`);
  }

  return { problems };
}

function main(argv) {
  const args = argv.slice(2);
  const dir = args.find(a => !a.startsWith("--")) ?? "docs/decisions";
  const budgetArg = args.find(a => a.startsWith("--budget="));
  const budget = budgetArg ? Number(budgetArg.split("=")[1]) : 70;

  let files;
  try {
    files = readdirSync(dir)
      .filter(f => /^\d{4}-.*\.md$/.test(f))
      .map(name => ({ name, text: readFileSync(join(dir, name), "utf8") }));
  } catch (e) {
    console.error(`adr-lint: cannot read ${dir}/ (need NNNN-*.md ADR files): ${e.message}`);
    process.exit(2);
  }

  const { problems } = lint({ files, budget });

  if (problems.length) {
    console.error(`adr-lint: ${problems.length} problem(s) in ${dir}/`);
    for (const p of problems) console.error(`  - ${p}`);
    process.exit(1);
  }
  console.log(`adr-lint: ${files.length} ADR(s) in ${dir}/ — corpus OK (budget ${budget}).`);
}

// Run main() only when invoked directly, so the test can import lint() cleanly.
if (process.argv[1] === fileURLToPath(import.meta.url)) main(process.argv);
