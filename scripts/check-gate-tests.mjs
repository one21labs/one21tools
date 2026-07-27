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
 * mere file existence. The pre-0064 hook tested via a `<basename>.test.mjs` that spawns the
 * real .sh (MJS_GRANDFATHERED_HOOKS) keeps that path, covered by a `node --test` glob; every
 * other hook must carry the .sh suite.
 *
 * Mechanism, reverse walk: the registration walk above only ever asks "does this REGISTERED hook
 * have a test?", so de-registering a hook leaves every gate green — the script, its test suite
 * and its canaries all survive as dead weight with nothing reporting the guard is gone (the
 * symmetric twin of the ADR 0086 scar this file was written to close). Every .sh in HOOK_DIRS
 * that no registration references is therefore a finding: re-register it or delete it.
 *
 * Mechanism, invocation-path canaries (ADR 0086, #276): every registered hook must also (a)
 * exist at its resolved path and be EXECUTABLE — the harness invokes the registered path
 * directly, so a 644 hook dies on Permission denied and fails open silently (the #84/#85 scar,
 * re-instanced by session-end-log.sh) — (b) carry a `# liveness:` classification its header
 * declares (consumed by scripts/scorecard.mjs's liveness readout, ADR 0086 (b)), and (c) pass
 * one behavioral canary per DECLARED input class: `# canary: {json}` lines in the hook header
 * name a synthetic representative (event, tool, stdin, expected effect); this gate asserts the
 * registration reaches the hook for that class (event registered, matcher covers the tool) and
 * EXECUTES the real hook file against the synthetic input in a throwaway fixture, asserting
 * the declared effect (deny / exit code / log append). A hook with zero canary lines
 * is not failed — its undeclared surface stays rung NONE, stated by the scorecard readout,
 * never claimed watched (ADR 0086 (e)). The declaration GRAMMAR's one home is the comment
 * block above parseLivenessDeclaration/parseCanaries below; hook headers cite this file.
 *
 * DESIGN CONSTRAINTS: zero dependencies; findMissingTests() is PURE (no fs — takes gatesYml text,
 * hook-registration texts, and an `existingFiles.has(path)` duck-typed lookup) so the decision
 * logic is unit-testable, matching check-restatement.mjs's detect()/main() split. main() is the
 * thin IO wrapper.
 *
 * Usage: node scripts/check-gate-tests.mjs [root]
 * Exit 1 listing every wired gate/hook missing a CI-visible decision-logic test; exit 0 otherwise.
 */
import { readFileSync, readdirSync, existsSync, statSync, mkdtempSync, mkdirSync, copyFileSync, writeFileSync, rmSync } from "node:fs";
import { join, dirname, resolve } from "node:path";
import { tmpdir } from "node:os";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const GATES_WORKFLOW = ".github/workflows/gates.yml";

/** Hooks predating ADR 0064 whose decision-logic tests stay `<basename>.test.mjs`; every other
 *  registered hook must carry a gates.yml-invoked sibling `test-<basename>.sh` (ADR 0064). */
export const MJS_GRANDFATHERED_HOOKS = new Set([
  "pdca-workflow/hooks/explicit-model-guard.sh",
]);
/** The repo's hook-registration files — ONE home; scripts/scorecard.mjs imports this for its
 *  liveness readout (ADR 0086). */
export const HOOK_REGISTRATIONS = [
  { path: "pdca-workflow/hooks/hooks.json", pluginRoot: "pdca-workflow" },
  { path: ".claude/settings.json", pluginRoot: "." },
  { path: ".claude/settings.local.json", pluginRoot: "." },
];
/** Where hook scripts live — the reverse walk's corpus. Scanning these dirs, rather than the
 *  registered set, is what makes a de-registration visible at all. */
export const HOOK_DIRS = ["pdca-workflow/hooks", ".claude/hooks"];

/** Hook scripts present in HOOK_DIRS that no registration references. `test-<basename>.sh` is a
 *  suite, not a hook. Findings share findMissingTests's row shape. */
export function findOrphanHooks(hookFiles, registeredPaths) {
  const registered = new Set(registeredPaths);
  return hookFiles
    .filter((p) => !p.slice(p.lastIndexOf("/") + 1).startsWith("test-") && !registered.has(p))
    .map((path) => ({
      kind: "hook",
      path,
      expected: `a "hooks" entry in one of: ${HOOK_REGISTRATIONS.map((r) => r.path).join(", ")}`,
      reason: "no registration references this hook — a de-registered guard whose script, tests and canaries all still read green; re-register it or delete it",
    }));
}

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

/** Every `python[3] [flags] <path>.py` gate invocation in a run: line — excluding test files,
 *  globs, and shell-variable args (`python3 "$t"`). A `-m module` gate has no .py token and is
 *  NOT captured (ADR 0069 revisit trigger). Deduped, in first-seen order. */
export function extractPyGates(gatesYml) {
  const out = [];
  for (const line of gatesYml.split("\n")) {
    const m = line.match(/\bpython3?\s+(?:-[^m\s]\S*\s+)*(\S+\.py)\b/);
    if (m && !m[1].endsWith("_test.py") && !m[1].includes("*") && !m[1].includes("$")) out.push(m[1]);
  }
  return [...new Set(out)];
}

/** How CI executes python tests: `*_test.py` glob tokens (for-loop style) plus direct
 *  `python[3] <x>_test.py` invocations. A `cd <dir> && python3 x_test.py` idiom resolves to
 *  `<dir>/x_test.py` — a bare basename never certifies a gate in another directory (red-team
 *  break on ADR 0069: two same-basename gates, one cd-run, must not both pass). */
export function extractPyTestExecutions(gatesYml) {
  const globs = [];
  const direct = [];
  for (const line of gatesYml.split("\n")) {
    for (const m of line.matchAll(/[^\s;'"`]+\*[^\s;'"`]*_test\.py/g)) globs.push(m[0]);
    const d = line.match(/\bpython3?\s+(?:-[^m\s]\S*\s+)*(\S+_test\.py)\b/);
    if (d) {
      const cd = line.match(/\bcd\s+([^\s;&]+)\s*&&/);
      direct.push(cd && !d[1].includes("/") ? `${cd[1].replace(/\/$/, "")}/${d[1]}` : d[1]);
    }
  }
  return { globs: [...new Set(globs)], direct: [...new Set(direct)] };
}

/** Line numbers where a variable assignment's VALUE starts with a literal absolute path root —
 *  the self-skip signature (ADR 0069): such a test SKIPs everywhere but one machine. Matches
 *  any assignment shape (export/readonly/local/declare prefixes, any-case names); a value whose
 *  ROOT is derived (`$(…)`, `${…}`, `$VAR`) is spared, but a literal root is flagged even when a
 *  variable appears later in the path (red-team: `/home/USER/${P}` is still machine-bound). */
export function selfSkipLines(shText) {
  const out = [];
  // Shell, JS and Python assignment shapes: the scar is machine-bound tests, and it is not
  // language-specific (ADR 0069's revisit trigger: "a self-skip lands via a mechanism neither
  // predicate catches"). `const R = "/home/…"` must flag exactly as `R=/home/…` does.
  const assign = /^\s*(?:export\s+|readonly\s+|local\s+(?:-\S+\s+)*|declare\s+(?:-\S+\s+)*|const\s+|let\s+|var\s+)?[A-Za-z_$][A-Za-z0-9_$]*\s*=\s*(.*)$/;
  shText.split("\n").forEach((line, i) => {
    const m = line.match(assign);
    if (!m) return;
    const value = m[1].replace(/^["']/, "");
    if (/^([A-Za-z]:[\\/]|\/(home|Users|mnt|root|opt|srv)\/)/.test(value)) out.push(i + 1);
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

/** Detailed hook registrations — [{event, matcher, path}] for every command hook in a
 *  hooks.json/settings "hooks" block, keeping the EVENT name and matcher regex the harness
 *  dispatches on (matcher null = the event carries no per-tool matcher, e.g. SessionEnd).
 *  Returns [] on absent/malformed input — a missing or hookless registration file is not this
 *  gate's failure mode. */
export function extractRegisteredHooksDetailed(registrationText, pluginRoot) {
  let parsed;
  try {
    parsed = JSON.parse(registrationText);
  } catch {
    return [];
  }
  const out = [];
  const hooks = parsed && typeof parsed === "object" ? parsed.hooks : null;
  if (!hooks || typeof hooks !== "object") return out;
  for (const [event, entries] of Object.entries(hooks)) {
    if (!Array.isArray(entries)) continue;
    for (const entry of entries) {
      for (const h of entry?.hooks ?? []) {
        if (h?.type !== "command" || typeof h.command !== "string") continue;
        const resolved = h.command
          .replaceAll("${CLAUDE_PLUGIN_ROOT}", pluginRoot)
          .replaceAll("${CLAUDE_PROJECT_DIR}", ".");
        const m = resolved.match(/([^\s'"]+\.sh)\b/);
        if (m) out.push({
          event,
          matcher: typeof entry.matcher === "string" ? entry.matcher : null,
          path: m[1].replace(/^\.\//, "").replaceAll("\\", "/"),
        });
      }
    }
  }
  return out;
}

/** Bash hook script paths (posix, repo-root-relative) registered in a hooks.json/settings
 *  "hooks" block's `command` fields — derived from the detailed extraction (one home). */
export function extractRegisteredHooks(registrationText, pluginRoot) {
  return [...new Set(extractRegisteredHooksDetailed(registrationText, pluginRoot).map((r) => r.path))];
}

// ---- ADR 0086: guard-liveness declarations + invocation-path canaries ----------------------
// ONE home of the declaration grammar hook headers carry:
//   `# liveness: boundary-coupled ...` or `# liveness: per-event-exempt ...` — the per-guard
//     classification ADR 0086 (b) requires; consumed by scripts/scorecard.mjs's liveness
//     readout. Mandatory for every wired hook (an unclassified silent guard is unjudgeable).
//   `# canary: {json}` — one line per DECLARED input class. Keys: event (required); tool
//     (matched against the registered matcher; omit for matcherless events); stdin (object
//     piped to the hook); env (extra env vars); copy (repo-relative files copied into the
//     fixture); files ({relpath: content} written into the fixture); git (true = init a repo with
//     one commit, "dirty" = also leave an uncommitted file, for guards whose decision is a fact
//     about the working tree); expect — exactly one of
//     {"deny":true} | {"exit":N} | {"append":"<fixture relpath>","match":"<regex>"}.
//     The substrings "__FIXTURE__" / "__REPO__" in stdin/env/files
//     values resolve at run time to the throwaway fixture dir / the repo root.

export const LIVENESS_CLASSES = ["boundary-coupled", "per-event-exempt"];

/** First `# liveness:` header line's class: a LIVENESS_CLASSES member, "invalid" for an
 *  unrecognized word (fail-loud, never silently unclassified), or null when absent. */
export function parseLivenessDeclaration(shText) {
  const m = (shText ?? "").match(/^#\s*liveness:\s*(\S+)/m);
  if (!m) return null;
  return LIVENESS_CLASSES.includes(m[1]) ? m[1] : "invalid";
}

/** Every `# canary: {json}` line, parsed. A line that fails to parse or lacks
 *  event/stdin/a recognized expect is reported in `malformed` (fail-loud, never skipped). */
export function parseCanaries(shText) {
  const canaries = [];
  const malformed = [];
  (shText ?? "").split("\n").forEach((line, i) => {
    // Any `# canary:` line is either parsed or reported malformed — a typo'd declaration must
    // never silently vanish (that would re-create FM-1 inside its own mitigation).
    const m = line.match(/^#\s*canary:\s*(.*)$/);
    if (!m) return;
    try {
      const decl = JSON.parse(m[1]);
      const known = Object.keys(decl.expect ?? {}).filter((k) => ["deny", "exit", "append"].includes(k));
      if (typeof decl.event !== "string" || typeof decl.stdin !== "object" || decl.stdin === null || known.length !== 1) {
        throw new Error("canary needs event, stdin, and exactly one of expect deny/exit/append");
      }
      canaries.push({ line: i + 1, ...decl });
    } catch (e) {
      malformed.push({ line: i + 1, error: String(e.message ?? e) });
    }
  });
  return { canaries, malformed };
}

/** Harness matcher semantics: the matcher string is a regex TESTED against the tool name;
 *  absent/empty matches every tool; an unparseable matcher matches nothing (fail-loud via the
 *  reachability finding, never a silent pass). */
export function matcherMatchesTool(matcher, tool) {
  if (matcher == null || matcher === "") return true;
  try {
    return new RegExp(matcher).test(tool ?? "");
  } catch {
    return false;
  }
}

/** One home of the canary-reachability predicate: some registration for this hook covers the
 *  canary's event, and its matcher covers the canary's tool (tool omitted = matcherless event).
 *  Shared by the pure findings pass and the runner so the two can never drift. */
export function canaryReachable(registrations, canary) {
  return registrations.some((r) => r.event === canary.event && (canary.tool == null || matcherMatchesTool(r.matcher, canary.tool)));
}

/**
 * Pure registration-surface verdicts (ADR 0086 (c)). registrations: detailed rows (above).
 * hookInfo: Map(path -> {exists, executable, text}). enforceExecutable=false skips the
 * exec-bit check (win32 checkouts carry no mode bits). Findings share findMissingTests's
 * row shape. A hook with zero canary lines is NOT failed here (ADR 0086 (e)).
 */
export function findCanaryRegistrationFindings({ registrations, hookInfo, enforceExecutable = true }) {
  const findings = [];
  const byPath = new Map();
  for (const r of registrations) {
    if (!byPath.has(r.path)) byPath.set(r.path, []);
    byPath.get(r.path).push(r);
  }
  for (const [path, regs] of byPath) {
    const info = hookInfo.get(path) ?? { exists: false, executable: false, text: null };
    if (!info.exists) {
      findings.push({ kind: "hook", path, expected: path, reason: "registered hook file does not exist — unreachable (ADR 0086)" });
      continue;
    }
    if (enforceExecutable && !info.executable) {
      findings.push({ kind: "hook", path, expected: `${path} mode +x`, reason: "registered hook not executable — the harness invokes the path directly, so it dies on Permission denied and fails open silently (ADR 0086; the session-end-log scar)" });
    }
    const cls = parseLivenessDeclaration(info.text);
    if (!LIVENESS_CLASSES.includes(cls)) {
      findings.push({ kind: "hook", path, expected: "# liveness: boundary-coupled|per-event-exempt", reason: cls === "invalid" ? "liveness classification is not a recognized class (ADR 0086 (b))" : "wired hook carries no liveness classification (ADR 0086 (b))" });
    }
    const { canaries, malformed } = parseCanaries(info.text);
    for (const mf of malformed) {
      findings.push({ kind: "hook", path, expected: `${path}:${mf.line}`, reason: `malformed canary declaration: ${mf.error}` });
    }
    for (const c of canaries) {
      if (!canaryReachable(regs, c)) {
        findings.push({ kind: "hook", path, expected: `${path}:${c.line}`, reason: `declared input class unreachable: no ${c.event} registration${c.tool ? ` whose matcher covers tool ${c.tool}` : ""} (ADR 0086; the spawn-log Agent-surface scar)` });
      }
    }
  }
  return findings;
}

/** Pure verdict on one executed canary. run: {status, stdout, appendText} where appendText is
 *  the expect.append target's content (null if absent). Returns null on pass, else the
 *  failure reason. */
export function evaluateCanaryRun(expect, run) {
  if (expect.deny) {
    return /"permissionDecision"\s*:\s*"deny"/.test(run.stdout ?? "") ? null : "expected a deny decision; none was printed";
  }
  if (expect.exit !== undefined) {
    return run.status === expect.exit ? null : `expected exit ${expect.exit}, got ${run.status}`;
  }
  if (expect.append) {
    if (run.appendText == null) return `expected append target ${expect.append} to exist; it does not`;
    try {
      return new RegExp(expect.match ?? "", "m").test(run.appendText) ? null : `append target ${expect.append} does not match /${expect.match}/`;
    } catch {
      return `invalid match regex /${expect.match}/`;
    }
  }
  return "unrecognized expect shape";
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
    } else {
      const known = readFile ? readFile(testPath) : null;   // null = unknown, "" = a real empty file
      const testText = known ?? "";
      const skips = selfSkipLines(testText);
      // A FILE IS NOT A TEST. Existence + glob coverage were the whole check, so
      // `: > scripts/check-newgate.test.mjs` satisfied "never ship a process-gating script without
      // a test of its decision logic" — and `node --test` exits 0 on a file declaring nothing, so
      // the suite agreed. That is the cheapest path for an agent adding a gate under time pressure,
      // and it leaves a gate with no assertions reported as "tests + invocation paths verified".
      // Declaring at least one case is a floor, not a ceiling: it does not prove the case is any
      // good, only that the file is not a placeholder standing in for work not done.
      if (skips.length) missing.push({ kind: "gate", path: gate, expected: testPath, reason: `test self-skips via hard-coded absolute path (${testPath}:${skips[0]}, ADR 0069)` });
      // Only when the text is actually AVAILABLE. With no readFile the caller has told us nothing,
      // and "" is not evidence of an empty file — claiming a finding from absent information is the
      // same fail-closed-on-missing-input defect this file exists to catch elsewhere.
      // `.only`/`.skip`/`.todo`/`.each` are real declarations — requiring the bare identifier to be
      // followed immediately by `(` false-flags a suite written entirely as `test.only(...)` as an
      // empty placeholder. A floor that rejects valid work is worse than no floor: it teaches
      // people the gate is wrong rather than that the file is.
      else if (known !== null && !/^[ \t]*(test|it|describe)(\.\w+)?\s*\(/m.test(testText)) {
        missing.push({ kind: "gate", path: gate, expected: testPath, reason: "test file declares no test()/it()/describe() case — an empty or placeholder file satisfies existence but asserts nothing" });
      }
    }
  }

  const pyExec = extractPyTestExecutions(gatesYml);
  for (const gate of extractPyGates(gatesYml)) {
    const testPath = gate.replace(/\.py$/, "_test.py");
    const executed = pyExec.globs.some((g) => globCoversPath(g, testPath))
      || pyExec.direct.includes(testPath);
    if (!existingFiles.has(testPath)) {
      missing.push({ kind: "gate", path: gate, expected: testPath, reason: "no sibling _test.py" });
    } else if (!executed) {
      missing.push({ kind: "gate", path: gate, expected: testPath, reason: "sibling _test.py exists but no gates.yml line executes it" });
    } else {
      const known = readFile ? readFile(testPath) : null;   // null = unknown, "" = a real empty file
      const testText = known ?? "";
      const skips = selfSkipLines(testText);
      // A FILE IS NOT A TEST. Existence + glob coverage were the whole check, so
      // `: > scripts/check-newgate.test.mjs` satisfied "never ship a process-gating script without
      // a test of its decision logic" — and `node --test` exits 0 on a file declaring nothing, so
      // the suite agreed. That is the cheapest path for an agent adding a gate under time pressure,
      // and it leaves a gate with no assertions reported as "tests + invocation paths verified".
      // Declaring at least one case is a floor, not a ceiling: it does not prove the case is any
      // good, only that the file is not a placeholder standing in for work not done.
      if (skips.length) missing.push({ kind: "gate", path: gate, expected: testPath, reason: `test self-skips via hard-coded absolute path (${testPath}:${skips[0]}, ADR 0069)` });
      // `async def test_` is a real pytest case (pytest-asyncio); the bare `def` form missed it.
      // The trailing underscore is NOT required either: unittest's discovery prefix is `test`, so
      // `def testRefusesBadInput(self)` is a real, running case that this floor called a
      // placeholder. Matching the runner's own rule beats matching the style we happen to write.
      else if (known !== null && !/^[ \t]*(async\s+)?def\s+test/m.test(testText)) {
        missing.push({ kind: "gate", path: gate, expected: testPath, reason: "test file declares no `def test...` case — an empty or placeholder file satisfies existence but asserts nothing" });
      }
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

/** IO half of the canary check: build a throwaway fixture per REACHABLE canary, execute the
 *  real hook file against the declared stdin, and judge via evaluateCanaryRun (the pure half).
 *  Unreachable canaries are skipped here — findCanaryRegistrationFindings already reported
 *  them. */
function runCanaries(root, registrations, hookInfo) {
  const findings = [];
  const repoAbs = resolve(root);
  for (const [path, info] of hookInfo) {
    if (!info.exists) continue;
    const regs = registrations.filter((r) => r.path === path);
    for (const c of parseCanaries(info.text).canaries) {
      if (!canaryReachable(regs, c)) continue;
      const fixture = mkdtempSync(join(tmpdir(), "canary-"));
      try {
        // docs/pdca is the ADR 0071 adoption marker most hooks are gated on.
        mkdirSync(join(fixture, "docs", "pdca"), { recursive: true });
        const sub = (s) => s.replaceAll("__FIXTURE__", fixture).replaceAll("__REPO__", repoAbs);
        for (const rel of c.copy ?? []) {
          mkdirSync(dirname(join(fixture, rel)), { recursive: true });
          copyFileSync(join(root, rel), join(fixture, rel));
        }
        for (const [rel, content] of Object.entries(c.files ?? {})) {
          mkdirSync(dirname(join(fixture, rel)), { recursive: true });
          writeFileSync(join(fixture, rel), sub(content));
        }
        // `git: true` makes the fixture a real repo with one commit; `git: "dirty"` additionally
        // leaves an uncommitted file. Needed because a git-aware guard's decision is a fact about
        // the TREE, not about its stdin — destructive-git-guard denies only when work would be
        // lost, so with no way to build a dirty fixture no canary of it could ever fire, and the
        // hook would have shipped declaring canaries that were structurally dead.
        if (c.git) {
          const g = (...a) => spawnSync("git", ["-C", fixture, ...a], { encoding: "utf8" });
          g("init", "-q", ".");
          g("-c", "user.email=canary@test", "-c", "user.name=canary", "commit", "-q", "--allow-empty", "-m", "base");
          if (c.git === "dirty") writeFileSync(join(fixture, "uncommitted-work.txt"), "work\n");
        }
        const env = { ...process.env, CLAUDE_PROJECT_DIR: fixture };
        for (const [k, v] of Object.entries(c.env ?? {})) env[k] = sub(v);
        const res = spawnSync("bash", [join(root, path)], { input: sub(JSON.stringify(c.stdin)), env, encoding: "utf8", timeout: 60000 });
        let appendText = null;
        if (c.expect.append) {
          try { appendText = readFileSync(join(fixture, c.expect.append), "utf8"); } catch { appendText = null; }
        }
        const err = evaluateCanaryRun(c.expect, { status: res.status, stdout: res.stdout ?? "", appendText });
        if (err) findings.push({ kind: "hook", path, expected: `${path}:${c.line}`, reason: `canary failed — dead on a declared input class (ADR 0086): ${err}` });
      } finally {
        rmSync(fixture, { recursive: true, force: true });
      }
    }
  }
  return findings;
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

  // Derived from the SAME read as findMissingTests's input — one read+parse pass over the
  // registration files (the extract findMissingTests re-runs internally stays behind its pure
  // signature boundary).
  const registrations = hookRegistrations.flatMap(({ text, pluginRoot }) => extractRegisteredHooksDetailed(text, pluginRoot));
  const hookInfo = new Map();
  for (const r of registrations) {
    if (hookInfo.has(r.path)) continue;
    const abs = join(root, r.path);
    let executable = false;
    try { executable = (statSync(abs).mode & 0o111) !== 0; } catch { /* exists=false below */ }
    hookInfo.set(r.path, { exists: existsSync(abs), executable, text: read(r.path) });
  }

  // An absent hook dir is tolerated (a consumer may have no plugin hooks); anything else throws.
  const hookFiles = HOOK_DIRS.flatMap((d) => {
    let names;
    try { names = readdirSync(join(root, d)); }
    catch (err) { if (err.code === "ENOENT") return []; throw err; }
    return names.filter((n) => n.endsWith(".sh")).map((n) => `${d}/${n}`);
  });

  const missing = [
    ...findMissingTests({ gatesYml, hookRegistrations, existingFiles, readFile: read }),
    ...findCanaryRegistrationFindings({ registrations, hookInfo, enforceExecutable: process.platform !== "win32" }),
    ...findOrphanHooks(hookFiles, [...hookInfo.keys()]),
    ...runCanaries(root, registrations, hookInfo),
  ];
  const wiredCount = extractWiredGates(gatesYml).length + extractPyGates(gatesYml).length;
  const hookCount = hookInfo.size;
  const canaryCount = [...hookInfo.values()].reduce((n, i) => n + parseCanaries(i.text).canaries.length, 0);
  const undeclared = [...hookInfo.entries()].filter(([, i]) => i.exists && parseCanaries(i.text).canaries.length === 0).map(([p]) => p);

  if (missing.length) {
    console.error(`check-gate-tests: ${missing.length} wired gate/hook finding(s):`);
    for (const m of missing) console.error(`  [${m.kind}] ${m.path} -> expected ${m.expected} (${m.reason})`);
    console.error("No gate ships without a decision-logic test (ADR 0047); no wired hook without a live invocation path (ADR 0086).");
    process.exit(1);
  }
  // A REGISTERED HOOK MUST DECLARE AT LEAST ONE CANARY. This was info-only, which made DELETING a
  // canary the cheapest way to clear a red one: a failing canary is exit 1, but a hook with zero
  // canaries printed a note and exited 0. The agent that maintains these headers is the agent whose
  // work the canary just blocked, so "remove the line that objected" was one edit away and left the
  // surface unwatched with no failing signal — the ADR 0086 gap the canaries exist to close,
  // reachable by subtraction. Every registered hook declares one today, so this fails nothing that
  // is currently green; it only removes the escape.
  if (undeclared.length) {
    console.error(`check-gate-tests: ${undeclared.length} registered hook(s) declare NO canary class, so nothing observes them fire: ${undeclared.join(", ")}`);
    console.error("Declare at least one `# canary:` line per hook (grammar in this file's header), or unregister the hook. Deleting a canary must never be the way a red one clears.");
    process.exit(1);
  }
  console.log(`check-gate-tests: ${wiredCount} wired gate(s), ${hookCount} registered hook(s), ${canaryCount} canary class(es) — tests + invocation paths verified.`);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) main(process.argv);
