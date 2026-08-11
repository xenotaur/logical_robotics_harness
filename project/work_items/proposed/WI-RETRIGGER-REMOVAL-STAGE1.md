---
resolution: null
blocked_reason: null
blocked: false
id: WI-RETRIGGER-REMOVAL-STAGE1
title: Remove GitHub bot retrigger commands fleet-wide (PROP-INVOCATION-AND-GATE-RESET Stage 1)
type: operation
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
  - project/design/proposals/proposed/invocation-and-gate-reset/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - retrigger_bot_review
acceptance:
  - No @codex review comment mention or --add-reviewer @copilot request remains anywhere under src/lrh/skills/lrh-confirm-fixes/, replaced by a provisional no-progress loop cap
  - PR 522 is rescoped to its Decision 3 (bounded background poll) per PROP-INVOCATION-AND-GATE-RESET's resolved Open Questions; its Decisions 1 and 2 are closed as obviated
  - self_review_preference is removed from project/config/chain-defaults.yaml, src/lrh/skills/_shared/chain-defaults.md, and its inlined copy in lrh-land/references/land-workflow.md (both src/lrh/skills/ and .claude/skills/ mirrors)
  - The two stalled-reviewer-detection backlog entries scoped to the gutted files are marked obsolete with a note that a dispatched subagent can also stall
  - lrh skills install is run for both the Claude and Codex targets after merge
  - The retrigger strings are verified absent from all three installed corpora, not just the source tree -- ~/.claude/skills/, ~/.agents/skills/ (the Codex target lrh skills install writes to), and the per-repo .claude/skills/ mirror in this repository
  - A note is recorded that in-flight Claude Code and Codex sessions must be restarted to pick up the change; a stale session keeps retriggering even after propagation
  - confirmed_commit in project/config/chain-defaults.yaml is re-stamped to the commit that lands this change
  - New Python carries unit tests
  - lrh validate reports 0 errors
  - diff -r between src/lrh/skills/lrh-confirm-fixes/ and .claude/skills/lrh-confirm-fixes/ reports no differences
required_evidence:
  - manual_review
  - lrh_validate
  - test_new_python
artifacts_expected:
  - src/lrh/skills/lrh-confirm-fixes/SKILL.md
  - src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md
  - .claude/skills/lrh-confirm-fixes/SKILL.md
  - .claude/skills/lrh-confirm-fixes/references/round-cap-gate.md
  - project/config/chain-defaults.yaml
  - src/lrh/skills/_shared/chain-defaults.md
  - src/lrh/skills/lrh-land/references/land-workflow.md
  - .claude/skills/lrh-land/references/land-workflow.md
  - project/design/backlog.md
---

# Remove GitHub bot retrigger commands fleet-wide

## Summary

Implement `PROP-INVOCATION-AND-GATE-RESET` Stage 1: remove the `@codex
review` comment mention and `--add-reviewer @copilot` request from
`/lrh-confirm-fixes`, replace them with a provisional no-progress loop cap,
and propagate the change to every installed skill corpus this machine and
this fleet actually run from -- not just this repository's source tree.

## Problem / Context

Retrigger commands are still live today. Verified directly, not assumed:
`src/lrh/skills/lrh-confirm-fixes/SKILL.md` and
`references/round-cap-gate.md` both still carry `@codex review` and
`--add-reviewer @copilot`. So does the installed corpus at
`~/.claude/skills/lrh-confirm-fixes/`. So does `~/.agents/skills/lrh-confirm-fixes/`
-- the directory `src/lrh/skills/installer.py:428-431`'s
`_default_skills_dir` resolves to for the Codex install target (the
Claude branch returns early at `:429-430`; the Codex path falls through to
`:431`), confirmed populated with both files, retrigger strings intact.

This is not hypothetical cost. An agent session burned roughly $5 of
GitHub review credits on a retrigger today, from a corpus that had not
picked up any part of this fix -- PR #535 and PR #536 only amended the
*plan* to remove retriggering (the proposal and this program's governing
workstream); no skill file has changed yet.

**Three install targets, three restart requirements, one exclusion.**
Codex has just picked up LRH skill support, so `~/.agents/skills/` is now a
live, populated corpus that needs the same fix and verification as
`~/.claude/skills/` -- previously the proposal and workstream only named
the Claude corpus. Both Claude Code and Codex sessions currently running
will keep the copy they loaded at start even after this change merges and
propagates; each needs restarting. Antigravity has not shipped skill
support yet, so it carries no corpus and is explicitly out of scope --
revisit if that changes.

**`self_review_preference` has a third copy, found during pre-merge
verification.** A round-1 review comment (posted as an issue comment, not
a formal review, so `lrh request review_response`'s fetch did not surface
it) claimed additional propagation gaps. Its own claimed fix was never
delivered to this PR or reachable from this repository -- committed, by
its own account, on an isolated branch with no git remote and no GitHub
auth, so nothing about the claim could be taken on trust. Verified
independently instead: `self_review_preference` also appears, inlined, in
`lrh-land/references/land-workflow.md` in both `src/lrh/skills/` and
`.claude/skills/` -- a third copy this work item's Required Changes and
`artifacts_expected` had missed. A second claim in the same comment, that
distinct in-repo Codex-specific `lrh-confirm-fixes` artifacts exist beyond
the installed runtime corpus, was checked and does not hold.

### Prior-art check

**Duplication search -- no duplicate.** No other work item names
retrigger removal (`git grep -li "retrigger removal" project/work_items/`
found nothing before this file was added -- it now matches this file
itself, which is expected and not a duplicate) and no execution record or
open PR implements this specific change; `WI-DELIBERATE-MODEL-INVOCATION` (Stage 2, resolved via
PR #533) and `WI-FRONT-OF-RUN-GATE-COLLAPSE` (Stage 3, proposed) cover
different, later stages of the same proposal and do not touch
`lrh-confirm-fixes`'s retrigger mechanism.

**Demand search -- demand is recorded and is now urgent.**
`PROP-INVOCATION-AND-GATE-RESET` names this as Stage 1, the first stage in
its strictly sequential implementation plan, and Decision 2 resolves the
mechanism (retrigger removal is unconditional, with a provisional cap
retained). This work item is that decision's implementation. The $5 leak
today is fresh, first-hand demand evidence beyond what the proposal itself
already argued.

## Scope

In scope: `lrh-confirm-fixes/SKILL.md` and `references/round-cap-gate.md`
in both `src/lrh/skills/` and `.claude/skills/`; `PR #522`'s rescope;
`self_review_preference` removal from the chain-defaults profile, its
canonical doc, and its inlined copy in `lrh-land/references/land-workflow.md`
(both mirrors); the two stalled-reviewer backlog entries; `lrh skills
install` for the Claude and Codex targets; verification against all three
installed corpora; the `confirmed_commit` re-stamp.

Out of scope: `disable-model-invocation` removal from any skill (Stage 2,
already resolved separately); the gate corpus audit and DEC record (Stage
3); chain-defaults activation (Stage 3.5); Antigravity, which has no
installed corpus to fix.

## Required Changes

1. Remove `@codex review` and `--add-reviewer @copilot` from
   `lrh-confirm-fixes/SKILL.md` and `round-cap-gate.md`, in both
   `src/lrh/skills/` and `.claude/skills/`. Replace with a provisional
   no-progress loop cap per Decision 2.
2. Rescope PR #522 to Decision 3 only (bounded background poll); close
   Decisions 1 and 2 as obviated per the proposal's resolved Open
   Questions.
3. Remove `self_review_preference` from `project/config/chain-defaults.yaml`,
   its canonical description in `src/lrh/skills/_shared/chain-defaults.md`,
   and its inlined copy in `lrh-land/references/land-workflow.md` (both
   `src/lrh/skills/` and `.claude/skills/`).
4. Mark the two stalled-reviewer-detection backlog entries obsolete in
   `project/design/backlog.md`, noting a dispatched subagent can also stall
   and would need its own heuristic if this is rebuilt.
5. Run `lrh skills install` for both the Claude and Codex targets after
   merge.
6. Verify the retrigger strings are absent from `~/.claude/skills/`,
   `~/.agents/skills/`, and this repository's own `.claude/skills/` mirror
   -- three separate checks, not one.
7. Re-stamp `confirmed_commit` in `project/config/chain-defaults.yaml` to
   the landing commit.

## Non-Goals

- Does not remove `disable-model-invocation` from any skill.
- Does not touch the gate corpus audit, policy proposal, or DEC record --
  Stage 3.
- Does not activate `chain_init_confirmation: skip_if_opted_in` -- Stage
  3.5.
- Does not add Antigravity to the verification scope.
- Does not restart any live session itself -- that is a human action this
  work item can only remind about, not perform.

## Acceptance Criteria

Consult the `acceptance:` frontmatter field, which is the authoritative
list.

## Validation

- lrh validate
- scripts/test
- diff -r src/lrh/skills/lrh-confirm-fixes .claude/skills/lrh-confirm-fixes
- diff -r src/lrh/skills/lrh-land .claude/skills/lrh-land
- grep -rl "codex review\|add-reviewer @copilot" ~/.claude/skills/ (expect no match after propagation)
- grep -rl "codex review\|add-reviewer @copilot" ~/.agents/skills/ (expect no match after propagation)
- grep -rl "codex review\|add-reviewer @copilot" .claude/skills/ (this repository's own mirror; expect no match)
- grep -rl "self_review_preference" src/lrh/skills/ .claude/skills/ project/config/ (expect no match after propagation)

## Risk Notes

**Propagation is the deliverable, not a side effect.** Landing on `main`
changes nothing until `lrh skills install` runs for each target and the
result is verified against the installed corpus, not the source tree --
that is exactly the gap that let the $5 leak happen today. Acceptance
criteria enforce all three corpora explicitly for this reason.

**Restart reminder has no mechanical enforcement.** A session that loaded
its skill copy before this change propagates will keep retriggering
regardless of what lands. This work item can only record the reminder; it
cannot verify any particular session has restarted.

**Sequencing.** This is Stage 1 of a proposal whose Implementation Plan
requires Stages 1, 2, and 3 to land strictly sequentially, sharing four
files. Stage 2 (`WI-DELIBERATE-MODEL-INVOCATION`) is already resolved, so
this work item has no `depends_on` blocker -- but Stage 3
(`WI-FRONT-OF-RUN-GATE-COLLAPSE`) already lists Stage 2 as its own
dependency, and nothing in this file's scope touches Stage 3's files, so no
new cross-dependency is introduced here.
