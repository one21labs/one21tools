/*
 * check-relocated-paths.test.mjs — proves check-relocated-paths' decision logic (ADR 0089: the
 * frozen-dir path-preservation gate). The two "flags" fixtures are the ADR's falsifiable
 * criterion: the real strands of commits 851d1cb and 6206630, as literal recreations — a
 * predicate that cannot flag both does not ship. Run: node --test scripts/*.test.mjs.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readdirSync, readFileSync, existsSync } from "node:fs";
import { extractPathTokens, checkRelocatedPaths, walkFrozenDirs, isShallowClone } from "./check-relocated-paths.mjs";

const TOP = new Set(["benchmarks", "skills", "skill-bench", "docs", "scripts", "pdca-workflow"]);
const run = (files, existing = [], ever = []) => checkRelocatedPaths({
  candidates: extractPathTokens(files, TOP),
  existingPaths: new Set(existing),
  everExisted: new Set(ever),
});

// Real scar: 851d1cb renamed benchmarks/lib/mechanized_checks.py -> skill-bench/scripts/lib/.
const SCAR_851 = {
  path: "benchmarks/2026-07-10-tiered-execution-fullgrid/README.md",
  text: "`outputs/cells/` via `benchmarks/lib/mechanized_checks.py` (tested: `mechanized_checks_test.py`).",
};
// Real scar: 6206630 renamed this reference -> skill-bench/skills/bench/references/.
const SCAR_620 = {
  path: "benchmarks/2026-07-09-description-ablation/README.md",
  text: "protocol + validity rules: `skills/building-skills/references/description-ablation.md`, ADR 0033;",
};

test("flags the 851d1cb instance: ever-existed path absent from worktree", () => {
  const { problems } = run([SCAR_851], [], ["benchmarks/lib/mechanized_checks.py"]);
  assert.equal(problems.length, 1);
  assert.match(problems[0], /README\.md:1: `benchmarks\/lib\/mechanized_checks\.py`/);
});

test("flags the 6206630 instance: .md extension, trailing prose in span's line", () => {
  const { problems } = run([SCAR_620], [], ["skills/building-skills/references/description-ablation.md"]);
  assert.equal(problems.length, 1);
});

test("flags BOTH instances in one run — regression guard on either regex path (.py vs .md)", () => {
  const { problems } = run([SCAR_851, SCAR_620], [],
    ["benchmarks/lib/mechanized_checks.py", "skills/building-skills/references/description-ablation.md"]);
  assert.equal(problems.length, 2);
});

test("clean: cited path exists in the worktree (the post-repair baseline)", () => {
  const { problems } = run([SCAR_851], ["benchmarks/lib/mechanized_checks.py"], []);
  assert.deepEqual(problems, []);
});

test("clean: absent path that NEVER existed (synthetic substrate) — the 0-false-positive claim", () => {
  const files = [{ path: "benchmarks/2026-07-12-pdca-decide-outcome/substrates/task.md",
    text: "edit `docs/guide.md` and run `scripts/gate.py` per the scenario" }];
  const { problems } = run(files, [], []);
  assert.deepEqual(problems, []);
});

test("extracts a path followed by CLI flags, and reports the line number", () => {
  const files = [{ path: "benchmarks/2026-07-08-x/README.md",
    text: "steps:\n\nrun `skills/building-skills/scripts/eval_verdict.py --check-audit-sample` last" }];
  const tokens = extractPathTokens(files, TOP);
  assert.deepEqual(tokens, [{ file: "benchmarks/2026-07-08-x/README.md", line: 3,
    path: "skills/building-skills/scripts/eval_verdict.py" }]);
});

test("extracts the path prefix of a `path.py:symbol` span", () => {
  const tokens = extractPathTokens(
    [{ path: "b/x.md", text: "the shared `benchmarks/lib/verdict.py:verdict_of` rule" }], TOP);
  assert.deepEqual(tokens.map(t => t.path), ["benchmarks/lib/verdict.py"]);
});

test("never extracts relative ../ forms — ADR 0089(d) residue, out of scope by decision", () => {
  const tokens = extractPathTokens(
    [{ path: "b/x.md", text: "then `../lib/mechanized_checks.py` and `../lib/cost_gate.py --cells 72`" }], TOP);
  assert.deepEqual(tokens, []);
});

test("rejects spans with shell/template chars anywhere in the span", () => {
  const tokens = extractPathTokens([{ path: "b/x.md",
    text: "`$FOO/bar.py` `{root}/scripts/a.py` `docs/a.md|docs/b.md` `scripts/*.test.mjs` `docs/<name>.md`" }], TOP);
  assert.deepEqual(tokens, []);
});

test("rejects tokens whose first segment is not a known top-level dir", () => {
  const tokens = extractPathTokens(
    [{ path: "b/x.md", text: "see `outputs/all.tar.gz` and `graded/items/x.json`" }], TOP);
  assert.deepEqual(tokens, []);
});

test("ignores fenced code blocks — the un-backticked/fenced residue is deliberate (ADR 0089(d))", () => {
  const files = [{ path: "benchmarks/2026-07-09-three-skills-remeasure/README.md",
    text: "```bash\n# persist per `benchmarks/lib/mechanized_checks.py` convention\n```\ndone" }];
  assert.deepEqual(extractPathTokens(files, TOP), []);
});

// Walk: scope + the #282/#284 ENOENT-vanish race, deterministic via injected readdir.
const dirent = (name, dir = false) => ({ name, isDirectory: () => dir });
test("walk scopes to dated dirs and gate extensions only", () => {
  const tree = {
    "benchmarks": [dirent("2026-07-10-x", true), dirent("lib", true), dirent("README.md")],
    "benchmarks/2026-07-10-x": [dirent("README.md"), dirent("run.py"), dirent("meta.json"), dirent("outputs", true)],
    "benchmarks/2026-07-10-x/outputs": [dirent("cell.md")],
  };
  const readdir = p => { const k = p.replace(/\\/g, "/").replace(/^\.\//, ""); if (!(k in tree)) { const e = new Error("ENOENT"); e.code = "ENOENT"; throw e; } return tree[k]; };
  assert.deepEqual(walkFrozenDirs(".", readdir).sort(), [
    "benchmarks/2026-07-10-x/README.md", "benchmarks/2026-07-10-x/outputs/cell.md", "benchmarks/2026-07-10-x/run.py"]);
});

test("walk tolerates a subdir vanishing mid-walk, never the benchmarks root", () => {
  const tree = {
    "benchmarks": [dirent("2026-07-10-x", true)],
    "benchmarks/2026-07-10-x": [dirent("gone", true), dirent("README.md")],
  };
  const readdir = p => { const k = p.replace(/\\/g, "/").replace(/^\.\//, ""); if (!(k in tree)) { const e = new Error("ENOENT"); e.code = "ENOENT"; throw e; } return tree[k]; };
  assert.deepEqual(walkFrozenDirs(".", readdir), ["benchmarks/2026-07-10-x/README.md"]);
  assert.throws(() => walkFrozenDirs("elsewhere", readdir), /ENOENT/);
});

test("a shallow clone is detected, so the gate cannot report a pass it could not have earned", () => {
  // Scar: this repo was cloned shallow and the gate printed "none stranded" for a whole session.
  // The header warned about it; warning is not detecting. `git log --all` on a shallow clone
  // returns nothing for EVERY path, so every cited path reads as never-existed and no strand can
  // ever be flagged - a permanent false negative that looks exactly like success.
  assert.equal(isShallowClone(() => "true\n"), true);
  assert.equal(isShallowClone(() => "false\n"), false);
  assert.equal(isShallowClone(() => "  true  "), true);
});

test("a git failure fails CLOSED, because the ever-existed filter cannot run there either", () => {
  // Not a work tree, git absent, permissions - all of them leave the filter unable to distinguish
  // relocated from never-existed. Returning false would hand back the same false green.
  assert.equal(isShallowClone(() => { throw new Error("not a git repository"); }), true);
  assert.equal(isShallowClone(() => { throw new Error("ENOENT git"); }), true);
});

test("only the exact string true counts - a chatty or empty git does not read as full history", () => {
  // Reading anything-not-"false" as full history would re-open the false green from the other side.
  assert.equal(isShallowClone(() => ""), false);
  assert.equal(isShallowClone(() => "false"), false);
});

test("every module a frozen dir imports THROUGH the shim layer has a forwarding shim", () => {
  // ADR 0089's class, in the dependency mechanism rather than a backticked path. benchmarks/lib
  // moved to skill-bench/scripts/lib (ADR 0055) and the shim set covered bench_io, verdict and
  // mechanized_checks - but not hermetic_driver, which frozen scripts import. Three of four
  // resolved, so the layer LOOKED complete. Frozen dirs are never edited (ADR 0041), so the only
  // remedy is that the shim exists.
  //
  // SCOPE IS THE WHOLE DIFFICULTY, and two earlier versions of this test got it wrong by being
  // broader than the invariant. Frozen dirs use TWO idioms and only one goes through the shim:
  //   shim layer:  sys.path.insert(0, str(HERE.parent / "lib"))
  //   direct:      sys.path.insert(0, str(REPO / "skill-bench" / "scripts" / "lib"))
  // A file on the direct path resolves against skill-bench and owes the shim layer nothing, so
  // counting its imports produced seven false positives.
  const SHIM_INSERT = /sys\.path\.insert\([^)]*\blib\b[^)]*\)/g;
  const files = [];
  const walk = (dir) => {
    for (const e of readdirSync(dir, { withFileTypes: true })) {
      const p = `${dir}/${e.name}`;
      if (e.isDirectory()) walk(p);
      else if (e.name.endsWith(".py")) files.push(p);
    }
  };
  for (const e of readdirSync("benchmarks", { withFileTypes: true })) {
    if (e.isDirectory() && /^20\d\d-\d\d-\d\d-/.test(e.name)) walk(`benchmarks/${e.name}`);
  }

  const realLib = new Set(readdirSync("skill-bench/scripts/lib")
    .filter((f) => f.endsWith(".py") && !f.endsWith("_test.py"))
    .map((f) => f.slice(0, -3)));

  const owed = new Set();
  for (const f of files) {
    const text = readFileSync(f, "utf8");
    const inserts = [...text.matchAll(SHIM_INSERT)].map((m) => m[0]);
    // Through the shim only if some insert names `lib` WITHOUT routing to skill-bench's copy.
    // The discriminator is `skill-bench` ALONE. An earlier `/skill-bench|scripts/` looked
    // equivalent but was not: `scripts` is unanchored, so ANY insert whose text happens to contain
    // that substring was classified as direct and the whole file skipped — its imports never
    // entered `owed`, and a missing shim for those modules would have passed silently. Every real
    // direct insert here spells `"skill-bench" / "scripts" / "lib"`, so the second alternative
    // bought nothing and cost soundness.
    if (!inserts.some((i) => !/skill-bench/.test(i))) continue;
    for (const m of text.matchAll(/^\s*(?:from|import)\s+([a-z_][a-z0-9_]*)/gim)) {
      if (realLib.has(m[1])) owed.add(m[1]);
    }
  }

  const missing = [...owed].filter((m) => !existsSync(`benchmarks/lib/${m}.py`)).sort();
  assert.deepEqual(missing, [],
    `frozen dirs route these through benchmarks/lib with no shim: ${missing.join(", ")}`);
  assert.ok(owed.has("hermetic_driver"), "the walk must still see the import this test was written for");
});
