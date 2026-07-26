/*
 * check-gate-tests.test.mjs — proves check-gate-tests's decision logic (ADR 0047 wave-1).
 * Run: node --test scripts/*.test.mjs from the repo root.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  extractWiredGates,
  extractTestGlobs,
  extractShInvocations,
  globCoversPath,
  extractRegisteredHooks,
  extractRegisteredHooksDetailed,
  extractPyGates,
  extractPyTestExecutions,
  selfSkipLines,
  findMissingTests,
  parseLivenessDeclaration,
  parseCanaries,
  matcherMatchesTool,
  findCanaryRegistrationFindings,
  evaluateCanaryRun,
  extractGuardedGates,
  guardedGateGaps,
} from "./check-gate-tests.mjs";

// hooks.json fixture registering one hook, plugin style.
const hookReg = (name) => ({
  text: JSON.stringify({
    hooks: { PreToolUse: [{ matcher: "Bash", hooks: [{ type: "command", command: `\${CLAUDE_PLUGIN_ROOT}/hooks/${name}.sh` }] }] },
  }),
  pluginRoot: "pdca-workflow",
});

const GATES_YML = [
  "jobs:",
  "  gates:",
  "    steps:",
  "      - run: node --test pdca-workflow/scripts/*.test.mjs scripts/*.test.mjs",
  "      - run: node pdca-workflow/scripts/adr-lint.mjs docs/decisions",
  "      - run: node scripts/check-restatement.mjs",
  "      - run: node scripts/set-version.mjs --dry-run", // NOT wired as a gate step in real gates.yml,
  // kept here only to prove the parser also handles a bare `node x.mjs` line if one existed —
  // this fixture treats it as wired to exercise the "unwired script ignored" case separately below.
].join("\n");

test("extractWiredGates finds every `node <path>.mjs` run line, excluding `node --test` lines", () => {
  const gates = extractWiredGates(GATES_YML);
  assert.deepEqual(gates, [
    "pdca-workflow/scripts/adr-lint.mjs",
    "scripts/check-restatement.mjs",
    "scripts/set-version.mjs",
  ]);
});

test("extractTestGlobs pulls the glob arguments off a `node --test` line", () => {
  assert.deepEqual(extractTestGlobs(GATES_YML), [
    "pdca-workflow/scripts/*.test.mjs",
    "scripts/*.test.mjs",
  ]);
});

test("globCoversPath matches a single-segment wildcard and rejects a different dir/extension", () => {
  assert.ok(globCoversPath("scripts/*.test.mjs", "scripts/check-restatement.test.mjs"));
  assert.ok(!globCoversPath("scripts/*.test.mjs", "scripts/sub/check-restatement.test.mjs"));
  assert.ok(!globCoversPath("scripts/*.test.mjs", "scripts/check-restatement.mjs"));
});

test("gate with a sibling test covered by the node --test glob passes (no finding)", () => {
  const existingFiles = new Set(["scripts/check-restatement.test.mjs"]);
  const gatesYml = [
    "run: node --test scripts/*.test.mjs",
    "run: node scripts/check-restatement.mjs",
  ].join("\n");
  assert.deepEqual(findMissingTests({ gatesYml, hookRegistrations: [], existingFiles }), []);
});

test("gate with no sibling test fails", () => {
  const existingFiles = new Set(); // no *.test.mjs at all
  const gatesYml = [
    "run: node --test scripts/*.test.mjs",
    "run: node scripts/check-restatement.mjs",
  ].join("\n");
  const missing = findMissingTests({ gatesYml, hookRegistrations: [], existingFiles });
  assert.equal(missing.length, 1);
  assert.equal(missing[0].kind, "gate");
  assert.equal(missing[0].path, "scripts/check-restatement.mjs");
  assert.match(missing[0].reason, /no sibling test file/);
});

test("gate whose test file exists but isn't covered by any node --test glob fails", () => {
  // test file lives under a directory the `node --test` step never globs.
  const existingFiles = new Set(["archive/check-restatement.test.mjs"]);
  const gatesYml = [
    "run: node --test scripts/*.test.mjs",
    "run: node archive/check-restatement.mjs",
  ].join("\n");
  const missing = findMissingTests({ gatesYml, hookRegistrations: [], existingFiles });
  assert.equal(missing.length, 1);
  assert.match(missing[0].reason, /not covered by any `node --test` glob/);
});

test("a script never wired into gates.yml (e.g. a manual bump tool) is ignored even with no test", () => {
  const existingFiles = new Set(); // set-version.test.mjs deliberately absent
  const gatesYml = "run: node --test scripts/*.test.mjs\n"; // set-version.mjs never appears in a run: line
  assert.deepEqual(findMissingTests({ gatesYml, hookRegistrations: [], existingFiles }), []);
});

test("extractRegisteredHooks resolves ${CLAUDE_PLUGIN_ROOT} and collects command .sh paths", () => {
  const hooksJson = JSON.stringify({
    hooks: {
      PreToolUse: [{ matcher: "Agent", hooks: [{ type: "command", command: "${CLAUDE_PLUGIN_ROOT}/hooks/explicit-model-guard.sh" }] }],
      PostToolUse: [{ matcher: "Bash", hooks: [{ type: "command", command: "${CLAUDE_PLUGIN_ROOT}/hooks/retrospect-reminder.sh" }] }],
    },
  });
  assert.deepEqual(extractRegisteredHooks(hooksJson, "pdca-workflow"), [
    "pdca-workflow/hooks/explicit-model-guard.sh",
    "pdca-workflow/hooks/retrospect-reminder.sh",
  ]);
});

test("extractRegisteredHooks returns [] for malformed JSON or a hookless settings file", () => {
  assert.deepEqual(extractRegisteredHooks("not json", "pdca-workflow"), []);
  assert.deepEqual(extractRegisteredHooks(JSON.stringify({ outputStyle: "x" }), "."), []);
});

test("hook registered without a CI-visible test fails", () => {
  const hooksJson = JSON.stringify({
    hooks: { PreToolUse: [{ matcher: "Agent", hooks: [{ type: "command", command: "${CLAUDE_PLUGIN_ROOT}/hooks/explicit-model-guard.sh" }] }] },
  });
  const gatesYml = "run: node --test pdca-workflow/scripts/*.test.mjs\n";
  const existingFiles = new Set(); // no explicit-model-guard.test.mjs anywhere
  const missing = findMissingTests({
    gatesYml,
    hookRegistrations: [{ text: hooksJson, pluginRoot: "pdca-workflow" }],
    existingFiles,
  });
  assert.equal(missing.length, 1);
  assert.equal(missing[0].kind, "hook");
  assert.equal(missing[0].path, "pdca-workflow/hooks/explicit-model-guard.sh");
});

test("grandfathered hook with a CI-visible <basename>.test.mjs in the sibling scripts/ dir passes", () => {
  const hooksJson = JSON.stringify({
    hooks: { PreToolUse: [{ matcher: "Agent", hooks: [{ type: "command", command: "${CLAUDE_PLUGIN_ROOT}/hooks/explicit-model-guard.sh" }] }] },
  });
  const gatesYml = "run: node --test pdca-workflow/scripts/*.test.mjs\n";
  const existingFiles = new Set(["pdca-workflow/scripts/explicit-model-guard.test.mjs"]);
  const missing = findMissingTests({
    gatesYml,
    hookRegistrations: [{ text: hooksJson, pluginRoot: "pdca-workflow" }],
    existingFiles,
  });
  assert.deepEqual(missing, []);
});

test("hook with a test file sitting next to it (not globbed) still fails — must be CI-visible", () => {
  const hooksJson = JSON.stringify({
    hooks: { PreToolUse: [{ matcher: "Agent", hooks: [{ type: "command", command: "${CLAUDE_PLUGIN_ROOT}/hooks/explicit-model-guard.sh" }] }] },
  });
  const gatesYml = "run: node --test pdca-workflow/scripts/*.test.mjs\n"; // does not glob pdca-workflow/hooks/
  const existingFiles = new Set(["pdca-workflow/hooks/explicit-model-guard.test.mjs"]);
  const missing = findMissingTests({
    gatesYml,
    hookRegistrations: [{ text: hooksJson, pluginRoot: "pdca-workflow" }],
    existingFiles,
  });
  assert.equal(missing.length, 1);
  assert.equal(missing[0].kind, "hook");
});

test("extractShInvocations pulls .sh paths and globs off run lines, including a for-loop glob", () => {
  const gatesYml = [
    "      - run: |",
    "          set -e",
    '          for t in pdca-workflow/hooks/test-*.sh; do',
    '            bash "$t"',
    "          done",
    "      - run: bash scripts/one-off-check.sh",
  ].join("\n");
  assert.deepEqual(extractShInvocations(gatesYml), [
    "pdca-workflow/hooks/test-*.sh",
    "scripts/one-off-check.sh",
  ]);
});

test("hook with a gates.yml-invoked test-<basename>.sh sibling passes (hooks-wave convention)", () => {
  const gatesYml = [
    "run: node --test pdca-workflow/scripts/*.test.mjs",
    'run: for t in pdca-workflow/hooks/test-*.sh; do bash "$t"; done',
  ].join("\n");
  const existingFiles = new Set(["pdca-workflow/hooks/test-gate-pipe-guard.sh"]);
  const missing = findMissingTests({
    gatesYml,
    hookRegistrations: [hookReg("gate-pipe-guard")],
    existingFiles,
  });
  assert.deepEqual(missing, []);
});

test("hook whose test-<basename>.sh exists but is invoked by no gates.yml run line fails", () => {
  const gatesYml = "run: node --test pdca-workflow/scripts/*.test.mjs\n"; // no .sh invocation anywhere
  const existingFiles = new Set(["pdca-workflow/hooks/test-gate-pipe-guard.sh"]);
  const missing = findMissingTests({
    gatesYml,
    hookRegistrations: [hookReg("gate-pipe-guard")],
    existingFiles,
  });
  assert.equal(missing.length, 1);
  assert.equal(missing[0].kind, "hook");
  assert.equal(missing[0].path, "pdca-workflow/hooks/gate-pipe-guard.sh");
  assert.match(missing[0].reason, /no gates\.yml run line invokes it/);
});

test("non-grandfathered hook with only a CI-visible <basename>.test.mjs fails (ADR 0064 standard)", () => {
  const gatesYml = [
    "run: node --test pdca-workflow/scripts/*.test.mjs",
    'run: for t in pdca-workflow/hooks/test-*.sh; do bash "$t"; done',
  ].join("\n");
  // the .mjs convention would have satisfied the pre-0064 predicate; the standard rejects it here.
  const existingFiles = new Set(["pdca-workflow/scripts/gate-pipe-guard.test.mjs"]);
  const missing = findMissingTests({
    gatesYml,
    hookRegistrations: [hookReg("gate-pipe-guard")],
    existingFiles,
  });
  assert.equal(missing.length, 1);
  assert.equal(missing[0].expected, "pdca-workflow/hooks/test-gate-pipe-guard.sh");
  assert.match(missing[0].reason, /standardize on a gates\.yml-invoked sibling test-<basename>\.sh \(ADR 0064\)/);
});

test("grandfathered hook may also satisfy the gate with a test-<basename>.sh suite", () => {
  const gatesYml = 'run: for t in pdca-workflow/hooks/test-*.sh; do bash "$t"; done\n';
  const existingFiles = new Set(["pdca-workflow/hooks/test-explicit-model-guard.sh"]);
  const missing = findMissingTests({
    gatesYml,
    hookRegistrations: [hookReg("explicit-model-guard")],
    existingFiles,
  });
  assert.deepEqual(missing, []);
});

// ---- ADR 0069: python gate-has-test + vacuous-test (literal-path self-skip) predicates ----

const PY_GATES_YML = [
  '          for d in dev-skills/skills/*/; do',
  '            python3 dev-skills/skills/building-skills/scripts/validate.py "$d"',
  "          done",
  "      - run: cd dev-skills/skills/building-skills/scripts && python3 validate_test.py",
  "      - run: |",
  "          python3 skill-bench/scripts/lib/check_reachability.py skill-bench/scripts skill-bench/scripts/lib",
  "          for t in skill-bench/scripts/*_test.py skill-bench/scripts/lib/*_test.py; do",
  '            python3 "$t"',
  "          done",
].join("\n");

test("extractPyGates keeps gate invocations, drops test files, globs, and loop variables", () => {
  assert.deepEqual(extractPyGates(PY_GATES_YML), [
    "dev-skills/skills/building-skills/scripts/validate.py",
    "skill-bench/scripts/lib/check_reachability.py",
  ]);
});

test("extractPyTestExecutions collects glob tokens and resolves cd-prefixed direct invocations", () => {
  const { globs, direct } = extractPyTestExecutions(PY_GATES_YML);
  assert.deepEqual(globs, ["skill-bench/scripts/*_test.py", "skill-bench/scripts/lib/*_test.py"]);
  assert.deepEqual(direct, ["dev-skills/skills/building-skills/scripts/validate_test.py"]);
});

test("red-team break 2 closed: a bare basename never certifies a same-named gate in another dir", () => {
  const gatesYml = [
    "run: python3 dirA/validate.py",
    "run: python3 dirB/validate.py",
    "run: cd dirB && python3 validate_test.py",
  ].join("\n");
  const existingFiles = new Set(["dirA/validate_test.py", "dirB/validate_test.py"]);
  const missing = findMissingTests({ gatesYml, hookRegistrations: [], existingFiles });
  assert.equal(missing.length, 1);
  assert.equal(missing[0].path, "dirA/validate.py");
});

test("red-team break 3 closed: flag-prefixed python3 and bare python invocations are captured", () => {
  assert.deepEqual(extractPyGates("run: python3 -B scripts/gate.py\n"), ["scripts/gate.py"]);
  assert.deepEqual(extractPyGates("run: python scripts/gate.py\n"), ["scripts/gate.py"]);
  // -m module gates carry no .py token — uncaptured by design (ADR 0069 revisit trigger)
  assert.deepEqual(extractPyGates("run: python3 -m pkg.gate --check\n"), []);
});

test("python gates with executed siblings pass: glob coverage and cd-then-direct-invocation both count", () => {
  const existingFiles = new Set([
    "dev-skills/skills/building-skills/scripts/validate_test.py",
    "skill-bench/scripts/lib/check_reachability_test.py",
  ]);
  assert.deepEqual(findMissingTests({ gatesYml: PY_GATES_YML, hookRegistrations: [], existingFiles }), []);
});

test("deleting a python gate's sibling test reds the corpus", () => {
  const existingFiles = new Set(["dev-skills/skills/building-skills/scripts/validate_test.py"]);
  const missing = findMissingTests({ gatesYml: PY_GATES_YML, hookRegistrations: [], existingFiles });
  assert.equal(missing.length, 1);
  assert.equal(missing[0].path, "skill-bench/scripts/lib/check_reachability.py");
  assert.match(missing[0].reason, /no sibling _test\.py/);
});

test("a python gate whose sibling exists but is never executed fails", () => {
  const gatesYml = 'run: python3 scripts/some-gate.py\n'; // no glob, no direct invocation
  const existingFiles = new Set(["scripts/some-gate_test.py"]);
  const missing = findMissingTests({ gatesYml, hookRegistrations: [], existingFiles });
  assert.equal(missing.length, 1);
  assert.match(missing[0].reason, /no gates\.yml line executes it/);
});

test("selfSkipLines flags literal absolute path-root assignments, spares derived ones", () => {
  assert.deepEqual(selfSkipLines('REPO="C:/Users/x/proj"\n'), [1]);
  assert.deepEqual(selfSkipLines('REAL_ROOT="/home/user/projects/x"\n'), [1]);
  assert.deepEqual(selfSkipLines('HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'), []);
  assert.deepEqual(selfSkipLines('ROOT="${CLAUDE_PROJECT_DIR}/x"\nHOOK="$HERE/x.sh"\n'), []);
  assert.deepEqual(selfSkipLines('echo "/home/user is not an assignment"\n'), []);
});

test("red-team break 1 closed: declaration keywords, any-case names, comments, and late-var paths", () => {
  assert.deepEqual(selfSkipLines('export REAL_PLUGIN_ROOT="/home/ajmcc/one21tools"\n'), [1]);
  assert.deepEqual(selfSkipLines('readonly REPO="/home/ajmcc/one21tools"\n'), [1]);
  assert.deepEqual(selfSkipLines('local repo="/home/ajmcc/one21tools"\n'), [1]);
  assert.deepEqual(selfSkipLines('declare -r REPO="/home/ajmcc/one21tools"\n'), [1]);
  assert.deepEqual(selfSkipLines('repo="/home/ajmcc/one21tools"\n'), [1]);
  assert.deepEqual(selfSkipLines('REPO="/home/ajmcc/x"   # or $(git rev-parse ...)\n'), [1]);
  assert.deepEqual(selfSkipLines('REPO="/home/ajmcc/${PROJECT}"\n'), [1]);
  // derived ROOT stays spared even with a keyword prefix
  assert.deepEqual(selfSkipLines('export ROOT="$(pwd)/x"\nlocal p="${HOME}/x"\n'), []);
});

test("a hook whose CI-invoked test-<basename>.sh hard-codes an absolute path fails as vacuous", () => {
  const gatesYml = [
    "run: node --test pdca-workflow/scripts/*.test.mjs",
    'run: for t in pdca-workflow/hooks/test-*.sh; do bash "$t"; done',
  ].join("\n");
  const existingFiles = new Set(["pdca-workflow/hooks/test-gate-pipe-guard.sh"]);
  const readFile = (p) =>
    p === "pdca-workflow/hooks/test-gate-pipe-guard.sh"
      ? 'HERE="$(cd x && pwd)"\nREAL_ROOT="C:/Users/ajmcc/projects/one21tools"\n'
      : null;
  const missing = findMissingTests({ gatesYml, hookRegistrations: [hookReg("gate-pipe-guard")], existingFiles, readFile });
  assert.equal(missing.length, 1);
  assert.equal(missing[0].kind, "hook");
  assert.match(missing[0].reason, /self-skips via hard-coded absolute path .*:2, ADR 0069/);
});

test("the same hook passes once the path root is derived (and without readFile the check is skipped)", () => {
  const gatesYml = 'run: for t in pdca-workflow/hooks/test-*.sh; do bash "$t"; done\n';
  const existingFiles = new Set(["pdca-workflow/hooks/test-gate-pipe-guard.sh"]);
  const readFile = () => 'REAL_ROOT="$(cd "$HERE/.." && pwd)"\n';
  assert.deepEqual(
    findMissingTests({ gatesYml, hookRegistrations: [hookReg("gate-pipe-guard")], existingFiles, readFile }),
    []
  );
  assert.deepEqual(
    findMissingTests({ gatesYml, hookRegistrations: [hookReg("gate-pipe-guard")], existingFiles }),
    []
  );
});

// ---- ADR 0086: liveness declarations, canary parsing, registration reachability ------------

test("extractRegisteredHooksDetailed keeps event + matcher; extractRegisteredHooks derives paths from it", () => {
  const text = JSON.stringify({
    hooks: {
      PreToolUse: [
        { matcher: "Agent|Task", hooks: [
          { type: "command", command: "${CLAUDE_PLUGIN_ROOT}/hooks/a.sh" },
          { type: "command", command: "${CLAUDE_PLUGIN_ROOT}/hooks/b.sh" },
        ] },
      ],
      SessionEnd: [
        { hooks: [{ type: "command", command: "${CLAUDE_PROJECT_DIR}/.claude/hooks/end.sh" }] },
      ],
    },
  });
  const detailed = extractRegisteredHooksDetailed(text, "pdca-workflow");
  assert.deepEqual(detailed, [
    { event: "PreToolUse", matcher: "Agent|Task", path: "pdca-workflow/hooks/a.sh" },
    { event: "PreToolUse", matcher: "Agent|Task", path: "pdca-workflow/hooks/b.sh" },
    { event: "SessionEnd", matcher: null, path: ".claude/hooks/end.sh" },
  ]);
  assert.deepEqual(extractRegisteredHooks(text, "pdca-workflow"),
    ["pdca-workflow/hooks/a.sh", "pdca-workflow/hooks/b.sh", ".claude/hooks/end.sh"]);
});

test("parseLivenessDeclaration: both classes parse, unknown word is 'invalid', absence is null", () => {
  assert.equal(parseLivenessDeclaration("#!/bin/bash\n# liveness: boundary-coupled -- note\n"), "boundary-coupled");
  assert.equal(parseLivenessDeclaration("# liveness: per-event-exempt -- deny-only\n"), "per-event-exempt");
  assert.equal(parseLivenessDeclaration("# liveness: sometimes\n"), "invalid");
  assert.equal(parseLivenessDeclaration("# no declaration here\n"), null);
});

test("parseCanaries: well-formed lines parse with line numbers; bad JSON and missing keys are malformed, never dropped", () => {
  const text = [
    "#!/bin/bash",
    '# canary: {"event":"PreToolUse","tool":"Bash","stdin":{"tool_name":"Bash"},"expect":{"deny":true}}',
    '# canary: {not json}',
    '# canary: {"event":"PreToolUse","stdin":{"x":1},"expect":{"frobnicate":true}}',
    '# canary: {"event":"SessionEnd","stdin":{"reason":"clear"},"expect":{"append":"docs/pdca/session-log.txt","match":" session-end clear$"}}',
  ].join("\n");
  const { canaries, malformed } = parseCanaries(text);
  assert.equal(canaries.length, 2);
  assert.equal(canaries[0].line, 2);
  assert.equal(canaries[1].event, "SessionEnd");
  assert.equal(malformed.length, 2);
  assert.deepEqual(malformed.map((m) => m.line), [3, 4]);
});

test("matcherMatchesTool: regex test semantics, empty/null matches all, unparseable matches nothing", () => {
  assert.ok(matcherMatchesTool("Agent|Task", "Agent"));
  assert.ok(matcherMatchesTool("Agent|Task", "Task"));
  assert.ok(!matcherMatchesTool("Skill", "Agent"));
  assert.ok(matcherMatchesTool(null, "Anything"));
  assert.ok(matcherMatchesTool("", "Anything"));
  assert.ok(!matcherMatchesTool("(", "Agent"));
});

const HOOK_TEXT_OK = [
  "# liveness: per-event-exempt -- x",
  '# canary: {"event":"PreToolUse","tool":"Skill","stdin":{"tool_name":"Skill"},"expect":{"deny":true}}',
].join("\n");

test("findCanaryRegistrationFindings: a fully declared, reachable, executable hook yields no findings", () => {
  const registrations = [{ event: "PreToolUse", matcher: "Skill", path: "h/a.sh" }];
  const hookInfo = new Map([["h/a.sh", { exists: true, executable: true, text: HOOK_TEXT_OK }]]);
  assert.deepEqual(findCanaryRegistrationFindings({ registrations, hookInfo }), []);
});

test("findCanaryRegistrationFindings: missing file, non-executable file, and missing liveness each fail", () => {
  const registrations = [
    { event: "PreToolUse", matcher: "Skill", path: "h/gone.sh" },
    { event: "PreToolUse", matcher: "Skill", path: "h/noexec.sh" },
    { event: "PreToolUse", matcher: "Skill", path: "h/undeclared.sh" },
  ];
  const hookInfo = new Map([
    ["h/gone.sh", { exists: false, executable: false, text: null }],
    ["h/noexec.sh", { exists: true, executable: false, text: HOOK_TEXT_OK }],
    ["h/undeclared.sh", { exists: true, executable: true, text: "# nothing declared\n" }],
  ]);
  const f = findCanaryRegistrationFindings({ registrations, hookInfo });
  assert.equal(f.length, 3);
  assert.match(f.find((x) => x.path === "h/gone.sh").reason, /does not exist/);
  assert.match(f.find((x) => x.path === "h/noexec.sh").reason, /not executable/);
  assert.match(f.find((x) => x.path === "h/undeclared.sh").reason, /no liveness classification/);
});

test("findCanaryRegistrationFindings: enforceExecutable=false spares the mode check (win32)", () => {
  const registrations = [{ event: "PreToolUse", matcher: "Skill", path: "h/noexec.sh" }];
  const hookInfo = new Map([["h/noexec.sh", { exists: true, executable: false, text: HOOK_TEXT_OK }]]);
  assert.deepEqual(findCanaryRegistrationFindings({ registrations, hookInfo, enforceExecutable: false }), []);
});

test("findCanaryRegistrationFindings: the spawn-log scar — a declared class whose tool no registered matcher covers fails", () => {
  // Hook declares an Agent-surface canary but is registered on Skill only.
  const text = [
    "# liveness: boundary-coupled -- x",
    '# canary: {"event":"PreToolUse","tool":"Agent","stdin":{"tool_name":"Agent"},"expect":{"append":"docs/pdca/session-log.txt","match":"agent-spawn"}}',
  ].join("\n");
  const registrations = [{ event: "PreToolUse", matcher: "Skill", path: "h/spawn.sh" }];
  const hookInfo = new Map([["h/spawn.sh", { exists: true, executable: true, text }]]);
  const f = findCanaryRegistrationFindings({ registrations, hookInfo });
  assert.equal(f.length, 1);
  assert.match(f[0].reason, /unreachable: no PreToolUse registration whose matcher covers tool Agent/);
});

test("findCanaryRegistrationFindings: a canary event with no registration for that event fails; matcherless events accept any canary tool omission", () => {
  const text = [
    "# liveness: boundary-coupled -- x",
    '# canary: {"event":"SessionEnd","stdin":{"reason":"clear"},"expect":{"append":"l.txt","match":"end"}}',
  ].join("\n");
  const wrongEvent = [{ event: "PreToolUse", matcher: null, path: "h/end.sh" }];
  const hookInfo = new Map([["h/end.sh", { exists: true, executable: true, text }]]);
  const f = findCanaryRegistrationFindings({ registrations: wrongEvent, hookInfo });
  assert.equal(f.length, 1);
  assert.match(f[0].reason, /no SessionEnd registration/);
  const rightEvent = [{ event: "SessionEnd", matcher: null, path: "h/end.sh" }];
  assert.deepEqual(findCanaryRegistrationFindings({ registrations: rightEvent, hookInfo }), []);
});

test("findCanaryRegistrationFindings: malformed canary lines are findings (fail-loud), zero canaries is not", () => {
  const malformedText = "# liveness: per-event-exempt -- x\n# canary: {broken\n";
  const bare = "# liveness: per-event-exempt -- x\n";
  const registrations = [
    { event: "PreToolUse", matcher: "Bash", path: "h/m.sh" },
    { event: "PreToolUse", matcher: "Bash", path: "h/bare.sh" },
  ];
  const hookInfo = new Map([
    ["h/m.sh", { exists: true, executable: true, text: malformedText }],
    ["h/bare.sh", { exists: true, executable: true, text: bare }],
  ]);
  const f = findCanaryRegistrationFindings({ registrations, hookInfo });
  assert.equal(f.length, 1);
  assert.match(f[0].reason, /malformed canary/);
});

test("evaluateCanaryRun: each expect shape passes on its effect and names the miss otherwise", () => {
  assert.equal(evaluateCanaryRun({ deny: true }, { status: 0, stdout: '{"hookSpecificOutput":{"permissionDecision":"deny"}}' }), null);
  assert.match(evaluateCanaryRun({ deny: true }, { status: 0, stdout: "" }), /expected a deny/);
  assert.equal(evaluateCanaryRun({ exit: 2 }, { status: 2, stdout: "" }), null);
  assert.match(evaluateCanaryRun({ exit: 2 }, { status: 0, stdout: "" }), /expected exit 2, got 0/);
  assert.equal(evaluateCanaryRun({ append: "l.txt", match: " session-end clear$" }, { status: 0, stdout: "", appendText: "2026-01-01T00:00:00Z session-end clear\n" }), null);
  assert.match(evaluateCanaryRun({ append: "l.txt", match: "x$" }, { status: 0, stdout: "", appendText: null }), /to exist/);
  assert.match(evaluateCanaryRun({ append: "l.txt", match: "nope" }, { status: 0, stdout: "", appendText: "other\n" }), /does not match/);
  assert.match(evaluateCanaryRun({ frobnicate: true }, { status: 0, stdout: "" }), /unrecognized expect/);
});

// --- gate-pipe guard coverage (the mirror-drift check) ---------------------------------------

const guard = (list) => `#!/usr/bin/env bash\n# header\nGATES="${list}"\nfor gate in $GATES; do :; done\n`;

test("extractGuardedGates reads the GATES line; absent or unquoted yields none", () => {
  assert.deepEqual(extractGuardedGates(guard("a.mjs b.py")), ["a.mjs", "b.py"]);
  assert.deepEqual(extractGuardedGates(guard("")), []);
  assert.deepEqual(extractGuardedGates("#!/usr/bin/env bash\necho no gates here\n"), []);
  // Only a line-initial GATES= assignment counts — a mention inside prose must not parse.
  assert.deepEqual(extractGuardedGates('# see GATES="not-real.mjs" in the header\n'), []);
});

test("guardedGateGaps flags a CI-wired gate no guard covers, across both guards' union", () => {
  const yml = [
    "      - run: node --test scripts/*.test.mjs",
    "      - run: node pdca-workflow/scripts/adr-lint.mjs docs/decisions",
    "      - run: node scripts/check-restatement.mjs",
    "      - run: node scripts/check-relocated-paths.mjs",
    "      - run: python3 skills/building-skills/scripts/validate.py skills/x",
  ].join("\n");
  // Split across two guard files exactly as the repo does (plugin guards its own gate).
  const covered = [guard("adr-lint.mjs"), guard("check-restatement.mjs check-relocated-paths.mjs validate.py")];
  assert.deepEqual(guardedGateGaps(yml, covered), []);

  // Drop the newest gate from the mirror — the real ADR 0089 scar.
  const drifted = [guard("adr-lint.mjs"), guard("check-restatement.mjs validate.py")];
  assert.deepEqual(guardedGateGaps(yml, drifted), ["scripts/check-relocated-paths.mjs"]);
});

test("guardedGateGaps matches on BASENAME, so a moved gate stays covered", () => {
  const yml = "      - run: node tools/nested/check-restatement.mjs";
  assert.deepEqual(guardedGateGaps(yml, [guard("check-restatement.mjs")]), []);
});

test("guardedGateGaps reports every uncovered gate, not just the first", () => {
  const yml = [
    "      - run: node scripts/a-gate.mjs",
    "      - run: python3 scripts/b_gate.py",
  ].join("\n");
  assert.deepEqual(guardedGateGaps(yml, [guard("")]), ["scripts/a-gate.mjs", "scripts/b_gate.py"]);
});

test("guardedGateGaps ignores `node --test` lines (test globs are not gates)", () => {
  const yml = "      - run: node --test scripts/*.test.mjs pdca-workflow/scripts/*.test.mjs";
  assert.deepEqual(guardedGateGaps(yml, [guard("")]), []);
});

// --- ADR 0069 vacuity detection now spans all three gate languages -----------------------------

test("selfSkipLines flags JS and Python machine-bound assignments, not just shell", () => {
  assert.deepEqual(selfSkipLines('const REPO = "/home/ajmcc/one21tools";'), [1]);
  assert.deepEqual(selfSkipLines('REPO = "/Users/ajmcc/one21tools"'), [1]);
  assert.deepEqual(selfSkipLines('let root = "C:/Users/ajmcc/repo"'), [1]);
  assert.deepEqual(selfSkipLines('REPO="/home/ajmcc/one21tools"'), [1]); // shell, unchanged
});

test("selfSkipLines spares derived roots in every language", () => {
  assert.deepEqual(selfSkipLines('const REPO = process.cwd();'), []);
  assert.deepEqual(selfSkipLines('REPO = os.path.dirname(__file__)'), []);
  assert.deepEqual(selfSkipLines('root=$(cd "$(dirname "$0")/../.." && pwd)'), []);
});

test("an .mjs gate whose CI-visible test is machine-bound now FAILS (was unguarded)", () => {
  const gatesYml = ["run: node --test scripts/*.test.mjs", "run: node scripts/a-gate.mjs"].join("\n");
  const existingFiles = new Set(["scripts/a-gate.test.mjs"]);
  const readFile = (p) => (p === "scripts/a-gate.test.mjs" ? 'const REPO = "/home/ajmcc/x";\n' : null);
  const missing = findMissingTests({ gatesYml, hookRegistrations: [], existingFiles, readFile });
  assert.equal(missing.length, 1);
  assert.match(missing[0].reason, /self-skips via hard-coded absolute path/);
});

test("a .py gate whose executed test is machine-bound now FAILS", () => {
  const gatesYml = ["run: python3 x/g.py", "run: python3 x/g_test.py"].join("\n");
  const existingFiles = new Set(["x/g_test.py"]);
  const readFile = (p) => (p === "x/g_test.py" ? 'REPO = "/home/ajmcc/x"\n' : null);
  const missing = findMissingTests({ gatesYml, hookRegistrations: [], existingFiles, readFile });
  assert.equal(missing.length, 1);
  assert.match(missing[0].reason, /ADR 0069/);
});

test("no readFile supplied keeps pre-0069 behaviour (no vacuity claim without the text)", () => {
  const gatesYml = ["run: node --test scripts/*.test.mjs", "run: node scripts/a-gate.mjs"].join("\n");
  const existingFiles = new Set(["scripts/a-gate.test.mjs"]);
  assert.deepEqual(findMissingTests({ gatesYml, hookRegistrations: [], existingFiles }), []);
});
