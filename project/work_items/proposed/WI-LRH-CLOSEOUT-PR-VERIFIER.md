---
resolution: null
blocked_reason: null
blocked: false
id: WI-LRH-CLOSEOUT-PR-VERIFIER
title: Add a mechanical verifier for closeout PRs against the approved closeout plan
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
  - create_file
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - weaken_human_gate
acceptance:
  - A gate-owned command (name settled at implementation, tentatively `lrh closeout verify-pr <pr-url>`) exits 0 when a closeout PR conforms to the approved plan, 1 when it diverges (printing a structured diff of the divergent fields), and 2 when the check itself could not run
  - "Every changed path must be in the allowed set: project/executions/**, project/work_items/**, project/workstreams/**, project/design/proposals/**, project/sessions/index.jsonl, and project/config/chain-defaults.yaml; any other path is a divergence"
  - project/config/chain-defaults.yaml may change only in its confirmed_commit and confirmed_at lines; any other line change is a divergence
  - Execution-record diffs must match the fields shown in the Step 6 closeout preview (commit placeholder filled with the real merge SHA is the only expected difference)
  - The PR head SHA must equal the SHA the caller states it pushed, and mergeable must be clean and required or reported CI green; anything else is a divergence
  - The command reads state only; it never merges, pushes, edits files or changes settings
  - Unit tests use unittest.TestCase, are hermetic (no network, no git remotes, no heavyweight subprocesses), and cover conforming, each divergence class, and the exit-2 path
  - The module docstring states that the verifier checks conformance to a human-authorized plan and is not an autopilot tier for the merge gate
  - scripts/test, scripts/lint, scripts/format --check --diff and lrh validate are all clean
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/closeout_pr_verifier.py
  - tests/closeout_pr_verifier_test.py
  - src/lrh/cli (subcommand wiring; exact module settled at implementation)
---

## Summary

Add a small, tested, read-only command that decides whether a closeout PR
conforms to the closeout plan a human approved at `/lrh-land` Step 6. It gives
the closeout-PR merge a mechanical, testable conformance check instead of
relying on the agent to grade its own compliance.

## Problem / Context

`/lrh-land` Step 7 is moving to landing closeout through a small closeout PR
(see `WI-LRH-LAND-WORDING-AND-CLOSEOUT-PR`), because a direct push to `main`
is denied in auto mode. The Step 6 summary will present that closeout PR's
concrete plan, and the human's single live reply authorizes it, but only if a
mechanical check confirms the PR that actually appears matches the plan. The
repo's gates already use gate-owned predicates for this
(`src/lrh/gate_staleness.py`, `src/lrh/confirm_fixes_batch.py`); prose-only
self-checking is the weaker alternative and was rejected in the design
discussion.

Evidence for the allowed path set: the two previous closeout PRs (#675, #679)
touched exactly `project/config/chain-defaults.yaml`,
`project/executions/AD_HOC/*` and `project/sessions/index.jsonl`.

This is a design constraint, not an autopilot tier:
`src/lrh/confirm_fixes_batch.py` states that the merge gate stays
"categorically excluded from any autopilot tier". The verifier only decides
whether a plan the human already authorized still holds; it never authorizes
anything.

Prior art check:

- **Duplication:** none. `gate_staleness.py` and `confirm_fixes_batch.py` are
  different predicates; no existing command inspects a PR's diff against an
  allowed path set.
- **Demand:** no existing work item requests this; it arises from the
  closeout-PR design in `WI-LRH-LAND-WORDING-AND-CLOSEOUT-PR`.

## Scope

- One pure conformance predicate plus a thin read-only CLI wrapper.
- Unit tests for the predicate; a light CLI test.

## Required Changes

- Implement the predicate and CLI as specified in the acceptance criteria.
- Keep it read-only, hermetic in tests, and free of any merge logic.
- Document the command's exit codes in its `--help` and module docstring.

## Non-Goals

- No merge, push or file edit behavior.
- No autopilot or unattended merge tier.
- No change to any skill text; skill wiring is `WI-LRH-LAND-WORDING-AND-CLOSEOUT-PR`.
- No probing of branch protection; that is `WI-LRH-BRANCH-PROTECTION-PROBE-AND-GUIDE`.

## Acceptance Criteria

- The command and exit-code contract described above.
- The allowed path set, the chain-defaults line restriction, the record-field
  match, the head-SHA lock and the mergeable/CI check.
- Read-only behavior and the module docstring statement.
- Hermetic `unittest` coverage.
- All validation commands below clean.

## Validation

- scripts/test
- scripts/lint
- scripts/format --check --diff
- lrh validate

## Risk Notes

- The allowed path set is gate-relevant; changing it later is a gate-semantics
  change and should go through the same review.
- The chain-defaults line check must be line-level, because that file's blob
  hash binds stored skip-consent.
- Command naming and CLI placement are settled at implementation; keep the
  predicate importable independent of the CLI.
