---
resolution: "Implemented and merged in PR #616 (commit 923d9c26)."
blocked_reason: null
blocked: false
id: WI-PII-SCAN-LAYER1-ENUMERATOR
title: Implement git-plumbing path enumerator and Layer 1 file-type/path detector
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
  - src/lrh/pii/enumerate.py correctly enumerates every path ever added across all refs in a test fixture repo, including every commit touching a Layer-1-flagged path
  - src/lrh/pii/config.py correctly auto-discovers .lrh-pii.toml and extends built-in defaults per the useDefault convention
  - src/lrh/pii/layer1.py correctly flags fixture files matching built-in default rules and does not flag fixture files that should not match
  - tests/pii_tests/enumerate_test.py and tests/pii_tests/layer1_test.py exist and pass, including a rename/merge fixture case
  - lrh validate passes with 0 errors
required_evidence:
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/pii/__init__.py
  - src/lrh/pii/enumerate.py
  - src/lrh/pii/config.py
  - src/lrh/pii/layer1.py
  - tests/pii_tests/enumerate_test.py
  - tests/pii_tests/layer1_test.py
---

## Summary

Implement `lrh.pii`'s git-plumbing-based full-history path enumerator and the Layer 1 file-type/path/filename heuristic detector, with `.lrh-pii.toml` auto-discovery and disclosed built-in defaults.

## Problem / Context

`PROP-LRH-PII-SCAN` Decisions 3 and 4 specify full-history coverage via lightweight git plumbing (not a bespoke blob-walker) and a repo-configurable `.lrh-pii.toml` rule file extending disclosed defaults. This is the largest, most novel build in the workstream — no equivalent engine exists in this repo (`lrh secrets` wraps `gitleaks` for this; `lrh.conversations.sensitivity` has no git-awareness at all).

### Duplication search
- In-repo: No existing git-history-walking or file-type/path classification code for this purpose. `lrh secrets scan` shells out to `gitleaks` for a related but distinct (credential-only, blob-content) problem.
- Sibling repos: LCATS's `.gitleaks.toml` is prior art for the config-file auto-discovery convention, not for path enumeration.
- External libraries: None — uses git's own plumbing commands directly, per the proposal's explicit choice to avoid a bespoke scanning engine.
- Recommendation: Proceed.

### Demand search
- Work items: None found prior to `WS-PII-SCAN`'s own creation.
- Proposals: `PROP-LRH-PII-SCAN` Decisions 3 and 4 (satisfied by this item).
- Backlog: No matching entries.
- Recommendation: No action.

## Scope

- Create `src/lrh/pii/` package with a history enumerator and Layer 1 detector
- Implement `.lrh-pii.toml` auto-discovery and `[extend] useDefault = true` config shape
- Add module test coverage

## Required Changes

1. Create `src/lrh/pii/__init__.py` and `src/lrh/pii/enumerate.py` implementing full-history path enumeration via `git log --all --diff-filter=A --name-only` (or equivalent `git rev-list --objects --all`), and, per every path Layer 1 flags, enumeration of every commit that touched that path (`git log --all --follow --name-only -- <path>`) per `PROP-LRH-PII-SCAN` Decision 3's revision — not only each path's add commit. Expose this per-commit enumeration as a function taking an explicit path set, not hardcoded to "Layer-1-flagged paths only" — `WI-PII-SCAN-LAYER2-CONTENT`'s `content_scan_scope: "all-text"` mode needs the same per-commit enumeration applied to every text path, not just flagged ones (PR #596 review, `chatgpt-codex-connector` P1), so the enumerator's path-set parameter is the seam that makes both callers correct without duplicating the git-plumbing logic.
2. Create `src/lrh/pii/config.py` implementing `.lrh-pii.toml` auto-discovery at `--project-root`, `[extend] useDefault = true` semantics, and the built-in default rule list (file-extension/path-glob signals and filename-keyword signals) disclosed per `PROP-LRH-PII-SCAN` Decision 4.
3. Create `src/lrh/pii/layer1.py` implementing the file-type/path/filename heuristic detector against the enumerated path set, using the config from (2).
4. Add `tests/pii_tests/enumerate_test.py` and `tests/pii_tests/layer1_test.py`, including explicit coverage of rename/merge behavior under `--diff-filter=A` per the proposal's own noted risk.

## Non-Goals

- Does not implement Layer 2 content-pattern detection — that's `WI-PII-SCAN-LAYER2-CONTENT`.
- Does not implement the allowlist or `pii_findings.json` output — that's `WI-PII-SCAN-ALLOWLIST-OUTPUT`.
- Does not wire anything into the CLI — that's `WI-PII-SCAN-CLI`.
- Does not implement OCR or content classification of any kind.

## Acceptance Criteria

- `src/lrh/pii/enumerate.py` correctly enumerates every path ever added across all refs in a test fixture repo, including every commit touching a Layer-1-flagged path.
- `src/lrh/pii/enumerate.py`'s per-commit enumeration function accepts an arbitrary path set (not hardcoded to Layer-1-flagged paths), so `WI-PII-SCAN-LAYER2-CONTENT` can request per-commit history for every text path under `content_scan_scope: "all-text"`.
- `src/lrh/pii/config.py` correctly auto-discovers `.lrh-pii.toml` and extends built-in defaults per the `useDefault` convention.
- `src/lrh/pii/layer1.py` correctly flags fixture files matching built-in default rules and correctly does not flag fixture files that shouldn't match.
- `tests/pii_tests/enumerate_test.py` and `tests/pii_tests/layer1_test.py` exist and pass, including a rename/merge fixture case.
- `lrh validate` passes with 0 errors.

## Risk Notes

- `--diff-filter=A` behavior under rename detection can under- or over-count add events depending on git's rename-similarity threshold; the fixture test must exercise a rename case explicitly, not assume the simple add/delete case generalizes.
- Full-history enumeration performance on very large repos is untested — acceptable for v1 per the proposal, but worth flagging if a fixture repo reveals a real scaling problem.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-PII-SCAN.md`
- Design: `project/design/proposals/proposed/lrh-pii-scan/00_proposal.md`
