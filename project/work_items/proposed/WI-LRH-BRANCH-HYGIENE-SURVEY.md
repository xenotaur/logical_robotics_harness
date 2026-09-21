---
id: WI-LRH-BRANCH-HYGIENE-SURVEY
title: Add a report-only lrh branch-hygiene survey command
type: deliverable
status: proposed
blocked: false
blocked_reason: null
resolution: null
owner: anthony
related_focus: []
related_roadmap: []
related_workstreams: []
related_design:
  - project/design/backlog.md
depends_on: []
expected_actions: [create_file, edit_file, add_cli_command, run_tests, write_docs, create_pr]
forbidden_actions: [delete_branch, force_push, merge_pr, run_lrh_agentic]
acceptance:
  - The command classifies every local branch into a documented class and never deletes or modifies any branch or ref.
  - Squash-merged branches are detected by comparing the local tip to the merged PR head (git ancestry alone is not used).
  - An optional output mode writes reviewable delete commands to a file; the command itself never runs them.
  - The default branch and any worktree paths are discovered, not hard-coded.
  - Behavior is covered by unittest tests using temporary git repositories and a stubbed gh runner.
required_evidence: [test_output, lrh_validate]
artifacts_expected:
  - src/lrh/ (new branch-survey module and CLI wiring)
  - tests/ (unittest coverage)
  - docs/reference/cli/ (command reference)
---

## Summary

Add a report-only `lrh` command that classifies local git branches (merged or
empty, squash-merged, checked out in a worktree, open PR, unique work, and
review-first for never-pushed branches with no PR) and can optionally write
reviewable delete commands to a file for a human to run. The command itself
never deletes or modifies any branch.

## Problem / Context

Local branches accumulate because this repository does not delete branches on
merge. One session hand-cleaned 76 local branches with two ad hoc scripts.
Squash-merged branches look unmerged to `git branch --merged`, so ancestry alone
gives wrong answers, and hand-written scripts embedded a worktree path and a
hard-coded branch list. Deletion is denied to agents
(`docs/how-to/project-setup/claude-code-permissions.md:79-85`), so the useful,
safe part to automate is the survey and the reviewable command list. The
`/lrh-land` closeout now pushes from a detached `HEAD`
(`docs/how-to/project-setup/claude-code-permissions.md:82-85`), which largely
stops new `tmp-*` branches, so the remaining sources are `gh pr checkout` copies,
auto-created worktree branches, and merged PR branches.

Repository conventions considered: `scripts/prompts/label-prompt:1-39` shows thin
wrappers delegating to `lrh`; `scripts/lint:31` lints only `src/lrh` and `tests`,
so logic under `scripts/` would be unlinted; `tests/scripts_tests/` and
`STYLE.md:22,306` establish `unittest`; `src/lrh/prompt_workflow_slug.py:417-461`
is the precedent for a `gh pr list` runner with a large `--limit`.

**Duplication search:** none found. `WI-SKILLS-LRH-WORK-AUDIT` covers work-item
drift, not branches. `WI-LAND-TMP-BRANCH-CLEANUP-CHECKOUT` (resolved) fixed how
`/lrh-land` creates and deletes temporary branches, not surveying. No existing
`lrh` command inspects local branches.

**Demand search:** `project/design/backlog.md:1684-1702` requests a report-first
stale-candidate triage and says cleanup should split into separate work items
(including branch/PR hygiene), stay gated before mutation, and align with
`WI-SKILLS-LRH-WORK-AUDIT`. This item is that branch-hygiene split.

## Scope

- A survey module under `src/lrh/` that reads local git state and `gh` PR data
  and classifies each local branch.
- CLI wiring and a command reference page. The command group and name are a
  design decision for this item (current groups include `github`, `sessions`,
  and `work-items`; see `src/lrh/cli/main.py:73-353`).
- An optional mode that writes reviewable delete commands to a file.
- Unit tests using temporary git repositories and a stubbed `gh` runner.

## Required Changes

1. Decide and document the command group and name, weighing a new group against
   extending `github` or `sessions`.
2. Implement the survey with these classes: merged or empty (ancestor of the
   default branch), squash-merged (local tip equals the head of a merged PR),
   in a worktree, open PR, unique work, and review-first (never pushed, no PR).
3. Discover the default branch (for example `git symbolic-ref
   refs/remotes/origin/HEAD`) and worktrees (`git worktree list --porcelain`)
   instead of hard-coding either.
4. Add an optional mode that writes `git branch -d` and `git branch -D` commands
   (squash-merged branches need `-D`) to a file, with review-first branches
   emitted commented out. The tool never executes them.
5. Add unittest coverage and a CLI reference page under `docs/reference/cli/`.

## Non-Goals

- Deleting or modifying any branch or ref; deletion stays a human action.
- Remote-branch cleanup in this first slice.
- Changing `/lrh-work-remains`, which stays report-only
  (`project/design/backlog.md:1696-1702`).
- Overlapping `WI-SKILLS-LRH-WORK-AUDIT`, which covers work-item drift.

## Acceptance Criteria

- The command classifies every local branch into a documented class and never
  deletes or modifies any branch or ref.
- Squash-merged branches are detected by comparing the local tip to the merged PR
  head (git ancestry alone is not used).
- An optional output mode writes reviewable delete commands to a file; the command
  itself never runs them.
- The default branch and any worktree paths are discovered, not hard-coded.
- Behavior is covered by unittest tests using temporary git repositories and a
  stubbed gh runner.

## Validation

- scripts/test
- scripts/lint
- scripts/format --check --diff
- lrh validate
- Run the new command's --help and a survey against a scratch repository

## Risk Notes

- A wrong classification could suggest deleting live work, so ambiguous or unknown
  cases must default to review-first rather than a delete command.
- `gh pr list` needs a very large `--limit` to avoid silently missing older PRs
  (see `src/lrh/prompt_workflow_slug.py:417-425`).
- Branch and worktree ownership cannot be inferred reliably from git state alone,
  so the report should flag other-session candidates rather than classify them.
