---
execution_id: 2026_05_04_18_25_13_AGENT_PHASE_VALIDATION_PROMPTS
prompt_id: PROMPT(WI-DEV-TOOLCHAIN-RECONCILIATION:AGENT_PHASE_VALIDATION_PROMPTS)[2026-05-04T09:05:00-04:00]
work_item: WI-DEV-TOOLCHAIN-RECONCILIATION
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-04T18:25:13+00:00
---

# Summary

Updated agent review-response prompt guidance to separate setup/bootstrap installation from ordinary task-phase validation in Codex Cloud. Added explicit version-first validation sequencing and setup/cache mismatch handling instructions, while keeping formatter/lint repair guidance conditional on correct tool versions.

# Result

Updated `src/lrh/assist/templates/request/review_response.md` so task-phase instructions run `scripts/version tools` first, do not routinely run `scripts/develop`, and treat task-phase `scripts/develop` proxy/tunnel/package-index failures as bootstrap warnings rather than code failures. Kept canonical validation and repair flow, but made formatter/lint repair contingent on matching Black/Ruff versions.

# Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`

# Follow-up

If future templates duplicate validation guidance, align them with the same setup-phase vs task-phase distinction to keep agent behavior consistent.
