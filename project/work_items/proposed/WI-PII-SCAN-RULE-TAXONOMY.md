---
resolution: null
blocked_reason: null
blocked: false
id: WI-PII-SCAN-RULE-TAXONOMY
title: Extract sensitivity.py rule taxonomy into a shared module
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-PII-SCAN
related_design:
  - project/design/proposals/proposed/lrh-pii-scan/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
acceptance:
  - src/lrh/shared/sensitivity_rules.py exists and exports the rule taxonomy
  - src/lrh/conversations/sensitivity.py imports from it and produces identical SensitiveScanResult output for the same input as before the refactor
  - tests/shared_tests/sensitivity_rules_test.py exists and passes
  - lrh validate passes with 0 errors
required_evidence:
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/shared/__init__.py
  - src/lrh/shared/sensitivity_rules.py
  - src/lrh/conversations/sensitivity.py
  - tests/shared_tests/sensitivity_rules_test.py
---

## Summary

Extract `lrh.conversations.sensitivity`'s `_Rule`/category/severity/confidence dataclasses and regex table into a new `src/lrh/shared/sensitivity_rules.py` module, and refactor `lrh.conversations.sensitivity` to import from it, as a pure, behavior-preserving extraction.

## Problem / Context

`PROP-LRH-PII-SCAN` Decision 5 calls for sharing `sensitivity.py`'s rule taxonomy (not its transcript-string runtime) with the new `lrh pii scan` command, so the two subsystems don't invent parallel definitions of "what counts as an email/SSN/IP." This item does the extraction on its own, ahead of any `lrh pii` code, so `lrh.conversations.sensitivity`'s behavior can be verified unchanged before anything new depends on the shared module.

### Duplication search
- In-repo: No existing shared-rules module. `src/lrh/conversations/sensitivity.py` currently defines the rule taxonomy inline — this item moves it, not duplicates it.
- Sibling repos: None applicable.
- External libraries: None — reuses this repo's own existing rule definitions.
- Recommendation: Proceed.

### Demand search
- Work items: None found prior to `WS-PII-SCAN`'s own creation.
- Proposals: `PROP-LRH-PII-SCAN` Decision 5 (satisfied by this item).
- Backlog: No matching entries.
- Recommendation: No action.

## Scope

- Create `src/lrh/shared/sensitivity_rules.py` containing the rule taxonomy currently defined in `src/lrh/conversations/sensitivity.py`
- Refactor `src/lrh/conversations/sensitivity.py` to import from the new shared module instead of defining rules inline
- Add test coverage for the extracted module

## Required Changes

1. Create `src/lrh/shared/__init__.py` (new package) and `src/lrh/shared/sensitivity_rules.py` with the `_Rule` dataclass, category/severity/confidence constants, and the full regex rule table (`_BASIC_RULES`, `_SECRET_ASSIGNMENT_PATTERN`, `_IP_ADDRESS_PATTERN`, `_CREDIT_CARD_CANDIDATE_PATTERN`, Luhn/IPv4 validators) moved verbatim from `src/lrh/conversations/sensitivity.py`.
2. Update `src/lrh/conversations/sensitivity.py` to import the rule table/dataclasses from `src/lrh/shared/sensitivity_rules.py` instead of defining them inline; `scan_text_for_sensitive_findings` and its helpers keep their current signatures and behavior unchanged.
3. Add `tests/shared_tests/sensitivity_rules_test.py` covering the extracted module directly.
4. Confirm the existing `sensitivity.py` test suite still passes unmodified against the refactored module, proving the extraction is behavior-preserving.

## Non-Goals

- Does not change any detection behavior, rule definitions, or output shape of `lrh.conversations.sensitivity` — this is a pure extraction.
- Does not implement any part of `lrh pii scan` itself — that's `WI-PII-SCAN-LAYER1-ENUMERATOR` and later items.
- Does not add new rule categories or tune existing regexes.

## Acceptance Criteria

- `src/lrh/shared/sensitivity_rules.py` exists and exports the rule taxonomy.
- `src/lrh/conversations/sensitivity.py` imports from it and produces identical `SensitiveScanResult` output for the same input as before the refactor.
- `tests/shared_tests/sensitivity_rules_test.py` exists and passes.
- `lrh validate` passes with 0 errors.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-PII-SCAN.md`
- Design: `project/design/proposals/proposed/lrh-pii-scan/00_proposal.md`
