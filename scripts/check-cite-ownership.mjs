#!/usr/bin/env node
/*
 * check-cite-ownership.mjs — ARCHITECTURE ROLE: the semantic half of ADR-cite validation.
 * `adr-lint` already fails a cite to an ADR id that does not EXIST; this gate fails a cite to a
 * REAL record that does not OWN the doctrine term the citing line names. That gap let the wrong
 * home propagate by copy: six instances in one session (2026-07-25) — the frozen-dir append-only
 * rule credited to ADR 0026 in four live places when ADR 0041 owns it (0041's own Assumptions
 * line already recorded "ADR 0026 silent on retrofit"), and the eval-clustered CI credited to
 * ADR 0025 in two when ADR 0019 owns it. Rung 4, cited scar, per ADR 0047.
 *
 * OWNERSHIP IS DERIVED, NOT LISTED (CLAUDE.md: delete the mirror). An ADR owns a term iff the
 * term appears in its text with at least one occurrence NOT credited to a different ADR on
 * either side. That second clause is what catches the 0025 case: every one of its three
 * "eval-clustered" occurrences credits ADR 0019 — one of them with the credit BEFORE the term
 * ("via the ADR 0019 eval-clustered CI") — so a cite naming 0025 for it is wrong even though
 * the words are present.
 *
 * PRECISION (the design constraint — a noisy doctrine gate would be ignored):
 * - TERMS is scar-backed, not speculative: an entry earns its place by a recorded mis-cite.
 * - Each term OCCURRENCE binds to its NEAREST `ADR NNNN` on the line and only that pairing is
 *   judged. Measured: without this, a line citing two ADRs for two mechanisms false-fires (ADR
 *   0024's summary correctly cites 0023 for the hermetic executor and 0019 for the clustered CI).
 * - Frozen dated benchmark dirs are out of scope: append-only (ADR 0041), unfixable by policy.
 *
 * TESTING: check-cite-ownership.test.mjs (`node --test scripts/*.test.mjs` from the repo root).
 * Usage: node scripts/check-cite-ownership.mjs [repoRoot]   (default: cwd)
 * Exit: 0 = clean · 1 = a cite names an ADR that does not own the term · 2 = corpus unreadable.
 */
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

/** Doctrine terms whose mis-attribution is a RECORDED scar. Add an entry only with one. */
export const TERMS = ["append-only", "eval-clustered"];

const CITE = /ADR (\d{4})/g;
// Chars EITHER SIDE of a term occurrence in which a cite reads as crediting it. 60, not 40:
// measured against all six real owner/non-owner pairs in the corpus, ADR 0025's third occurrence
// ("the eval-clustered mean delta (with - without) + 95% CI (ADR 0019)") puts its credit 40 chars
// out — one past a 40 window — and the record then read as the OWNER of a term it never claims.
// 80 classifies identically, so 60 is the smallest window that separates every known case.
const CREDIT_WINDOW = 60;
// The BACKWARD window is deliberately tighter. A credit before the term only disclaims in the
// tight possessive form ("via the ADR 0019 eval-clustered CI" — 1 char gap); reaching further
// back lets a PRIOR sentence's citation bleed forward and disclaim a term the record then
// claims on its own account. Measured: 25 separates every real pair in the corpus.
const CREDIT_WINDOW_BEFORE = 25;
const BIND_WINDOW = 30;   // max chars between a term occurrence and the cite bound to it
const EXTENSIONS = /\.(md|mjs|js|py|sh|yml)$/;
const FROZEN = /^\d{4}-\d{2}-\d{2}-/;
const SKIP_DIRS = new Set([".git", "node_modules", "outputs", "graded"]);
// This gate and its test quote the terms and the scar ids as prose; they are not doctrine cites.
const SELF = /^scripts\/check-cite-ownership(\.test)?\.mjs$/;

/**
 * Does ADR `id` own `term`? Pure. `adrText` = the record's full text (null = unknown id, which
 * adr-lint's dangling-cite check owns, so treat as owning and stay silent here).
 * Owns iff the term occurs AND at least one occurrence is not credited to a DIFFERENT ADR within
 * the next CREDIT_WINDOW chars.
 */
export function ownsTerm(adrText, id, term) {
  if (adrText == null) return true;
  const low = adrText.toLowerCase();
  let i = -1;
  while ((i = low.indexOf(term, i + 1)) !== -1) {
    // A credit can sit on EITHER side: "eval-clustered CI (ADR 0019)" and "the ADR 0019
    // eval-clustered CI" both disclaim. Checking only forward missed the second shape and let
    // ADR 0025 — this gate's own founding example — read as the owner (red-team, round 3).
    const after = low.slice(i + term.length, i + term.length + CREDIT_WINDOW).match(/adr (\d{4})/);
    const beforeAll = [...low.slice(Math.max(0, i - CREDIT_WINDOW_BEFORE), i).matchAll(/adr (\d{4})/g)];
    const credits = [after?.[1], beforeAll.at(-1)?.[1]].filter(Boolean);
    // Self-credit is ownership; a credit naming another record disclaims THIS occurrence; an
    // uncredited occurrence anywhere is a claim of ownership.
    if (!credits.length || credits.includes(id)) return true;
  }
  return false;
}

/**
 * Pure line scan: for each term occurrence, bind the NEAREST cite on the line and judge only
 * that pairing. `ownsFn(id, term) -> boolean`. Returns [{ term, adr, column }].
 */
export function scanLine(line, ownsFn, terms = TERMS) {
  const low = line.toLowerCase();
  const cites = [...line.matchAll(CITE)].map((m) => ({ id: m[1], index: m.index }));
  if (!cites.length) return [];
  const out = [];
  for (const term of terms) {
    let i = -1;
    while ((i = low.indexOf(term, i + 1)) !== -1) {
      const termEnd = i + term.length;
      // Attribution convention is "<term> (ADR N)", so a FOLLOWING cite always wins; a preceding
      // one binds only in the possessive form ("ADR N's <term>") where nothing follows. Without
      // this, `(ADR 0023) + eval-clustered CI (ADR 0019)` binds to the nearer, wrong record.
      const after = cites.filter((c) => c.index >= termEnd)
        .reduce((b, c) => (b && b.index <= c.index ? b : c), null);
      const before = cites.filter((c) => c.index < i)
        .reduce((b, c) => (b && b.index >= c.index ? b : c), null);
      const best = after ?? before;
      const bestDist = !best ? Infinity : best === after ? best.index - termEnd : i - (best.index + 8);
      if (best && bestDist <= BIND_WINDOW && !ownsFn(best.id, term)) {
        out.push({ term, adr: best.id, column: i + 1 });
      }
    }
  }
  return out;
}

export function walkLiveFiles(root, readdir = readdirSync) {
  const out = [];
  const stack = [""];
  while (stack.length) {
    const rel = stack.pop();
    let entries;
    try { entries = readdir(rel ? join(root, rel) : root, { withFileTypes: true }); }
    catch (e) { if (e.code === "ENOENT" && rel) continue; throw e; }
    for (const e of entries) {
      if (SKIP_DIRS.has(e.name)) continue;
      const p = rel ? `${rel}/${e.name}` : e.name;
      if (e.isDirectory()) { if (!(rel === "benchmarks" && FROZEN.test(e.name))) stack.push(p); }
      else if (EXTENSIONS.test(e.name) && !SELF.test(p)) out.push(p);
    }
  }
  return out;
}

function main(argv) {
  const root = argv[2] ?? ".";
  let adrFiles;
  try { adrFiles = readdirSync(join(root, "docs/decisions")); }
  catch (e) {
    console.error(`check-cite-ownership: cannot read docs/decisions: ${e.message}`);
    process.exit(2);
  }
  const adrs = new Map();
  for (const f of adrFiles) {
    const m = f.match(/^(\d{4})-/);
    if (m) adrs.set(m[1], readFileSync(join(root, "docs/decisions", f), "utf8"));
  }
  const ownsFn = (id, term) => ownsTerm(adrs.get(id) ?? null, id, term);

  const problems = [];
  for (const rel of walkLiveFiles(root)) {
    let text;
    try { text = readFileSync(join(root, rel), "utf8"); }
    catch (e) { if (e.code === "ENOENT") continue; throw e; }
    text.split("\n").forEach((line, i) => {
      for (const hit of scanLine(line, ownsFn)) {
        problems.push(`${rel}:${i + 1}: cites ADR ${hit.adr} for "${hit.term}", but that record `
          + `does not own the term (it never states it, or states it while crediting another ADR) `
          + `— cite the owning record`);
      }
    });
  }
  if (problems.length) {
    console.error(`check-cite-ownership: ${problems.length} mis-attributed cite(s)`);
    for (const p of problems) console.error(`  - ${p}`);
    process.exit(1);
  }
  console.log(`check-cite-ownership: ${adrs.size} ADR(s), ${TERMS.length} scar-backed term(s) — `
    + `every bound cite names the owning record.`);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) main(process.argv);
