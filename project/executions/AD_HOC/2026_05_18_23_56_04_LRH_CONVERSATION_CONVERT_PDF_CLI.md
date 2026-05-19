---
execution_id: 2026_05_18_23_56_04_LRH_CONVERSATION_CONVERT_PDF_CLI
prompt_id: PROMPT(AD_HOC:LRH_CONVERSATION_CONVERT_PDF_CLI)[2026-05-16T00:48:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-18T23:56:04+00:00
---

# Summary

Added the `lrh conversation convert-pdf INPUT.pdf --out OUTPUT.md` CLI path for
converting local ChatGPT PDF conversation exports with extractable text into
private, non-authoritative Markdown transcripts using the existing
`lrh.conversations.pdf_import` converter library.

# Result

Implemented CLI-facing behavior for:

- required `--out` output path;
- `--force` overwrite protection override;
- `--no-scan-sensitive` for unscanned transcript metadata;
- concise deterministic success summaries with pages, privacy, sensitivity, and
  warning counts;
- stderr warnings for extraction warnings and potential heuristic sensitivity
  findings;
- nonzero, actionable failures for missing input, existing output without
  `--force`, no-text/encrypted PDF errors, and filesystem/converter failures.

Added CLI tests covering help language, conversion of a synthetic sanitized PDF,
output writing, overwrite refusal, forced overwrite, unscanned sensitivity
metadata, missing input errors, and private/non-authoritative transcript
frontmatter.

Updated minimal discoverability docs in the conversation package README,
conversation docs README, and CLI reference.

# Validation

- `scripts/version tools` — passed before task-phase validation; Black 26.3.1
  and Ruff 0.15.12 matched repository expectations.
- `python -m unittest tests.cli_tests.conversation_test tests.conversations_tests.pdf_import_test`
  — passed; 17 tests ran successfully.
- `scripts/test` — passed; 582 tests ran successfully.
- `scripts/lint` — passed.
- `scripts/format --check` — passed.
- `lrh validate` — passed with 0 errors and 0 warnings.

# Follow-up

- Expand full user-facing conversation-import documentation under
  `docs/conversations/` in the planned documentation PR.
- Add dogfood fixtures or sample outputs only if they remain synthetic or fully
  sanitized; do not commit real private ChatGPT transcripts.
