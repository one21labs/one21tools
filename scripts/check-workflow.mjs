#!/usr/bin/env node
/*
 * check-workflow.mjs — required CI checks for *.workflow.js files under a root dir; gates.yml
 * runs it over benchmarks/ (issue #61, wired as a gate by ADR 0029):
 *   1. model-key lint: every agent() call chooses its model — the rule and its test live in
 *      pdca-workflow/scripts/workflow-model.mjs (findMissingModel), imported here.
 *   2. wrap-and-syntax-check: workflow scripts use top-level return/await, legal only inside the
 *      Workflow runner's async wrapper — bare `node --check` false-positives (.mjs) or silently
 *      under-validates (.js). Emulate the wrapper, then syntax-check.
 *
 * wrapForCheck is pure and unit-tested (check-workflow.test.mjs); main() is the thin IO wrapper. Runs in gates.yml on every PR.
 * Required-gate status was an owner call (#54, retired ADR 0029): the missing-model defect
 * recurred across 5 merged files before #53 backfilled it — prevent beat advisory.
 *
 * Usage: node scripts/check-workflow.mjs [dir]   (dir default: benchmarks)
 * Exit 1 listing every syntax or missing-model problem; exit 0 otherwise.
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { findMissingModel } from "../pdca-workflow/scripts/workflow-model.mjs";

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
