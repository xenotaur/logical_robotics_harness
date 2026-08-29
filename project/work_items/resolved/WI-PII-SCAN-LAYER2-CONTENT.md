---
resolution: "Implemented and merged in PR #646 (commit f3331f9d)."
blocked_reason: null
blocked: false
id: WI-PII-SCAN-LAYER2-CONTENT
title: Implement Layer 2 scoped content-pattern detection
type: deliverable
status: resolved
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
  - WI-PII-SCAN-RULE-TAXONOMY
  - WI-PII-SCAN-LAYER1-ENUMERATOR
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
  - Layer 2 correctly detects rule-table matches inside Layer-1-flagged files' content under the default content_scan_scope
  - Layer 2 correctly extends detection to ordinary (non-flagged) text files only when content_scan_scope is set to all-text
  - PDF text extraction reuses lrh.conversations.pdf_import without duplicating its parsing logic
  - tests/pii_tests/layer2_test.py exists and passes
  - lrh validate passes with 0 errors
required_evidence:
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/pii/layer2.py
  - src/lrh/pii/config.py
  - tests/pii_tests/layer2_test.py
---

## Summary

Implement `lrh pii scan`'s Layer 2 text-pattern content detection, scoped by default to Layer-1-flagged files with an opt-in `content_scan_scope: "all-text"` config, reusing the extracted rule taxonomy and the existing non-OCR PDF text extractor.

## Problem / Context

`PROP-LRH-PII-SCAN` Decision 2 (as revised during PR #591 review) scopes Layer 2 to Layer-1-flagged files by default to avoid false-positiving on legitimate content like a contributor's email in `CODEOWNERS`, while adding an opt-in `content_scan_scope: "all-text"` so a repo can trade precision for recall on ordinary-file PII. This item depends on the shared rule taxonomy (`WI-PII-SCAN-RULE-TAXONOMY`) and the path/commit enumeration plus flagged-file set (`WI-PII-SCAN-LAYER1-ENUMERATOR`).

### Duplication search
- In-repo: No existing content-pattern detector scoped this way. `lrh.conversations.sensitivity` runs its regex rules unconditionally across a transcript string, with no file-type/path scoping concept at all.
- Sibling repos: None applicable.
- External libraries: None.
- Recommendation: Proceed.

### Demand search
- Work items: None found prior to `WS-PII-SCAN`'s own creation.
- Proposals: `PROP-LRH-PII-SCAN` Decision 2 revision (satisfied by this item).
- Backlog: No matching entries.
- Recommendation: No action.

## Scope

- Create the Layer 2 content detector module
- Wire the `content_scan_scope` config option into `.lrh-pii.toml`
- Reuse `lrh.conversations.pdf_import`'s PDF text extraction and the shared rule taxonomy

## Required Changes

1. Create `src/lrh/pii/layer2.py` implementing content-pattern detection using `src/lrh/shared/sensitivity_rules.py`'s rule table, run by default only against files `src/lrh/pii/layer1.py` already flagged, fetching content per the per-commit enumeration from `WI-PII-SCAN-LAYER1-ENUMERATOR` (`git show <commit>:<path>`).
2. Extend `src/lrh/pii/config.py` with the `content_scan_scope` setting (`"flagged"` default, `"all-text"` opt-in) per `PROP-LRH-PII-SCAN` Decision 2's revision.
3. **When `content_scan_scope` is `"all-text"`, request per-commit enumeration for every text path from `WI-PII-SCAN-LAYER1-ENUMERATOR`'s enumerator (its path-set parameter, not just Layer-1-flagged paths) — not only the working-tree-current content of each file.** Per PR #596 review (`chatgpt-codex-connector` P1): without this, a text file added benign, later modified to add PII, then subsequently cleaned or deleted, has no revision stream for Layer 2 to scan in `"all-text"` mode, contradicting the full-history scope the rest of the design claims.
4. Integrate `src/lrh/conversations/pdf_import.py`'s existing non-OCR PDF text extraction for PDF files reached by either scan scope; plain-text files are read directly; other binary formats are skipped with a disclosed gap.
5. Add `tests/pii_tests/layer2_test.py` covering both `content_scan_scope` values, including: a fixture proving a flagged-file email match is caught; a fixture proving an ordinary-file (unflagged path) email match is only caught under `"all-text"`; and a modify-after-add fixture proving that in `"all-text"` mode, PII added to an ordinary text file in a commit *after* its initial (benign) add is detected — not just current-content or add-commit-only detection.

## Non-Goals

- Does not implement OCR for scanned-image PDFs or other image formats.
- Does not implement ML/NLP-based content classification.
- Does not implement the allowlist or output schema — that's `WI-PII-SCAN-ALLOWLIST-OUTPUT`.

## Acceptance Criteria

- Layer 2 correctly detects rule-table matches inside Layer-1-flagged files' content under the default `content_scan_scope`.
- Layer 2 correctly extends detection to ordinary (non-flagged) text files only when `content_scan_scope: "all-text"` is set.
- Under `content_scan_scope: "all-text"`, Layer 2 detects PII added to an ordinary text file in a commit after its initial add, using per-commit enumeration for every text path, not only each file's current working-tree content.
- PDF text extraction reuses `lrh.conversations.pdf_import` without duplicating its parsing logic.
- `tests/pii_tests/layer2_test.py` exists and passes.
- `lrh validate` passes with 0 errors.

## Dependencies / Order

Depends on `WI-PII-SCAN-RULE-TAXONOMY` for the shared rule table and `WI-PII-SCAN-LAYER1-ENUMERATOR` for the flagged-file set and per-commit content-fetch enumeration. Should not start until both are merged, since Layer 2's own test fixtures need real flagged-path data to scope against.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-PII-SCAN.md`
- Design: `project/design/proposals/proposed/lrh-pii-scan/00_proposal.md`
