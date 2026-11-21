#!/usr/bin/env node
/*
 * workflow-model.mjs — ARCHITECTURE ROLE: the one home for "does every agent() call in a
 * Workflow script choose its model". An agent() call with no model runs on the session's model,
 * so a large fan-out launched from an Opus session bills every bulk worker at the top tier.
 *
 * USED BY:
 *   hooks/explicit-model-guard.sh — pipes a Workflow tool call here (--hook) before it runs.
 *   a repo's own CI — import findMissingModel to lint committed *.workflow.js files.
 *
 * DESIGN CONSTRAINTS: zero dependencies; findMissingModel() is pure. --hook mode FAILS OPEN:
 * unreadable input, a named workflow (no script to read), or a script file that cannot be read
 * prints nothing and exits 0 — a broken guard must never block every workflow.
 *
 * Usage: node workflow-model.mjs --hook   (stdin: the PreToolUse hook JSON for a Workflow call)
 *   Prints a deny decision when a script has an agent() call with no model, else nothing.
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

/**
 * One problem string per agent() call whose arguments carry neither a `model:` key nor an
 * `agentType:` key (a registered agent brings its own model). Scans each `agent(` to its
 * balanced closing paren — naive about strings and comments, which errs toward passing a call.
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
    if (!/\b(model|agentType)\s*:/.test(call))
      problems.push(`${name}:${line}: agent() call without a model: key (inherits the session model) — add an explicit model: to the opts object so the fan-out tier is a decision, not an accident`);
  }
  return problems;
}

/** The hook's decision for one PreToolUse payload: a deny object, or null to let the call run. */
export function hookDecision(payload, readFile = (p) => readFileSync(p, "utf8")) {
  const input = payload?.tool_input;
  if (!input || typeof input !== "object") return null;
  let source = typeof input.script === "string" ? input.script : null;
  if (source === null && typeof input.scriptPath === "string") {
    try { source = readFile(input.scriptPath); } catch { return null; }
  }
  if (source === null) return null;
  const problems = findMissingModel(source, "script");
  if (problems.length === 0) return null;
  const lines = problems.map((p) => p.split(": agent()")[0]).join(", ");
  return {
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason:
        `Denied: ${problems.length} agent() call(s) in this workflow script set no model (${lines}), ` +
        "so each would run on the session's model. Add model to each call's options: sonnet for " +
        "bulk work (finders, reviewers, graders), haiku for mechanical steps, opus only for " +
        "planning or final judgment. Then run the workflow again.",
    },
  };
}

function main() {
  let raw = "";
  try { raw = readFileSync(0, "utf8"); } catch { return; }
  let payload;
  try { payload = JSON.parse(raw); } catch { return; }
  const decision = hookDecision(payload);
  if (decision) process.stdout.write(JSON.stringify(decision));
}

if (process.argv[1] === fileURLToPath(import.meta.url) && process.argv.includes("--hook")) main();
