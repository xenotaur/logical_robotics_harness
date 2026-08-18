---
resolution: null
blocked_reason: null
blocked: false
id: WI-SECRETS-SCAN
title: Implement lrh secrets scan
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
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - add_cli_command
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - implement_lrh_secrets_review
  - implement_lrh_secrets_purge
acceptance:
  - src/lrh/secrets/scan.py exists and wraps gitleaks as described in Required Changes
  - lrh secrets scan --help works and lrh secrets requires a subcommand error names scan
  - lrh secrets scan fails fast with an install hint when gitleaks is not on PATH
  - lrh secrets scan never passes a config-related flag that would suppress gitleaks auto-discovering a target repo's own .gitleaks.toml
  - lrh validate passes with 0 errors
  - tests/secrets_tests/scan_test.py and the scan portion of tests/cli_tests/secrets_test.py pass
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/secrets/__init__.py
  - src/lrh/secrets/scan.py
  - tests/secrets_tests/scan_test.py
  - tests/cli_tests/secrets_test.py
---

## Summary

Implement `lrh secrets scan`, a read-only subcommand that wraps `gitleaks`
to scan a target repository's full git history for leaked secrets and
write `findings.json` + a draft `replacements.txt` for later review.

## Problem / Context

LCATS's experimental `find_secrets.py` already implements this behavior
but is scoped to one repo's tree and has no test coverage. This item
graduates the logic into `src/lrh/secrets/scan.py` as the first of three
subcommands under the new `lrh secrets` command group, per
`PROP-LRH-SECRETS-COMMAND` Decision 1 and 2.

While this work item's governing proposal was in review, LCATS PR #315
(`fa308bb18`) found and removed a second live secret — a hardcoded Azure
OpenAI key in a notebook, missed by `gitleaks`' default ruleset — and
fixed the gap with a repo-root `.gitleaks.toml` custom rule that
`gitleaks detect` auto-discovers with no extra flag. Per
`PROP-LRH-SECRETS-COMMAND` Decision 6, this makes "never suppress that
auto-discovery" an explicit, tested requirement of this item (see
Required Changes item 2 and the added test case below), not an implicit
assumption.

### Duplication search
- In-repo: No existing implementation found.
- Sibling repos: LCATS `lcats/experimental/secrets_hygiene/find_secrets.py` — source being graduated.
- External libraries: `gitleaks` — already the chosen tool.
- Recommendation: Proceed.

### Demand search
- Work items: None found.
- Proposals: None found (this item's own governing proposal, `PROP-LRH-SECRETS-COMMAND`, is what's requesting it).
- Backlog: No matching entries.
- Recommendation: No action.

## Scope

- Implement `src/lrh/secrets/scan.py` wrapping `gitleaks detect --log-opts=--all`
- Wire the `secrets` subparser group (with `scan` as its first subcommand) into `src/lrh/cli/main.py`
- Add module and CLI test coverage

## Required Changes

1. Create `src/lrh/secrets/__init__.py`.
2. Create `src/lrh/secrets/scan.py`: fail fast with an install hint if `gitleaks` is not on `PATH` (mirror `find_secrets.py`'s `_check_gitleaks_available` message); accept `--project-root` (default cwd) and `--out-dir`; run `gitleaks detect --source <project-root> --log-opts=--all --report-format json --report-path <out-dir>/findings.json`; dedupe findings by secret value and write `<out-dir>/replacements.txt` (`<secret>==>***REMOVED-<RuleID>***` per line); support `--format text|json` for the summary printed to stdout. **Do not pass `--config`, `--no-git`, or any other flag that would suppress `gitleaks`' automatic discovery of a `.gitleaks.toml` at `--project-root`** — a target repo (e.g. LCATS, whose repo-root `.gitleaks.toml` adds a custom `azure-openai-key-contextual` rule after a real live-key incident) may depend on that auto-discovery for correct scan coverage; document this explicitly in the module docstring.
3. In `src/lrh/cli/main.py`: add `secrets_parser = subparsers.add_parser("secrets", help=...)`, `secrets_subparsers = secrets_parser.add_subparsers(dest="secrets_command")`, a `scan` sub-parser with the above arguments, and a dispatch branch `if args.command == "secrets": if args.secrets_command == "scan": ...`. Include a `parser.error("secrets requires a subcommand ...")` fallback (this will be extended by `WI-SECRETS-REVIEW` and `WI-SECRETS-PURGE`).
4. Create `tests/secrets_tests/scan_test.py` mocking the `gitleaks` subprocess call (mirror `tests/assist_tests/sourcetree_surveyor_test.py`'s structure), covering: findings parsed correctly, dedup behavior, missing-binary fail-fast, no-findings case (does not write `replacements.txt`), and a regression-guard asserting the constructed `gitleaks` command never includes `--config`/`--no-config`/`--no-git` or any other flag that would override or suppress `.gitleaks.toml` auto-discovery.
5. Create `tests/cli_tests/secrets_test.py` covering `lrh secrets scan --help`, the missing-subcommand error path, and argv-delegation (mirror `tests/cli_tests/survey_test.py`).

## Non-Goals

- Does not implement `lrh secrets review` or `lrh secrets purge` — separate work items.
- Does not vendor or pip-install `gitleaks`.
- Does not tune `gitleaks` rule coverage (e.g. Azure-key detection gaps).

## Acceptance Criteria

- `lrh secrets scan --help` works and documents `--project-root`, `--out-dir`, `--format`.
- Running against a repo with no `gitleaks` on `PATH` prints the install hint and exits nonzero.
- `lrh validate` reports 0 errors.
- `tests/secrets_tests/scan_test.py` and the `scan` portion of `tests/cli_tests/secrets_test.py` pass.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh secrets scan --help`

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-SECRETS-COMMAND.md`
- Design: `project/design/proposals/proposed/lrh-secrets-command/00_proposal.md`
