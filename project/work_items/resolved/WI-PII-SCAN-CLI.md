---
resolution: "Implemented and merged in PR #654 (commit 469580cb)."
blocked_reason: null
blocked: false
id: WI-PII-SCAN-CLI
title: Wire lrh pii scan into the LRH CLI
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
  - WI-PII-SCAN-LAYER2-CONTENT
  - WI-PII-SCAN-ALLOWLIST-OUTPUT
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - run_tests
  - add_cli_command
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
acceptance:
  - lrh pii scan --project-root <path> --out-dir <dir> runs successfully against a fixture repo and writes pii_findings.json
  - tests/cli_tests/pii_test.py exists and passes
  - lrh validate passes with 0 errors
required_evidence:
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/cli/main.py
  - tests/cli_tests/pii_test.py
---

## Summary

Wire `lrh pii scan --project-root --out-dir --config` into `src/lrh/cli/main.py` as a new `pii` nested-subcommand group, following the `lrh secrets` dispatch precedent, and add CLI-dispatch test coverage.

## Problem / Context

This is the final integration item: it makes the `src/lrh/pii` package built by the four prior work items reachable as an actual `lrh` command, following the exact nested-group convention `lrh secrets scan|review|purge` already established.

### Duplication search
- In-repo: `src/lrh/cli/main.py`'s existing `secrets` subcommand group is the direct pattern precedent, not a duplicate — this item adds a new, distinct `pii` group alongside it.
- Sibling repos: None applicable.
- External libraries: None.
- Recommendation: Proceed.

### Demand search
- Work items: None found prior to `WS-PII-SCAN`'s own creation.
- Proposals: `PROP-LRH-PII-SCAN` Decision 1 (command shape, satisfied by this item).
- Backlog: No matching entries.
- Recommendation: No action.

## Scope

- Add `pii` command dispatch to `src/lrh/cli/main.py`
- Add CLI-level argument parsing (`--project-root`, `--out-dir`, `--config`)
- Add CLI-dispatch tests

## Required Changes

1. Add a `pii` subcommand group to `src/lrh/cli/main.py`, dispatching `if args.command == "pii": if args.pii_command == "scan": ...` following the `secrets` group's dispatch pattern.
2. Wire `--project-root` (default cwd), `--out-dir`, and `--config` flags to the underlying `src/lrh/pii` package functions from `WI-PII-SCAN-RULE-TAXONOMY` through `WI-PII-SCAN-ALLOWLIST-OUTPUT`.
3. Add `tests/cli_tests/pii_test.py` covering CLI argument parsing and dispatch, mirroring `tests/cli_tests/secrets_test.py`.
4. Update any CLI command listing this repo's convention expects (check existing `lrh secrets` documentation entries for precedent) to include `lrh pii scan`.

## Non-Goals

- Does not add any subcommand beyond `scan` (no review/purge-equivalent) — out of scope per the proposal's Non-Goals.
- Does not change `lrh secrets`' own CLI dispatch.

## Acceptance Criteria

- `lrh pii scan --project-root <path> --out-dir <dir>` runs successfully against a fixture repo and writes `pii_findings.json`.
- `tests/cli_tests/pii_test.py` exists and passes.
- `lrh validate` passes with 0 errors.

## Dependencies / Order

Depends on all four prior work items — this item only wires already-implemented functionality into the CLI and cannot meaningfully start until `src/lrh/pii`'s public functions exist and are stable.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-PII-SCAN.md`
- Design: `project/design/proposals/proposed/lrh-pii-scan/00_proposal.md`
