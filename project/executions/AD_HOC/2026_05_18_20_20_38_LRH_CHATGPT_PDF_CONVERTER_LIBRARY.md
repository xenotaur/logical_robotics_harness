---
execution_id: 2026_05_18_20_20_38_LRH_CHATGPT_PDF_CONVERTER_LIBRARY
prompt_id: PROMPT(AD_HOC:LRH_CHATGPT_PDF_CONVERTER_LIBRARY)[2026-05-16T00:47:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-05-18T20:20:38+00:00
---

# Summary

Implemented a private-by-default ChatGPT PDF conversion library at
`src/lrh/conversations/pdf_import.py` that converts text-layer PDFs into Markdown
transcripts with deterministic cleanup and sensitivity scanner integration.

Extraction backend selected: a small local extractor for PDF text token streams
(`(... ) Tj`) to avoid adding heavyweight/OCR dependencies and to keep behavior
maintainable and deterministic in this environment.

# Result

Added typed conversion models, preflight checks (missing file, unreadable/non-PDF,
encrypted marker, empty/no extractable text), cleanup rules (PDFCrowd footer removal,
page-counter removal, repeated-title dedupe, blank-line normalization), and YAML
frontmatter/body transcript rendering.

Added deterministic unit tests in `tests/conversations_tests/pdf_import_test.py`
covering conversion path, stable frontmatter fields/defaults, cleanup behavior,
sensitivity potential/not-run states, UTF-8 output, and error handling.

Updated `src/lrh/conversations/README.md` with a high-level converter note.

# Validation

- `scripts/version tools`
- `scripts/format --check`
- `scripts/lint`
- `scripts/test`
- `lrh validate`

# Follow-up

- Add CLI integration for importing conversation PDFs.
- Add dogfood sample fixtures/docs for user-facing conversation workflows.
- Consider swapping extraction internals to a dedicated parser dependency if future
  fixture diversity requires broader PDF compatibility.
