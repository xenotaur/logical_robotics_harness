---
execution_id: 2026_05_19_01_27_56_LRH_CONVERSATION_PDF_DOGFOOD_DOCS
prompt_id: PROMPT(AD_HOC:LRH_CONVERSATION_PDF_DOGFOOD_DOCS)[2026-05-16T00:49:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-19T01:27:56+00:00
---

# Summary

Added user-facing documentation for ChatGPT PDF conversion under `docs/conversations/`, added synthetic/sanitized fixture guidance under `tests/fixtures/conversations/chatgpt_pdf/`, and updated docs indexes so the workflow is discoverable.

# Result

- Added `docs/conversations/chatgpt_pdf_import.md` with:
  - workflow motivation;
  - ChatGPT web PDF save steps;
  - `lrh conversation convert-pdf ... --out ...` usage;
  - supported vs unsupported PDF modes;
  - metadata and frontmatter semantics (`privacy`, `sensitivity`, `authority`, source hash, page count, extraction warnings);
  - dogfood classification model (`public-reviewed`, `private-local`, `transient-local`, `synthetic-fixtures`);
  - safety guidance (manual review, no automatic redaction/publication, no external service calls).
- Updated `docs/conversations/README.md` to link to the new user-facing import guide.
- Updated `docs/README.md` CLI reference list to include `lrh conversation`.
- Added fixture docs and a tiny synthetic expected transcript fixture:
  - `tests/fixtures/conversations/chatgpt_pdf/README.md`
  - `tests/fixtures/conversations/chatgpt_pdf/sample_chatgpt_pdf_transcript.expected.md`

# Validation

- `scripts/version tools`
- `lrh prompt check-execution --prompt-id 'PROMPT(AD_HOC:LRH_CONVERSATION_PDF_DOGFOOD_DOCS)[2026-05-16T00:49:00-04:00]' --project-root .`
- `lrh conversation convert-pdf --help`
- `lrh validate`
- `scripts/test`
- `scripts/lint`
- `scripts/format --check`

# Follow-up

- Add a small automated doc/fixture consistency test if conversation-fixture coverage expands.
- If future storage promotion flows land, link this conversion guide directly to storage/import docs and enforcement behavior.
