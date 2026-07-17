#!/usr/bin/env node
/*
 * check-restatement.mjs — ARCHITECTURE ROLE: gate the literal half of the one-home/altitude
 * rule (ADR 0046): no two markdown files may share a long verbatim word span. A higher doc
 * restating a lower home starts, in the observed corpus, as copy-paste — this catches that
 * class deterministically; paraphrase is out of scope (owned by the muda-review prompt + the
 * ADR 0039 audit cadence, per ADR 0046).
 *
 * Mechanism: normalized word shingles (WINDOW consecutive words, code fences stripped,
 * lowercased) shared across two distinct .md files, merged into maximal spans. ALLOW_PAIRS is
 * the only pair-exemption list: permanent structural cases (generated-from-template files,
 * append-only twin records) where duplication is intentional or immutable. Everything else
 * fails the gate — the corpus stays clean, there is no debt register. Corpus: every .md under
 * root except .git, node_modules, and dated benchmarks/20YY-* run archives (immutable run
 * records, not living docs).
 *
 * DESIGN CONSTRAINTS: zero dependencies (plain node .mjs, same as adr-lint.mjs); detect() is
 * PURE (no fs) so the decision logic is unit-testable ("no process-gating script without a
 * test of its decision logic"); main() is the thin IO wrapper. Repo-instance tooling like
 * check-workflow.mjs, NOT shipped with a plugin (ADR 0046: the scanner + allowlist encode this
 * repo's structure; the traveling rule is ssot-enforcement.md's).
 *
 * Usage: node scripts/check-restatement.mjs [root] [--window=N]
 * Exit 1 on any non-allowlisted span.
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";

export const WINDOW = 12; // words; ADR 0046 operating point (measured: catches the #88 literal
                          // truth set; below ~10 boilerplate noise rises, above ~18 recall drops)

// Permanent structural exemptions — INTENTIONAL duplication, never debt (ADR 0046):
// generated-from-template families share their template's shell; append-only twin verdict
// records share arm boilerplate and cannot be edited.
export const ALLOW_PAIRS = [
  [/^\.claude\/agents\//, /^\.claude\/agents\//],
  [/^\.claude\/agents\//, /^pdca-workflow\/skills\/pdca-init\/references\/advisor-template\.md$/],
  [/^CLAUDE\.md$/, /^pdca-workflow\/skills\/pdca-init\/references\/claude-md-template\.md$/],
  [/^\.claude\/output-styles\/plain-summary\.md$/, /^pdca-workflow\/templates\/plain-summary\.md$/],
  [/^docs\/decisions\/README\.md$/, /^pdca-workflow\/skills\/pdca-init\//],
  [/^docs\/decisions\/0035-/, /^docs\/decisions\/0036-/],
];

const SKIP = /(^|[\\/])(\.git|node_modules|benchmarks[\\/]20\d\d-)/;

export function allowed(a, b, pairs = ALLOW_PAIRS) {
  return pairs.some(([p, q]) => (p.test(a) && q.test(b)) || (p.test(b) && q.test(a)));
}

function tokenize(text) {
  const out = [];
  let inFence = false;
  let inFrontmatter = false;
  text.split("\n").forEach((line, i) => {
    if (i === 0 && line.trim() === "---") { inFrontmatter = true; return; }
    if (inFrontmatter) { if (line.trim() === "---") inFrontmatter = false; return; }
    if (line.trim().startsWith("```")) { inFence = !inFence; return; }
    if (inFence) return;
    // Template-mandated ADR metadata fields are definitionally identical across a same-day
    // batch — structure, not restatement.
    if (/^- (Date|Owner|Panel):/.test(line.trim())) return;
    for (const m of line.toLowerCase().matchAll(/[a-z0-9][a-z0-9'./-]*/g))
      out.push([m[0], i + 1]);
  });
  return out;
}

/**
 * Pure decision logic. files = [{ name, text }]. Returns spans:
 * [{ words, a: "file:line", b: "file:line", pair: "fileA|fileB", snippet }] for every maximal
 * cross-file span of >= window shared words, excluding allowlisted pairs.
 */
export function detect(files, { window = WINDOW, allowPairs = ALLOW_PAIRS } = {}) {
  const toks = files.map(f => ({ name: f.name, toks: tokenize(f.text.replace(/\r\n/g, "\n")) }));
  const map = new Map();
  toks.forEach((f, fi) => {
    for (let i = 0; i + window <= f.toks.length; i++) {
      const key = f.toks.slice(i, i + window).map(t => t[0]).join(" ");
      let arr = map.get(key);
      if (!arr) map.set(key, arr = []);
      arr.push({ fi, i });
    }
  });

  const pairHits = new Map();
  for (const locs of map.values()) {
    if (new Set(locs.map(l => l.fi)).size < 2) continue;
    for (let a = 0; a < locs.length; a++)
      for (let b = a + 1; b < locs.length; b++) {
        if (locs[a].fi === locs[b].fi) continue;
        const [x, y] = locs[a].fi < locs[b].fi ? [locs[a], locs[b]] : [locs[b], locs[a]];
        const k = `${x.fi}|${y.fi}`;
        let arr = pairHits.get(k);
        if (!arr) pairHits.set(k, arr = []);
        arr.push([x.i, y.i]);
      }
  }

  const spans = [];
  for (const [k, hits] of pairHits) {
    const [fiA, fiB] = k.split("|").map(Number);
    if (allowed(toks[fiA].name, toks[fiB].name, allowPairs)) continue;
    hits.sort((p, q) => p[0] - q[0] || p[1] - q[1]);
    let cur = null;
    for (const [ia, ib] of hits) {
      if (cur && ia === cur.ea + 1 && ib === cur.eb + 1) { cur.ea = ia; cur.eb = ib; }
      else { if (cur) spans.push(cur); cur = { fiA, fiB, sa: ia, sb: ib, ea: ia, eb: ib }; }
    }
    if (cur) spans.push(cur);
  }

  return spans.map(s => {
    const A = toks[s.fiA], B = toks[s.fiB];
    return {
      words: s.ea - s.sa + window,
      a: `${A.name}:${A.toks[s.sa][1]}`,
      b: `${B.name}:${B.toks[s.sb][1]}`,
      pair: [A.name, B.name].sort().join("|"),
      snippet: A.toks.slice(s.sa, s.sa + 10).map(t => t[0]).join(" "),
    };
  }).sort((x, y) => y.words - x.words);
}

function mdFiles(dir, out = []) {
  for (const e of readdirSync(dir)) {
    const p = join(dir, e);
    if (SKIP.test(p)) continue;
    if (statSync(p).isDirectory()) mdFiles(p, out);
    else if (e.endsWith(".md")) out.push(p);
  }
  return out;
}

function main(argv) {
  const args = argv.slice(2);
  const root = args.find(a => !a.startsWith("--")) ?? ".";
  const window = Number((args.find(a => a.startsWith("--window=")) ?? `--window=${WINDOW}`).split("=")[1]);

  const files = mdFiles(root).map(p => ({
    name: relative(root, p).replaceAll("\\", "/"),
    text: readFileSync(p, "utf8"),
  }));

  const spans = detect(files, { window });
  if (spans.length) {
    console.error(`check-restatement: ${spans.length} cross-file restatement span(s) (window=${window}):`);
    for (const s of spans)
      console.error(`  ${s.words}w  ${s.a} <-> ${s.b}\n      "${s.snippet}..."`);
    console.error("One home per fact: point at the owning file instead of restating (ADR 0046).");
    process.exit(1);
  }
  console.log(`check-restatement: ${files.length} md files, no cross-file restatement (window=${window}).`);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) main(process.argv);
