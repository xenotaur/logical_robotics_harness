# Review Protocol (Packaged)

This is the packaged review protocol used by `review_response` so guidance remains available when LRH is installed outside a source checkout.

For repository-local maintenance and governance, see root `REVIEWS.md` when present.

## 1) Triage each reported comment/issue

For each review comment or reported issue:

1. **Presence check**: Is the issue still present on the current branch state?
2. **Validity check**: Is the concern valid and worth addressing?
3. **Feasibility check**: Is remediation feasible in this change?

If not present/valid/feasible, explain briefly and stop processing that comment.

## 2) Canonical validation protocol

When validating or repairing failures, first identify and run canonical repository entrypoints.

Use this task-phase set when available:

```bash
scripts/version tools
scripts/format --check --diff
scripts/lint
scripts/test
```

Before lint/format/test, verify `scripts/version tools` reports expected Black/Ruff versions.
If versions are missing/mismatched, stop formatter debugging and report setup/bootstrap mismatch.

If canonical commands fail with missing install/import errors (for example `ModuleNotFoundError: lrh`), report setup/bootstrap mismatch instead of code regression.

## 3) Repair sequencing

After tool versions match:

- fix formatting with repo formatter command, then lint, then tests
- fix lint with repo lint fix command, then lint, then tests

Do not substitute direct `black`/`ruff` commands for canonical repository entrypoints.

## 4) Evidence and policy reminders

- Provide command evidence when claiming drift or non-repro.
- Respect repository `AGENTS.md` and `STYLE.md`.
- Keep affected-directory `README.md` guidance up to date.
