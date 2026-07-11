#!/usr/bin/env node
/*
 * check-workflow.mjs — required CI checks for benchmarks/**\/*.workflow.js (issue #61, wired as a
 * gate by ADR 0029):
 *   1. model-key lint: every agent() call's options object must carry a `model:` key, else the
 *      agent silently inherits the session model (Opus — the defect #53 had to backfill across
 *      5 merged files). The tiering rule's prose home is optimizing-context's subagents.md.
 *   2. wrap-and-syntax-check: workflow scripts use top-level return/await, legal only inside the
 *      Workflow runner's async wrapper — bare `node --check` false-positives (.mjs) or silently
 *      under-validates (.js). Emulate the wrapper, then syntax-check.
 *
 * Decision logic (findMissingModel, wrapForCheck) is pure and unit-tested
 * (check-workflow.test.mjs); main() is the thin IO wrapper. Runs in gates.yml on every PR.
 *
 * Usage: node scripts/check-workflow.mjs [dir]   (dir default: benchmarks)
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

/**
 * Return one problem string per agent() call whose options object lacks a `model:` key.
 * Scans each `agent(` to its balanced closing paren (string/template/comment-naive but
 * sufficient for this repo's workflow style); a call with no object literal at all is
 * also flagged (its options can't carry model:).
 */
export function findMissingModel(source, name = "workflow") {
  const problems = [];
  const re = /\bagent\(/g;
  let m;
  while ((m = re.exec(source)) !== null) {
    const start = m.index + m[0].length;
    let depth = 1, i = start;
    while (i < source.length && depth > 0) {
      const c = source[i];
      if (c === "(") depth++;
      else if (c === ")") depth--;
      i++;
    }
    const call = source.slice(start, i - 1);
    const line = source.slice(0, m.index).split("\n").length;
    if (!/model\s*:/.test(call))
      problems.push(`${name}:${line}: agent() call without a model: key (inherits the session model)`);
  }
  return problems;
}

/** Emulate the Workflow runner's async wrapper so top-level return/await parse. */
export function wrapForCheck(source) {
  const body = source.replace(/^export /gm, "");
  return `async function __wf(agent, pipeline, parallel, log, phase, args, budget, workflow) {\n${body}\n}\n`;
}

function syntaxProblems(source, name) {
  const res = spawnSync(process.execPath, ["--check", "-"], {
    input: wrapForCheck(source), encoding: "utf8",
  });
  if (res.status === 0) return [];
  const firstErr = (res.stderr || "syntax check failed").split("\n").find(l => /Error/.test(l)) || "syntax error";
  return [`${name}: ${firstErr.trim()}`];
}

function* walk(dir) {
  for (const entry of readdirSync(dir)) {
    const p = join(dir, entry);
    if (statSync(p).isDirectory()) yield* walk(p);
    else if (entry.endsWith(".workflow.js")) yield p;
  }
}

function main(argv) {
  const dir = argv[2] ?? "benchmarks";
  const problems = [];
  let count = 0;
  for (const file of walk(dir)) {
    count++;
    const source = readFileSync(file, "utf8");
    problems.push(...syntaxProblems(source, file));
    problems.push(...findMissingModel(source, file));
  }
  if (problems.length) {
    console.error(`check-workflow: ${problems.length} problem(s) across ${count} workflow file(s)`);
    for (const p of problems) console.error(`  - ${p}`);
    process.exit(1);
  }
  console.log(`check-workflow: ${count} workflow file(s) OK (syntax + model: on every agent() call).`);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) main(process.argv);
