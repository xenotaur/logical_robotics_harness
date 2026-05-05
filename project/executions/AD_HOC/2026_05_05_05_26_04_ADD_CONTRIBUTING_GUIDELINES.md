---
execution_id: 2026_05_05_05_26_04_ADD_CONTRIBUTING_GUIDELINES
prompt_id: PROMPT(AD_HOC:ADD_CONTRIBUTING_GUIDELINES)[2026-05-05T01:45:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 698179960524723f5be58b21ec26ab6d25d4fb7f
created_at: 2026-05-05T05:26:04+00:00
---

# Summary

Added a new root-level `CONTRIBUTING.md` as a concise contributor gateway for LRH, linking
canonical docs and documenting contribution expectations for scoped, evidence-backed,
human-auditable, AI-compatible work.

# Result

Completed the requested documentation change:

- Added `CONTRIBUTING.md` at repository root.
- Included LRH-specific contribution principles, workflow expectations, AI-assisted work rules,
  prompt/execution-record guidance, and references to canonical repository documents.
- Kept scope narrow to contributor docs plus this prompt's execution record only.

# Validation

Ran lightweight documentation-appropriate checks and repository validation:

- `scripts/version tools`
- local Markdown link-target existence check for `CONTRIBUTING.md`
- `lrh validate`

All executed checks passed in this environment.

# Follow-up

- Add PR identifier to this record after PR creation (if desired by maintainers).
- Transition status to `landed` when the PR is merged.
