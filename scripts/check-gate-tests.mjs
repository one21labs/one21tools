#!/usr/bin/env node
/*
 * check-gate-tests.mjs — ARCHITECTURE ROLE: gate ADR 0047 wave-1's self-application amendment
 * ("no gate ships without a decision-logic test") by making it executable instead of prose. Every
 * script wired into .github/workflows/gates.yml as a `node <path>.mjs` invocation, and every bash
 * hook wired into a hooks.json/settings "hooks" block, must have a sibling decision-logic test
 * that the gates workflow's own `node --test` step actually picks up — a test file that exists
 * but isn't globbed by CI is exactly as unverified as no test at all.
 *
 * Mechanism, .mjs gates: parse gates.yml's `run:` lines for `node <path>.mjs` (excluding
 * `node --test ...` lines, which name GLOBS of tests, not a gate to test) to get the wired set;
 * the expected test is `<path without .mjs>.test.mjs`; it must exist AND match one of the globs
 * named on a `node --test` line.
 *
 * Mechanism, python gates (ADR 0069): every `python3 <path>.py` gate invocation on a run: line
 * (excluding *_test.py, globs, and shell-variable args like `python3 "$t"`) requires a sibling
 * `<path>_test.py` that CI executes — matched by a `*_test.py` glob token or invoked directly
 * on a `python3 ..._test.py` line (basename match covers the `cd <dir> && python3 x_test.py`
 * idiom).
 *
 * Vacuity check (ADR 0069): a resolved test-<basename>.sh whose text assigns a path-root
 * variable a LITERAL absolute path (no `$(`/`${` derivation) is flagged — the machine-path
 * SKIP-exit-0 scar class where CI asserts nothing everywhere but one machine.
 *
 * Mechanism, bash hooks: parse pdca-workflow/hooks/hooks.json and any .claude/settings*.json for
 * a "hooks" block's `command` strings ending in .sh (resolving ${CLAUDE_PLUGIN_ROOT} /
 * ${CLAUDE_PROJECT_DIR}) to get the registered set. The standard (ADR 0064) is a self-contained
 * sibling `test-<basename>.sh` suite matched by a .sh path/glob appearing in a gates.yml run:
 * line (e.g. the `for t in pdca-workflow/hooks/test-*.sh` step) — a CI-verified invocation, not
 * mere file existence. The two pre-0064 hooks tested via a `<basename>.test.mjs` that spawns the
 * real .sh (MJS_GRANDFATHERED_HOOKS) keep that path, covered by a `node --test` glob; every
 * other hook must carry the .sh suite.
 *
 * DESIGN CONSTRAINTS: zero dependencies; findMissingTests() is PURE (no fs — takes gatesYml text,
 * hook-registration texts, and an `existingFiles.has(path)` duck-typed lookup) so the decision
 * logic is unit-testable, matching check-restatement.mjs's detect()/main() split. main() is the
 * thin IO wrapper.
 *
 * Usage: node scripts/check-gate-tests.mjs [root]
 * Exit 1 listing every wired gate/hook missing a CI-visible decision-logic test; exit 0 otherwise.
 */
import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const GATES_WORKFLOW = ".github/workflows/gates.yml";

/** Hooks predating ADR 0064 whose decision-logic tests stay `<basename>.test.mjs`; every other
 *  registered hook must carry a gates.yml-invoked sibling `test-<basename>.sh` (ADR 0064). */
export const MJS_GRANDFATHERED_HOOKS = new Set([
  "pdca-workflow/hooks/explicit-model-guard.sh",
]);
const HOOK_REGISTRATIONS = [
  { path: "pdca-workflow/hooks/hooks.json", pluginRoot: "pdca-workflow" },
  { path: ".claude/settings.json", pluginRoot: "." },
  { path: ".claude/settings.local.json", pluginRoot: "." },
];

/** Every `node <path>.mjs` invocation in a `run:` line, excluding `node --test ...` lines
 *  (those name test globs, not a gate). Dedaped, in first-seen order. */
export function extractWiredGates(gatesYml) {
  const out = [];
  for (const line of gatesYml.split("\n")) {
    if (/\bnode\s+--test\b/.test(line)) continue;
    const m = line.match(/\bnode\s+(\S+\.mjs)\b/);
    if (m && !m[1].includes("*")) out.push(m[1]);
  }
  return [...new Set(out)];
}

/** Every `python3 <path>.py` gate invocation in a run: line — excluding test files, globs, and
 *  shell-variable args (`python3 "$t"`). Deduped, in first-seen order. */
export function extractPyGates(gatesYml) {
  const out = [];
  for (const line of gatesYml.split("\n")) {
    const m = line.match(/\bpython3\s+(\S+\.py)\b/);
    if (m && !m[1].endsWith("_test.py") && !m[1].includes("*") && !m[1].includes("$")) out.push(m[1]);
  }
  return [...new Set(out)];
}

/** How CI executes python tests: `*_test.py` glob tokens (for-loop style) plus direct
 *  `python3 <x>_test.py` invocations (kept verbatim; basename covers the cd-then-run idiom). */
export function extractPyTestExecutions(gatesYml) {
  const globs = [];
  const direct = [];
  for (const line of gatesYml.split("\n")) {
    for (const m of line.matchAll(/[^\s;'"`]+\*[^\s;'"`]*_test\.py/g)) globs.push(m[0]);
    const d = line.match(/\bpython3\s+(\S+_test\.py)\b/);
    if (d) direct.push(d[1]);
  }
  return { globs: [...new Set(globs)], direct: [...new Set(direct)] };
}

/** Line numbers assigning a path-root variable a literal absolute path with no derivation —
 *  the self-skip signature (ADR 0069): such a test SKIPs everywhere but one machine. */
export function selfSkipLines(shText) {
  const out = [];
  shText.split("\n").forEach((line, i) => {
    if (/^\s*[A-Z_]+=["']?([A-Za-z]:[\\/]|\/(home|Users|mnt|root|opt|srv)\/)/.test(line)
        && !line.includes("$(") && !line.includes("${")) out.push(i + 1);
  });
  return out;
}

/** Every glob argument following `node --test` on any line. */
export function extractTestGlobs(gatesYml) {
  const out = [];
  for (const line of gatesYml.split("\n")) {
    const m = line.match(/\bnode\s+--test\s+(.+)$/);
    if (m) out.push(...m[1].trim().split(/\s+/));
  }
  return out;
}

/** Every .sh path or glob appearing anywhere in gates.yml (run: lines invoke them directly or
 *  via a `for t in dir/test-*.sh` loop — either way the token names what CI executes). */
export function extractShInvocations(gatesYml) {
  const out = [];
  for (const line of gatesYml.split("\n")) {
    for (const m of line.matchAll(/[^\s'"`;()]+\.sh(?![\w.])/g)) out.push(m[0]);
  }
  return [...new Set(out)];
}

/** True if `path` matches `glob` (glob's only wildcard is `*`, matching within one path segment
 *  — sufficient for gates.yml's `dir/*.test.mjs` style globs). */
export function globCoversPath(glob, path) {
  const re = new RegExp(
    "^" + glob.split("*").map((s) => s.replace(/[.+^${}()|[\]\\]/g, "\\$&")).join("[^/]*") + "$"
  );
  return re.test(path);
}

/** Bash hook script paths (posix, repo-root-relative) registered in a hooks.json/settings
 *  "hooks" block's `command` fields. Returns [] on absent/malformed input — a missing or
 *  hookless registration file is not this gate's failure mode. */
export function extractRegisteredHooks(registrationText, pluginRoot) {
  let parsed;
  try {
    parsed = JSON.parse(registrationText);
  } catch {
    return [];
  }
  const out = [];
  const hooks = parsed && typeof parsed === "object" ? parsed.hooks : null;
  if (!hooks || typeof hooks !== "object") return out;
  for (const event of Object.values(hooks)) {
    if (!Array.isArray(event)) continue;
    for (const matcher of event) {
      for (const h of matcher?.hooks ?? []) {
        if (h?.type !== "command" || typeof h.command !== "string") continue;
        const resolved = h.command
          .replaceAll("${CLAUDE_PLUGIN_ROOT}", pluginRoot)
          .replaceAll("${CLAUDE_PROJECT_DIR}", ".");
        const m = resolved.match(/([^\s'"]+\.sh)\b/);
        if (m) out.push(m[1].replace(/^\.\//, "").replaceAll("\\", "/"));
      }
    }
  }
  return [...new Set(out)];
}

/**
 * Pure decision logic. gatesYml: text of gates.yml. hookRegistrations: [{ text, pluginRoot }] for
 * each registration file present. existingFiles: anything exposing `.has(posixRelPath)`.
 * readFile(posixRelPath) -> string|null enables the ADR 0069 vacuity check; omitted, that check
 * is skipped (pre-0069 behavior). Returns [{ kind: "gate"|"hook", path, expected, reason }] for
 * every wired gate/hook lacking a CI-visible (and non-vacuous) test; [] means the corpus passes.
 */
export function findMissingTests({ gatesYml, hookRegistrations = [], existingFiles, readFile = null }) {
  const testGlobs = extractTestGlobs(gatesYml);
  const shInvocations = extractShInvocations(gatesYml);
  const missing = [];

  for (const gate of extractWiredGates(gatesYml)) {
    const testPath = gate.replace(/\.mjs$/, ".test.mjs");
    if (!existingFiles.has(testPath)) {
      missing.push({ kind: "gate", path: gate, expected: testPath, reason: "no sibling test file" });
    } else if (!testGlobs.some((g) => globCoversPath(g, testPath))) {
      missing.push({ kind: "gate", path: gate, expected: testPath, reason: "test file exists but not covered by any `node --test` glob" });
    }
  }

  const pyExec = extractPyTestExecutions(gatesYml);
  for (const gate of extractPyGates(gatesYml)) {
    const testPath = gate.replace(/\.py$/, "_test.py");
    const baseName = testPath.slice(testPath.lastIndexOf("/") + 1);
    const executed = pyExec.globs.some((g) => globCoversPath(g, testPath))
      || pyExec.direct.some((d) => d === testPath || d === baseName);
    if (!existingFiles.has(testPath)) {
      missing.push({ kind: "gate", path: gate, expected: testPath, reason: "no sibling _test.py" });
    } else if (!executed) {
      missing.push({ kind: "gate", path: gate, expected: testPath, reason: "sibling _test.py exists but no gates.yml line executes it" });
    }
  }

  const hooks = hookRegistrations.flatMap(({ text, pluginRoot }) => extractRegisteredHooks(text, pluginRoot));
  for (const hook of [...new Set(hooks)]) {
    const slash = hook.lastIndexOf("/");
    const dir = slash === -1 ? "." : hook.slice(0, slash);
    const base = (slash === -1 ? hook : hook.slice(slash + 1)).replace(/\.sh$/, "");
    const shCandidate = `${dir}/test-${base}.sh`;
    const shHit = existingFiles.has(shCandidate) && shInvocations.some((g) => globCoversPath(g, shCandidate));
    if (shHit) {
      const text = readFile ? readFile(shCandidate) : null;
      const skips = text == null ? [] : selfSkipLines(text);
      if (skips.length) {
        missing.push({
          kind: "hook",
          path: hook,
          expected: shCandidate,
          reason: `test self-skips via hard-coded absolute path (${shCandidate}:${skips[0]}, ADR 0069)`,
        });
      }
      continue;
    }
    if (MJS_GRANDFATHERED_HOOKS.has(hook)) {
      const scriptsDir = dir.replace(/\/hooks$/, "/scripts");
      const mjsCandidates = [...new Set([`${dir}/${base}.test.mjs`, `${scriptsDir}/${base}.test.mjs`])];
      if (mjsCandidates.some((c) => existingFiles.has(c) && testGlobs.some((g) => globCoversPath(g, c)))) continue;
      missing.push({
        kind: "hook",
        path: hook,
        expected: [...mjsCandidates, shCandidate].join(" or "),
        reason: "no CI-visible <basename>.test.mjs (grandfathered) or gates.yml-invoked test-<basename>.sh",
      });
    } else {
      missing.push({
        kind: "hook",
        path: hook,
        expected: shCandidate,
        reason: existingFiles.has(shCandidate)
          ? "test-<basename>.sh exists but no gates.yml run line invokes it"
          : "hook tests standardize on a gates.yml-invoked sibling test-<basename>.sh (ADR 0064)",
      });
    }
  }

  return missing;
}

function main(argv) {
  const root = argv[2] && !argv[2].startsWith("--") ? argv[2] : ".";
  const read = (relPath) => {
    try {
      return readFileSync(join(root, relPath), "utf8");
    } catch {
      return null;
    }
  };

  const gatesYml = read(GATES_WORKFLOW);
  if (gatesYml == null) {
    console.error(`check-gate-tests: ${GATES_WORKFLOW} not found — nothing to check.`);
    process.exit(1);
  }

  const hookRegistrations = HOOK_REGISTRATIONS
    .map(({ path, pluginRoot }) => ({ text: read(path), pluginRoot }))
    .filter((r) => r.text != null);

  const existingFiles = { has: (relPath) => existsSync(join(root, relPath)) };

  const missing = findMissingTests({ gatesYml, hookRegistrations, existingFiles, readFile: read });
  const wiredCount = extractWiredGates(gatesYml).length + extractPyGates(gatesYml).length;
  const hookCount = new Set(hookRegistrations.flatMap((r) => extractRegisteredHooks(r.text, r.pluginRoot))).size;

  if (missing.length) {
    console.error(`check-gate-tests: ${missing.length} wired gate/hook missing a CI-visible decision-logic test:`);
    for (const m of missing) console.error(`  [${m.kind}] ${m.path} -> expected ${m.expected} (${m.reason})`);
    console.error("No gate ships without a decision-logic test (ADR 0047).");
    process.exit(1);
  }
  console.log(`check-gate-tests: ${wiredCount} wired gate(s), ${hookCount} registered hook(s), all have CI-visible tests.`);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) main(process.argv);
