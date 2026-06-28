#!/usr/bin/env node
/*
 * adr-lint.mjs — ARCHITECTURE ROLE: the executable guard for an ADR ledger
 * (docs/decisions/). Fails the build on the drifts manual numbering + parallel
 * branches invite: duplicate IDs, INDEX <-> file divergence, and over-budget
 * records. The poka-yoke for the ADR system the /roadmap-review skill ships.
 *
 * DESIGN CONSTRAINTS:
 * - Zero dependencies. Node is the one runtime every consumer provably has
 *   (Claude Code runs on it), so this stays a plain `.mjs` — no test framework,
 *   no npm install, runs in CI / a git hook / by hand on any stack incl. Windows.
 * - lint() is PURE (no fs/process) so its decision logic is unit-testable, per
 *   "no process-gating script without a test of its decision logic" — see
 *   adr-lint.test.mjs. main() is the thin IO wrapper.
 * - The INDEX row link format `[NNNN](NNNN-slug.md)` is load-bearing: it is the
 *   format pinned in adr-template.md ("INDEX.md — catalog + shared register").
 *   Keep the regex and that doc in sync.
 *
 * SEE ALSO: ../skills/roadmap-review/references/adr-lint.md (the spec + the 4
 *   checks), ../skills/roadmap-review/references/adr-template.md (numbering +
 *   budget rules this enforces).
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
 * Pure decision logic. Inputs are already-gathered facts so this is IO-free:
 *   files      — ADR filenames on disk, e.g. ["0001-slug.md", ...]
 *   indexLinks — [[id, file], ...] parsed from INDEX.md's markdown links
 *   lineCounts — { "0001-slug.md": 42, ... }
 *   budget     — max lines per ADR (absolute)
 * Returns { problems: string[] } — empty = ledger OK.
 */
export function lint({ files, indexLinks, lineCounts, budget }) {
  const problems = [];

  // 1. No duplicate ADR IDs on disk (parallel branches grabbing the same int).
  const ids = files.map(f => f.slice(0, 4));
  const dupes = [...new Set(ids.filter((id, i) => ids.indexOf(id) !== i))];
  if (dupes.length) problems.push(`Duplicate ADR IDs on disk: ${dupes.join(", ")}`);

  // 2. Every ADR file is linked in INDEX.md.
  const indexed = new Set(indexLinks.map(l => l[1]));
  const missing = files.filter(f => !indexed.has(f));
  if (missing.length) problems.push(`ADR files not linked in INDEX.md: ${missing.join(", ")}`);

  // 3. Every INDEX link resolves to a file whose name matches the link's ID label.
  const onDisk = new Set(files);
  const broken = indexLinks.filter(l => !onDisk.has(l[1]) || !l[1].startsWith(l[0]));
  if (broken.length)
    problems.push(`INDEX.md links broken or label != file: ${broken.map(l => `[${l[0]}](${l[1]})`).join(", ")}`);

  // 4. No ADR exceeds the line budget (a missed lower home — relocate, keep the crux).
  const over = files.filter(f => (lineCounts[f] ?? 0) > budget);
  if (over.length)
    problems.push(`ADRs over the ${budget}-line budget: ${over.map(f => `${f}:${lineCounts[f]}`).join(", ")}`);

  return { problems };
}

function main(argv) {
  const args = argv.slice(2);
  const dir = args.find(a => !a.startsWith("--")) ?? "docs/decisions";
  const budgetArg = args.find(a => a.startsWith("--budget="));
  const budget = budgetArg ? Number(budgetArg.split("=")[1]) : 70;

  let files, indexText;
  try {
    files = readdirSync(dir).filter(f => /^\d{4}-.*\.md$/.test(f));
    indexText = readFileSync(join(dir, "INDEX.md"), "utf8");
  } catch (e) {
    console.error(`adr-lint: cannot read ${dir}/ (need NNNN-*.md files + INDEX.md): ${e.message}`);
    process.exit(2);
  }

  const indexLinks = [...indexText.matchAll(/\[(\d{4})\]\((\d{4}-[^)]+\.md)\)/g)].map(m => [m[1], m[2]]);
  const lineCounts = Object.fromEntries(
    files.map(f => [f, readFileSync(join(dir, f), "utf8").split("\n").length]),
  );

  const { problems } = lint({ files, indexLinks, lineCounts, budget });

  if (problems.length) {
    console.error(`adr-lint: ${problems.length} problem(s) in ${dir}/`);
    for (const p of problems) console.error(`  - ${p}`);
    process.exit(1);
  }
  console.log(`adr-lint: ${files.length} ADR(s) in ${dir}/ — ledger OK (budget ${budget}).`);
}

// Run main() only when invoked directly, so the test can import lint() cleanly.
if (process.argv[1] === fileURLToPath(import.meta.url)) main(process.argv);
