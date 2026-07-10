/*
 * consumer-layout.test.mjs — smoke test for the vendored linter AS A CONSUMER SEES IT (pdca-init's
 * copy set), not as this repo runs it (#84). Root cause of #84: every existing test asserted
 * adr-lint's decision logic, but nothing exercised the surface a consumer actually invokes — a
 * flat `<repo>/scripts/` one level deep (not this plugin's `pdca-workflow/scripts/`, two levels
 * deep), which broke on a missing `char-budget.mjs` import and a hardcoded `../../` root. This
 * test copies EXACTLY the files pdca-init's SKILL.md vendors into a temp dir shaped like a
 * consumer repo, then runs `adr-lint.mjs` there via `node`, the same way the SKILL.md tells the
 * user to — pinning the contract so it can't silently break again.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, mkdirSync, copyFileSync, writeFileSync, rmSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";

const SCRIPTS_DIR = fileURLToPath(new URL(".", import.meta.url));

// The exact vendor set pdca-init's SKILL.md copies into a consumer's scripts/ (SSoT: SKILL.md
// step 3 — keep this list in sync with it).
const VENDOR_FILES = ["adr-lint.mjs", "adr-lint.test.mjs", "char-budget.mjs", "char-budget.test.mjs"];

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
  } finally {
    rmSync(consumerRoot, { recursive: true, force: true });
  }
});
