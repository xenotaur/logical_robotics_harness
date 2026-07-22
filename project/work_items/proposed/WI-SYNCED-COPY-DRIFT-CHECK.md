---
resolution: null
blocked_reason: null
blocked: false
id: WI-SYNCED-COPY-DRIFT-CHECK
title: Add mechanical drift-check for manually-synced template/doc copy pairs
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
  - project/design/backlog.md
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - implement_target_agent_publication_guidance
  - modify_ci_pipeline
acceptance:
  - lrh validate includes a new rule that diffs each registered synced-copy pair and reports a finding on unauthorized drift
  - The rule covers both known pairs — src/lrh/skills/_shared/prior-art-check.md vs its 5 skill copies, and src/lrh/assist/templates/request/review_response.md vs review_protocol.md — with normalization for known variable-placeholder differences
  - The existing header-wording drift between review_response.md and review_protocol.md is reconciled so the new check passes cleanly against current repo state
  - scripts/test passes, including a test that injects a synthetic divergence into a copy pair and confirms the check fails
  - lrh validate reports 0 errors after implementation
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/control/validator.py (or a new src/lrh/control/synced_copies.py module)
  - src/lrh/assist/templates/request/review_response.md (header reconciliation)
  - src/lrh/assist/templates/request/review_protocol.md (header reconciliation)
  - tests covering the new drift-check rule
---

## Summary

Add a mechanical `lrh validate` check that diffs each of a registered set of
manually-synced copy pairs and fails when their content drifts beyond an
allowed normalization — replacing reliance on comment-only "keep these in
sync" conventions with an enforced invariant.

## Problem / Context

Two independent copy-pair families in this repo are kept in sync by human
convention rather than mechanically: (1) `src/lrh/skills/_shared/prior-art-check.md`,
mirrored into 5 skills' `references/prior-art-check.md` via a header comment
naming the master; and (2) `src/lrh/assist/templates/request/review_response.md`
vs `review_protocol.md`, mirrored via a "Sync note." A 2026-07-22 `/lrh-design`
review of the backlog entry "Agent-specific publication guidance for
`review_response`/`review_protocol`" found that pair 2 had already drifted in
section-header wording (`## 1) Triage` vs `## 1) Triage each reported comment/issue`,
and similarly for sections 4 and 5) within the same PR (#405) that introduced
both copies' shared content — harmless so far, but a real instance of the
failure mode the sibling backlog entry "Validator drift-check for synced
skill references" was waiting to observe before graduating. See
`project/design/backlog.md` for both entries.

### Duplication search
- In-repo: No existing implementation found. No drift-check logic exists in
  `src/lrh/control/validator.py` or elsewhere; the only mechanism today is
  the header-comment convention in `prior-art-check.md` copies and the
  "Sync note" in `review_protocol.md`.
- Sibling repos: None identified.
- External libraries: None identified — this is a small, repo-specific
  structural check, not a general-purpose doc-drift tool.
- Recommendation: Proceed.

### Demand search
- Work items: None found.
- Proposals: None found.
- Backlog: Found: "Validator drift-check for synced skill references"
  (`project/design/backlog.md`) — this work item is the intended
  graduation of that entry, now that its revisit trigger has fired.
- Recommendation: Offer to cross-reference that backlog entry to this work
  item once created (not close it outright — leave it as the historical
  record).

## Scope

- Add a mechanical drift-check to `lrh validate` for the two known
  manually-synced copy-pair families in this repo.
- Reconcile the currently-known drift (header wording) so the new check
  starts clean.
- Do not add new templating/include machinery to eliminate the duplication
  itself — this only detects and enforces against drift.

## Required Changes

1. Add a drift-check rule to `src/lrh/control/validator.py` (or a small new
   module, e.g. `src/lrh/control/synced_copies.py`), with a registry of
   copy-pairs to check.
2. Register pair 1: `src/lrh/skills/_shared/prior-art-check.md` vs each of
   its 5 `references/prior-art-check.md` copies (`lrh-design`,
   `lrh-implement`, `lrh-proposal`, `lrh-work-item`, `lrh-workstream`).
3. Register pair 2: `src/lrh/assist/templates/request/review_response.md`
   vs `review_protocol.md`, with normalization for known variable-placeholder
   differences (`{{REVIEW_URL}}` vs `<pr-url>`, `{{REPO_NAME}}` vs "the base
   repository", etc.).
4. Reconcile the existing header-wording drift between `review_response.md`
   and `review_protocol.md` so the new check passes cleanly at merge time.
5. Add unit tests exercising both the pass case and a synthetic-drift
   failure case.
6. Update the header comment in `prior-art-check.md` copies and the "Sync
   note" in `review_protocol.md` to reference the new mechanical check.

## Non-Goals

- Do not implement the `--target-agent`/injected publication-guidance
  mechanism (Force B in the design review) — that stays deferred in
  `project/design/backlog.md`.
- Do not introduce a template "include" mechanism to de-duplicate content —
  this work item only detects and enforces against drift; it does not
  eliminate the manual double-edit.
- Do not rewrite protocol substance beyond what's needed to make the two
  files byte-comparable (e.g. reconciling header wording).

## Acceptance Criteria

- `lrh validate` includes a new rule that diffs each registered synced-copy
  pair and reports a finding on unauthorized drift.
- The rule covers both known pairs, with normalization for known
  variable-placeholder differences.
- The existing header-wording drift between `review_response.md` and
  `review_protocol.md` is reconciled so the check passes cleanly against
  current repo state.
- `scripts/test` passes, including a test that injects a synthetic
  divergence and confirms the check fails.
- `lrh validate` reports 0 errors after implementation.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
