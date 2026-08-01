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
  - "/lrh-closeout uses a rename-aware diff to derive candidate skill names by path shape, then partitions by _skill_names() membership at both old and current revisions into added/modified vs. removed/renamed vs. not-a-skill, in that order"
  - A skill in the added/modified set is refreshed even when its previously installed bytes differ from a stale prior package revision, not blocked by the coarse-grained USER_MODIFIED check
  - A skill not in that touched set, but with genuine local modifications, still reports user_modified and is left untouched
  - A skill in the removed/renamed set is reported as an explicit anomaly, not silently left stale or auto-uninstalled, including a rename's old name
  - A changed path under an excluded directory like _shared produces no candidate and no anomaly
  - The planned refresh is disclosed and approved at the confirm gate before any file under ~/.claude/skills/ is written
  - The outcome is shown in the closeout report
  - New unit tests cover the targeted refresh, candidate derivation excluding non-skill files like installer.py, both-revisions partitioning (removed vs. excluded-directory), and an actual rename
  - SKILL.md is updated to document the new step
  - This WI's own implementation PR's closeout invokes the targeted refresh capability scoped to lrh-closeout alone, loaded from the merged checkout, not a plain non-force lrh skills install or an unrelated installed distribution
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
   skills' status computation untouched. This function takes names already
   known to exist in the current package — deriving and classifying that
   name set is item 2's job, not this one's; **do not** filter the input
   here by package membership, since a caller needs to be able to detect
   an *absent* name too (item 2's removed-skill case).
   Cover it with unit tests in `tests/skills_installer_test.py` (a
   targeted refresh overwrites a named skill even when its installed
   bytes differ from the package; an unnamed skill with differing bytes
   is left alone and still reports `USER_MODIFIED`).
2. Extend `.claude/skills/lrh-closeout/SKILL.md` (and its
   `src/lrh/skills/lrh-closeout/SKILL.md` mirror) with a new step, placed
   after the PR's changes are known to be merged, that:
   - Diffs the closed-out PR's changed files against `.claude/skills/` and
     `src/lrh/skills/` path prefixes using a **rename-aware** listing
     (e.g. `git diff --name-status -M` or the platform API's
     `previous_filename`/equivalent, not a name-only listing) — a
     name-only diff commonly exposes only a rename's *destination* path,
     which would make a renamed skill look purely "added" and never
     surface its now-orphaned old name in `~/.claude/skills/<old-name>`.
   - Derives **candidate** skill names using a purely *structural*
     filter: the immediate subdirectory component of each changed
     old-or-new path under either prefix. A changed path with no
     subdirectory component (a file directly under the prefix, e.g.
     `src/lrh/skills/installer.py`) yields no candidate at all — this
     distinction is about path shape, not package membership, so it
     excludes `installer.py`-like non-skill files without also excluding
     a genuinely removed or renamed skill directory (whose name, by
     definition, no longer appears in the current package).
   - **Only then**, partitions the candidate names by membership in
     `_skill_names()` **at both the old (pre-merge) and current
     revisions** — not current alone: present in current →
     **added/modified** (refresh via item 1); present in the old
     revision but absent from current → **removed/renamed** (the skill
     existed before, evidenced by the diff, but not now, so there is no
     source to refresh from); absent from **both** revisions → not a
     skill at all, ignored. This last case specifically covers a changed
     path under an excluded directory like `src/lrh/skills/_shared/`
     (`_skill_names()` deliberately excludes underscore-prefixed
     directories) — without the both-revisions check, `_shared` would
     wrongly be classified removed/renamed on every PR that touches it,
     since it was never in `_skill_names()` at either revision. Applying
     the package-membership filter *before* the structural filter, or
     checking only the current revision, would both defeat the
     removed-skill handling below — the structural filter must run
     first, and both-revisions membership second.
   - For removed/renamed names, does not attempt to "refresh" a
     nonexistent source — reports the stale `~/.claude/skills/<old-name>`
     as an explicit anomaly needing human attention (uninstalling it
     automatically is out of scope here; see Non-Goals) rather than
     silently leaving it installed with no signal.
   - **Includes this planned mutation, and which skill names it would
     touch, in the closeout confirm gate (mirroring `/lrh-closeout`'s
     existing Step 2 plan / Step 4 confirm-gate structure) before any
     file under `~/.claude/skills/` is written** — this bypasses the
     default non-force `USER_MODIFIED` safety check for the named subset,
     so it must be disclosed and approved pre-action, not only reported
     after the fact.
   - If the (approved) added/modified set is non-empty, invokes the
     targeted refresh from item 1 (from a checkout known to be on `main`
     post-merge) for exactly those names, and reports the outcome —
     which skills were refreshed, any removed-skill anomalies, and
     whether any refreshed skill is still not up to date afterward
     (which would indicate a bug in the targeted refresh itself, since a
     name in the approved set should always succeed).
   Cover the candidate-derivation/partition logic in
   `tests/skills_installer_test.py` or an adjacent test module: a diff
   containing `src/lrh/skills/installer.py` yields no candidate for it; a
   diff containing a path under a skill directory present in the old
   revision's `_skill_names()` but absent from the current one is
   classified removed, not silently dropped; a diff containing a path
   under `src/lrh/skills/_shared/` yields no candidate and no anomaly
   (absent from `_skill_names()` at both revisions); an actual rename
   (old and new paths both present, per a rename-aware diff) reports the
   old name as removed and the new name as added/modified, not just the
   new name alone.
3. Update the Quality Checklist and "What This Skill Does Not Do" sections
   of `/lrh-closeout` to reflect the new step's scope and limits.
4. Keep both `.claude/skills/lrh-closeout/` and `src/lrh/skills/lrh-closeout/`
   trees byte-identical per the existing skill-mirror convention.
5. **Bootstrap the fix's own rollout.** The globally installed
   `/lrh-closeout` skill that drives a `/lrh-land` or `/lrh-closeout`
   session only picks up this new step once `~/.claude/skills/lrh-closeout`
   itself has been refreshed — but refreshing it is exactly what the new
   step exists to do, so it cannot bootstrap its own first activation.
   When *this work item's own implementation PR* is closed out, that
   closeout must explicitly invoke the **targeted refresh capability from
   item 1, scoped to `lrh-closeout` alone**. It must **not** use a plain,
   non-force `lrh skills install` — the installed `lrh-closeout` copy
   necessarily differs from the just-merged package (that's the premise
   of this bootstrap step), so a non-force run would classify it
   `USER_MODIFIED` and skip it, the exact root-cause bug this WI exists
   to fix. It must also not use a blanket `--force` (Non-Goals).

   **The bootstrap call must load the targeted-refresh function from the
   merged checkout, not merely assume it's importable.** This only holds
   automatically for an *editable* `lrh` install pointing at that exact
   checkout (the environment this WI was authored in) — for the
   documented, supported `pipx install lrh` / `pip install lrh` paths
   (`README.md`), the installed distribution is a frozen copy unaffected
   by this PR merging into some separate git checkout, so
   `importlib.resources.files("lrh.skills")` keeps resolving to the old,
   pre-fix package regardless. The bootstrap step must therefore either
   run with `PYTHONPATH` (or equivalent) explicitly pointed at the merged
   checkout's `src/`, or detect that the loaded package doesn't match the
   merge and stop with an explicit error rather than silently refreshing
   `lrh-closeout` from stale package data. Call the outcome out explicitly
   in the closeout report rather than assuming it happened silently,
   since a missed or mismatched bootstrap is invisible until the *next*
   skill-touching PR fails to trigger the new step at all.

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
  `.claude/skills/` or `src/lrh/skills/` using a rename-aware listing,
  derives candidate skill names by path shape (a non-skill file directly
  under the prefix, e.g. `installer.py`, yields no candidate), then
  partitions candidates by membership in `_skill_names()` at *both* the
  old and current revisions into added/modified vs. removed/renamed vs.
  not-a-skill — in that order, so a removed name is never discarded
  before it can be classified, and a name excluded from `_skill_names()`
  at both revisions (e.g. `_shared`) is never misreported as removed.
- A skill in the added/modified set is refreshed even when its previously
  installed bytes differ from a stale prior package revision — not
  blocked by the coarse-grained `USER_MODIFIED` check.
- A skill *not* in that touched set, but with genuine local modifications,
  still reports `user_modified` and is left untouched.
- A skill in the removed/renamed set is reported as an explicit anomaly,
  not silently left stale with no signal and not auto-uninstalled; a
  rename's old name is detected even when the diff listing would
  otherwise expose only the new path.
- A changed path under an excluded directory (e.g. `_shared`) produces no
  candidate and no anomaly.
- The planned refresh (which skill names, added/modified vs. removed) is
  disclosed in the closeout plan and explicitly approved at the confirm
  gate *before* any file under `~/.claude/skills/` is written — not only
  reported after the fact.
- The outcome (which skills were refreshed, any anomalies) is shown in the
  closeout report.
- New unit tests cover: the targeted refresh (named skill with differing
  bytes is overwritten; unnamed skill with differing bytes is left
  alone); candidate derivation (`installer.py` yields no candidate);
  both-revisions partitioning (a removed skill is classified removed, an
  excluded directory like `_shared` is classified as not-a-skill, not
  removed); and an actual rename (old name reported removed, new name
  added/modified).
- SKILL.md (both trees) is updated to document the new step.
- This work item's own implementation PR's closeout invokes the targeted
  refresh capability (item 1), scoped to `lrh-closeout` alone, loaded
  from the merged checkout (not an unrelated installed distribution) —
  not a plain non-force `lrh skills install`, which would itself
  misclassify the stale installed copy as `USER_MODIFIED` and skip it —
  and calls this out explicitly in the closeout report.
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
  `src/lrh/skills/installer.py` and confirm it yields no candidate
- Manual smoke test: run against a PR whose diff removes or renames a
  skill directory and confirm it is reported as an anomaly (both the
  removed old name and the added new name, for a rename), not silently
  dropped or refreshed
- Manual smoke test: run against a PR whose diff touches
  `src/lrh/skills/_shared/` and confirm no candidate/anomaly is produced
- `diff -r .claude/skills/lrh-closeout src/lrh/skills/lrh-closeout` (mirror
  parity)
- After this WI's own implementation PR closes out: confirm
  `~/.claude/skills/lrh-closeout` was refreshed via the targeted-refresh
  capability, loaded from the merged checkout, not a plain non-force
  `lrh skills install` or an unrelated installed distribution (Required
  Changes item 5)

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
- Self-bootstrap: the globally installed `lrh-closeout` skill is what a
  session actually executes, and it only gains the new step once
  refreshed — but refreshing it is the new step's own job. A plain,
  non-force `lrh skills install` cannot do this bootstrap refresh either,
  for the identical reason the rest of this WI exists: the installed copy
  necessarily differs from the just-merged package and would be
  classified `USER_MODIFIED` and skipped. Required Changes item 5
  therefore requires the targeted-refresh capability itself, scoped to
  `lrh-closeout`, not the plain command — without it, the very first
  opportunity to activate the fix silently doesn't, and every session
  keeps running the pre-fix workflow until someone happens to notice and
  fix it by hand.
- The bootstrap call itself only reaches the new package if the invoking
  environment's `lrh` is editable-installed against the merged checkout.
  A standard `pipx`/`pip` install of `lrh` is a frozen snapshot untouched
  by this PR merging into some separate git checkout — the bootstrap must
  either explicitly point its Python path at the merged checkout or
  detect and refuse a mismatched loaded package, or it will either fail
  outright or (worse) silently "succeed" while copying stale pre-fix
  package data.
- The removed/renamed detection must check `_skill_names()` membership at
  *both* the old and current package revisions, not current alone —
  otherwise a directory that was always excluded from installable skills
  (e.g. `_shared`, underscore-prefixed by convention) gets misreported as
  a removed skill on any PR that happens to touch it, a false-positive
  anomaly with no real fix available.
