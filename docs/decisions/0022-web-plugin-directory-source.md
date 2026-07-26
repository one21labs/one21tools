---
id: 0022
title: "pdca-workflow loads in web sessions via a local directory marketplace source"
status: accepted
tier: lite
summary: "The repo's own plugin was enabled repo-wide via a GITHUB marketplace source since PR #4, but it silently does not load in Claude Code web sessions — /retrospect is Unknown there. Switch to a local directory source (path: ./): the repo IS the marketplace, so no network fetch, no auth, no copy into .claude/."
---

# 0022 — web sessions load pdca-workflow from a directory source

- Date: 2026-07-07
- Decision: `.claude/settings.json`'s `extraKnownMarketplaces.one21tools.source` becomes `{"source": "directory", "path": "./"}` — the repo root already holds `.claude-plugin/marketplace.json` and `pdca-workflow/`, so the source resolves from the cloned working tree with no network fetch and no auth. `enabledPlugins` is unchanged; the plugin is NOT vendored into the repo (the CLI's install cache lives under `~/.claude` regardless of scope).
- Why: a directory source is strictly more robust in web than github (removes the network + auth dependency web startup evidently doesn't satisfy) with no downside if web doesn't auto-install at all. Proof: the directory source installs the full plugin (6 skills, 5 agents, the PostToolUse hook).
- Rejected: keep the github source — silently no-ops in web. Vendor the plugin into `.claude/plugins/` — never the CLI's install target, would drift. Expose skills as top-level `.claude/skills/` — duplicates the plugin's skills or breaks distributability.
- Reopen-if: a fresh web session still lacks `/retrospect` after this lands -> try an absolute/`${CLAUDE_PROJECT_DIR}` path, then fall back to top-level skills. Claude Code web gains documented repo-plugin auto-load -> reconcile.
- Enforced: `.claude/settings.json` (`extraKnownMarketplaces.one21tools.source`).
