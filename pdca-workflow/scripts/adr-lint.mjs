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
 *   --new-adrs: the change's ADDED ADR files (CI passes the PR diff) — advisory set/margin WARNs, ADR 0051/0067
 *   Exit: 0 = corpus OK · 1 = problems found · 2 = cannot read decisionsDir.
 */
import { readFileSync, readdirSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { overBudget, oversizeDocs, oversizeAgents, agentNameMismatches, ADR_CHAR_BUDGET, ADR_CHAR_MARGIN, LITE_ADR_CHAR_BUDGET, AGENT_CHAR_BUDGET, DOC_BUDGETS } from "./char-budget.mjs";

// All relative paths below resolve against the CURRENT WORKING DIRECTORY, not this file's
// location — see char-budget.mjs's header comment: a fixed offset from this file would break a
// vendored consumer copy, whose `scripts/` sits one level deep, not `pdca-workflow/scripts/`'s two.

/**
 * Pure decision logic. `files` is [{ name, text }] for each NNNN-*.md; `budget` is the char max
 * (defaults from char-budget.mjs in main(); passed in so the decision logic stays unit-testable).
 * Returns { problems: string[] } — empty = corpus OK.
 */
export function lint({ files, budget = ADR_CHAR_BUDGET, liteBudget = LITE_ADR_CHAR_BUDGET, repoFiles }) {
  const problems = [];
  const adrs = [];

  // Lite `Enforced:` resolution (ADR 0087): `repoFiles` is the repo-relative file list the cited
  // tokens resolve against (main() walks the tree; omit to skip resolution — presence is still
  // checked). Basename matching is deliberate: Enforced lines legitimately cite bare filenames
  // (`gates.yml`, `verifier.md:22-24`); a basename that still exists is grep-findable.
  const repoPaths = repoFiles && new Set(repoFiles);
  const repoBases = repoFiles && new Set(repoFiles.map(p => p.split("/").pop()));

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
    adrs.push({ name, id: name.slice(0, 4), text, chars: text.length, lite: props.tier === "lite", status: props.status ?? "" });
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

    // Outcome vocabulary (ADR 0079, spec check 13): every `## Act` `- [outcome]` row carries
    // EXACTLY ONE of verified|violated|still-open — the controlled input a scorecard/hit-rate
    // consumer classifies on. Free-text synonyms ("FALSIFIED") or double-tags are unclassifiable,
    // and a dropped miss reads as no miss (unknown != healthy). Applies to every tier.
    a.text.split("\n").forEach((line, i) => {
      const m = line.match(/^-\s*\[outcome\]\s*(.*)$/);
      if (!m) return;
      const words = new Set([...m[1].matchAll(/\b(verified|violated|still-open)\b/g)].map(x => x[1]));
      if (words.size !== 1)
        problems.push(`${a.name}:${i + 1}: [outcome] row must carry exactly one of verified|violated|still-open (has ${words.size})`);
    });

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
      // Positive lite bar (ADR 0087): settled = "enforced by a test/script/commit"
      // (adr-template.md lite shape) — so the line must EXIST, and any file-like token it cites
      // must still resolve (a deleted/renamed enforcement file = rotted citation). Token-free
      // free-form ("absence", a CI-run description) passes: whether such text truly enforces is
      // review's semantic call, not lint's. Frontmatter is stripped so a summary mention can't
      // satisfy presence, and a backtick-quoted `Enforced:` is prose ABOUT the marker, not the
      // marker (0087 itself discusses the rule; the real line is never backtick-quoted). ALL
      // unquoted occurrences are validated — first-occurrence-only let a prose mention shadow
      // the real line, leaving the gate vacuous on exactly the records that discuss enforcement.
      // Each region spans its line plus wrapped continuation lines.
      const regions = [...a.text.replace(/^---\n[\s\S]*?\n---/, "")
        .matchAll(/(?<!`)Enforced:[ \t]*([^\n]*(?:\n(?![ \t]*(?:[-*#]|$))[^\n]*)*)/g)];
      if (!regions.length)
        problems.push(`${a.name}: lite ADR has no 'Enforced:' line (settled = enforced somewhere findable — adr-template.md lite shape)`);
      else if (repoFiles) {
        const tokens = regions.flatMap(r => r[1].match(/[\w./-]*[\w-]\.(?:mjs|js|ts|md|sh|yml|yaml|json|py|txt)\b/g) ?? []);
        const missing = [...new Set(tokens)].filter(t => !repoPaths.has(t) && !repoBases.has(t.split("/").pop()));
        if (missing.length)
          problems.push(`${a.name}: 'Enforced:' cites file(s) not on disk: ${missing.join(", ")} — stale citation (re-cite or restore)`);
      }
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

  // Stale status on recorded discharge (ADR 0088): "ADR NNNN ... discharged" is a state-changing
  // event usually written into a SIBLING file; if NNNN itself still says `status: proposed`, the
  // record and the state drifted (0057 sat proposed 5 days after 0062 recorded its loop
  // discharged). The unit is a `;`-split clause of one line — the split that dodged the corpus's
  // one near-false-positive: a discharge clause sharing its line with an unrelated then-proposed
  // cite. A 4-digit token counts only if it is an id on disk and not date-adjacent.
  for (const a of adrs) {
    const flagged = new Set();
    for (const line of a.text.split("\n")) {
      for (const clause of line.split(";")) {
        if (!/discharg/i.test(clause)) continue;
        for (const m of clause.matchAll(/(?<![#\d-])(\d{4})(?![\d-])/g)) {
          const t = byId.get(m[1]);
          if (m[1] !== a.id && t && /^proposed/.test(t.status) && !flagged.has(m[1])) {
            flagged.add(m[1]);
            problems.push(`${a.name}: records ADR ${m[1]} discharged, but ${m[1]} is still status: proposed — flip its status or amend the record`);
          }
        }
      }
    }
  }

  return { problems };
}

/**
 * Doc-indexed constant cross-check (ADR 0088): an .md line that backtick-names a char-budget.mjs
 * scalar constant AND contains a 3+-digit number must include that constant's CURRENT value —
 * doc-budgets.md indexes the caps for navigation and its header forbids drift, but a stale
 * NUMBER is invisible to check-restatement (which matches prose). Presence-direction only:
 * extra numbers on the line are fine (a tok-estimate column, a margin), so the corpus measures
 * zero false positives. `docs` = [{ name, text }] candidate .md files — the CALLER excludes
 * docs/decisions/ (records hold as-of-decision numbers, e.g. 0067's then-current margin).
 * `constants` = {NAME: number} scalars; `docBudgets` = the DOC_BUDGETS map — a line naming
 * `DOC_BUDGETS` plus a backticked filename matching a key's basename must show that key's value.
 */
export function docIndexDrift(docs, constants, docBudgets = {}) {
  const problems = [];
  const budgetByBase = new Map(Object.entries(docBudgets).map(([p, v]) => [p.split("/").pop(), v]));
  for (const { name, text } of docs) {
    text.split("\n").forEach((line, i) => {
      const nums = (line.match(/\d{1,3}(?:,\d{3})+|\d{3,}/g) ?? []).map(n => Number(n.replace(/,/g, "")));
      if (!nums.length) return;
      const demand = Object.entries(constants).filter(([c]) => line.includes(`\`${c}\``));
      if (line.includes("`DOC_BUDGETS`"))
        for (const m of line.matchAll(/`([^`]+\.md)`/g)) {
          const v = budgetByBase.get(m[1].split("/").pop());
          if (v !== undefined) demand.push([m[1], v]);
        }
      for (const [label, v] of demand)
        if (!nums.includes(v))
          problems.push(`${name}:${i + 1}: cites ${label} beside number(s) ${nums.join(",")} but its current value is ${v} — stale index (derive from char-budget.mjs)`);
    });
  }
  return problems;
}

// Doc-selection for docIndexDrift (ADR 0088): every .md OUTSIDE the decisions dir — records
// legitimately hold as-of-decision numbers. `dir` arrives verbatim from argv, so normalize a
// trailing slash (bash tab-completion appends one) or the exclusion silently fails open and
// the gate false-positives on historical ADR numbers. Exported so a test binds the SHIPPED
// filter, not a re-implementation.
export const indexScanSet = (repoFiles, dir) => {
  const d = dir.replace(/\/+$/, "");
  return repoFiles.filter(p => p.endsWith(".md") && !p.startsWith(`${d}/`));
};

/**
 * Advisory decision-set note (ADR 0051 as amended): when a change introduces more than one new
 * ADR, report — WARN, never fail — any that sit outside the largest connected component of the
 * undirected cite graph (an edge = either record cites the other, `ADR NNNN` or `[NNNN]`). The
 * PR itself is the batching unit (a deliberately grouped work package is legitimate even when
 * its members share no cite — WP1's 0064-0068 is the precedent); the note exists so an
 * ACCIDENTAL grab-bag is visible at review, not to judge cohesion. `newEntries` are 4-digit
 * ids or `NNNN-*.md` paths; `files` is the corpus. Fewer than two new ADRs = nothing to report.
 */
// `--new-adrs` entries are 4-digit ids or `NNNN-*.md` paths; one home for the parse.
const parseNewAdrIds = (newEntries) => [...new Set(newEntries
  .map(e => e.match(/(\d{4})[^/\\]*\.md$/)?.[1] ?? e.match(/^(\d{4})$/)?.[1])
  .filter(Boolean))];

export function decisionSetWarnings(newEntries, files) {
  const ids = parseNewAdrIds(newEntries);
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
    ? [`new ADRs ${ids.join(", ")} are cite-unconnected (${stranded.join(", ")}) — fine for a deliberate work package; confirm this isn't an accidental grab-bag (ADR 0051)`]
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
// Both walks are ENOENT-tolerant, so a consumer with neither dir is unaffected. `pdca-workflow/
// agents` is a SOURCE-REPO path — inert once vendored; a consumer keeps only `.claude/agents`.
export function agentProblems(dirs = ["pdca-workflow/agents", ".claude/agents"]) {
  const out = [];
  for (const d of dirs) {
    out.push(...oversizeAgents(d).map(a => `agent over budget: ${a}`));
    out.push(...agentNameMismatches(d).map(a => `agent name mismatch: ${a}`));
  }
  return out;
}

// Advisory drafting-margin WARN (ADR 0067): a NEW full ADR drafted past ADR_CHAR_MARGIN has no
// room left for its `## Act` block at ship time. Warning-only, never a problem — and scoped to
// the --new-adrs set so the legacy near-cap corpus stays quiet. Lite ADRs are exempt (own cap,
// no Act machinery).
export function marginWarnings(newEntries, files, margin = ADR_CHAR_MARGIN) {
  const ids = new Set(parseNewAdrIds(newEntries));
  return files
    .filter(({ name, text }) => ids.has(name.slice(0, 4))
      && !/^tier:\s*lite\s*$/m.test(text)
      && text.length > margin)
    .map(({ name, text }) => `${name}: ${text.length} chars > ~${margin} drafting margin (adr-template.md) — no room for \`## Act\` at ship time`);
}

// IO helper (ADR 0087): repo-relative file list for the lite `Enforced:` resolution check.
// A plain walk, not `git ls-files` — the gate needs no git at run time, and "exists on disk"
// (not "is tracked") is the bar. Only .git/node_modules are skipped; symlinked dirs read as
// files (no cycle risk). A subdir that vanishes between discovery and read is skipped (#282:
// sibling test fixtures come and go in the repo root under the concurrent `node --test` run) —
// ONLY ENOENT, and never for the root itself, so the gate cannot go silently vacuous.
// Exported so the test can run the real-corpus case through it; `readdir` injectable so the
// vanish race is testable deterministically.
export function repoFileList(root = ".", readdir = readdirSync) {
  const skip = new Set([".git", "node_modules"]);
  const out = [];
  const stack = [""];
  while (stack.length) {
    const rel = stack.pop();
    let entries;
    try { entries = readdir(rel ? join(root, rel) : root, { withFileTypes: true }); }
    catch (e) {
      if (e.code === "ENOENT" && rel) continue;
      throw e;
    }
    for (const e of entries) {
      if (skip.has(e.name)) continue;
      const p = rel ? `${rel}/${e.name}` : e.name;
      if (e.isDirectory()) stack.push(p);
      else out.push(p);
    }
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
  const repoFiles = repoFileList();
  const { problems } = lint({ files, budget, repoFiles });
  problems.push(...oversizeDocs().map(d => `doc over budget: ${d}`));
  problems.push(...agentProblems());
  problems.push(...manifestDrift(manifestPairs()));

  // Doc-indexed constant cross-check (ADR 0088) over the indexScanSet selection. A file that
  // vanishes between the walk and this read is the same #282 fixture race — skip it.
  // `dir` arrives verbatim from argv, and the plugin's post-edit hook passes an ABSOLUTE path
  // while repoFiles are cwd-relative — normalize here or the decisions-dir exclusion silently
  // fails open and every ADR edit false-positives on as-of-decision numbers (found by the
  // #286-session retrospect; regression pinned in test-adr-lint-post-edit.sh).
  const scanDir = relative(".", dir) || ".";
  const mdDocs = [];
  for (const p of indexScanSet(repoFiles, scanDir)) {
    try { mdDocs.push({ name: p, text: readFileSync(p, "utf8") }); }
    catch (e) { if (e.code !== "ENOENT") throw e; }
  }
  problems.push(...docIndexDrift(mdDocs,
    { ADR_CHAR_BUDGET, ADR_CHAR_MARGIN, LITE_ADR_CHAR_BUDGET, AGENT_CHAR_BUDGET }, DOC_BUDGETS));

  // PR-scoped advisories: CI's PR-only step passes the diff-added ADR files (ADR 0051/0067).
  const newArg = args.find(a => a.startsWith("--new-adrs="));
  if (newArg) {
    const entries = newArg.slice("--new-adrs=".length).split(",").map(s => s.trim()).filter(Boolean);
    for (const w of decisionSetWarnings(entries, files)) console.error(`  WARN (advisory, ADR 0051): ${w}`);
    for (const w of marginWarnings(entries, files)) console.error(`  WARN (advisory, ADR 0067): ${w}`);
  }

  if (problems.length) {
    console.error(`adr-lint: ${problems.length} problem(s) in ${dir}/`);
    for (const p of problems) console.error(`  - ${p}`);
    process.exit(1);
  }
  console.log(`adr-lint: ${files.length} ADR(s) in ${dir}/ — corpus OK (ADR budget ${budget} chars).`);
}

// Run main() only when invoked directly, so the test can import lint() cleanly.
if (process.argv[1] === fileURLToPath(import.meta.url)) main(process.argv);
