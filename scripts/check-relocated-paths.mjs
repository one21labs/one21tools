#!/usr/bin/env node
/*
 * check-relocated-paths.mjs — ARCHITECTURE ROLE: the frozen-dir path-preservation gate
 * (ADR 0089): every backticked repo-relative path cited inside a frozen dated benchmark dir
 * (`benchmarks/<YYYY-MM-DD>-*`) must still resolve in the worktree IF it ever existed in git
 * history. Frozen dirs are append-only (ADR 0041) — their committed reproduce steps cannot be
 * swept when shared code moves, so the remedy is path-end preservation (shim or pointer stub,
 * precedent PR #230); this gate FAILs when a relocation strands one instead.
 *
 * The ever-existed filter (`git log --all -- <path>` non-empty) is what makes the predicate
 * decidable without inferring intent: a synthetic substrate/fixture path never existed here; a
 * relocated one did. Measured on the current tree: 0 false positives (ADR 0089 Assumptions).
 * CI NOTE: requires full history — gates.yml checks out with fetch-depth: 0; a shallow clone
 * would silently report every path as never-existed (permanent false negative).
 *
 * APPENDING A CORRECTION (ADR 0089(b)(ii)): name the stranded path in PLAIN TEXT, not backticks.
 * A correction note is appended INSIDE the frozen dir, so a backticked path there is a new
 * gate-visible cite — the remedy would trip this gate and force a path restore it was chosen to
 * avoid. Backtick the NEW location (it resolves); leave the old one bare.
 *
 * SCOPE (ADR 0089(c)/(d), precision over recall like check-references.mjs): single-backtick
 * spans only, outside fenced ``` blocks; token starts with a known top-level dir, ends in a
 * file extension, whole span free of $ * < > { } | (shell vars, globs, templates); relative
 * (`../lib/...`) and un-backticked forms are recorded residue, deliberately missed.
 *
 * DESIGN CONSTRAINTS (inherited from the sibling gates): zero dependencies; extraction +
 * decision are PURE functions (CLAUDE.md process-gating-script rule) with injectable readdir
 * for the walk (the #282/#284 ENOENT-vanish race is testable); main() is the thin IO wrapper.
 *
 * TESTING: check-relocated-paths.test.mjs (`node --test scripts/*.test.mjs` from repo root).
 * Usage: node scripts/check-relocated-paths.mjs [repoRoot]   (default: cwd)
 * Exit: 0 = clean · 1 = stranded path(s) · 2 = benchmarks/ unreadable or git failure.
 */
import { execSync } from "node:child_process";
import { readdirSync, readFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const DATED_DIR = /^\d{4}-\d{2}-\d{2}-.+$/;
const EXTENSIONS = new Set([".md", ".py", ".sh", ".js"]);
const FENCE = /^\s*```/;
const SPAN = /`([^`]+)`/g;
// Repo-relative path at the START of a span: first segment / rest, extension-terminated.
// Trailing span content after the match (a :symbol, CLI flags) is allowed.
const PATH_RE = /^([A-Za-z0-9_.-]+)\/[A-Za-z0-9_./-]*\.[A-Za-z0-9]+/;
const FORBIDDEN = /[$*<>{}|]/;

/**
 * Pure extraction. `files` = [{ path, text }]; `knownTopDirs` = Set of repo-root dir names.
 * Returns [{ file, line, path }] — every backticked, top-dir-anchored, extension-terminated
 * path token outside fenced blocks. Rejection of `..`-relative forms falls out of the
 * knownTopDirs check ("../" first segment is ".."), asserted explicitly in the test.
 */
export function extractPathTokens(files, knownTopDirs) {
  const out = [];
  for (const { path, text } of files) {
    let inFence = false;
    const lines = text.split("\n");
    for (let i = 0; i < lines.length; i++) {
      if (FENCE.test(lines[i])) { inFence = !inFence; continue; }
      if (inFence) continue;
      for (const m of lines[i].matchAll(SPAN)) {
        const span = m[1];
        if (FORBIDDEN.test(span)) continue;
        const p = span.match(PATH_RE);
        if (!p || !knownTopDirs.has(p[1])) continue;
        out.push({ file: path, line: i + 1, path: p[0] });
      }
    }
  }
  return out;
}

/**
 * Pure decision. `candidates` from extractPathTokens; `existingPaths` = Set of candidates
 * present in the worktree; `everExisted` = Set of absent candidates with non-empty
 * `git log --all` history. Problem iff absent AND ever-existed (a stranded relocation).
 */
export function checkRelocatedPaths({ candidates, existingPaths, everExisted }) {
  const problems = candidates
    .filter(c => !existingPaths.has(c.path) && everExisted.has(c.path))
    .map(c => `${c.file}:${c.line}: \`${c.path}\` is cited by this frozen dir but absent from the `
      + `worktree despite existing in git history — a relocation stranded it; restore it at the `
      + `old path (shim or pointer stub, ADR 0089/PR #230), never edit the frozen line`);
  return { problems };
}

/**
 * Walk each benchmarks/<YYYY-MM-DD>-* dir recursively for scoped extensions. ENOENT-tolerant below the
 * root (#282/#284: concurrent fixture churn), never for benchmarks/ itself — the gate must not
 * go silently vacuous. `readdir` injectable for tests.
 */
export function walkFrozenDirs(root, readdir = readdirSync) {
  const datedRoots = readdir(join(root, "benchmarks"), { withFileTypes: true })
    .filter(e => e.isDirectory() && DATED_DIR.test(e.name))
    .map(e => `benchmarks/${e.name}`);
  const out = [];
  const stack = [...datedRoots];
  while (stack.length) {
    const rel = stack.pop();
    let entries;
    try { entries = readdir(join(root, rel), { withFileTypes: true }); }
    catch (e) {
      if (e.code === "ENOENT") continue;
      throw e;
    }
    for (const e of entries) {
      const p = `${rel}/${e.name}`;
      if (e.isDirectory()) stack.push(p);
      else if (EXTENSIONS.has(e.name.slice(e.name.lastIndexOf(".")))) out.push(p);
    }
  }
  return out;
}

function main(argv) {
  const root = argv[2] ?? ".";
  let filePaths, knownTopDirs;
  try {
    filePaths = walkFrozenDirs(root);
    knownTopDirs = new Set(readdirSync(root, { withFileTypes: true })
      .filter(e => e.isDirectory() && e.name !== ".git" && e.name !== "node_modules")
      .map(e => e.name));
  } catch (e) {
    console.error(`check-relocated-paths: cannot walk ${root}/benchmarks: ${e.message}`);
    process.exit(2);
  }
  const files = [];
  for (const p of filePaths) {
    try { files.push({ path: p, text: readFileSync(join(root, p), "utf8") }); }
    catch (e) { if (e.code !== "ENOENT") throw e; }
  }
  const candidates = extractPathTokens(files, knownTopDirs);
  const existingPaths = new Set(), everExisted = new Set();
  for (const path of new Set(candidates.map(c => c.path))) {
    if (existsSync(join(root, path))) { existingPaths.add(path); continue; }
    try {
      if (execSync(`git log --all --format=%h -- "${path}"`, { cwd: root, encoding: "utf8" }).trim())
        everExisted.add(path);
    } catch (e) {
      console.error(`check-relocated-paths: git log failed for ${path}: ${e.message}`);
      process.exit(2);
    }
  }
  const { problems } = checkRelocatedPaths({ candidates, existingPaths, everExisted });
  if (problems.length) {
    console.error(`check-relocated-paths: ${problems.length} stranded path(s)`);
    for (const p of problems) console.error(`  - ${p}`);
    process.exit(1);
  }
  console.log(`check-relocated-paths: ${candidates.length} cited path token(s) across `
    + `${files.length} frozen-dir file(s) — none stranded.`);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) main(process.argv);
