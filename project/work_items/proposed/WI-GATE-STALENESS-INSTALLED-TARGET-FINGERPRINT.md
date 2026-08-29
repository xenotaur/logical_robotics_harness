---
resolution: null
blocked_reason: null
blocked: false
id: WI-GATE-STALENESS-INSTALLED-TARGET-FINGERPRINT
title: Fix gate-staleness detection to work once LRH is installed outside this repo
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams:
  - WS-INVOCATION-AND-GATE-RESET
related_design:
  - project/design/proposals/adopted/lrh-gate-policy/00_proposal.md
  - project/memory/decisions/DEC-CHAIN-INIT-SKIP-CONSENT.md
  - project/work_items/resolved/WI-LRH-CHAIN-DEFAULTS-INCREMENT-3.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - ship_skip_if_opted_in_as_default
acceptance:
  - check_gate_staleness detects a material gate-definition change even when src/lrh/skills/ doesn't exist in the checkout, for both a project-local git-tracked installed target and a user-scope/untracked installed target
  - For a project-local git-tracked installed target, the fix watches the resolved installed-target paths via the existing marker-scoped git-based comparison, reusing installer.py's target-resolution logic
  - For a user-scope or otherwise untracked installed target (outside any git working tree, e.g. installer.py's Path.home()-based default), the fix persists a content/version fingerprint at consent-grant time and compares current file content against it directly -- not via git history, which cannot work for an untracked path
  - When the installed target can't be resolved, or a required fingerprint is missing/unreadable, the check fails closed (reports stale, never silently stale=False) -- this is distinguishable from a genuine no-change result
  - New/updated unit tests cover both the project-local git-tracked case and the user-scope/untracked case explicitly, with a fixture that does not itself commit the installed path (which would hide the untracked-target gap, as the PR #648 review caught in an earlier draft)
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_new_python
artifacts_expected:
  - src/lrh/gate_staleness.py
  - tests/gate_staleness_test.py
---

# Fix gate-staleness detection to work once LRH is installed outside this repo

## Summary

`src/lrh/gate_staleness.py`'s staleness check for `chain_init_confirmation:
skip_if_opted_in` hardcodes a watch list of `src/lrh/skills/...` paths and
compares them via `git show <commit>:<path>` against this harness repo's own
history. In a client repo that installed LRH as a package (the documented
supported case — no `src/lrh/skills/` tree present), every watched path is
absent at both the confirmed commit and `HEAD`, and the check silently
reports `stale=False` unconditionally. A `skip_if_opted_in` consent can
therefore survive a material gate redesign and skip a live confirmation
that `DEC-CHAIN-INIT-SKIP-CONSENT` requires.

## Problem / Context

This is a Codex P1 finding from PR #512's review
(`https://github.com/xenotaur/logical_robotics_harness/pull/512#discussion_r3738156886`
and the reply thread at
`https://github.com/xenotaur/logical_robotics_harness/pull/512#discussion_r3882456470`),
investigated and confirmed still real against the current implementation —
not fixed by the later `WI-LRH-CHAIN-DEFAULTS-INCREMENT-3` redesign, which
changed the check from file-granular to marker-scoped (semantic
`GATE-DEFINITION` regions) but never changed *what paths* it watches:

- `src/lrh/gate_staleness.py:34-45` (`DEFAULT_WATCHED_FILES`) hardcodes 10
  paths, every one under `src/lrh/skills/`.
- `src/lrh/gate_staleness.py:186-208` (`_show_file_at`) runs
  `git show {commit}:{relative_path}` against those exact repo-relative
  paths — nothing target-aware.
- `src/lrh/gate_staleness.py:211-232` (`check_file_staleness`): when a path
  is absent at both commits, it returns
  `FileStaleness(..., stale=False, reason="absent at both commits")` — the
  same code path a genuine "nothing changed" case takes.

`WI-LRH-CHAIN-DEFAULTS-INCREMENT-3`'s own scope
(`project/work_items/resolved/WI-LRH-CHAIN-DEFAULTS-INCREMENT-3.md`) never
mentions "installed," "client repo," or "fingerprint" anywhere — it was
scoped entirely to this harness repo's own semantics, and the
cross-installation case was never in scope for that work item.

`src/lrh/skills/installer.py:485-486,557-559` already resolves per-target
skill directories (`.claude/skills/`, `.agents/skills/`,
`.gemini/plugins/lrh/skills/`) for install purposes — this work item's fix
should reuse that existing target-resolution logic rather than inventing a
new one.

### Prior Art Check

#### Duplication search

- **In-repo:** No existing work item addresses installed-target gate
  staleness. `WI-CHAIN-DEFAULTS-STALENESS-RESTAMP` (resolved, PR #632) is
  unrelated — it re-stamps `confirmed_commit` after a live reconfirmation,
  not the underlying staleness-check watch-path logic.
  `WI-LRH-CHAIN-DEFAULTS-INCREMENT-3` (resolved, PR #623) redesigned the
  check's granularity but explicitly did not address this axis, confirmed
  by reading its own acceptance criteria and body text directly.
- **Sibling repos:** Not applicable — specific to this harness's own
  distribution model.
- **External libraries:** Not applicable.
- **Recommendation:** Proceed.

#### Demand search

- **Work items:** None found requesting this specific fix.
- **Proposals:** `PROP-LRH-GATE-POLICY` (adopted) Decision 6 defines the
  staleness-watch principle in general terms ("watch the files that carry
  gate-definition statements") but does not itself resolve the
  installed-target gap — its own reference implementation
  (`gate_staleness.py`) is what has the gap.
- **Backlog:** No matching entry in `project/design/backlog.md`.
- **Recommendation:** No existing artifact to close or link; proceed as new.

## Scope

Fix `check_gate_staleness`/`check_file_staleness` (and their watch-path
configuration) to correctly detect gate-definition changes when LRH is
installed into a client repository without a `src/lrh/skills/` tree. Out of
scope: any other staleness-check redesign, and any change to
`chain_init_confirmation`'s two-step consent contract itself
(`DEC-CHAIN-INIT-SKIP-CONSENT`), which this work item must not weaken.

## Required Changes

1. Resolve the actually-installed skill target (reusing
   `src/lrh/skills/installer.py`'s existing per-target path resolution)
   before deciding which paths to watch, instead of hardcoding
   `src/lrh/skills/...` unconditionally.
2. When no `src/lrh/skills/` tree exists, resolve the installed target
   (reusing `installer.py`'s resolution) and branch on whether that target
   lives inside a git-tracked checkout under `project_root`:
   - **Project-local installed target inside a git checkout** (e.g. a
     client repo's own `.claude/skills/lrh-land/SKILL.md`, committed to
     that repo): watch the resolved installed-target paths using the same
     marker-scoped (`GATE-DEFINITION`) semantic `git show`-based
     comparison `WI-LRH-CHAIN-DEFAULTS-INCREMENT-3` already established.
   - **User-scope or otherwise untracked install target** (the documented
     default install location, e.g. `~/.claude/skills/`, which is outside
     any git working tree and has no history to diff against
     `confirmed_commit` — confirmed via `installer.py`'s
     `_default_skills_dir`, which resolves under `Path.home()`): a
     `git show`-based comparison cannot work here at all, regardless of
     which path is watched. Persist a content/version fingerprint (e.g. a
     hash of the installed gate-bearing files' current content) at the
     moment `skip_if_opted_in` consent is granted, and compare current
     file content against that stored fingerprint on each check — not
     against git history.
3. **Fail closed, never silently pass, when neither comparison is
   possible** — if the installed target can't be resolved, or a stored
   fingerprint is missing/unreadable for an untracked target, the check
   must report `stale=True` (or an explicit error the caller treats as
   staleness), never `stale=False`. Distinguish this from "path existed at
   both commits with no change" — a genuine no-change result and an
   unable-to-verify result must never share the same silent
   `stale=False` outcome.
4. Add unit tests exercising the installed-target case explicitly (a
   fixture checkout with no `src/lrh/skills/` tree, only an installed
   target directory, containing a `GATE-DEFINITION`-marked change between
   two commits) — not just the harness-repo self-check the current test
   suite covers.
5. Mirror any skill-level documentation changes into `.claude/skills/` per
   the usual convention, if this work touches skill-facing text describing
   the staleness check's behavior.

## Non-Goals

- Does not change `DEC-CHAIN-INIT-SKIP-CONSENT`'s two-step consent
  contract, the value-hash binding, or the special-conditions check — only
  the staleness-detection watch-path logic.
- Does not ship `chain_init_confirmation: skip_if_opted_in` as a default —
  `forbidden_actions` explicitly excludes this, matching
  `WI-LRH-CHAIN-DEFAULTS-INCREMENT-3`'s own convention.
- Does not redesign the marker-scoped (`GATE-DEFINITION`) comparison
  mechanism itself — reuses it as-is for whichever paths are actually
  watched.

## Acceptance Criteria

- `check_gate_staleness` detects a material gate-definition change for
  both a project-local git-tracked installed target and a user-scope/
  untracked installed target
- The git-tracked case reuses the existing marker-scoped `git show`-based
  comparison against the resolved installed-target paths
- The untracked case (e.g. the default `~/.claude/skills/` install,
  outside any git working tree) compares current file content against a
  content/version fingerprint persisted at consent-grant time — not via
  git history, which cannot work there
- An unresolvable target or missing/unreadable fingerprint fails closed
  (`stale=True`, never a silent `stale=False`) — distinguishable from a
  genuine no-change result
- New/updated unit tests cover both cases explicitly, with a fixture that
  does not itself commit the installed path
- `lrh validate` reports 0 errors

## Validation

- lrh validate
- New unit tests for both the project-local git-tracked and the
  user-scope/untracked installed-target cases, alongside the existing
  harness-repo self-check tests in `tests/gate_staleness_test.py`
- Manual verification, both cases: (a) a project-local installed client
  checkout (no `src/lrh/skills/` tree, but the installed target is
  git-tracked) correctly detects a `GATE-DEFINITION`-region change as
  stale; (b) a user-scope install (target outside any git working tree)
  correctly fails closed or detects staleness via the persisted
  fingerprint — never silently reports `stale=False`

## Risk Notes

The primary risk is fixing this narrowly enough that it doesn't
accidentally weaken the existing harness-repo self-check (this repo itself
always has `src/lrh/skills/`, so the fix must not regress detection there
while adding the installed-target paths). A second, distinct risk — caught
during this work item's own review (PR #648) — is that a test fixture
which commits the installed path into a git repo can hide the untracked
(user-scope) gap entirely, since that fixture never exercises the
"target has no git history at all" case the default install actually
produces. Any implementation should be checked in three directions: the
harness repo's own staleness check still works exactly as before; a
project-local, git-tracked installed-target checkout now correctly
detects staleness instead of silently reporting none; and a user-scope,
untracked installed target — verified with a fixture that does *not*
commit the installed path — either fails closed or correctly detects
staleness via the persisted fingerprint.
