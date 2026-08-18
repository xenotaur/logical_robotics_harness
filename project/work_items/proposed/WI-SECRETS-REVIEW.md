---
resolution: null
blocked_reason: null
blocked: false
id: WI-SECRETS-REVIEW
title: Implement lrh secrets review
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-SECRETS-COMMAND
related_design:
  - project/design/proposals/proposed/lrh-secrets-command/00_proposal.md
depends_on:
  - WI-SECRETS-SCAN
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - add_cli_command
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - implement_lrh_secrets_scan
  - implement_lrh_secrets_purge
acceptance:
  - src/lrh/secrets/review.py exists and implements decisions-file-gated triage as described in Required Changes
  - lrh secrets review --check exits nonzero when any finding lacks a recorded decision
  - lrh secrets review --apply refuses to write a final replacements.reviewed.txt when any finding is undecided
  - lrh secrets review --apply writes to out-dir/replacements.reviewed.txt, distinct from scan's draft out-dir/replacements.txt, and never overwrites the draft
  - lrh validate passes with 0 errors
  - tests/secrets_tests/review_test.py and the review portion of tests/cli_tests/secrets_test.py pass
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/secrets/review.py
  - tests/secrets_tests/review_test.py
  - tests/cli_tests/secrets_test.py
---

## Summary

Implement `lrh secrets review`, a new subcommand with no LCATS-script
analog that turns the currently-manual, unaudited hand-editing of
`replacements.txt` into an auditable, CI-checkable triage step gated by an
explicit decisions file.

## Problem / Context

Today, a human hand-edits `find_secrets.py`'s draft `replacements.txt`
directly, with no record of which findings were reviewed or why a given
line was kept or dropped. `PROP-LRH-SECRETS-COMMAND` Decision 3 resolves
this by requiring an explicit `--decisions` file (per-secret keep/ignore +
reason) before a finalized `replacements.txt` can be written, consistent
with LRH's no-interactive-prompts, flag-gated mutation convention. This
item depends on `WI-SECRETS-SCAN` because it consumes `scan`'s
`findings.json`/`replacements.txt` output format directly.

Per `PROP-LRH-SECRETS-COMMAND`'s revised Decision 3 (handoff-prompt
update): the original design had `--apply` overwrite `scan`'s draft
`replacements.txt` in place, leaving no filename signal distinguishing
reviewed from unreviewed output — a real gap, since the handoff prompt is
explicit that `purge` "must refuse to run without an explicit,
human-reviewed input from the scan stage — never scan-then-auto-purge."
This item now writes the finalized output to a distinctly-named
`replacements.reviewed.txt` instead (see Required Changes item 1).

### Duplication search
- In-repo: No existing implementation found — this is a new capability, not a graduation of existing LCATS code.
- Sibling repos: None identified (LCATS has no equivalent review step today — this closes that gap).
- External libraries: None identified.
- Recommendation: Proceed.

### Demand search
- Work items: None found.
- Proposals: None found (governed by `PROP-LRH-SECRETS-COMMAND`).
- Backlog: No matching entries.
- Recommendation: No action.

## Scope

- Implement `src/lrh/secrets/review.py`
- Wire a `review` subcommand under the `secrets` group in `src/lrh/cli/main.py`
- Define and document the `--decisions` file format
- Add module and CLI test coverage

## Required Changes

1. Create `src/lrh/secrets/review.py`: accept `--out-dir` (containing `findings.json` and the draft `replacements.txt` from `scan`) and `--decisions <path>`. Default mode (no `--check`/`--apply`): print an annotated report of findings against any existing decisions. `--check`: exit nonzero if any unique secret in `findings.json` lacks a matching entry in the decisions file. `--apply`: require every finding decided; write the finalized `<out-dir>/replacements.reviewed.txt` (a name distinct from `scan`'s draft `<out-dir>/replacements.txt`, never overwriting the draft), filtered to only `keep`-decided secrets — this filename distinction is the mechanism that stops `purge` from ever being pointed at unreviewed output by accident (see `PROP-LRH-SECRETS-COMMAND` Decision 3).
2. Define the `--decisions` file format (e.g. one YAML mapping per secret hash/prefix → `{decision: keep|ignore, reason: str}`) and document it in the module docstring.
3. In `src/lrh/cli/main.py`: add a `review` sub-parser under the existing `secrets_subparsers` (from `WI-SECRETS-SCAN`), with `--out-dir`, `--decisions`, `--check`, `--apply` (assert `--check`/`--apply` are not combined with contradictory flags, per this repo's mutation-flag convention), and a dispatch branch.
4. Create `tests/secrets_tests/review_test.py`: covers undecided-finding `--check` failure, `--apply` with full decisions writing a correctly filtered `replacements.reviewed.txt`, and `--apply` refusing to write when any finding is undecided.
5. Extend `tests/cli_tests/secrets_test.py` with `lrh secrets review --help` and dispatch coverage.

## Non-Goals

- Does not implement `lrh secrets scan` or `lrh secrets purge` — separate work items.
- Does not add an interactive prompt loop — decisions are supplied via file, not live y/N input, per this repo's established convention.

## Acceptance Criteria

- `lrh secrets review --help` documents `--out-dir`, `--decisions`, `--check`, `--apply`.
- `--check` exits nonzero on any undecided finding and exits 0 when all are decided.
- `--apply` never writes a final `replacements.reviewed.txt` unless every finding is decided.
- `lrh validate` reports 0 errors.
- `tests/secrets_tests/review_test.py` and the `review` portion of `tests/cli_tests/secrets_test.py` pass.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh secrets review --help`

## Dependencies / Order

Depends on `WI-SECRETS-SCAN` because `review` reads `scan`'s `findings.json`/`replacements.txt` output format directly; implement after `scan` lands.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-SECRETS-COMMAND.md`
- Design: `project/design/proposals/proposed/lrh-secrets-command/00_proposal.md`
