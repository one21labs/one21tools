#!/usr/bin/env node
/*
 * adr-lint.mjs — ARCHITECTURE ROLE: guard the ADR corpus (docs/decisions/). There is NO
 * materialized index — poka-yoke: a mirror you don't keep can't drift, so the ADR files ARE
 * the catalog (skim them via their `summary`/`status` frontmatter). This module only CHECKS.
 *
 * Reference implementation of the spec at ../skills/decide/references/adr-lint.md — that file
 * carries the authoritative, numbered guard list; this header stays a pointer, not a second copy,
 * so the two can't drift apart guard-by-guard.
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
 * SEE ALSO: ../skills/decide/references/adr-lint.md (spec — the guard list), adr-template.md (the rules).
 * TESTING: adr-lint.test.mjs (`node --test pdca-workflow/scripts/*.test.mjs` from the repo root).
 *
 * Usage:
 *   node scripts/adr-lint.mjs [decisionsDir] [--budget=N] [--new-adrs=<ids-or-paths,comma-sep>]
 *   decisionsDir default: docs/decisions   ·   --budget default: ADR_CHAR_BUDGET (char-budget.mjs)
 *   --new-adrs: the change's ADDED ADR files (CI passes the PR diff) — decision-set check, ADR 0051
 */
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { overBudget, oversizeDocs, oversizeAgents, agentNameMismatches, ADR_CHAR_BUDGET, LITE_ADR_CHAR_BUDGET } from "./char-budget.mjs";

// All relative paths below resolve against the CURRENT WORKING DIRECTORY, not this file's
// location — see char-budget.mjs's header comment: a fixed offset from this file would break a
// vendored consumer copy, whose `scripts/` sits one level deep, not `pdca-workflow/scripts/`'s two.

/**
 * Pure decision logic. `files` is [{ name, text }] for each NNNN-*.md; `budget` is the char max
 * (defaults from char-budget.mjs in main(); passed in so the decision logic stays unit-testable).
 * Returns { problems: string[] } — empty = corpus OK.
 */
export function lint({ files, budget = ADR_CHAR_BUDGET, liteBudget = LITE_ADR_CHAR_BUDGET }) {
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
    adrs.push({ name, id: name.slice(0, 4), text, chars: text.length, lite: props.tier === "lite" });
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
    // Tier boundary (`tier: lite` frontmatter): a lite ADR records a SETTLED decision —
    // decision + why + where it's enforced, under the lite budget. The boundary is mechanical:
    // a live revisit trigger or open assumption means the decision is NOT settled, so a lite
    // ADR carrying one must GRADUATE to a full ADR (where the criterion gate below applies).
    if (a.lite) {
      if (/REOPEN-IF/i.test(a.text) || /^## Revisit triggers/m.test(a.text)
          || /^\s*[-*]\s*\[unverifiable\]/m.test(a.text))
        problems.push(`${a.name}: lite ADR carries a revisit trigger/open assumption — graduate it to a full ADR`);
      if (overBudget(a.chars, liteBudget))
        problems.push(`${a.name}: ${a.chars} chars > ${liteBudget}-char lite budget`);
      continue; // the falsifiability gate below is a FULL-ADR requirement (settled = nothing to test)
    }

    const hasCriterion = /^\s*[-*]\s*\[(?:checkable|checkable-doc|contradiction)\]/m.test(a.text);
    const hasRevisitable = /^\s*[-*]\s*\[unverifiable\][^\n]*REOPEN-IF/im.test(a.text);
    if (!hasCriterion && !hasRevisitable)
      problems.push(`${a.name}: states no falsifiable criterion ([checkable]/[checkable-doc]/[contradiction], or an [unverifiable] with REOPEN-IF) — UNFALSIFIABLE`);

    // Char budget (ungameable by long lines, unlike a line cap — see ADR 0008): an ADR over the cap
    // is a violation. No exemptions — 0008 chose rewrite-under-budget over a grandfather allowlist.
    if (overBudget(a.chars, budget))
      problems.push(`${a.name}: ${a.chars} chars > ${budget}-char budget`);
  }

  // Amendment backlink (ADR 0040): an ADR that ACTIVELY amends another ("amends ADR NNNN") must
  // be cited back from the amended ADR — an unpointed amendment is invisible from the record it
  // changes (adr-template.md "Rationalize in place"). Passive "amended by NNNN" already carries
  // the cite in the amended record itself, so only the active voice is checked.
  const byId = new Map(adrs.map(x => [x.id, x]));
  for (const a of adrs) {
    for (const m of a.text.matchAll(/\bamend(?:s|ing)?\s+(?:ADR ?)?(\d{4})/gi)) {
      const target = m[1];
      if (target === a.id || !onDisk.has(target)) continue; // dangling cites are reported above
      const t = byId.get(target);
      if (t && !t.text.includes(a.id))
        problems.push(`${a.name}: amends ADR ${target}, but ${target} does not cite ${a.id} back (unpointed amendment)`);
    }
  }

  return { problems };
}

/**
 * Pure decision logic for one-decision-set-per-PR (ADR 0051): when a change introduces more
 * than one new ADR, they must form ONE connected component of the undirected cite graph — an
 * edge exists when either record cites the other (`ADR NNNN` or `[NNNN]`). Entangled records
 * are exactly those the dangling-cite guard would fail if shipped apart; unrelated decisions
 * belong in separate PRs. `newEntries` are 4-digit ids or `NNNN-*.md` paths; `files` is the
 * corpus [{ name, text }]. Fewer than two new ADRs = nothing to check (fail open).
 */
export function decisionSetProblems(newEntries, files) {
  const ids = [...new Set(newEntries
    .map(e => e.match(/(\d{4})[^/\\]*\.md$/)?.[1] ?? e.match(/^(\d{4})$/)?.[1])
    .filter(Boolean))];
  if (ids.length < 2) return [];
  const byId = new Map(files.map(({ name, text }) => [name.slice(0, 4), text]));
  const inSet = new Set(ids);
  const adj = new Map(ids.map(id => [id, new Set()]));
  for (const id of ids) {
    for (const m of (byId.get(id) ?? "").matchAll(/ADR ?(\d{4})|\[(\d{4})\]/g)) {
      const cited = m[1] ?? m[2];
      if (cited !== id && inSet.has(cited)) { adj.get(id).add(cited); adj.get(cited).add(id); }
    }
  }
  const seen = new Set([ids[0]]);
  const queue = [ids[0]];
  while (queue.length) for (const next of adj.get(queue.shift())) if (!seen.has(next)) { seen.add(next); queue.push(next); }
  const stranded = ids.filter(id => !seen.has(id));
  return stranded.length
    ? [`new ADRs ${ids.join(", ")} are not one connected decision set (unconnected: ${stranded.join(", ")}) — one decision-set per PR (ADR 0051)`]
    : [];
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
    try { return JSON.parse(readFileSync(rel, "utf8")); }
    catch (e) { if (e.code === "ENOENT") return null; throw e; }
  };
  const marketplace = read(".claude-plugin/marketplace.json");
  return (marketplace?.plugins ?? []).flatMap((entry) => {
    const plugin = entry.source && read(join(entry.source, ".claude-plugin", "plugin.json"));
    return plugin ? [{ name: entry.name, entry, plugin }] : [];
  });
}

// Both agent homes get the same budget + name-matches-filename checks: the plugin's shipped
// meta-roles (pdca-workflow/agents) and this repo's advisor panel (.claude/agents, ADR 0028).
// Both walks are ENOENT-tolerant, so a consumer with neither dir is unaffected.
export function agentProblems(dirs = ["pdca-workflow/agents", ".claude/agents"]) {
  const out = [];
  for (const d of dirs) {
    out.push(...oversizeAgents(d).map(a => `agent over budget: ${a}`));
    out.push(...agentNameMismatches(d).map(a => `agent name mismatch: ${a}`));
  }
  return out;
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
  problems.push(...agentProblems());
  problems.push(...manifestDrift(manifestPairs()));

  // One-decision-set-per-PR (ADR 0051): CI's PR-only step passes the diff-added ADR files.
  const newArg = args.find(a => a.startsWith("--new-adrs="));
  if (newArg) problems.push(...decisionSetProblems(newArg.slice("--new-adrs=".length).split(",").map(s => s.trim()).filter(Boolean), files));

  if (problems.length) {
    console.error(`adr-lint: ${problems.length} problem(s) in ${dir}/`);
    for (const p of problems) console.error(`  - ${p}`);
    process.exit(1);
  }
  console.log(`adr-lint: ${files.length} ADR(s) in ${dir}/ — corpus OK (ADR budget ${budget} chars).`);
}

// Run main() only when invoked directly, so the test can import lint() cleanly.
if (process.argv[1] === fileURLToPath(import.meta.url)) main(process.argv);
