#!/usr/bin/env node
/*
 * check-references.mjs — ARCHITECTURE ROLE: the reference-veracity write-time gate (ADR 0079,
 * mechanizing the owner ruling recorded at docs/research/loop-engineering.md "Reference-veracity
 * rule"): a change that ADDS an external reference (URL / arXiv id / bare domain with a path) to
 * a tracked corpus file (docs/research/*.md, docs/decisions/*.md) must also touch a
 * `sources/*reference-audit*` record in the same change — the fetch-audit travels with the
 * citation the way a Testing section travels with a PR.
 *
 * The hook is SYNTACTIC on purpose: it forces the audit record to EXIST; whether the audit is
 * truthful stays the manual adversarial step (layered guards, ADR 0046). Raw lane files under
 * docs/research/sources/ are not trigger paths — they are the audit substrate itself.
 *
 * DESIGN CONSTRAINTS (inherited from the sibling gates):
 * - Zero dependencies; checkReferences() is PURE so the decision logic is unit-testable per
 *   CLAUDE.md's process-gating-script rule. main() is the thin git-diff IO wrapper.
 * - Two-dot diff from the base ref, matching gates.yml's decision-set step (CI checks out the
 *   PR merge commit, so base..HEAD is exactly the PR's changes).
 * - Known limitation (recorded, not hidden): a bare domain WITHOUT a path ("skillsbench.ai")
 *   is not matched — precision over recall; the escalation path is ADR 0079's revisit trigger.
 *
 * TESTING: check-references.test.mjs (`node --test scripts/*.test.mjs` from the repo root).
 * Usage: node scripts/check-references.mjs [baseRef]   (default: origin/main)
 * Exit: 0 = clean · 1 = external ref added without an audit-record touch · 2 = git failure.
 */
import { execSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const TRACKED = /^docs\/(research|decisions)\/[^/]+\.md$/;
const AUDIT = /reference-audit/;
// One alternation per external-reference shape; own-repo links are not external citations.
const EXTERNAL_REF = new RegExp(
  "https?://(?!github\\.com/one21labs/)\\S+"
  + "|\\barXiv:\\s?\\d{4}\\.\\d{4,5}\\b"
  + "|\\b(?!github\\.com/one21labs/)[a-z0-9][a-z0-9.-]*\\.(?:com|org|ai|io|dev|net|edu)/[A-Za-z0-9][^\\s)]*",
  "i");

/**
 * Pure decision logic. `addedByFile` = { path: [added line, ...] } (diff "+" lines, no prefix);
 * `changedFiles` = every path the change touches. Returns { problems }.
 */
export function checkReferences({ addedByFile, changedFiles }) {
  const problems = [];
  const auditTouched = changedFiles.some(f => AUDIT.test(f));
  for (const [path, lines] of Object.entries(addedByFile)) {
    if (!TRACKED.test(path)) continue;
    const hits = lines.filter(l => EXTERNAL_REF.test(l)).length;
    if (hits && !auditTouched)
      problems.push(`${path}: adds ${hits} external reference line(s) but the change touches no `
        + `sources/*reference-audit* record — commit the fetch-audit with the citation (ADR 0079; `
        + `docs/research/loop-engineering.md Reference-veracity rule)`);
  }
  return { problems };
}

function main(argv) {
  const base = argv[2] ?? "origin/main";
  let nameOnly, diff;
  try {
    nameOnly = execSync(`git diff --name-only ${base} HEAD`, { encoding: "utf8" });
    diff = execSync(`git diff --unified=0 ${base} HEAD -- docs/research docs/decisions`, { encoding: "utf8" });
  } catch (e) {
    console.error(`check-references: git diff against ${base} failed: ${e.message}`);
    process.exit(2);
  }
  const addedByFile = {};
  let file = null;
  for (const line of diff.split("\n")) {
    const f = line.match(/^\+\+\+ b\/(.*)$/);
    if (f) { file = f[1]; continue; }
    if (file && line.startsWith("+")) (addedByFile[file] ??= []).push(line.slice(1));
  }
  const { problems } = checkReferences({ addedByFile, changedFiles: nameOnly.split("\n").filter(Boolean) });
  if (problems.length) {
    console.error(`check-references: ${problems.length} problem(s)`);
    for (const p of problems) console.error(`  - ${p}`);
    process.exit(1);
  }
  console.log("check-references: no unaudited external reference added.");
}

if (process.argv[1] === fileURLToPath(import.meta.url)) main(process.argv);
