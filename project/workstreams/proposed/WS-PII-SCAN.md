---
id: WS-PII-SCAN
kind: planning_node
title: "lrh pii scan — Detection Engine Implementation"
status: proposed
stage: planned
origin: design_review
summary: Implement lrh pii scan per PROP-LRH-PII-SCAN — two-layer PII/misplaced-document detection (file-type/path heuristics, then scoped content-pattern checks) across full git history via lightweight git plumbing, with repo-configurable rules and a content-bound allowlist.
related_focus: []
related_roadmap: []
related_design:
  - project/design/proposals/proposed/lrh-pii-scan/00_proposal.md
work_items:
  - WI-PII-SCAN-RULE-TAXONOMY
  - WI-PII-SCAN-LAYER1-ENUMERATOR
  - WI-PII-SCAN-LAYER2-CONTENT
  - WI-PII-SCAN-ALLOWLIST-OUTPUT
  - WI-PII-SCAN-CLI
exit_criteria:
  - lrh pii scan is implemented, tested, and merged, wired into src/lrh/cli/main.py
  - Each work item has module-level tests under tests/pii_tests/ and CLI-dispatch tests in tests/cli_tests/pii_test.py
  - .lrh-pii.toml auto-discovery (useDefault-extendable) and .lrh-pii-allowlist (content-bound fingerprint) both function with sensible, disclosed built-in defaults
  - No OCR, ML/NLP classification, or cloud DLP dependency is introduced — detection stays local and deterministic per the proposal's Non-Goals
---

## Purpose

This workstream coordinates implementation of `lrh pii scan`, the audit-only PII/misplaced-document detector designed in `PROP-LRH-PII-SCAN`. It groups the five implementing work items — rule-taxonomy extraction, the git-plumbing path enumerator and Layer 1 detector, Layer 2 content detection, the allowlist and output schema, and CLI wiring — under one planning node so the full build stays visible from design through closeout, following the `WS-SECRETS-COMMAND` precedent for a sibling command's own graduation.

## Scope

- Extract `sensitivity.py`'s rule taxonomy into a shared module reusable by both `lrh.conversations.sensitivity` and the new detector
- Implement `lrh pii scan`'s two-layer detection engine under a new `src/lrh/pii/` package
- Wire the `pii` subcommand group into `src/lrh/cli/main.py`
- Add module and CLI test coverage for every work item
- Land each work item through the standard LRH execution lifecycle

## Prior Art Check

### Duplication search
- In-repo: No existing implementation — this workstream is the implementation of `PROP-LRH-PII-SCAN`, whose own prior-art check already found no functional overlap with `lrh secrets` or `lrh.conversations.sensitivity`.
- Sibling repos: None beyond what the proposal already surveyed (LCATS's `.gitleaks.toml`/`.pre-commit-config.yaml`, not a PII scanner).
- External libraries: None — the proposal explicitly rejected cloud DLP/ML dependencies (Non-Goals).
- Recommendation: Proceed.

### Demand search
- Work items: None found prior to this workstream's own.
- Proposals: `PROP-LRH-PII-SCAN` (this workstream's governing design) — satisfied by this workstream's creation, not a duplicate.
- Backlog: No matching entries.
- Recommendation: No action.

## Work Items

- **WI-PII-SCAN-RULE-TAXONOMY** — Extract `sensitivity.py`'s `_Rule`/category/severity/confidence dataclasses and regex table into `src/lrh/shared/sensitivity_rules.py`; refactor `lrh.conversations.sensitivity` to import from it (behavior-preserving, own test coverage). No dependencies.
- **WI-PII-SCAN-LAYER1-ENUMERATOR** — Implement the git-plumbing-based path enumerator (every path ever added across all refs, plus every commit touching a flagged path per the proposal's Decision 3 revision) and the Layer 1 file-type/path/filename detector, with `.lrh-pii.toml` auto-discovery and disclosed defaults. No dependencies.
- **WI-PII-SCAN-LAYER2-CONTENT** — Implement Layer 2 content-pattern detection, scoped to Layer-1-flagged files by default with the opt-in `content_scan_scope: "all-text"` config (Decision 2 revision), reusing the extracted rule taxonomy and `lrh.conversations.pdf_import`'s non-OCR PDF text extraction. Depends on `WI-PII-SCAN-RULE-TAXONOMY`, `WI-PII-SCAN-LAYER1-ENUMERATOR`.
- **WI-PII-SCAN-ALLOWLIST-OUTPUT** — Implement the `.lrh-pii-allowlist` mechanism with the content-bound fingerprint (Decision 6 revision) and the `pii_findings.json`/text-summary output with the revised schema (`commit`, `content_digest` fields — Decision 7 revision). Depends on `WI-PII-SCAN-LAYER1-ENUMERATOR`, `WI-PII-SCAN-LAYER2-CONTENT`.
- **WI-PII-SCAN-CLI** — Wire `lrh pii scan --project-root --out-dir --config` into `src/lrh/cli/main.py`, following the `lrh secrets` nested-group dispatch precedent. Depends on all four above.

## Exit Criteria

- All five work items implemented, tested, and merged to `main`
- `lrh validate` passes with 0 errors after each work item lands
- `tests/pii_tests/` (hermetic) and `tests/cli_tests/pii_test.py` exist and pass
- `.lrh-pii.toml`/`.lrh-pii-allowlist` auto-discovery works with disclosed, reviewable defaults — not claimed-complete
- Output explicitly discloses known detection gaps (no OCR, no ML/NLP classification) in the tool's own text output, not only in documentation

## Non-Goals

- Does not implement a purge/remediation subcommand — carried forward from the proposal's own Non-Goals.
- Does not implement OCR, ML/NLP content classification, or any cloud DLP integration.
- Does not wire `lrh pii scan` into pre-commit hooks or CI for any repo.
- Does not implement `project_bootstrap` tier placement for the CLI tool itself — the companion doc already landed in `PROP-LRH-PII-SCAN`'s PR; tier wiring for the tool is a separate, later decision if pursued.
- Does not revisit any of `PROP-LRH-PII-SCAN`'s Open Questions (full-history-vs-working-tree scope was already resolved as full-history in the proposal; allowlist auditability and the filename-keyword default list are scoped into `WI-PII-SCAN-ALLOWLIST-OUTPUT` and `WI-PII-SCAN-LAYER1-ENUMERATOR` respectively, not reopened here).

## Relationship to Design

- Design proposal: `project/design/proposals/proposed/lrh-pii-scan/00_proposal.md`
- Sibling graduation precedent: `project/workstreams/resolved/WS-SECRETS-COMMAND.md`
