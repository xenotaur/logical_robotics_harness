---
resolution: null
blocked_reason: null
blocked: false
id: WI-LRH-ASSISTANTS-STAGE-1
title: Stage 1 — Assistant docs-only package convention
type: deliverable
status: proposed
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
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - project/assistants/README.md documents the artifact class, read order, what is authoritative, and where live state lives
  - one fully worked assistant package (serve-interface-steward) exists with all canonical companion files
  - an authoritative markdown token vocabulary lists the legal capability, permission, obligation, prohibition, and escalation tokens
  - no Python, runtime behavior, launching, monitoring, scheduling, or run mutation is introduced
  - the worked package uses flat frontmatter and namespaced string tokens only (no nested frontmatter mappings)
required_evidence:
  - manual_review
artifacts_expected:
  - documentation
---

# WI-LRH-ASSISTANTS-STAGE-1 — Stage 1: Assistant docs-only package convention

## Summary

Deliver Stage 1 of `PROP-LRH-ASSISTANTS`: the documentation-only
`project/assistants/` package convention. This establishes the artifact-class
entry point, one fully worked assistant package, and the authoritative token
vocabulary — with no Python and no runtime authority.

## Problem / Context

The adopted design
([`PROP-LRH-ASSISTANTS`](../../design/proposals/adopted/lrh-assistants/00_proposal.md))
introduces the assistant as a persistent, backend-neutral organizational role.
Its staged plan begins with a docs-only convention so the package shape and
policy-token vocabulary can be reviewed and dogfooded before any typed models,
validation, or CLI are built. Decision 9 of the proposal requires the token
vocabulary to ship with the convention (a template without its catalog is
inert); this work item delivers the markdown vocabulary now, leaving the
Python validating catalog to Stage 3.

Prior-art check: no existing `project/assistants/` convention exists. The
similarly named `src/lrh/assist/` package is the unrelated request / run-packet
tooling. No duplication; no open demand item beyond this workstream.

## Scope

In scope:
- `project/assistants/README.md` — artifact-class entry point.
- `project/assistants/token-vocabulary.md` — authoritative token catalog
  (markdown).
- `project/assistants/serve-interface-steward/` — one fully worked package:
  `README.md`, `assistant.md`, `scope.md`, `policy.md`, `preferences.md`,
  `communication-policy.md`, `context-policy.md`, `review-policy.md`,
  `SKILL.md`, plus `references/`, `memory/`, and `evaluations/` scaffolds.

Out of scope (later stages):
- Typed models, loaders, validation, CLI (Stages 2–5).
- The `assistant_role:` execution-record field (Stage 2).
- Communication rendering, memory tooling, evaluations harness (Stages 6–7).
- Any runtime, dogfood binding, or scheduling (Stages 8–10).

## Required Changes

Create the files listed in Scope, modeling frontmatter and body on the worked
examples in the adopted proposal. All frontmatter must be flat (scalars, block
lists, and namespaced string tokens only) because the LRH parser rejects nested
mappings.

## Acceptance Criteria

See the `acceptance` frontmatter. In short: the entry point, one complete
worked package, and the token vocabulary all exist; no Python or runtime
behavior is introduced; and every companion file is parser-safe.

## Validation

- `lrh validate` — 0 errors (the new `project/assistants/` tree is
  documentation and must not break control-plane validation).
- `lrh work-items validate` — this work item resolves cleanly.
- Manual review that the worked package is internally self-consistent and
  usable as the template Stage 2 will validate against.
