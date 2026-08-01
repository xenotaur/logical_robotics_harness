---
resolution: null
blocked_reason: null
blocked: false
id: WI-CLOSEOUT-SKILLS-INSTALL-SYNC
title: Closeout/land never reinstalls a skill-touching PR's global skill copy
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-SKILLS-CLOSEOUT
related_design: []
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - modify_unrelated_skills
  - auto_merge_pr
acceptance:
  - "/lrh-closeout detects when the PR's merged diff touches .claude/skills/ or src/lrh/skills/"
  - On detection, it runs lrh skills install (non-force) or explicitly prompts the human to, with output/reminder shown in the report
  - A skill with genuine local modifications still reports user_modified rather than being silently overwritten
  - SKILL.md is updated to document the new step
  - lrh validate reports 0 errors
  - Manual smoke test against a skill-touching PR shows the step firing
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - .claude/skills/lrh-closeout/SKILL.md (edited — new step)
  - src/lrh/skills/lrh-closeout/SKILL.md (edited — mirror of the above)
---

## Summary

After a PR that edits an existing skill under `.claude/skills/` or
`src/lrh/skills/` merges, nothing in the LRH workflow ever runs
`lrh skills install` to refresh `~/.claude/skills/`. The global copy
silently drifts from the canonical `src/lrh/skills/` source until someone
happens to run the command by hand.

## Problem / Context

Confirmed live during a `/lrh-land` run on PR #452:
`~/.claude/skills/lrh-confirm-fixes/SKILL.md` was missing the entire
round-cap-gate mechanism added by PR #445 (`references/round-cap-gate.md`
citation, the round-cap retrigger gating, the anchored `find` pattern for
prior `_CONFIRM` records) plus the `@copilot` bare-comment coding-agent
fix. A repo-wide diff of all 13 skills under `src/lrh/skills/` against
`~/.claude/skills/` in that session found 6 diverged: `lrh-confirm-fixes`,
`lrh-land`, `lrh-proposal`, `lrh-review-response`, `lrh-work-item`,
`lrh-workstream` — all manually reinstalled as a stopgap by direct file
copy, not through this WI's fix.

Root cause: `.claude/skills/lrh-closeout/SKILL.md`'s 8 execution steps
(Parse input, Assess state, Resolve session transcript, Confirm gate,
Execute confirmed actions, Validate, Session reflection, Report and
commit) never call `lrh skills install`. The only skill that documents
running `lrh skills install` is `lrh-create-skill/SKILL.md` (line 231),
which explicitly scopes itself to newly-created skills only ("Does not
modify existing skills — only creates new ones", line 261). A PR that
*edits* an existing skill has no workflow step anywhere that reinstalls
it globally.

`lrh skills install` (`src/lrh/skills/installer.py`) resolves its
"package" source via `importlib.resources.files("lrh.skills")`, which for
an editable install resolves to whatever branch is currently checked out
in the invoking process's Python environment — so an automated install
step must be careful to run against the checkout it just landed onto
(post-merge, on `main`), not assume any given working directory is on
`main`.

### Duplication search
- In-repo: No existing mechanism auto-runs `lrh skills install` after a
  merge. Related: `src/lrh/skills/installer.py` (the command itself),
  `.claude/skills/lrh-closeout/SKILL.md` (the workflow with the gap).
- Sibling repos: None identified.
- External libraries: N/A — this is an LRH-workflow-internal gap.
- Recommendation: Proceed.

### Demand search
- Work items: `WI-SKILLS-INSTALL-DIFF` (resolved, PR #404) added the
  `--diff` flag to inspect divergence but does not trigger reinstall —
  no overlap. `PROP-LRH-SKILLS-TARGET-AWARE-INSTALL` (PR #449, proposed)
  extends install to additional target directories (`.agents/skills/`
  for Codex) — orthogonal, no overlap.
- Proposals: None found addressing auto-reinstall-on-merge.
- Backlog: No matching entries.
- Recommendation: Proceed.

## Scope

- Add a step to `/lrh-closeout` (the shared terminal phase whether
  invoked standalone or via `/lrh-land`) that detects whether the
  closed-out PR's merged diff touched `.claude/skills/` or
  `src/lrh/skills/`.
- On detection, either run `lrh skills install` (no `--force`, so genuine
  local modifications elsewhere still surface a `user_modified` warning
  instead of being silently overwritten) or explicitly surface a reminder
  to the human, and report the outcome in the closeout report.

## Required Changes

1. Extend `.claude/skills/lrh-closeout/SKILL.md` (and its
   `src/lrh/skills/lrh-closeout/SKILL.md` mirror) with a new step, placed
   after the PR's changes are known to be merged, that:
   - Diffs the closed-out PR's changed files against `.claude/skills/` and
     `src/lrh/skills/` path prefixes.
   - If either prefix was touched, runs `lrh skills install` (non-force)
     from a checkout known to be on `main` post-merge, and reports its
     per-skill status lines in the closeout report.
   - If a skill reports `user_modified`, surfaces that explicitly rather
     than silently skipping it.
2. Update the Quality Checklist and "What This Skill Does Not Do" sections
   of `/lrh-closeout` to reflect the new step's scope and limits.
3. Keep both `.claude/skills/lrh-closeout/` and `src/lrh/skills/lrh-closeout/`
   trees byte-identical per the existing skill-mirror convention.

## Non-Goals

- Does not change `lrh skills install`'s own diffing/force/target-directory
  semantics — that is `WI-SKILLS-INSTALL-DIFF` and
  `PROP-LRH-SKILLS-TARGET-AWARE-INSTALL` territory.
- Does not retroactively fix any other stale global skill install beyond
  what was already manually patched in the session that filed this WI.
- Does not run `lrh skills install --force` automatically — a genuinely
  locally modified skill must still warn, not be silently overwritten.
- Does not add this step to any skill other than `/lrh-closeout`.

## Acceptance Criteria

- `/lrh-closeout` detects when the PR's merged diff touches
  `.claude/skills/` or `src/lrh/skills/`.
- On detection, it runs `lrh skills install` (non-force) or explicitly
  prompts the human to, with the outcome shown in the closeout report.
- A skill with genuine local modifications still reports `user_modified`
  rather than being silently overwritten.
- SKILL.md (both trees) is updated to document the new step.
- `lrh validate` reports 0 errors.
- Manual smoke test against a skill-touching PR shows the step firing.

## Validation

- `lrh validate`
- Manual smoke test: run `/lrh-closeout` against a PR that edits an
  existing skill and confirm the new step fires and reports correctly
- `diff -r .claude/skills/lrh-closeout src/lrh/skills/lrh-closeout` (mirror
  parity)

## Risk Notes

- Detecting "the closed-out PR's diff" requires the closeout step to know
  the PR's file list at closeout time — if `/lrh-closeout` is ever run
  detached from the original PR context (e.g. a bare execution-record
  cleanup with no PR reference), the detection has nothing to check
  against; the implementation should degrade to a no-op in that case, not
  fail the whole closeout.
- Running `lrh skills install` mutates the invoking user's
  `~/.claude/skills/` directory as a side effect of a control-plane
  workflow step — this is a new class of action for `/lrh-closeout` and
  should be called out explicitly in its report so it is never a silent
  side effect.
- The editable-install package-source resolution (see Problem/Context)
  means running this step from a stale or wrong-branch checkout could
  install the wrong content; the implementation must establish it is
  running against a checkout that matches the merged `main`, not assume
  the invoking directory is correct.
