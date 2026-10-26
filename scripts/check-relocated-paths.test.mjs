/*
 * check-relocated-paths.test.mjs — proves check-relocated-paths' decision logic (ADR 0089: the
 * frozen-dir path-preservation gate). The two "flags" fixtures are the ADR's falsifiable
 * criterion: the real strands of commits 851d1cb and 6206630, as literal recreations — a
 * predicate that cannot flag both does not ship. Run: node --test scripts/*.test.mjs.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { extractPathTokens, checkRelocatedPaths, walkFrozenDirs, shippedSkillDirs, movedMarkers, DEPARTED } from "./check-relocated-paths.mjs";
import { readFileSync, mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { execFileSync, spawnSync } from "node:child_process";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const TOP = new Set(["benchmarks", "skills", "skill-measure", "docs", "scripts", "pdca-workflow"]);
const run = (files, existing = [], ever = []) => checkRelocatedPaths({
  candidates: extractPathTokens(files, TOP),
  existingPaths: new Set(existing),
  everExisted: new Set(ever),
});

// Real scar: 851d1cb renamed benchmarks/lib/mechanized_checks.py -> skill-measure/scripts/lib/.
const SCAR_851 = {
  path: "benchmarks/2026-07-10-tiered-execution-fullgrid/README.md",
  text: "`outputs/cells/` via `benchmarks/lib/mechanized_checks.py` (tested: `mechanized_checks_test.py`).",
};
// Real scar: 6206630 renamed this reference -> skill-measure/skills/bench/references/.
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

// ADR 0089 Act: the shipped-skill MOVED-marker exemption. Doc-only paths under a manifest
// skills[] dir may delete behind a structured marker in the citing file; everything else FAILs.
const SHIPPED = new Set(["skills/building-skills"]);
const OLD_MD = "skills/building-skills/references/description-ablation.md";
const NEW_MD = "docs/moved/description-ablation.md";  // in-repo target; departed targets: below
const CITE = { path: "benchmarks/2026-07-09-description-ablation/README.md",
  text: "protocol + validity rules: `" + OLD_MD + "`, ADR 0033;\n\nMOVED: " + OLD_MD + " -> `" + NEW_MD + "`" };
const runX = (files, ever, extra = {}) => checkRelocatedPaths({
  candidates: extractPathTokens(files, TOP), existingPaths: new Set(), everExisted: new Set(ever),
  shippedDirs: SHIPPED, markersByFile: movedMarkers(files),
  resolvableNewPaths: new Set([NEW_MD]), ...extra });

test("exemption: shipped .md with resolving MOVED marker passes", () => {
  assert.equal(runX([CITE], [OLD_MD]).problems.length, 0);
});

test("shipped .md WITHOUT a marker still FAILs", () => {
  const noMarker = { path: CITE.path, text: "cites `" + OLD_MD + "` here" };
  assert.equal(runX([noMarker], [OLD_MD]).problems.length, 1);
});

test("marker whose new path does not resolve still FAILs", () => {
  assert.equal(runX([CITE], [OLD_MD], { resolvableNewPaths: new Set() }).problems.length, 1);
});

test("executables never qualify: .py under a shipped dir FAILs despite a marker", () => {
  const oldPy = "skills/building-skills/scripts/eval_verdict.py";
  const f = { path: CITE.path,
    text: "run `" + oldPy + "`\nMOVED: " + oldPy + " -> `skill-measure/scripts/eval_verdict.py`" };
  assert.equal(runX([f], [oldPy], { resolvableNewPaths: new Set(["skill-measure/scripts/eval_verdict.py"]) }).problems.length, 1);
});

test("a MOVED line with trailing prose is not a marker", () => {
  const f = { path: CITE.path,
    text: "cites `" + OLD_MD + "`\nMOVED: " + OLD_MD + " -> `" + NEW_MD + "` (see notes)" };
  assert.equal(runX([f], [OLD_MD]).problems.length, 1);
});

test("unshipped path is untouched by the exemption machinery", () => {
  const oldDoc = "docs/pdca/gone.md";
  const f = { path: CITE.path, text: "cites `" + oldDoc + "`\nMOVED: " + oldDoc + " -> `" + NEW_MD + "`" };
  assert.equal(runX([f], [oldDoc]).problems.length, 1);
});

// ADR 0102: trees that left the repo. Their cites are external, never stranded — and reported.
const SB = "skill-bench/scripts/lib/verdict.py";
const TOP_D = new Set([...TOP, ...DEPARTED.keys()]);

test("departed: a cite under a departed tree is never a problem, even if it ever existed", () => {
  const f = { path: CITE.path, text: "imports `" + SB + "` and `skill-measure/README.md`" };
  const r = checkRelocatedPaths({ candidates: extractPathTokens([f], TOP_D),
    existingPaths: new Set(), everExisted: new Set([SB, "skill-measure/README.md"]) });
  assert.equal(r.problems.length, 0);
  assert.deepEqual(r.departed.map(c => c.path), [SB, "skill-measure/README.md"]);
});

test("ignored: a cite to a gitignored path is never stranded, and is reported", () => {
  const log = "docs/pdca/session-log.txt";
  const f = { path: CITE.path, text: "session log at `" + log + "`" };
  const r = checkRelocatedPaths({ candidates: extractPathTokens([f], TOP),
    existingPaths: new Set(), everExisted: new Set([log]), ignoredPaths: new Set([log]) });
  assert.equal(r.problems.length, 0);
  assert.deepEqual(r.ignored.map(c => c.path), [log]);
});

// main() reads presence from the git index: an untracked copy on disk is still a strand, and
// a gitignored one is not. A temp repo reproduces the 26-Oct local-pass/CI-fail split.
test("main: an untracked file strands, even one only a personal exclude ignores; a committed-ignore one does not", () => {
  const root = mkdtempSync(join(tmpdir(), "relocated-"));
  const git = (...a) => execFileSync("git", ["-c", "user.email=t@t", "-c", "user.name=t", ...a], { cwd: root });
  mkdirSync(join(root, "benchmarks/2026-01-01-x"), { recursive: true });
  mkdirSync(join(root, ".claude-plugin"));
  mkdirSync(join(root, "docs"));
  writeFileSync(join(root, ".claude-plugin/marketplace.json"), '{"plugins":[]}');
  writeFileSync(join(root, "benchmarks/2026-01-01-x/README.md"), "cites `docs/moved.md`, `docs/log.md` and `docs/mine.md`\n");
  for (const f of ["docs/moved.md", "docs/log.md", "docs/mine.md"]) writeFileSync(join(root, f), "x\n");
  git("init", "-q");
  git("add", ".");
  git("commit", "-qm", "base");
  git("rm", "-q", "--cached", "docs/moved.md", "docs/log.md", "docs/mine.md");
  writeFileSync(join(root, ".git/info/exclude"), "docs/mine.md\n");
  writeFileSync(join(root, ".gitignore"), "docs/log.md\n");
  git("add", ".gitignore");
  git("commit", "-qm", "untrack");
  const r = spawnSync(process.execPath, [fileURLToPath(new URL("./check-relocated-paths.mjs", import.meta.url)), root], { encoding: "utf8" });
  assert.equal(r.status, 1);
  assert.match(r.stderr, /`docs\/moved\.md` is cited/);
  assert.match(r.stderr, /`docs\/mine\.md` is cited/);
  assert.doesNotMatch(r.stderr, /docs\/log\.md/);
});

test("departed: both the old symlink name and the moved dir are declared", () => {
  assert.deepEqual([...DEPARTED.keys()].sort(), ["skill-bench", "skill-measure"]);
});

test("departed: a shipped .md MOVED into a departed tree passes without resolving locally", () => {
  const dep = "skill-measure/skills/bench/references/description-ablation.md";
  const f = { path: CITE.path, text: "rules: `" + OLD_MD + "`;\n\nMOVED: " + OLD_MD + " -> `" + dep + "`" };
  assert.equal(runX([f], [OLD_MD], { resolvableNewPaths: new Set() }).problems.length, 0);
});

test("departed does not widen to executables: a .py MOVED into a departed tree still FAILs", () => {
  const oldPy = "skills/building-skills/scripts/eval_verdict.py";
  const f = { path: CITE.path, text: "run `" + oldPy + "`\nMOVED: " + oldPy + " -> `skill-measure/scripts/eval_verdict.py`" };
  assert.equal(runX([f], [oldPy], { resolvableNewPaths: new Set() }).problems.length, 1);
});

test("shippedSkillDirs derives skills[] entries only, never bare source roots", () => {
  const manifest = { plugins: [
    { name: "dev-skills", source: "./skills", skills: ["./code-standards", "./building-skills"] },
    { name: "skill-measure", source: "./skill-measure" },
  ] };
  assert.deepEqual([...shippedSkillDirs(manifest)].sort(),
    ["skills/building-skills", "skills/code-standards"]);
});

// Pin today's real derivation: a marketplace.json edit that moves the exemption set must
// surface HERE, in a failing test, not only in a silently different gate verdict.
test("real manifest pins the exemption set (ADR 0089 Act: blast radius is reviewable)", () => {
  const real = JSON.parse(readFileSync(".claude-plugin/marketplace.json", "utf8"));
  assert.deepEqual([...shippedSkillDirs(real)].sort(), [
    "skills/building-skills", "skills/code-standards", "skills/control-narratives",
    "skills/engineering-principles", "skills/optimizing-context"]);
});
