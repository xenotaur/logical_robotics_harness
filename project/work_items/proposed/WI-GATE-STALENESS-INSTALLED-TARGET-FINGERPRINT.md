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
  - check_gate_staleness detects a material gate-definition change even when src/lrh/skills/ doesn't exist in the checkout (the documented installed-client-repo case), verified against at least one installed target
  - The fix fingerprints the actually-installed skill content per target rather than assuming a fixed harness-repo-relative path list
  - DEFAULT_WATCHED_FILES's hardcoded src/lrh/skills/... list (src/lrh/gate_staleness.py:34-45) either becomes target-aware or is replaced by a target-resolution step reusing src/lrh/skills/installer.py's existing target logic
  - git diff / git show calls no longer silently classify "path absent at both commits" as stale=False when that absence is because the target wasn't checked, vs. a genuine no-change -- the two cases must be distinguishable
  - New/updated unit tests cover the installed-target case explicitly, not just the harness-repo self-check
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
2. When no `src/lrh/skills/` tree exists, fall back to watching the
   resolved installed-target paths (e.g. `.claude/skills/lrh-land/SKILL.md`)
   for the same gate-bearing skills, using the same marker-scoped
   (`GATE-DEFINITION`) semantic comparison `WI-LRH-CHAIN-DEFAULTS-INCREMENT-3`
   already established.
3. Distinguish "path never existed at either commit because the wrong
   target was checked" from "path existed at both commits with no change"
   — the former must not silently resolve to `stale=False`; it should
   either resolve the correct target first, or surface as an error/warning
   rather than a false negative.
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

- `check_gate_staleness` detects a material gate-definition change even
  when `src/lrh/skills/` doesn't exist in the checkout, verified against
  at least one installed target
- The fix fingerprints the actually-installed skill content per target
  rather than assuming a fixed harness-repo-relative path list
- `DEFAULT_WATCHED_FILES`'s hardcoded list either becomes target-aware or
  is replaced by a target-resolution step reusing `installer.py`'s
  existing target logic
- "Path absent because the wrong target was checked" is distinguishable
  from "no change" — no silent false negative
- New/updated unit tests cover the installed-target case explicitly
- `lrh validate` reports 0 errors

## Validation

- lrh validate
- New unit tests for the installed-target fingerprinting path, alongside
  the existing harness-repo self-check tests in `tests/gate_staleness_test.py`
- Manual verification: simulate an installed client-repo checkout (no
  `src/lrh/skills/` tree) and confirm a `GATE-DEFINITION`-region change to
  the installed target's `SKILL.md` is correctly detected as stale

## Risk Notes

The primary risk is fixing this narrowly enough that it doesn't
accidentally weaken the existing harness-repo self-check (this repo itself
always has `src/lrh/skills/`, so the fix must not regress detection there
while adding the installed-target path). Any implementation should be
checked in both directions: the harness repo's own staleness check still
works exactly as before, and an installed-target checkout with no
`src/lrh/skills/` tree now correctly detects staleness instead of silently
reporting none.
