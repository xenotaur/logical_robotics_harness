---
id: WI-SKILLS-PLANNING-ID-PROPOSAL
title: Make lrh-work-item, lrh-proposal, and lrh-workstream propose IDs instead of requiring them
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design:
  - project/memory/decisions/DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - add_cli_command
  - write_docs
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - auto_allocate_id_without_model_proposal
  - change_step5_confirmation_gate
  - modify_prompt_slug_idempotence_mechanism
acceptance:
  - lrh-work-item, lrh-proposal, and lrh-workstream Inputs sections make the ID/slug argument optional
  - each skill gains a pre-Step-1 sequence that classifies scope, researches, and proposes a candidate ID/slug before any existing-item check runs
  - a new deterministic CLI check (e.g. lrh work-items check-id, lrh workstreams check-id, an equivalent for proposals) replaces each skill's inlined find as the collision check, searching local buckets and open PRs (including forks)
  - each new CLI check has unit tests covering no-match, local-match, and cross-PR-match cases
  - the existing Step 5 confirmation gate is unchanged - the proposed ID is shown and confirmed before any write, exactly as a user-supplied ID is today
  - both SKILL.md mirrors (src/lrh/skills and .claude/skills) are updated identically for all three migrated skills, verified by diff -r
  - lrh validate passes with 0 errors and the full test suite passes
required_evidence:
  - code_diff
  - unit_tests
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-work-item/SKILL.md
  - .claude/skills/lrh-work-item/SKILL.md
  - src/lrh/skills/lrh-proposal/SKILL.md
  - .claude/skills/lrh-proposal/SKILL.md
  - src/lrh/skills/lrh-workstream/SKILL.md
  - .claude/skills/lrh-workstream/SKILL.md
  - src/lrh/cli/main.py
  - tests/ (new test module(s) for the candidate-ID check command(s))
blocked: false
blocked_reason: null
resolution: null
---

# Make lrh-work-item, lrh-proposal, and lrh-workstream propose IDs instead of requiring them

## Summary

`lrh-work-item`, `lrh-proposal`, and `lrh-workstream` each currently require
the user to supply a `WI-*`/`WS-*`/slug identifier as an argument before the
skill will proceed ([SKILL.md:31-38](../../../src/lrh/skills/lrh-work-item/SKILL.md),
and the identical pattern in `lrh-proposal`/`lrh-workstream`). This work item
makes the identifier optional: the agent classifies the requested scope,
researches existing conventions, proposes a collision-checked candidate ID,
and presents it at the existing confirmation gate - the same behavior Claude
has apparently been defaulting to already, now made explicit, reliable, and
uniform across agents instead of resting on prose compliance.

## Problem / Context

Investigation grounded directly against the repo established:

- The "ask for the ID if missing" instruction has been present since the
  skill's first commit (`5f85fcb9`, 2026-06-23) in all three planning
  skills - not a recent regression, and not caused by stale installs
  (`diff`'d canonical source against the live global installs both Claude
  and Codex load; the Inputs-section text is byte-identical in all copies).
- Claude has historically not followed that instruction literally - it
  proposes a scope-derived ID rather than asking. Codex followed the
  written contract exactly as phrased. The observed "regression" was
  inconsistent compliance with an instruction that was always there, not a
  broken or drifted skill.
- Formalizing Claude's observed behavior as prose alone reproduces the same
  reliability problem just diagnosed - prose compliance is exactly what
  varied between agents. The decisive option is a deterministic CLI
  collision check, reusing the architecture this codebase already
  validated once for a sibling problem:
  `project/memory/decisions/DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT.md` and
  `WI-SLUG-IDEMPOTENCE-CLI-TOOLING`'s `lrh prompt check-execution --slug`,
  which searches the local checkout **and open PRs (including forks)** via
  `refs/pull/<N>/head` rather than trusting an inlined `find`.
- `lrh work-items validate` already flags duplicate frontmatter IDs
  project-wide (`src/lrh/work_items/validate.py:229-240`), but only after a
  file is written - a necessary backstop, not a substitute for a pre-write
  check.
- No ID-allocation or candidate-naming logic exists anywhere in the
  codebase today (checked `references/work-item-schema.md` and grepped for
  `next-id`/allocator commands - none found).

Prior-art check performed 2026-09-22:

- **Duplication search:** No existing work item covers this.
  `WI-SLUG-IDEMPOTENCE-CLI-TOOLING` (active) is architecturally adjacent -
  it replaces inlined shell (`find`/`gh pr list`/`merge-base`) with a
  tested `lrh prompt check-execution --slug` CLI command - but it checks
  for a **prior execution record** (has this task already run), not
  whether a **candidate planning-artifact ID already exists**
  (`project/work_items/`, `project/workstreams/`,
  `project/design/proposals/`). Different question, same architecture. Not
  a duplicate, but it is active and touches the same three `SKILL.md`
  files (its own Step 4, not this item's Inputs/Step 1) - see Risk Notes.
  Verdict: no duplicate.
- **Demand search:** No prior work item, proposal, or backlog entry
  requests this. Demand is this conversation's own finding (a Codex vs.
  Claude instruction-compliance divergence on the ID-required contract).
  No existing WI/proposal to close or link.

## Scope

Replace each skill's local-only `find` existing-item check with a two-part
flow: (1) the agent proposes a semantically meaningful candidate ID/slug
from the researched scope - unchanged from what the model already does
well in Step 2/3 of each skill - and (2) a new deterministic `lrh` command
verifies the candidate is actually free, checking local status-bucket
directories and open PRs. The existing `lrh work-items`/`lrh workstreams`
CLI groups already exist (`src/lrh/cli/main.py:358`,
`src/lrh/cli/main.py:746`); a `proposals`-scoped equivalent does not yet
exist and will need to be added or folded into an adjacent group.

Explicitly not in scope: an algorithm that invents the ID from a title
without model involvement (a fully automated allocator was evaluated and
disqualified in the design discussion preceding this work item - good
WI/WS names are a summarization judgment call, not a string transform),
and any change to `WI-SLUG-IDEMPOTENCE-CLI-TOOLING`'s own mechanism or to
the Step 5 confirmation gate in any of the three skills.

## Required Changes

- `lrh-work-item`, `lrh-proposal`, `lrh-workstream` Inputs sections: make
  the ID/slug an optional argument.
- Insert a step before each skill's existing "Check for existing X" step
  that: classifies the requested scope, runs the skill's existing
  research/prior-art steps, proposes a candidate ID/slug, and calls the
  new CLI check.
- Add the new collision-check CLI surface: extend `lrh work-items` and
  `lrh workstreams` with a `check-id` (or similarly named) subcommand; add
  an equivalent for proposals (new `proposals` subparser group or an
  existing adjacent one). Each checks local status buckets plus open PRs
  (including forks) for a colliding ID/slug.
- Add unit tests for each new check command: no match, local match,
  cross-PR match.
- Update both `SKILL.md` mirrors (`src/lrh/skills/` and `.claude/skills/`)
  identically for all three skills.
- Leave the Step 5 confirmation gate, and everything downstream of it
  (branch creation, write, validate, PR, execution record), unchanged -
  this work item only changes how the ID reaches that gate.

## Non-Goals

- No fully automated ID allocation from a title with no model involvement.
- No change to `WI-SLUG-IDEMPOTENCE-CLI-TOOLING`'s prompt-slug idempotence
  mechanism, scope, or the `lrh-review-response`/`lrh-confirm-fixes`
  skills it also touches.
- No change to the Step 5 confirmation gate's behavior or placement in any
  of the three skills.
- No change to `lrh work-items validate`'s existing post-write duplicate-ID
  detection - it remains the backstop, unmodified.

## Acceptance Criteria

- `lrh-work-item`, `lrh-proposal`, and `lrh-workstream` Inputs sections
  make the ID/slug argument optional.
- Each skill gains a pre-Step-1 sequence that classifies scope, researches,
  and proposes a candidate ID/slug before any existing-item check runs.
- A new deterministic CLI check replaces each skill's inlined `find` as the
  collision check, searching local buckets and open PRs (including forks).
- Each new CLI check has unit tests covering no-match, local-match, and
  cross-PR-match cases.
- The existing Step 5 confirmation gate is unchanged - the proposed ID is
  shown and confirmed before any write, exactly as a user-supplied ID is
  today.
- Both `SKILL.md` mirrors are updated identically for all three migrated
  skills, verified by `diff -r`.
- `lrh validate` passes with 0 errors and the full test suite passes.

## Validation

- `pytest` on the new CLI check command's test module(s), plus the full
  existing suite.
- `diff -r src/lrh/skills/<skill> .claude/skills/<skill>` exits 0 for all
  three migrated skills.
- `lrh validate` reports 0 errors.
- Manual dogfood: invoke each migrated skill with no ID/slug argument and
  confirm it proposes a candidate, checks it, and stops at the same Step 5
  gate a user-supplied ID would reach.

## Risk Notes

Coordination risk with `WI-SLUG-IDEMPOTENCE-CLI-TOOLING`, currently active
and touching the same three `SKILL.md` files (its own Step 4, not this
item's Inputs/Step 1) - sequence or rebase carefully to avoid merge
conflicts on the same files; this is a file-overlap risk, not a scope
conflict. Per the pattern that produced roughly 18 combined review rounds
across the three PRs that built the slug-idempotence mechanism (per that
work item's own Risk Notes), keep this bounded to the collision-check and
prose changes specified above; if new edge cases surface mid-implementation,
file them as follow-up rather than expanding scope in-flight.
