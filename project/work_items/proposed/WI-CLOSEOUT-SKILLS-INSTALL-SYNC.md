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
  - "/lrh-closeout detects when the PR's merged diff touches .claude/skills/ or src/lrh/skills/, and identifies which skill names"
  - A skill named in that touched set is refreshed even when its previously installed bytes differ from a stale prior package revision, not blocked by the coarse-grained USER_MODIFIED check
  - A skill not in that touched set, but with genuine local modifications, still reports user_modified and is left untouched
  - The outcome is shown in the closeout report
  - New unit tests in tests/skills_installer_test.py cover the targeted refresh
  - SKILL.md is updated to document the new step
  - lrh validate reports 0 errors; scripts/test passes
  - Manual smoke test against a skill-touching PR shows the step firing
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/skills/installer.py (edited — targeted, named-subset force-install capability)
  - tests/skills_installer_test.py (edited — targeted refresh coverage)
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
`~/.claude/skills/` in that session found 6 that had diverged: `lrh-confirm-fixes`,
`lrh-land`, `lrh-proposal`, `lrh-review-response`, `lrh-work-item`,
`lrh-workstream` — all manually reinstalled as a stopgap by direct file
copy, not through this WI's fix.

Note: a plain non-force `lrh skills install` run after such a merge would
not have fixed any of these 6 — see Scope below for why.

Root cause: `.claude/skills/lrh-closeout/SKILL.md`'s 8 execution steps
(Parse input, Assess state, Resolve session transcript, Confirm gate,
Execute confirmed actions, Validate, Session reflection, Report and
commit) never call `lrh skills install`. `lrh-create-skill/SKILL.md` is
the only skill whose own execution steps direct the agent to run
`lrh skills install`, and it explicitly scopes that to newly-created
skills only ("Does not modify existing skills — only creates new ones").
`lrh skills install` is also described informationally elsewhere —
`lrh-implement`'s reference doc explains it as a one-time global-install
step (not part of `/lrh-implement`'s own workflow), and
`_shared/lifecycle-chain.md`'s table references it only in
`lrh-create-skill`'s own row. None of these amount to a workflow step
that reinstalls an *existing, edited* skill.

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
  `src/lrh/skills/`, and if so, which skill names.
- On detection, refresh **only those named skills**, overwriting the
  installed copy from the current package regardless of whether its
  installed bytes differ (a targeted, PR-scoped overwrite) — and leave
  every other skill subject to the ordinary non-force check, so a
  genuine local edit in an unrelated skill still surfaces as
  `user_modified` rather than being silently overwritten.

  A **blanket non-force `lrh skills install` cannot do this**:
  `_skill_differs_from_package` (`installer.py`) classifies any installed
  skill whose bytes differ from the current package as `USER_MODIFIED`
  and skips it — including a stale, unmodified copy of the *previous*
  package revision, which is exactly the state every just-changed skill
  is in immediately after this kind of merge. A plain non-force run would
  skip precisely the skills it needs to fix (confirmed retroactively: none
  of the 6 skills found stale this session would have been refreshed by
  it). A blanket `--force` is also wrong, since it would overwrite
  unrelated skills that happen to carry real local edits. The fix must be
  scoped to "skills this specific merge touched," not "all skills" in
  either direction.

## Required Changes

1. Add a way to force-install a *named subset* of skills — `installer.py`
   currently only exposes all-or-nothing `force` across every installed
   skill (`install_skills(force=True)`). Add a targeted variant (e.g. a
   `skill_names` filter parameter, or a small new function built on the
   existing `_copy_skill`) that overwrites only the given skill names
   regardless of their `USER_MODIFIED` classification, leaving all other
   skills' status computation untouched. Cover it with unit tests in
   `tests/skills_installer_test.py` (a targeted refresh overwrites a named
   skill even when its installed bytes differ from the package; an
   unnamed skill with differing bytes is left alone and still reports
   `USER_MODIFIED`).
2. Extend `.claude/skills/lrh-closeout/SKILL.md` (and its
   `src/lrh/skills/lrh-closeout/SKILL.md` mirror) with a new step, placed
   after the PR's changes are known to be merged, that:
   - Diffs the closed-out PR's changed files against `.claude/skills/` and
     `src/lrh/skills/` path prefixes to derive the set of touched skill
     names.
   - If the set is non-empty, invokes the targeted refresh from item 1
     (from a checkout known to be on `main` post-merge) for exactly those
     names, and reports the outcome in the closeout report.
   - Surfaces the outcome explicitly in every case — which skills were
     refreshed, and whether any of them are still not up to date
     afterward (which would indicate a bug in the targeted refresh itself,
     since a name in the touched set should always succeed).
3. Update the Quality Checklist and "What This Skill Does Not Do" sections
   of `/lrh-closeout` to reflect the new step's scope and limits.
4. Keep both `.claude/skills/lrh-closeout/` and `src/lrh/skills/lrh-closeout/`
   trees byte-identical per the existing skill-mirror convention.

## Non-Goals

- Does not change `lrh skills install`'s existing CLI-level
  `--force`/`--diff`/target-directory semantics — that is
  `WI-SKILLS-INSTALL-DIFF` and `PROP-LRH-SKILLS-TARGET-AWARE-INSTALL`
  territory. The targeted-refresh capability added here (Required Changes
  item 1) is a new, narrowly-scoped addition alongside those, not a
  replacement.
- Does not run a **blanket** `--force` across all installed skills — only
  the specific skill names the merged PR's diff identifies are refreshed;
  every other skill still goes through the ordinary non-force check, and a
  genuinely locally modified skill outside that set must still warn, not
  be silently overwritten.
- Does not retroactively fix any other stale global skill install beyond
  what was already manually patched in the session that filed this WI.
- Does not add this step to any skill other than `/lrh-closeout`.

## Acceptance Criteria

- `/lrh-closeout` detects when the PR's merged diff touches
  `.claude/skills/` or `src/lrh/skills/`, and identifies which skill names.
- A skill named in that touched set is refreshed even when its previously
  installed bytes differ from a stale prior package revision — not
  blocked by the coarse-grained `USER_MODIFIED` check.
- A skill *not* in that touched set, but with genuine local modifications,
  still reports `user_modified` and is left untouched.
- The outcome (which skills were refreshed, any anomalies) is shown in the
  closeout report.
- New unit tests in `tests/skills_installer_test.py` cover the targeted
  refresh (named skill with differing bytes is overwritten; unnamed skill
  with differing bytes is left alone).
- SKILL.md (both trees) is updated to document the new step.
- `lrh validate` reports 0 errors; `scripts/test` passes.
- Manual smoke test against a skill-touching PR shows the step firing.

## Validation

- `scripts/test`
- `lrh validate`
- Manual smoke test: run `/lrh-closeout` against a PR that edits an
  existing skill and confirm the new step fires, refreshes exactly the
  touched skills, and leaves an unrelated locally-modified skill alone
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
