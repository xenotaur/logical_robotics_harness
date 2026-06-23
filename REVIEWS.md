# Review Protocol — LRH-Specific Overrides and Supplements

This document records LRH-specific overrides and supplements to the base
review-response protocol. The base protocol is maintained in
`src/lrh/assist/templates/request/review_protocol.md` and its steps are
embedded in `src/lrh/assist/templates/request/review_response.md`.

Agents working in the LRH repository read this file when the
`review_response` template instructs them to check for a `REVIEWS.md` at
the repository root. Content here takes precedence over the base protocol
for LRH-specific cases.

## 1) Triage each reported comment/issue

For each review comment or reported issue:

1. **Presence check**: Is the issue still present on the current branch state?
   - If no, briefly explain why and stop processing that comment.
2. **Validity check**: Is the concern valid and worth addressing?
   - If no, briefly explain why and stop processing that comment.
3. **Feasibility check**: Is remediation feasible in this change?
   - If no, briefly explain why and stop processing that comment.

If present, valid, and feasible issues remain, implement fixes and prepare a PR.

## 2) Validation protocol for reported failures

When validating or repairing a failure, identify and run canonical repository entrypoints (README, CI, scripts, maintainer docs).

Use this canonical task-phase sequence when available:

```bash
scripts/version tools
scripts/format --check --diff
scripts/lint
scripts/test
```

### Tool/version gate (required)

Before lint/format/test, verify `scripts/version tools` reports expected Black/Ruff versions.

If Black/Ruff are missing or mismatched:

- Stop formatter/linter debugging.
- Report a Codex setup/cache mismatch.
- State that `scripts/develop` must run during setup/bootstrap phase (or environment cache must be reset).

If `scripts/develop` was run during task phase and failed due to proxy/tunnel/index errors, treat that as a bootstrap warning, not a code failure. Continue only if `scripts/version tools` confirms required versions.

If canonical validation fails with missing-install/import errors (for example `ModuleNotFoundError: lrh`), stop and report setup/bootstrap mismatch rather than code regression.

## 3) Execution and fallback rules

- Do **not** treat direct `black --check .` or `ruff check .` as canonical substitutes.
- Direct Black/Ruff invocations are allowed only as follow-up diagnostics after canonical commands.
- If canonical commands are missing, run the closest repo-approved equivalents and explicitly report what was unavailable and what was used.

## 4) Repair loops

If formatting fails (and required tool versions are present), repair and re-validate in this order:

```bash
<repo formatter fix command>
git diff
<repo canonical lint command>
<repo canonical test command>
```

If lint fails with fixable issues (and required tool versions are present), repair and re-validate in this order:

```bash
<repo lint fix command>
git diff
<repo canonical lint command>
<repo canonical test command>
```

Do not manually re-wrap code purely to satisfy Black; run the repository formatter and commit its output.

## 5) Evidence requirements before claiming drift/non-repro

Do not claim pre-existing/unrelated drift or non-reproducibility without command evidence from the current branch state:

```bash
git rev-parse HEAD
git status --short
<repo tool/version command>
<repo canonical lint command>
<repo canonical format check command>
<repo canonical test command>
```

If any canonical command is absent, explicitly report that gap and the nearest equivalent used.

## 6) Repository-policy reminders inside review prompts

Review prompts should remind agents to:

- respect repository `AGENTS.md` and `STYLE.md`
- keep `README.md` guidance current in directories with affected code
