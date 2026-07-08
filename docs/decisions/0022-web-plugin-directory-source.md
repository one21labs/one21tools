---
id: 0022
title: "pdca-workflow loads in web sessions via a local directory marketplace source"
status: accepted
summary: "The repo's own plugin was enabled repo-wide via a GITHUB marketplace source (source: github, one21labs/one21tools) since PR #4, but it silently does not load in Claude Code web sessions — /retrospect is Unknown there. Switch the source to a local directory source (path: ./): the repo IS the marketplace, so no network fetch, no auth, and no copy into .claude/ is needed. Rejected: vendoring the plugin into .claude/plugins/ (the CLI stores installs in ~/.claude cache, never the repo; would duplicate the in-repo source); exposing the skills as top-level .claude/skills/ (duplicates the plugin's skills or breaks its distributability). The fix is unverifiable in-session — only a live web session confirms it."
---

# 0022 — web sessions load pdca-workflow from a directory source

- Date: 2026-07-07
- Owner: PM
- Panel: owner-direct (PM chose the directory source over expose-as-skills and accept-the-limitation when offered the trade-offs). Check: local `claude` CLI empirical probes — manifest validation + a full install from a directory source.
- Context: `.claude/settings.json` has enabled `pdca-workflow@one21tools` repo-wide since PR #4, sourced from a `github` marketplace (`one21labs/one21tools`). In a Claude Code web session the plugin is absent — `/retrospect` returns "Unknown command", so CLAUDE.md's "run /retrospect before every PR" forcing function cannot fire in the environment the owner actually uses (issue #34). The github source re-fetches over the network the very repo the session is already sitting in, and needs marketplace-repo auth that web startup evidently does not supply.

## Decision
1. **Directory marketplace source** (`.claude/settings.json`): `extraKnownMarketplaces.one21tools.source` becomes `{"source": "directory", "path": "./"}`. The repo root already holds `.claude-plugin/marketplace.json` (the marketplace) and `pdca-workflow/` (the plugin), so the source resolves from the cloned working tree — no network, no auth, no copy into `.claude/`. `enabledPlugins` is unchanged.
2. **No vendoring.** The plugin is NOT copied into the repo (`.claude/plugins/` or elsewhere): the repo IS the plugin source, so a copy would be a duplicated home (muda). `claude plugin install` stores its cache under `~/.claude` regardless of scope, confirming the repo is not the install target.

## Justification
The one broken thing is the source resolver, and the repo already contains everything the marketplace needs. A directory source is strictly more robust in web than github (removes the network + auth dependency that the github path needs and web startup does not satisfy) with no downside if web turns out not to auto-install at all — both fail equally in that case, so the change cannot regress. Local proof: the directory source installs the full plugin — 6 skills (advise, decide, pdca-init, red-team, retrospect, verify), 5 agents, the PostToolUse hook.

## Assumptions
- [checkable] a directory source over this repo installs the whole plugin — owner: `claude` CLI; result: green (`marketplace add ./` + `plugin install pdca-workflow@one21tools` → 6 skills / 5 agents / 1 hook; `plugin validate .` passes).
- [unverifiable] WEAKEST: web-session startup resolves the RELATIVE `./` directory source against the project root and auto-installs the enabled plugin — headless `claude -p` does not run the settings→install reconciliation, so this cannot be tested in-container. REOPEN-IF a fresh web session's `/retrospect` is still "Unknown command" after this lands → try an absolute/`${CLAUDE_PROJECT_DIR}` path, and if web does not auto-install any plugin from repo settings, fall back to exposing `/retrospect` + `/decide` as top-level `.claude/skills/` or to issue #34's PR-body-visibility line.

## Rejected alternatives
- **Keep the github source** — the status quo that silently no-ops in web; needs network + marketplace-repo auth to fetch a repo the session already has.
- **Vendor the plugin into `.claude/plugins/`** — the CLI never installs into the repo (cache lives in `~/.claude`, even at `--scope project`); a hand-copy would duplicate the in-repo `pdca-workflow/` source and drift from it.
- **Expose the skills as top-level `.claude/skills/`** — auto-loads in web without any plugin machinery, but either duplicates the plugin's skills (SSoT break) or moves them out of the plugin and breaks its `/plugin install` distributability; drops the agents + hook.

## Revisit triggers
- A fresh web session still lacks `/retrospect` after this lands -> the REOPEN-IF above (absolute/variable path, then skills-fallback).
- Claude Code web gains documented first-class repo-plugin auto-load -> reconcile this source form with it.
