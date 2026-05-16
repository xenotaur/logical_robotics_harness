---
execution_id: 2026_05_16_08_42_44_LRH_CONVERSATIONS_STORAGE_INTEROP_DESIGN
prompt_id: PROMPT(AD_HOC:LRH_CONVERSATIONS_STORAGE_INTEROP_DESIGN)[2026-05-16T00:30:00-04:00]
work_item: AD_HOC
status: landed
rerun_of:
pr:
commit:
created_at: 2026-05-16T08:42:44+00:00
---

# Summary

Created a documentation-only design proposal for LRH Conversations, Storage,
and External Agent Interop. The proposal records a unified architecture for
private-by-default conversation capture, policy-aware storage, explicit
promotion, and stable external adapter surfaces.

# Result

- Added `project/design/proposals/proposed/lrh-conversations-storage-interop/00_proposal.md`.
- Added the proposal-set README at
  `project/design/proposals/proposed/lrh-conversations-storage-interop/README.md`.
- Updated `project/design/proposals/README.md` with a concise proposal index entry.
- Recorded the core decisions that LRH Conversations are non-authoritative until
  promoted, raw conversations are private by default, storage policy must be
  explicit, Git stores curated artifacts rather than raw chat by default,
  external tools integrate through stable protocol surfaces, and chat-to-run
  requires proposal, approval, evidence, and status interpretation.

# Validation

- `scripts/version tools` passed for available package, CLI, Python, Ruff,
  Black, Pyright, and pip metadata; Pylint and Conda were reported as not
  installed by the version script.
- `lrh prompt check-execution --prompt-id "$PROMPT_ID" --project-root .`
  reported no prior execution records for this exact prompt ID before work
  began.
- `lrh validate` passed with 0 errors and 3 pre-existing planning orphan warnings.
- `scripts/test` passed: 522 tests.
- `scripts/lint` passed Ruff and Black checks.
- `scripts/format --check` passed Black formatting checks.

# Follow-up

- Implement the proposal only through later staged PRs, beginning with policy
  typed models, an in-memory backend for tests, a filesystem backend for
  debugging/import/export, and metadata validation.
- Defer SQLite, conversation import/export, promotion, provider-neutral ask,
  external protocols, chat-to-run, and `lrh serve` integration until their
  earlier semantic prerequisites are stable.
