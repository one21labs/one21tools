#!/usr/bin/env node
/*
 * set-version.mjs — repo-governance WRITER for registry versions (ADR 0017).
 * One command writes a version to its correct home, so hand-editing the Sacred manifests
 * can't fat-finger the registry or split a version across two homes:
 *   - a plugin WITH its own .claude-plugin/plugin.json (e.g. pdca-workflow): the version's
 *     home is plugin.json (the lower home; the marketplace entry derives it — ADR 0011).
 *     Writes plugin.json; syncs the marketplace entry ONLY if it already states a version
 *     (derive-don't-mirror: an omitting entry never gains one).
 *   - a plugin WITHOUT plugin.json (dev-skills, engineering-skills): the marketplace entry
 *     IS the home; writes it there.
 *   - target `marketplace`: writes metadata.version.
 * WRITER ONLY — the matching drift CHECK lives in adr-lint.mjs (manifestDrift); a checker
 * here would duplicate the gate.
 *
 * DESIGN CONSTRAINTS: zero dependencies, plain .mjs — the repo-governance population runs on
 * node (ADR 0010). plan() is pure (no fs/process) so the decision logic is unit-testable,
 * per "no process-gating script without a test of its decision logic"; main() is the IO.
 *
 * Usage: node scripts/set-version.mjs <plugin-name|marketplace> <x.y.z>
 * TESTING: set-version.test.mjs (node --test scripts/*.test.mjs from the repo root).
 */
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

// Repo root (this file lives at <root>/scripts/).
const ROOT = fileURLToPath(new URL("../", import.meta.url));

const VERSION_RE = /^\d+\.\d+\.\d+$/;

/**
 * Pure decision logic. Returns { marketplace, pluginJson } — deep copies with the version
 * written to its correct home(s); pluginJson is null when the target has no plugin.json.
 * Never mutates its inputs. Throws on a bad version or an unknown target.
 */
export function plan(target, version, marketplace, pluginJson = null) {
  if (!VERSION_RE.test(version))
    throw new Error(`version must be three dot-separated integers, got '${version}'`);
  const mp = structuredClone(marketplace);

  if (target === "marketplace") {
    mp.metadata = { ...mp.metadata, version };
    return { marketplace: mp, pluginJson: null };
  }

  const entry = (mp.plugins ?? []).find((p) => p.name === target);
  if (!entry) {
    const names = (mp.plugins ?? []).map((p) => p.name).join(", ");
    throw new Error(`no plugin '${target}' in the marketplace (have: ${names}, marketplace)`);
  }

  if (pluginJson) {
    const pj = structuredClone(pluginJson);
    pj.version = version;
    // Derive-don't-mirror (ADR 0011): only sync an entry that already states a version.
    if (entry.version !== undefined) entry.version = version;
    return { marketplace: mp, pluginJson: pj };
  }

  entry.version = version; // the entry IS the home
  return { marketplace: mp, pluginJson: null };
}

function main(argv) {
  const [target, version] = argv.slice(2);
  if (!target || !version) {
    console.error("usage: node scripts/set-version.mjs <plugin-name|marketplace> <x.y.z>");
    process.exit(2);
  }

  const mpPath = join(ROOT, ".claude-plugin", "marketplace.json");
  const marketplace = JSON.parse(readFileSync(mpPath, "utf8"));

  let pjPath = null;
  let pluginJson = null;
  const entry = (marketplace.plugins ?? []).find((p) => p.name === target);
  if (entry?.source) {
    const candidate = join(ROOT, entry.source, ".claude-plugin", "plugin.json");
    if (existsSync(candidate)) {
      pjPath = candidate;
      pluginJson = JSON.parse(readFileSync(candidate, "utf8"));
    }
  }

  let result;
  try {
    result = plan(target, version, marketplace, pluginJson);
  } catch (e) {
    console.error(`set-version: ${e.message}`);
    process.exit(1);
  }

  const write = (path, data) => {
    writeFileSync(path, JSON.stringify(data, null, 2) + "\n");
    console.log(`  wrote ${path}`);
  };
  write(mpPath, result.marketplace);
  if (result.pluginJson) write(pjPath, result.pluginJson);
  console.log(`set-version: ${target} -> ${version}`);
}

// Run main() only when invoked directly, so the test can import plan() cleanly.
if (process.argv[1] === fileURLToPath(import.meta.url)) main(process.argv);
