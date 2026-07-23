---
id: 0056
title: "PR sizing: cohesive PRs over one-concern-per-PR"
status: accepted
tier: lite
summary: "Relax CLAUDE.md's 'one concern per PR' to 'size PRs for reviewability': a coherent unit ships in one PR across many files; split only when changes have different revert boundaries or one risks reddening main. Owner-direct — the count-based rule fragmented cohesive work into many small PRs, the proliferation it was meant to avoid. ADR 0048 (version-bump own PR) and 0051 (decision-set per PR) unchanged. Surfaced shipping skill-bench (ADR 0055) as one cohesive multi-commit branch."
---

# 0056 — cohesive PRs over one-concern-per-PR

- Decision: reword CLAUDE.md Shipping to "size PRs for reviewability, not one-concern" — ship a coherent unit together across files; split only to keep a clean revert boundary or main green. Version bumps keep their own PR (ADR 0048); decision-set-per-PR (ADR 0051) still applies.
- Why: owner-direct, larger PRs preferred. A concern-count rule splits cohesive work into many small PRs — proliferation, the opposite of the rule's intent. Reviewability and a clean revert boundary are the real goals, not a count. Surfaced shipping skill-bench (ADR 0055) as one multi-commit branch.
- Enforced: prose in CLAUDE.md (no gate — PR sizing is a judgment a linter can't check).
- Amended (owner, 23-Jul-2026): while a session's PR is open, add to it — a second PR needs a
  reason that outweighs merge-then-rebase churn under strict checks (PRs #278/#279).
