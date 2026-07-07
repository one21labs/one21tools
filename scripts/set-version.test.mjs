/*
 * set-version.test.mjs — decision-logic test for set-version.mjs's plan() (ADR 0017; "never
 * ship a process-gating script without a test of its decision logic" — this writes the Sacred
 * manifests). Run: node --test scripts/*.test.mjs from the repo root.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { plan } from "./set-version.mjs";

const marketplace = () => ({
  name: "m",
  metadata: { description: "d", version: "0.1.0" },
  plugins: [
    { name: "inline-plugin", version: "0.1.0", source: "./skills" },
    { name: "manifest-plugin", source: "./manifest-plugin" },
    { name: "redundant-plugin", version: "0.1.0", source: "./redundant-plugin" },
  ],
});

test("inline plugin: the marketplace entry is the home", () => {
  const { marketplace: mp, pluginJson } = plan("inline-plugin", "0.2.0", marketplace());
  assert.equal(mp.plugins[0].version, "0.2.0");
  assert.equal(pluginJson, null);
});

test("plugin.json plugin: plugin.json is the home; an omitting entry never gains a version", () => {
  const pj = { name: "manifest-plugin", version: "0.1.0" };
  const { marketplace: mp, pluginJson } = plan("manifest-plugin", "0.2.0", marketplace(), pj);
  assert.equal(pluginJson.version, "0.2.0");
  assert.equal(mp.plugins[1].version, undefined); // derive-don't-mirror (ADR 0011)
});

test("entry that redundantly states a version is synced with plugin.json", () => {
  const pj = { name: "redundant-plugin", version: "0.1.0" };
  const { marketplace: mp, pluginJson } = plan("redundant-plugin", "0.2.0", marketplace(), pj);
  assert.equal(pluginJson.version, "0.2.0");
  assert.equal(mp.plugins[2].version, "0.2.0");
});

test("marketplace target writes metadata.version", () => {
  const { marketplace: mp, pluginJson } = plan("marketplace", "0.3.0", marketplace());
  assert.equal(mp.metadata.version, "0.3.0");
  assert.equal(pluginJson, null);
});

test("bad version throws", () => {
  assert.throws(() => plan("inline-plugin", "1.2", marketplace()), /three dot-separated/);
  assert.throws(() => plan("inline-plugin", "v1.2.3", marketplace()), /three dot-separated/);
});

test("unknown target throws and names the valid targets", () => {
  assert.throws(() => plan("nope", "0.2.0", marketplace()), /inline-plugin.*marketplace/s);
});

test("plan never mutates its inputs", () => {
  const mp = marketplace();
  const pj = { name: "manifest-plugin", version: "0.1.0" };
  plan("manifest-plugin", "9.9.9", mp, pj);
  plan("marketplace", "9.9.9", mp);
  assert.equal(mp.metadata.version, "0.1.0");
  assert.equal(mp.plugins[1].version, undefined);
  assert.equal(pj.version, "0.1.0");
});
