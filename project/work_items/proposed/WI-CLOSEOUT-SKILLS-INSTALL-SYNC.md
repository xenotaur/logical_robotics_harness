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
  - "/lrh-closeout detects when the PR's merged diff touches .claude/skills/ or src/lrh/skills/, and identifies which skill names, filtered to actual packaged skill directories"
  - A skill named in that touched, filtered set is refreshed even when its previously installed bytes differ from a stale prior package revision, not blocked by the coarse-grained USER_MODIFIED check
  - A skill not in that touched set, but with genuine local modifications, still reports user_modified and is left untouched
  - A skill the merge removed or renamed is reported as an explicit anomaly, not silently left stale or auto-uninstalled
  - The planned refresh is disclosed and approved at the confirm gate before any file under ~/.claude/skills/ is written
  - The outcome is shown in the closeout report
  - New unit tests in tests/skills_installer_test.py cover the targeted refresh, including a diff containing src/lrh/skills/installer.py itself
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
   skills' status computation untouched. **Filter the derived name set
   against the actual packaged skill directories (`_skill_names()`)
   before passing it to this function** — a changed-path prefix match on
   `src/lrh/skills/` also matches non-skill files directly under that
   directory (e.g. `installer.py` itself, a module rather than a skill
   tree); passing such a name to `_copy_skill` raises
   `NotADirectoryError`. Cover it with unit tests in
   `tests/skills_installer_test.py` (a targeted refresh overwrites a named
   skill even when its installed bytes differ from the package; an
   unnamed skill with differing bytes is left alone and still reports
   `USER_MODIFIED`; a diff that includes `src/lrh/skills/installer.py`
   itself does not attempt to treat `installer.py` as a skill name).
2. Extend `.claude/skills/lrh-closeout/SKILL.md` (and its
   `src/lrh/skills/lrh-closeout/SKILL.md` mirror) with a new step, placed
   after the PR's changes are known to be merged, that:
   - Diffs the closed-out PR's changed files against `.claude/skills/` and
     `src/lrh/skills/` path prefixes to derive the set of touched skill
     names, filtered to actual packaged skill directories (item 1).
   - Splits that set into **added/modified** (present in the current
     package) and **removed** (a skill deleted or renamed by the merge,
     so the old name no longer exists in the package and cannot be
     refreshed by copying). For added/modified names, this step performs
     the targeted refresh. For removed names, it does not attempt to
     "refresh" a nonexistent source — it reports the stale
     `~/.claude/skills/<old-name>` as an explicit anomaly needing human
     attention (uninstalling it automatically is out of scope here; see
     Non-Goals) rather than silently leaving it installed with no signal.
   - **Includes this planned mutation, and which skill names it would
     touch, in the closeout confirm gate (mirroring `/lrh-closeout`'s
     existing Step 2 plan / Step 4 confirm-gate structure) before any
     file under `~/.claude/skills/` is written** — this is a
     `~force`-bypassing overwrite of a user-machine directory, not an
     ordinary control-plane commit, so it must be disclosed and approved
     pre-action, not only reported after the fact.
   - If the (approved) added/modified set is non-empty, invokes the
     targeted refresh from item 1 (from a checkout known to be on `main`
     post-merge) for exactly those names, and reports the outcome —
     which skills were refreshed, any removed-skill anomalies, and
     whether any refreshed skill is still not up to date afterward
     (which would indicate a bug in the targeted refresh itself, since a
     name in the approved set should always succeed).
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
- Does not automatically uninstall `~/.claude/skills/<name>` for a skill
  the merge removed or renamed — that old copy has no current package
  source to refresh from, so the step reports it as an anomaly for the
  human to act on rather than deleting a directory unprompted.

## Acceptance Criteria

- `/lrh-closeout` detects when the PR's merged diff touches
  `.claude/skills/` or `src/lrh/skills/`, and identifies which skill
  names — filtered to actual packaged skill directories, so a non-skill
  file directly under `src/lrh/skills/` (e.g. `installer.py`) is never
  treated as a skill name.
- A skill named in that touched, filtered set is refreshed even when its
  previously installed bytes differ from a stale prior package revision —
  not blocked by the coarse-grained `USER_MODIFIED` check.
- A skill *not* in that touched set, but with genuine local modifications,
  still reports `user_modified` and is left untouched.
- A skill the merge removed or renamed is reported as an explicit
  anomaly, not silently left stale with no signal and not auto-uninstalled.
- The planned refresh (which skill names, added/modified vs. removed) is
  disclosed in the closeout plan and explicitly approved at the confirm
  gate *before* any file under `~/.claude/skills/` is written — not only
  reported after the fact.
- The outcome (which skills were refreshed, any anomalies) is shown in the
  closeout report.
- New unit tests in `tests/skills_installer_test.py` cover the targeted
  refresh (named skill with differing bytes is overwritten; unnamed skill
  with differing bytes is left alone; a diff containing
  `src/lrh/skills/installer.py` does not attempt to treat it as a skill).
- SKILL.md (both trees) is updated to document the new step.
- `lrh validate` reports 0 errors; `scripts/test` passes.
- Manual smoke test against a skill-touching PR shows the step firing.

## Validation

- `scripts/test`
- `lrh validate`
- Manual smoke test: run `/lrh-closeout` against a PR that edits an
  existing skill and confirm the new step fires, surfaces the planned
  refresh at the confirm gate, refreshes exactly the touched skills, and
  leaves an unrelated locally-modified skill alone
- Manual smoke test: run against a PR whose diff includes
  `src/lrh/skills/installer.py` and confirm it is not treated as a skill
  name
- `diff -r .claude/skills/lrh-closeout src/lrh/skills/lrh-closeout` (mirror
  parity)

## Risk Notes

- Detecting "the closed-out PR's diff" requires the closeout step to know
  the PR's file list at closeout time — if `/lrh-closeout` is ever run
  detached from the original PR context (e.g. a bare execution-record
  cleanup with no PR reference), the detection has nothing to check
  against; the implementation should degrade to a no-op in that case, not
  fail the whole closeout.
- The targeted refresh mutates the invoking user's `~/.claude/skills/`
  directory, bypassing the ordinary `USER_MODIFIED` check for the named
  skills — if a touched skill also happens to carry genuine local edits
  (a human hand-editing the global copy directly for some reason unrelated
  to this merge), the refresh would irreversibly overwrite them. This is
  why the plan must be disclosed and approved at the confirm gate
  *before* any file is written (Required Changes item 2), not merely
  reported afterward — an after-the-fact report cannot undo a
  destructive overwrite.
- The editable-install package-source resolution (see Problem/Context)
  means running this step from a stale or wrong-branch checkout could
  install the wrong content; the implementation must establish it is
  running against a checkout that matches the merged `main`, not assume
  the invoking directory is correct.
