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
related_workstreams: []
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
  - "/lrh-closeout gets the PR's changed-file list from the REST PR Files endpoint specifically, fully paginated (not gh pr view --json files, not a post-merge git diff), derives candidate skill names by path shape, then partitions by _skill_names() membership at both base and current revisions into added/modified vs. removed/renamed vs. not-a-skill, in that order"
  - If the paginated file list reaches the REST endpoint's 3,000-file ceiling, the step reports an anomaly and skips install for that PR rather than assuming completeness
  - If the file-list fetch itself fails, the step reports an anomaly and skips install for that run rather than failing open
  - The base-revision _skill_names() lookup uses the colon path form (<baseRefOid>:src/lrh/skills), not the pathspec form, which only returns the directory entry itself
  - The whole step, not only item 5's bootstrap, loads _skill_names() and the targeted-refresh function from the merged checkout on every run, not just the first bootstrap invocation
  - The targeted-refresh function validates each name against the current package before any destructive filesystem operation and returns an explicit absent-name result rather than deleting an existing installed directory first
  - A skill in the added/modified set is refreshed even when its previously installed bytes differ from a stale prior package revision, not blocked by the coarse-grained USER_MODIFIED check
  - A skill not in that touched set, but with genuine local modifications, still reports user_modified and is left untouched
  - A skill in the removed/renamed set is reported as an explicit anomaly, not silently left stale, auto-uninstalled, or destroyed by an invalid targeted-refresh call, including a rename's old name via previous_filename
  - A changed path under an excluded directory like _shared produces no candidate and no anomaly
  - The planned refresh is disclosed and approved at the confirm gate before any file under ~/.claude/skills/ is written
  - The outcome is shown in the closeout report
  - New unit tests cover the targeted refresh (including the absent-name safety case), candidate derivation excluding non-skill files like installer.py, both-revisions partitioning (removed vs. excluded-directory), and an actual rename via previous_filename
  - SKILL.md is updated to document the new step
  - This WI's own implementation PR's closeout invokes the targeted refresh capability scoped to lrh-closeout alone, loaded from the merged checkout, not a plain non-force lrh skills install or an unrelated installed distribution
  - The implementation PR itself documents that whoever closes it out must run this bootstrap step by hand, since no closeout automation can trigger it on its own PR
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
   skills' status computation untouched.

   **Validate each name against the current package before performing
   any destructive filesystem operation.** `_copy_skill` currently
   `rmtree`s the destination *before* attempting to read the package
   source — for a name absent from the current package (a removed or
   renamed skill, or any other caller error), that sequencing would
   delete the existing `~/.claude/skills/<name>` and then raise trying
   to traverse a nonexistent package resource, destroying exactly the
   stale directory the removed-skill policy (item 2) says to preserve
   and report, not delete. The targeted function must check
   `_skill_names()` membership for each name *first* and return an
   explicit absent-name result (not raise mid-copy, not silently skip)
   before touching the filesystem for that name — classification of
   *why* a name is absent (removed vs. renamed vs. never valid) remains
   item 2's job; this function's job is only to refuse to delete-then-fail
   on a name it can't actually refresh.
   Cover it with unit tests in `tests/skills_installer_test.py` (a
   targeted refresh overwrites a named skill even when its installed
   bytes differ from the package; an unnamed skill with differing bytes
   is left alone and still reports `USER_MODIFIED`; calling the targeted
   function with a name absent from the current package returns the
   explicit absent-name result and leaves any existing installed
   directory for that name untouched — not deleted, not raised through).
2. Extend `.claude/skills/lrh-closeout/SKILL.md` (and its
   `src/lrh/skills/lrh-closeout/SKILL.md` mirror) with a new step, placed
   after the PR's changes are known to be merged, that:
   - Gets the closed-out PR's full changed-file list from the **REST PR
     Files endpoint specifically** —
     `gh api repos/<owner>/<repo>/pulls/<N>/files --paginate`, or the
     equivalent direct REST call — not a post-merge `git diff` against
     some inferred parent commit, and **not** `gh pr view --json files`.
     That form of `gh pr view` resolves through GitHub's GraphQL
     `PullRequestChangedFile` type, which exposes `path`, additions, and
     deletions but has **no previous-path field at all** — only the REST
     endpoint's file schema includes `previous_filename` for a renamed
     file, so a rename's old path is unrecoverable from the GraphQL form
     regardless of pagination. A squash or rebase merge collapses the
     PR's commits into one (or rewrites them), so diffing the merge
     result against its immediate parent can miss changes from earlier
     commits in a multi-commit PR or misidentify the comparison range
     entirely; the REST PR Files endpoint always reflects the PR's full,
     correct cumulative diff regardless of merge strategy.
   - **Paginates the REST response fully** — GitHub's PR Files endpoint
     defaults to 30 files per page (100 max) and does not return the
     complete list in one call for a PR with more files than that; use
     `gh api --paginate` (or manually follow `Link` headers /
     `page`/`per_page`) rather than assuming a single page is complete,
     which would silently truncate the changed-file list on a
     large-enough PR.
   - **Detects the endpoint's own hard ceiling.** GitHub's documented
     behavior for this endpoint caps the response at 3,000 files total,
     even with full pagination — a PR changing more files than that
     cannot have its complete file list obtained through this endpoint at
     all, regardless of how thoroughly pagination is implemented. If the
     paginated result reaches this ceiling (a strong signal, though not a
     guaranteed exact count, that more files exist beyond it), do not
     silently proceed as if the list were complete: report an explicit
     anomaly and skip the skill-install step for this PR rather than
     risk missing a touched skill with no signal. (No PR in this
     repository's history has come close to this size — this is a
     defensive ceiling check, not a scenario expected to occur in
     practice.)
   - **Handles the file-list fetch itself failing** (authentication,
     rate-limit, network error, or any non-2xx response from the REST
     call) the same way as the ceiling case above: report an explicit
     anomaly and skip the skill-install step for this run — never fail
     open by silently skipping detection and proceeding as if the PR
     touched no skills. A fail-open implementation here would reproduce
     exactly the silent-staleness bug this WI exists to close, just
     triggered by a transient API failure instead of a missing workflow
     step.
   - Filters that file list to `.claude/skills/` and `src/lrh/skills/`
     path prefixes (checking both `filename` and, when present,
     `previous_filename`, so a rename's old path is captured even if only
     the new path matches a prefix on its own).
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
     `_skill_names()` **at both the PR's base revision and the current
     (post-merge `main`) revision** — not current alone. "Base revision"
     is the PR's `baseRefOid` as recorded by the PR API (the same API
     call as above, or `gh pr view --json baseRefOid`) — i.e. `main` as
     it stood before this PR's changes. To list `_skill_names()`-eligible
     entries at that revision, use the **colon path form**,
     `git ls-tree -d --name-only <baseRefOid>:src/lrh/skills` (or a
     checkout of that SHA) — this resets the tree root to
     `src/lrh/skills` itself and lists *its* immediate children. The
     space-separated pathspec form, `git ls-tree -d --name-only
     <baseRefOid> -- src/lrh/skills`, does **not** do this: a pathspec
     limits which entries of the *root* tree are shown, so a non-recursive
     `ls-tree` given a nested-directory pathspec prints only that one
     tree entry (`src/lrh/skills` itself), not its contents — verified
     live against this repository's own tree (the pathspec form emits a
     single line, `src/lrh/skills`; the colon form correctly emits all
     15 child skill directory names). Getting this wrong silently empties
     the base-revision membership set, which would misclassify every
     genuinely removed or renamed skill as absent-from-both-revisions
     (Non-Goal territory, not the removed/renamed anomaly it should be).
     Also note: `git show <rev>:<path>` requires `<path>` to name a
     single blob (file), not a directory, so it is not the right form for
     this at all — use `ls-tree`, not `show`. Either way, this is a
     lookup against the already-fetched base commit, not something to be
     inferred from post-merge commit parentage.
     Present in current → **added/modified** (refresh via item 1);
     present at the base revision but absent from current →
     **removed/renamed** (the skill existed before, evidenced by the
     diff, but not now, so there is no source to refresh from); absent
     from **both** revisions → not a skill at all, ignored. This last
     case specifically covers a changed path under an excluded directory
     like `src/lrh/skills/_shared/` (`_skill_names()` deliberately
     excludes underscore-prefixed directories) — without the
     both-revisions check, `_shared` would wrongly be classified
     removed/renamed on every PR that touches it, since it was never in
     `_skill_names()` at either revision. Applying the package-membership
     filter *before* the structural filter, or checking only the current
     revision, would both defeat the removed-skill handling below — the
     structural filter must run first, and both-revisions membership
     second.
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
   - **This whole step — not only item 5's one-time bootstrap — must load
     `_skill_names()` (both revisions) and the targeted-refresh function
     from the merged `main` checkout, subject to the identical
     editable-vs-frozen-install caveat item 5 describes.** Item 5's
     `PYTHONPATH`-or-detect-mismatch requirement was written for the
     one-time bootstrap case, but every ordinary run of this step, on
     every later skill-touching PR, calls the same
     `_skill_names()`/`importlib.resources.files("lrh.skills")` machinery
     and is subject to the exact same frozen-distribution problem for a
     `pipx`/`pip`-installed (non-editable) `lrh` — not just the first,
     bootstrap-only invocation. Apply the same requirement here as a
     standing precondition for this step generally, not a special case
     limited to item 5.
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

   **Who actually performs this call, concretely: this is a manual,
   one-time exception, not something the automated new step can trigger
   on its own PR.** The session closing out this WI's own implementation
   PR is, by definition, still running whatever `lrh-closeout` version
   was installed *before* this PR merged — which does not contain the
   new step being added, so there is no automated path that "notices"
   the bootstrap is needed and runs it. The implementation PR itself
   (its description, or its own execution record's Follow-up section)
   must explicitly instruct whoever closes it out to run the targeted
   refresh for `lrh-closeout` by hand as a documented, called-out
   exception step — not leave it implicit or assume the ordinary closeout
   flow will somehow cover it, since it structurally cannot.

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

- `/lrh-closeout` gets the PR's changed-file list from the **REST** PR
  Files endpoint specifically, fully paginated (not `gh pr view --json
  files`, whose GraphQL schema has no previous-path field at all; not a
  post-merge `git diff`, which is unreliable across squash/rebase merges
  and multi-commit PRs; and not a single unpaginated page, which silently
  truncates on a large PR), derives candidate skill names by path shape
  (a non-skill file directly under the prefix, e.g. `installer.py`,
  yields no candidate), then partitions candidates by membership in
  `_skill_names()` at *both* the PR's base revision (`baseRefOid`) and
  current (`main`) into added/modified vs. removed/renamed vs.
  not-a-skill — in that order, so a removed name is never discarded
  before it can be classified, and a name excluded from `_skill_names()`
  at both revisions (e.g. `_shared`) is never misreported as removed.
- If the paginated file list reaches the REST endpoint's documented
  3,000-file ceiling, the step reports an explicit anomaly and skips the
  install step for that PR, rather than silently proceeding as if the
  list were known-complete.
- If the file-list fetch itself fails (auth, rate-limit, network, or any
  non-2xx response), the step reports an explicit anomaly and skips
  install for that run — it never fails open by proceeding as if the PR
  touched no skills.
- The base-revision `_skill_names()` lookup uses the colon path form
  (`git ls-tree -d --name-only <baseRefOid>:src/lrh/skills`), not the
  pathspec form, which returns only the `src/lrh/skills` entry itself
  and would silently empty the base-membership set.
- This whole step (not only item 5's bootstrap) loads `_skill_names()`
  and the targeted-refresh function from the merged checkout under the
  same editable-vs-frozen-install requirement, on every run — not just
  the first, bootstrap-only invocation.
- The targeted-refresh function (item 1) validates each name against the
  current package *before* any destructive filesystem operation, and
  returns an explicit absent-name result rather than deleting an existing
  installed directory and then failing to find its package source.
- A skill in the added/modified set is refreshed even when its previously
  installed bytes differ from a stale prior package revision — not
  blocked by the coarse-grained `USER_MODIFIED` check.
- A skill *not* in that touched set, but with genuine local modifications,
  still reports `user_modified` and is left untouched.
- A skill in the removed/renamed set is reported as an explicit anomaly,
  not silently left stale with no signal, not auto-uninstalled, and not
  destroyed by an invalid targeted-refresh call; a rename's old name is
  detected via the PR API's `previous_filename`, not a raw name-only diff.
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
  alone; a name absent from the current package returns an explicit
  absent-name result and does not delete an existing installed
  directory); candidate derivation (`installer.py` yields no candidate);
  both-revisions partitioning (a removed skill is classified removed, an
  excluded directory like `_shared` is classified as not-a-skill, not
  removed); and an actual rename via `previous_filename` (old name
  reported removed, new name added/modified).
- SKILL.md (both trees) is updated to document the new step.
- This work item's own implementation PR's closeout invokes the targeted
  refresh capability (item 1), scoped to `lrh-closeout` alone, loaded
  from the merged checkout (not an unrelated installed distribution) —
  not a plain non-force `lrh skills install`, which would itself
  misclassify the stale installed copy as `USER_MODIFIED` and skip it —
  and calls this out explicitly in the closeout report.
- The implementation PR itself explicitly documents (in its description
  or execution record) that whoever closes it out must run this
  bootstrap step by hand, since the closeout automation that would
  otherwise trigger it does not yet exist in the pre-fix
  `lrh-closeout` that session is running.
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
  dropped, refreshed, or destroyed by a mishandled targeted-refresh call
- Manual smoke test: run against a multi-commit, squash- or rebase-merged
  PR touching a skill and confirm the REST PR Files endpoint still
  surfaces the full changed-skill set (not just the final rebased
  commit's diff)
- Manual smoke test: run against a PR with more changed files than one
  page of the REST PR Files endpoint returns (30 default / 100 max) and
  confirm the full list is retrieved, not truncated to the first page
- Manual smoke test: run against a PR whose diff touches
  `src/lrh/skills/_shared/` and confirm no candidate/anomaly is produced
- Manual smoke test: simulate the file-list fetch failing (auth error,
  rate limit, or network failure) and confirm the step reports an
  anomaly and skips install, rather than proceeding as if no skills were
  touched
- `diff -r .claude/skills/lrh-closeout src/lrh/skills/lrh-closeout` (mirror
  parity)
- After this WI's own implementation PR closes out: confirm
  `~/.claude/skills/lrh-closeout` was refreshed via the targeted-refresh
  capability, loaded from the merged checkout, not a plain non-force
  `lrh skills install` or an unrelated installed distribution (Required
  Changes item 5), and confirm the implementation PR's own description or
  execution record documented this manual step for the closing session

## Risk Notes

- Detecting "the closed-out PR's diff" requires the closeout step to know
  the PR's file list at closeout time — if `/lrh-closeout` is ever run
  detached from the original PR context (e.g. a bare execution-record
  cleanup with no PR reference), the detection has nothing to check
  against; the implementation should degrade to a no-op in that case, not
  fail the whole closeout. The same "do not fail the whole closeout"
  principle applies if PR context exists but the file-list fetch itself
  fails (see Required Changes item 2's explicit fail-closed-on-detection,
  fail-open-on-the-rest-of-closeout handling) — the distinction that
  matters is skipping *this step*, not the entire closeout run.
- Item 5's bootstrap step has no automated trigger by construction — the
  closeout session that would need to invoke it is, by definition,
  running a pre-fix `lrh-closeout` that doesn't know to. This is not an
  implementation bug to fix later; it is a structural one-time exception
  that must be handled by explicit human-readable documentation on the
  implementation PR itself, not by any mechanism this WI's own scope can
  automate.
- A post-merge `git diff` against an inferred parent commit is not a
  reliable source for "this PR's changed files" — squash and rebase
  merges can collapse or rewrite the commit history such that diffing
  the merge result against its immediate parent misses changes from
  earlier commits in a multi-commit PR. The REST PR Files endpoint must
  be the source of truth, not derived git history, and specifically not
  `gh pr view --json files` — that form resolves through GraphQL's
  `PullRequestChangedFile` type, which has no previous-path field, so
  rename detection (item 2's structural filter needs both old and new
  paths) is silently impossible through it regardless of pagination.
- The REST PR Files endpoint paginates (30/page default, 100 max) — an
  implementation that reads only the first page silently truncates the
  changed-file list on any PR larger than that, potentially missing
  skill-touching files entirely with no error or signal.
- Pagination alone does not make the file list unbounded: GitHub
  documents a hard 3,000-file ceiling on this endpoint's total response,
  beyond which no amount of paginating recovers the rest. No PR in this
  repository's actual history has approached that size, so this is a
  defensive check, not an anticipated real occurrence — but silently
  treating a list that happens to hit the ceiling as complete would be
  the same kind of silent-staleness bug this WI exists to close.
- A caller bug that passes a name absent from the current package to the
  targeted-refresh function could, without item 1's validation
  requirement, delete an existing installed skill directory before
  failing to find its package source — turning a removed-skill anomaly
  (meant to be reported, not touched) into actual data loss.
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
- **This is not unique to the bootstrap.** Every routine run of the new
  step (item 2, on every later skill-touching PR) calls the same
  `_skill_names()` and `importlib.resources.files("lrh.skills")`
  machinery, and is subject to the identical frozen-vs-editable-install
  problem — not only the one-time bootstrap invocation on this WI's own
  implementation PR. An implementation that only applies the
  merged-checkout-loading requirement to item 5 and not to item 2's
  ordinary operation would leave every subsequent skill-touching PR
  broken in a non-editable `lrh` environment, silently.
- The base-revision `_skill_names()` lookup's exact `git` invocation
  matters: a space-separated pathspec (`git ls-tree ... <rev> --
  src/lrh/skills`) does not list a directory's children — only the
  colon path form (`<rev>:src/lrh/skills`) resets the tree root and
  lists them. Getting this wrong doesn't error; it silently returns an
  empty or wrong membership set, which would misclassify every genuinely
  removed or renamed skill.
- The removed/renamed detection must check `_skill_names()` membership at
  *both* the old and current package revisions, not current alone —
  otherwise a directory that was always excluded from installable skills
  (e.g. `_shared`, underscore-prefixed by convention) gets misreported as
  a removed skill on any PR that happens to touch it, a false-positive
  anomaly with no real fix available.
