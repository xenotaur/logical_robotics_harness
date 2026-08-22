---
resolution: null
blocked_reason: null
blocked: false
id: WI-PII-SCAN-ALLOWLIST-OUTPUT
title: Implement content-bound allowlist and pii_findings.json output
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
depends_on:
  - WI-PII-SCAN-LAYER1-ENUMERATOR
  - WI-PII-SCAN-LAYER2-CONTENT
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
  - .lrh-pii-allowlist correctly suppresses a previously-approved (path, rule_id, content_digest) finding
  - .lrh-pii-allowlist does not suppress a new finding at the same path/rule when content_digest differs
  - pii_findings.json matches the revised schema and the printed text summary includes the disclosure block
  - tests/pii_tests/allowlist_test.py and tests/pii_tests/output_test.py exist and pass
  - lrh validate passes with 0 errors
required_evidence:
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/pii/allowlist.py
  - src/lrh/pii/output.py
  - tests/pii_tests/allowlist_test.py
  - tests/pii_tests/output_test.py
---

## Summary

Implement `lrh pii scan`'s `.lrh-pii-allowlist` mechanism with a content-bound fingerprint (`sha256(path + rule_id + content_digest)`) and `pii_findings.json`/text-summary output with the revised schema (`commit`, `content_digest`) per `PROP-LRH-PII-SCAN` Decisions 6 and 7.

## Problem / Context

The proposal's allowlist and output schema decisions were both revised during PR #591 review after `chatgpt-codex-connector` found that a location-only fingerprint (`sha256(path + rule_id)`) would let one approved benign match silently suppress a later, genuinely sensitive value at the same path/rule. This item implements the corrected, content-bound design, and depends on both prior layers since a finding's `content_digest` and shape come from whichever layer produced it.

### Duplication search
- In-repo: `lrh secrets review`'s decisions-file/marker-gate model is a related but deliberately heavier mechanism — not reused here, since there is no purge step in v1 to gate (Decision 6). No existing lighter allowlist mechanism exists in this repo to reuse instead.
- Sibling repos: LCATS's `.gitleaksignore`-style convention is the pattern this item follows, not a duplicate.
- External libraries: None.
- Recommendation: Proceed.

### Demand search
- Work items: None found prior to `WS-PII-SCAN`'s own creation.
- Proposals: `PROP-LRH-PII-SCAN` Decisions 6 and 7 (satisfied by this item).
- Backlog: No matching entries.
- Recommendation: No action.

## Scope

- Implement the allowlist file format and content-bound fingerprint
- Implement structured JSON output and human-readable text summary

## Required Changes

1. Create `src/lrh/pii/allowlist.py` implementing a repo-committed, auto-discovered `.lrh-pii-allowlist` file, fingerprint-keyed by `sha256(path + rule_id + content_digest)` (git blob SHA for a Layer 1 match, hash of the matched substring for a Layer 2 match), with an optional reason comment, `.gitleaksignore`-style.
2. Create `src/lrh/pii/output.py` implementing `pii_findings.json` as a list of `{path, rule_id, category, severity, confidence, commit, content_digest, still_in_working_tree, matched_layer}` plus a text summary ending in a disclosure block (no OCR, no ML/NLP classification, heuristic only), consuming Layer 1/Layer 2 findings and filtering allowlisted ones.
3. Add `tests/pii_tests/allowlist_test.py` and `tests/pii_tests/output_test.py`, including a fixture proving that a content change at an allowlisted path/rule produces a fresh (non-suppressed) finding.

## Non-Goals

- Does not implement any purge/remediation path for allowlisted or non-allowlisted findings.
- Does not implement the review/decisions-file ceremony `lrh secrets review` uses — this is the deliberately lighter mechanism per Decision 6.

## Acceptance Criteria

- `.lrh-pii-allowlist` correctly suppresses a previously-approved `(path, rule_id, content_digest)` finding.
- `.lrh-pii-allowlist` does not suppress a new finding at the same path/rule when `content_digest` differs.
- `pii_findings.json` matches the revised schema and the printed text summary includes the disclosure block.
- `tests/pii_tests/allowlist_test.py` and `tests/pii_tests/output_test.py` exist and pass.
- `lrh validate` passes with 0 errors.

## Dependencies / Order

Depends on `WI-PII-SCAN-LAYER1-ENUMERATOR` and `WI-PII-SCAN-LAYER2-CONTENT` — the allowlist fingerprint and output schema both need real finding shapes (including `content_digest`) from both layers to test against meaningfully.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-PII-SCAN.md`
- Design: `project/design/proposals/proposed/lrh-pii-scan/00_proposal.md`
