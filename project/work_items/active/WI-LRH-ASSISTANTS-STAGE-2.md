---
resolution: null
blocked_reason: >
  Sequenced behind PROP-LRH-SESSION-ARCHIVE-SYNC (session-ID mapping and
  durable transcript archive/reconciler) and the broader execution-tree /
  session-tracking work landing first. WS-LRH-ASSISTANTS' gate now covers
  Stages 2-8, not only 9-10. Cannot express this as depends_on: the governing
  work items for PROP-LRH-SESSION-ARCHIVE-SYNC do not exist yet (its
  workstream is still to be created); lrh validate resolves depends_on only
  against work items that exist on main. Re-express as depends_on once those
  work items land.
blocked: true
id: WI-LRH-ASSISTANTS-STAGE-2
title: Stage 2 — Assistant typed models and loaders
type: deliverable
status: active
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-04
related_workstreams:
  - WS-LRH-ASSISTANTS
related_design:
  - project/design/proposals/adopted/lrh-assistants/00_proposal.md
depends_on:
  - WI-LRH-ASSISTANTS-STAGE-1
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - typed dataclasses Assistant, AssistantProfile, AssistantBinding and the modular profile objects (scope, policy, preferences, communication, context, review) exist in src/lrh/control
  - a loader discovers exactly project/assistants/*/assistant.md and assembles an AssistantProfile from its companion files
  - Workstream gains managed_by and the assistant contract fields, and AssistantBinding is compiled from them
  - the execution-record model gains an optional, nullable assistant_role field with no backfill of existing records, left un-enum-validated like agent
  - project/executions/README.md documents assistant_role as the canonical source; no duplicate field documentation is created elsewhere
  - an assistants_by_id index is available on the loaded project state
  - the serve-interface-steward package loads cleanly through the new loader
  - all new Python has unit tests and lrh validate stays green
required_evidence:
  - code_diff
  - lrh_validate
  - manual_review
artifacts_expected:
  - code
  - unit_tests
---

# WI-LRH-ASSISTANTS-STAGE-2 — Stage 2: Assistant typed models and loaders

## Summary

Deliver Stage 2 of `PROP-LRH-ASSISTANTS`: the typed runtime models and loaders
for the assistant artifact class introduced (docs-only) in Stage 1. This is the
first Python increment. It adds no validation rules (Stage 3), no core-state
context projection (Stage 4), and no CLI (Stage 5).

**Status: blocked.** See `blocked_reason` in the frontmatter. This work item is
filed now (rather than left unfiled) so the design decisions below are recorded
before the blocker lifts, and so `WS-LRH-ASSISTANTS` has a visible, honest leaf
instead of an implicit gap. Nothing in this work item's own scope technically
requires session tracking — the block reflects a deliberate sequencing decision
to let `PROP-LRH-SESSION-ARCHIVE-SYNC` and the execution-tree work stabilize
first, not a hard code dependency.

## Problem / Context

Stage 1 established the `project/assistants/` package convention, the token
vocabulary, and a fully worked `serve-interface-steward` package as
documentation only ([WI-LRH-ASSISTANTS-STAGE-1](WI-LRH-ASSISTANTS-STAGE-1.md),
merged in PR #418). Nothing yet parses those files into typed objects, so no
consumer can depend on them. Stage 2 makes the convention real in code, giving
later stages (validation, projection, inspection) typed models to build on.

This work item implements the resolved decisions recorded in the adopted
proposal:
- **Code layout (Q1):** the `Assistant` / `AssistantProfile` / `AssistantBinding`
  dataclasses live in `src/lrh/control` alongside `Workstream`, `WorkItem`, and
  `DesignProposal`. Assistant *behavior* and the `lrh assistant` CLI are
  deferred to a new top-level `src/lrh/assistants/` package in later stages;
  Stage 2 is models + loaders only.
- **Execution-record linkage (Q2):** the optional `assistant_role:` field is
  added now, alongside `AssistantBinding`, as an optional nullable field with no
  backfill.

Two further decisions, resolved 2026-07-25 following review from the session
that reworked the execution-record schema (`PROP-LRH-EXECUTION-SESSIONS`,
landed via PR #421):

- **`assistant_role:` is open-ended, not enum-validated** — follows the
  `agent:` precedent in `src/lrh/control/validator.py`
  (`_validate_execution_record`), which is deliberately left un-enum-validated
  because the schema is open-ended. Assistant IDs are an extensible namespaced
  set (`ASST-*`), not a fixed catalog, so the same reasoning applies. If any
  validation is added, remember `_parse_simple_yaml` strips quotes from scalars
  but not list elements (`element.strip("'\"")` needed) and to guard non-`str`
  values before pattern checks.
- **Documentation location: `project/executions/README.md` is canonical** for
  execution-record optional fields. Add `assistant_role:` there (grammar +
  worked example, alongside `agent`/`instruction_source`/`session_transcript`);
  do not create a fourth copy of the field documentation. `PROMPTS.md` and the
  `lrh-implement` skill reference should point at the README, not restate it.

Prior-art check: no assistant models exist in `src/lrh/control/models.py` today;
the similarly named `src/lrh/assist/` package is the unrelated request /
run-packet tooling. No duplication.

## Scope

In scope:
- Dataclasses in `src/lrh/control/models.py`: `Assistant`, `AssistantScope`,
  `AssistantPolicy`, `AssistantPreferences`, `AssistantCommunicationPolicy`,
  `AssistantContextPolicy`, `AssistantReviewPolicy`, `AssistantProfile`,
  `AssistantBinding`.
- Loader support (in `src/lrh/control/loader.py`) that discovers
  `project/assistants/*/assistant.md`, parses the companion files, and assembles
  an `AssistantProfile`; plus an `assistants_by_id` index on the loaded state.
- `Workstream` gains `managed_by` and the assistant contract fields
  (`assistant_contract`, `assistant_escalates_on`, `assistant_reports_on`,
  `assistant_cadence_mode`); `AssistantBinding` is compiled from them, so
  downstream consumers depend on the binding rather than raw workstream fields.
- The execution-record model gains an optional, nullable `assistant_role`
  field; existing records without it remain valid (no backfill).
- Unit tests for every new model, loader path, and the binding compilation,
  including loading the `serve-interface-steward` package.

Out of scope (later stages):
- Validation rules for assistants, bindings, tokens, memory, path safety
  (Stage 3).
- `AssistantState` / core-state context projection and named views (Stage 4).
- `lrh assistant list | inspect | context` CLI and the `src/lrh/assistants/`
  behavior package (Stage 5+).
- Any runtime, dispatch, scheduling, or dogfood binding.

## Required Changes

Add the dataclasses and loader logic above, keeping all parsing tolerant of the
flat-frontmatter + namespaced-token convention (the parser rejects nested
mappings). Keep `assistant_role` and the new `Workstream` fields optional so
existing artifacts continue to load and validate unchanged.

## Acceptance Criteria

See the `acceptance` frontmatter. In short: the typed models and loaders exist
in `src/lrh/control`, the `serve-interface-steward` package loads into an
`AssistantProfile`, `AssistantBinding` compiles from workstream fields, the
optional `assistant_role` field is added without backfill, and all new code has
unit tests with `lrh validate` green.

## Validation

- `scripts/test` — new unit tests pass (models, loaders, binding compilation,
  worked-package load).
- `scripts/format --check` and `scripts/lint` — clean.
- `lrh validate` — 0 errors; existing artifacts still load with the new
  optional fields absent.
