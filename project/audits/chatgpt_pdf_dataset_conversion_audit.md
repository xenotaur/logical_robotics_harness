# ChatGPT PDF Dataset Conversion Audit

## Purpose

Audit `lrh conversation convert-pdf` against the external ChatGPT/PDFCrowd-style
dataset and classify failures without changing converter implementation.

## Dataset path

- Default dataset root: `$HOME/Workspace/LogicalRoboticsHarness/Datasets/ChatSessions`
- This Codex Cloud run should treat that directory as optional; when absent,
  run fallback checks (`--help` and missing-path behavior).

## Audit commands

```bash
scripts/audits/audit-chatgpt-pdf-dataset --help
scripts/audits/audit-chatgpt-pdf-dataset --dataset-root /tmp/does-not-exist
# If dataset exists:
scripts/audits/audit-chatgpt-pdf-dataset --dataset-root "$HOME/Workspace/LogicalRoboticsHarness/Datasets/ChatSessions" --out tmp/chatgpt-pdf-audit
```

## Environment and backend probe model

The audit script reports backend availability without requiring all libraries:

- `pypdf`
- `fitz` (PyMuPDF)
- `pdfplumber`

It also records `file` command output when available.

## Result taxonomy

- `PASS`
- `FAIL-BUG`
- `FAIL-DIAGNOSTICS`
- `UNSUPPORTED-EXPECTED`
- `SKIPPED-NO-BACKEND`
- `ERROR-AUDIT`

## Known dogfood failure under investigation

The audit explicitly flags any file with SHA-256:

`e22bb22f25edd544762d5013fe468e3ba53ee74b489e1808fa2d72d24957fd17`

If present and independent extraction finds text, failed converter output should
be classified as `FAIL-BUG` or `FAIL-DIAGNOSTICS` (depending on stderr quality).

## Findings from this Codex Cloud run

- Script added and runnable.
- In this environment, dataset availability is determined at runtime by checking
  the external path above.
- If the dataset is missing, the script exits non-zero with a clear message and
  does not claim conversion findings.
- If present, per-file logs are written to `tmp/chatgpt-pdf-audit/logs/`, with
  `summary.md` and `summary.json` at `tmp/chatgpt-pdf-audit/`.

## Recommended follow-up PRs

1. Dependency/packaging: ensure the chosen extraction backend is declared and
   installed in standard developer bootstrap flow.
2. Diagnostics: distinguish missing backend vs unreadable/encrypted vs no text
   vs cleanup-removes-content vs converter errors.
3. Preflight: accept files when sampled pages include meaningful text.
4. Fixture/regression: add synthetic/sanitized ChatGPT/PDFCrowd-style fixture.
5. User docs: add explicit troubleshooting for backend-missing vs image-only.

## Validation commands run

- `scripts/version tools`
- `scripts/audits/audit-chatgpt-pdf-dataset --help`
- `scripts/audits/audit-chatgpt-pdf-dataset --dataset-root /tmp/does-not-exist`
- `lrh validate`
- `scripts/format --check`
- `scripts/lint`
- `scripts/test`
