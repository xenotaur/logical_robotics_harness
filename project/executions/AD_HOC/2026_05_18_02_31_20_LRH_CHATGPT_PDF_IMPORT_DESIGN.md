---
execution_id: 2026_05_18_02_31_20_LRH_CHATGPT_PDF_IMPORT_DESIGN
prompt_id: PROMPT(AD_HOC:LRH_CHATGPT_PDF_IMPORT_DESIGN)[2026-05-16T00:45:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-05-18T02:31:20+00:00
---

# Summary

Added a documentation-only design note for a future ChatGPT PDF conversation
conversion adapter. The design records a local deterministic path from ChatGPT
browser Save as PDF exports to LRH Markdown transcripts with provenance,
privacy, authority, and sensitivity metadata.

# Result

- Added `project/design/proposals/proposed/lrh-conversations-storage-interop/01_chatgpt_pdf_import.md`.
- Recorded the future command contract:
  `lrh conversation convert-pdf INPUT.pdf --out OUTPUT.md`.
- Addressed review feedback by keeping `--privacy` aligned to documented
  privacy classes and leaving transient/session behavior on the durability
  axis.
- Documented default metadata values: `privacy: private`,
  `authority: non_authoritative_context`, and `scan_sensitive: true`.
- Documented the conversion pipeline, Markdown frontmatter shape,
  sensitivity model, expected architecture locations, dogfood dataset guidance,
  and explicit non-goals.
- Updated the LRH Conversations proposal-set README and top-level proposal
  index to link and summarize the new adapter design.
- Added a small companion reference from the umbrella conversations/storage
  proposal to the focused adapter note.

# Validation

- `lrh prompt check-execution --prompt-id 'PROMPT(AD_HOC:LRH_CHATGPT_PDF_IMPORT_DESIGN)[2026-05-16T00:45:00-04:00]' --project-root .` before changes reported no prior execution records.
- `scripts/version tools` completed successfully; `pylint` and `conda` are not
  installed but the command reports them informationally and exits 0.
- `lrh validate` completed with 0 errors and 0 warnings.
- `scripts/test` passed: 529 tests ran successfully.
- `scripts/lint` passed Ruff and Black checks.
- `scripts/format --check` passed Black formatting checks.

# Follow-up

- Choose a deterministic local PDF text extraction library and fixture strategy.
- Define exact transcript body conventions after testing real browser PDF output
  patterns.
- Design and implement the conservative local sensitivity scanner in a later PR.
- Decide where private-local transcript corpora live outside the public LRH
  repository.
- Add user-facing documentation only after the command exists.
