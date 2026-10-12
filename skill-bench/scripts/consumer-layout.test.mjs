/*
 * consumer-layout.test.mjs — proves skill-bench runs AS AN INSTALLED PLUGIN would (#170 M2/M6):
 * copy scripts/ into a temp dir shaped like the plugin cache, build a synthetic graded benchmark,
 * and run bench_verdict.py from an UNRELATED working directory with NO grok/claude CLI (the offline
 * --cache path). Pins cwd-independence + self-containment (lib imports resolve via the script's own
 * dir, not the caller's) so cross-repo use can't silently break.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, mkdirSync, cpSync, writeFileSync, readFileSync, rmSync } from "node:fs";
import { join, dirname } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";

const SCRIPTS_DIR = fileURLToPath(new URL(".", import.meta.url)); // skill-bench/scripts/

// 6 cells: arms A/B/C across scenarios S1/S2 so clustered stats are finite (>=2 clusters).
const ARM_MAP = [
  ["b1", "A", "S1", "1"], ["b2", "B", "S1", "1"], ["b3", "C", "S1", "1"],
  ["b4", "A", "S2", "1"], ["b5", "B", "S2", "1"], ["b6", "C", "S2", "1"],
];
const NORM = { decision: "d", options: ["o1", "REJECTED: o2 — r"], criterion: "c", risks: [], assumptions: [] };
// cached regraded met: C=1.0, B=0.5, A=0.25 -> C-B = +0.5 (KEEP)
const MET = { b1: [1, 0, 0, 0], b2: [1, 1, 0, 0], b3: [1, 1, 1, 1],
              b4: [1, 0, 0, 0], b5: [1, 1, 0, 0], b6: [1, 1, 1, 1] };

function expsFrom(mets) {
  return mets.map((m, i) => ({ id: i + 1, met: !!m, why: "" }));
}

test("bench_verdict reproduces a verdict from an installed-plugin layout, offline, cwd-independent", () => {
  const root = mkdtempSync(join(tmpdir(), "skillbench-consumer-"));
  const otherCwd = mkdtempSync(join(tmpdir(), "skillbench-cwd-"));
  try {
    // 1. "Install" the plugin scripts (self-contained: bench_*.py + lib/) into the consumer root.
    cpSync(SCRIPTS_DIR, join(root, "scripts"), { recursive: true });

    // 2. Synthetic graded benchmark dir in the ADR 0025/0026 layout.
    const graded = join(root, "bench", "graded");
    mkdirSync(graded, { recursive: true });
    writeFileSync(join(graded, "arm_map.tsv"),
      "bid\tarm\tscenario\trep\n" + ARM_MAP.map((r) => r.join("\t")).join("\n") + "\n");
    writeFileSync(join(graded, "verdicts.jsonl"),
      ARM_MAP.map(([bid, , scn]) =>
        JSON.stringify({ bid, scenario: scn, norm: NORM, expectations: expsFrom(MET[bid]) })).join("\n") + "\n");
    const synthKey = { type: "synthetic", shape: "x", trap: "y", expectations: ["e1", "e2", "e3"] };
    writeFileSync(join(graded, "keys.json"), JSON.stringify({ S1: synthKey, S2: synthKey }));

    // 3. Cache of a prior judge run (per-cell met) -> no live grok/claude needed.
    const cache = join(root, "cache.jsonl");
    writeFileSync(cache,
      ARM_MAP.map(([bid]) => JSON.stringify({ bid, expectations: expsFrom(MET[bid]) })).join("\n") + "\n");

    // 4. Run from an UNRELATED cwd, invoking the script by absolute path (as ${CLAUDE_PLUGIN_ROOT} would).
    const out = join(root, "report.json");
    const r = spawnSync("python3",
      [join(root, "scripts", "bench_verdict.py"), "--dir", join(root, "bench"),
       "--judge", "auto", "--cache", cache, "--out", out],
      { cwd: otherCwd, encoding: "utf8" });
    assert.equal(r.status, 0, `bench_verdict failed: ${r.stderr}`);

    const report = JSON.parse(readFileSync(out, "utf8"));
    assert.equal(report.n_cells, 6);
    assert.equal(report.regraded.arm_means.C, 1.0);
    assert.equal(report.regraded.arm_means.B, 0.5);
    assert.equal(report.regraded.C_minus_B.mean, 0.5);
    assert.equal(report.regraded.C_minus_B.verdict, "KEEP");
  } finally {
    rmSync(root, { recursive: true, force: true });
    rmSync(otherCwd, { recursive: true, force: true });
  }
});
