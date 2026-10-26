/*
 * consumer-layout.test.mjs — smoke test for the vendored linter AS A CONSUMER SEES IT (pdca-init's
 * copy set), not as this repo runs it: a consumer's flat `<repo>/scripts/` sits one level deep,
 * not this plugin's `pdca-workflow/scripts/`, two levels deep. This test copies EXACTLY the files
 * pdca-init's SKILL.md vendors into a temp dir shaped like a consumer repo, then runs
 * `adr-lint.mjs` there via `node`, the same way the SKILL.md tells the user to — pinning the
 * contract so it can't silently break. The vendor set is DERIVED from pdca-init SKILL.md step 3,
 * which owns what is vendored; a vendored `*.test.mjs` must pass where it lands.
 * Runs with the other gate tests: `node --test pdca-workflow/scripts/*.test.mjs` (gates.yml).
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, mkdirSync, copyFileSync, writeFileSync, rmSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";

const SCRIPTS_DIR = fileURLToPath(new URL(".", import.meta.url));
const PDCA_INIT_SKILL = fileURLToPath(new URL("../skills/pdca-init/SKILL.md", import.meta.url));

// The vendor set = every backticked `*.mjs` named in pdca-init SKILL.md step 3 (its one home).
export function vendorFilesFromSkill(skillText) {
  const step3 = skillText.match(/^3\. [\s\S]*?(?=^4\. )/m);
  if (!step3) throw new Error("pdca-init SKILL.md: step 3 not found");
  const names = [...step3[0].matchAll(/`(?:\$\{CLAUDE_PLUGIN_ROOT\}\/scripts\/)?([\w.-]+\.mjs)`/g)]
    .map(m => m[1]);
  return [...new Set(names)];
}

const VENDOR_FILES = vendorFilesFromSkill(readFileSync(PDCA_INIT_SKILL, "utf8"));

// Run `node --test <file>` in `cwd` from inside this test runner. NODE_TEST_CONTEXT is stripped:
// inherited from the outer runner, it turns the nested run into a reporting child that exits 0
// even when its tests fail.
export function runNodeTest(cwd, file) {
  const { NODE_TEST_CONTEXT, ...env } = process.env;
  return spawnSync(process.execPath, ["--test", file], { cwd, encoding: "utf8", env });
}

test("runNodeTest reports a failing test as a failure from inside this runner", () => {
  const dir = mkdtempSync(join(tmpdir(), "pdca-nested-test-"));
  try {
    writeFileSync(join(dir, "fail.test.mjs"),
      'import { test } from "node:test"; import assert from "node:assert"; test("f", () => assert.fail());\n');
    writeFileSync(join(dir, "pass.test.mjs"), 'import { test } from "node:test"; test("p", () => {});\n');
    assert.notEqual(runNodeTest(dir, "fail.test.mjs").status, 0);
    assert.equal(runNodeTest(dir, "pass.test.mjs").status, 0);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("vendor set derives from SKILL.md step 3 and holds the linter + its import", () => {
  assert.ok(VENDOR_FILES.includes("adr-lint.mjs"), `derived: ${VENDOR_FILES}`);
  assert.ok(VENDOR_FILES.includes("char-budget.mjs"), `derived: ${VENDOR_FILES}`);
});

test("vendorFilesFromSkill reads only step 3, with or without the plugin-root prefix", () => {
  const skill = [
    "2. Other step names `elsewhere.mjs`.",
    "3. Copy `${CLAUDE_PLUGIN_ROOT}/scripts/a.mjs` and `b.mjs`; not `notes.md`.",
    "4. Later step names `later.mjs`.",
  ].join("\n");
  assert.deepEqual(vendorFilesFromSkill(skill), ["a.mjs", "b.mjs"]);
});

test("adr-lint runs cleanly from a consumer-shaped layout (pdca-init's vendor set, one level deep)", () => {
  const consumerRoot = mkdtempSync(join(tmpdir(), "pdca-consumer-layout-"));
  try {
    const scriptsDir = join(consumerRoot, "scripts");
    const decisionsDir = join(consumerRoot, "docs", "decisions");
    mkdirSync(scriptsDir, { recursive: true });
    mkdirSync(decisionsDir, { recursive: true });

    for (const f of VENDOR_FILES) copyFileSync(join(SCRIPTS_DIR, f), join(scriptsDir, f));

    // A minimal CLAUDE.md, as pdca-init step 2 scaffolds — well under the char budget.
    writeFileSync(join(consumerRoot, "CLAUDE.md"), "# Consumer\n\nMinimal.\n");

    // One valid ADR, matching adr-template.md's frontmatter schema.
    writeFileSync(join(decisionsDir, "0001-first-decision.md"), [
      "---",
      "id: 0001",
      'title: "First decision"',
      "status: accepted",
      'summary: "A consumer-layout smoke-test ADR."',
      "---",
      "",
      "# 0001 -- First decision",
      "",
      "- [checkable] it works -- owner, verified",
      "",
    ].join("\n"));

    const result = spawnSync(process.execPath, ["scripts/adr-lint.mjs", "docs/decisions"], {
      cwd: consumerRoot,
      encoding: "utf8",
    });

    assert.equal(result.status, 0,
      `adr-lint exited ${result.status} in a consumer layout\nstdout: ${result.stdout}\nstderr: ${result.stderr}`);
    assert.equal(result.stderr, "");
    assert.match(result.stdout, /corpus OK/);

    for (const t of VENDOR_FILES.filter(f => f.endsWith(".test.mjs"))) {
      const run = runNodeTest(consumerRoot, join("scripts", t));
      assert.equal(run.status, 0, `vendored ${t} fails in a consumer layout\n${run.stdout}${run.stderr}`);
    }
  } finally {
    rmSync(consumerRoot, { recursive: true, force: true });
  }
});
