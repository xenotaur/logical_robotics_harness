---
resolution: null
blocked_reason: null
blocked: false
id: WI-VCS-SAFE-OPERATIONS-BACKEND
title: Audit and design a backend-abstracted safe-invocation path for git/GitHub mutation operations
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design: []
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - create_report
  - add_cli_command
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
acceptance:
  - "An audit artifact enumerates git/gh mutation operations (branch/PR create, push, merge, modify) used across LRH skills, each flagged for known or plausible auto-mode-classifier denial risk, evidence-linked to PR #742's gh pr merge --match-head-commit denial"
  - A backend-abstraction design documents an interface separating a stereotyped VCS action (create branch, push, open PR, SHA-locked merge) from the concrete backend executing it, with git/GitHub as the first implementation
  - At least the SHA-locked merge action from /lrh-confirm-fixes and /lrh-land's merge gate is exposed through the new interface for the git/GitHub backend
  - The tool surfaces a classifier/permission denial clearly rather than retrying or silently bypassing it
  - lrh validate and scripts/test pass
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - project/audits/2026-09-28-vcs-mutation-operations-audit.md
  - src/lrh/vcs/backend.py (or equivalent module path, name TBD by implementor)
---

## Summary

Audit which git/GitHub mutation operations LRH skills use to create, push,
modify, and merge PRs, then design a backend-abstracted interface for the
stereotyped, already-gated ones (starting with the SHA-locked merge action)
so they can be invoked through a narrower, more legible surface than a raw
shell command — and so a non-git/non-GitHub backend could implement the
same interface later without a redesign.

## Problem / Context

During `/lrh-land`'s closeout of PR #742, this session's auto-mode
permission classifier denied a fully pre-verified, SHA-locked
`gh pr merge --match-head-commit <sha>` command with no explanation, even
though the project has had many other merges succeed via the identical
command shape. The only recourse was handing the exact command to the
human to run themselves. This is not an isolated case — prior sessions
have hit the same classifier denying `git push --force-with-lease` and
`git reset --hard` regardless of context (see agent memory
`feedback_force_push_blocked_use_merge_instead` and
`gh_pr_merge_classifier_denial_handoff`). These are all stereotyped,
already-gated LRH actions: by the time the command is presented, the
safety argument (SHA lock, prior CI/review checks, live human
authorization) has already been assembled by the calling skill, not
something the classifier needs to re-derive from the raw shell command's
shape.

### Duplication search
- In-repo: No existing implementation found (`src/lrh/` has no VCS/backend abstraction module)
- Sibling repos: None identified
- External libraries: None identified
- Recommendation: Proceed

### Demand search
- Work items: None found
- Proposals: None found
- Backlog: Found: "Safe tooling for the SHA-locked `gh pr merge` action that keeps tripping the auto-mode classifier" (`project/design/backlog.md`, added 2026-09-28) — may be satisfied
- Recommendation: Offer to close/link this backlog entry once this WI is created

## Scope

- Audit which git/gh mutation operations (branch/PR create, push, modify, merge) used by LRH skills are known or plausible auto-mode-classifier denial candidates.
- Design a backend-abstracted interface for these stereotyped VCS actions, with git/GitHub as the first (and, for this work item, only) implementation.
- Implement the SHA-locked merge action through this interface as the first concrete case.

## Required Changes

1. Grep across `src/lrh/skills/` (and the `.claude/`/`.agents/` rendered mirrors as needed) for every `gh`/`git` command that creates, pushes, modifies, or merges a branch or PR — e.g. `gh pr merge`, `gh pr create`, `git push`, `git checkout -b`, `resolveReviewThread` via `gh api graphql` — and record which are known (from session/memory evidence) or plausible denial candidates.
2. Write the audit findings to `project/audits/2026-09-28-vcs-mutation-operations-audit.md`, one row per operation, citing evidence.
3. Design a backend interface (e.g. `src/lrh/vcs/backend.py`, exact module path at implementor's discretion) with a protocol/ABC covering the stereotyped actions named above, and a `GitHubBackend` (or similarly named) implementation using `gh`/`git` under the hood.
4. Implement at least the SHA-locked merge action through this interface, and make it available to `/lrh-confirm-fixes`'s and `/lrh-land`'s existing merge one-liner (wiring those skills to use it is in scope only if it doesn't require redesigning their gate logic — see Non-Goals).
5. Document the new interface and its extension points (how a future backend would implement it) in the relevant `docs/reference/` location.

## Non-Goals

- Does not implement a second (non-git) backend in this work item — only designs the abstraction so one could be added later.
- Does not attempt to influence, detect, or reverse-engineer the auto-mode classifier's internal decision logic — that is outside LRH's control. The goal is a narrower, more legible invocation surface, not a guaranteed bypass.
- Does not change the existing human-authorization merge gate design (`DEC-AGENT-EXECUTED-MERGE-GATE`, `/lrh-land` Step 6, `/lrh-confirm-fixes` Step 8) — this item is about the underlying invocation mechanism those gates call once authorized, not the authorization policy itself.
- Does not attempt to cover every possible classifier-denied operation (e.g. `git reset --hard`, `git clean`) beyond the create/push/modify/merge-PR operations named in scope — other denied operations already have documented safer alternatives and are out of scope unless the audit finds they share the same stereotyped-command shape.

## Acceptance Criteria

- An audit artifact enumerates git/gh mutation operations used across LRH skills, each flagged for known or plausible auto-mode-classifier denial risk, evidence-linked to PR #742's denial.
- A backend-abstraction design documents an interface separating a stereotyped VCS action from the concrete backend executing it, with git/GitHub as the first implementation.
- At least the SHA-locked merge action is exposed through the new interface for the git/GitHub backend.
- The tool surfaces a classifier/permission denial clearly rather than retrying or silently bypassing it.
- `lrh validate` and `scripts/test` pass.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`

## Risk Notes

- The auto-mode classifier's decision logic is opaque and may not respond predictably to a narrower invocation surface — the audit and design should not overpromise that this "fixes" denials, only that it makes the safety argument more legible.
- Designing a backend abstraction before a second real backend exists risks speculative generality — keep the interface minimal and driven by the git/GitHub case, not hypothetical future needs.

## Open Questions

- No existing workstream's scope closely matches this item (`WS-INVOCATION-AND-GATE-RESET` governs gate *policy*, not the underlying VCS invocation mechanism). Leaving `related_workstreams` empty; a future `/lrh-design` pass or the user may want to fold this into a new or existing workstream.
