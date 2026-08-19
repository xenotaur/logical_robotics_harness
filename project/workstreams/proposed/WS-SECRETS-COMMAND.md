---
id: WS-SECRETS-COMMAND
kind: planning_node
title: "lrh secrets — Scan/Review/Purge Command Graduation"
status: proposed
stage: designed
origin: design_review
summary: Graduate LCATS's experimental secrets-hygiene scripts into a permanent lrh secrets scan|review|purge command, with a new review subcommand closing the manual replacements.txt triage gap.
related_focus: []
related_roadmap: []
related_design:
  - project/design/proposals/proposed/lrh-secrets-command/00_proposal.md
work_items:
  - WI-SECRETS-SCAN
  - WI-SECRETS-REVIEW
  - WI-SECRETS-PURGE
exit_criteria:
  - lrh secrets scan, lrh secrets review, and lrh secrets purge are all implemented, tested, and merged
  - Each subcommand has module-level tests under tests/secrets_tests/ and CLI-dispatch tests in tests/cli_tests/secrets_test.py
  - lrh secrets purge preserves every safety invariant from purge_history.py (mandatory refs-file, mirror-only, verify-after, no auto-push) with no relaxation
  - A companion LCATS PR deleting the experimental scripts has been opened (tracked as follow-up, not blocking this workstream's closure)
---

## Purpose

This workstream coordinates the graduation of LCATS's experimental
secrets-hygiene tooling (`find_secrets.py`, `purge_history.py`) into a
permanent LRH command surface, `lrh secrets`, following the
`sourcetree_surveyor` → `lrh survey` precedent. It groups the three
subcommand implementations, their required test coverage, and the
follow-on LCATS-side cleanup under one planning node so the full graduation
stays visible from design through closeout.

## Scope

- Implement `lrh secrets scan`, `lrh secrets review`, and `lrh secrets purge` under `src/lrh/secrets/`
- Wire the `secrets` nested-subcommand group into `src/lrh/cli/main.py`
- Add module and CLI test coverage for all three subcommands
- Land each work item through the standard LRH execution lifecycle

## Prior Art Check

### Duplication search
- In-repo: No existing implementation found. Related-but-distinct: `src/lrh/conversations/sensitivity.py` (transcript PII scanning, not git-history scanning).
- Sibling repos: LCATS `lcats/experimental/secrets_hygiene/` — the source being graduated.
- External libraries: `gitleaks`, `git-filter-repo` — already the chosen wrapped tools; no alternative considered.
- Recommendation: Proceed.

### Demand search
- Work items: None found.
- Proposals: None found.
- Backlog: No matching entries.
- Recommendation: No action.

## Work Items

- **WI-SECRETS-SCAN** — Implement `lrh secrets scan`, wrapping `gitleaks` for a read-only full-history scan writing `findings.json` + draft `replacements.txt`.
- **WI-SECRETS-REVIEW** — Implement `lrh secrets review`, a decisions-file-gated triage step producing a finalized, auditable `replacements.reviewed.txt` (distinct from `scan`'s draft `replacements.txt`).
- **WI-SECRETS-PURGE** — Implement `lrh secrets purge`, wrapping `git-filter-repo` for a mirror-clone rewrite scoped to explicit refs, with mandatory post-rewrite verification and a printed-never-run push command.

## Exit Criteria

- All three subcommands implemented, tested, and merged to `main`
- `lrh validate` passes with 0 errors after each work item lands
- `tests/secrets_tests/` (fully mocked/hermetic) and `tests/cli_tests/secrets_test.py` exist and pass; `tests/smoke/secrets_purge_smoke.py` (real `git-filter-repo` mirror-clone/verify, run via `scripts/smoke`) exists and passes when `git-filter-repo` is installed
- Every safety invariant from `purge_history.py` (mandatory `--refs-file`, mirror-only operation, mandatory post-rewrite verification, no code path to `git push`) is preserved unmodified in the graduated `purge` command, including a runtime-enforced (not just documented) reviewed-replacements gate and literal-string (not regex) secret verification
- A companion LCATS PR removing `lcats/experimental/secrets_hygiene/{find_secrets.py,purge_history.py}` and repointing its docs at `lrh secrets` has been opened

## Non-Goals

- Does not implement any form of automated `git push --force` execution — stays permanently manual.
- Does not expand `gitleaks` rule coverage (e.g. the known Azure-key detection gap) — scan-quality tuning is separate follow-up work, not blocking this workstream.
- Does not decide whether/when LCATS actually executes an all-branches history purge against its real leaked-key incident — that operational decision belongs to LCATS, not this workstream.
- Does not include the LCATS-side script deletion PR itself as a work item under this workstream — that PR lives in a different repository and is tracked as a follow-up, not a dependency gating this workstream's closure.
- Does not implement repo-local `.gitleaks.toml` scaffolding/management, a periodic key-lifecycle/audit reminder mode, or remediation-pattern nudging in scan/review output — three ideas surfaced by a PR #315 handoff prompt, recorded as Open Questions in `PROP-LRH-SECRETS-COMMAND` for possible future scoping, not part of this workstream's exit criteria.

## Relationship to Design

- Design proposal: `project/design/proposals/proposed/lrh-secrets-command/00_proposal.md`
- Graduation precedent: `src/lrh/assist/sourcetree_surveyor.py`, `tests/cli_tests/survey_test.py`
- Grouped-command precedent: `src/lrh/work_items/` package, `src/lrh/cli/main.py` `work-items` dispatch

## Open Questions

- `purge`'s exact `--source` default-derivation behavior (see the proposal's Open Questions) may be revisited during `WI-SECRETS-PURGE` implementation.
