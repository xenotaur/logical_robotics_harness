---
execution_id: 2026_07_25_14_18_28_WI_EVIDENCE_WORKBOOKS_DIRECTORY_REVIEW
prompt_id: PROMPT(AD_HOC:WI_EVIDENCE_WORKBOOKS_DIRECTORY_REVIEW)[2026-07-25T14:11:45-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/416
commit: b5ca51c0089fc52820c7dcbad372531cf6fa085f
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/416
session_transcript: claude-app:a787b253-6f9b-4896-a9ec-383fb1c6b1ac
created_at: 2026-07-25T14:18:28-04:00
---

# Summary

Address review feedback on PR #416 (WI-EVIDENCE-WORKBOOKS-DIRECTORY,
a planning-artifact PR — no primary execution record of its own, so
`rerun_of` is left empty per the review-response workflow's edge-case
guidance for PRs created outside `/lrh-implement`).

# Result

Addressed 2 open review comments from `chatgpt-codex-connector`,
both P2, both verified against the cited examples before fixing:

1. **No machine-readable clean-pass marker.** Verified against PR #400:
   three `_CONFIRM.md` records all carry `status: landed`, but their
   actual verdicts ("not green" / "green" / a self-correction of an
   earlier mis-ordered "green" claim) exist only as unstructured body
   prose. Fixed by rewriting the WI's Required Change 3 and Acceptance
   Criteria to stop claiming the script can determine which pass was
   "the" clean one; it now reports pass counts and best-effort prose
   verdicts labeled as unverified, and a Risk Note records the gap with
   the verified PR #400 evidence. Added a Non-Goal explicitly deferring a
   structured `verdict:` schema field to future work.
2. **Filename suffix is not a valid review/confirm cohort predicate.**
   Verified against PR #413:
   `project/executions/WI-SKILLS-NEXT-STEP-CHAIN/2026_07_24_00_08_21_ADDRESS_412_REVIEW.md`
   is the primary work-item record (slug happens to end in "review"),
   while the true review-response side-record is
   `project/executions/AD_HOC/2026_07_24_00_31_50_LRH_NEXT_STEP_CHAIN_FOLLOWUP_REVIEW.md`
   — suffix-only counting would have reported 2 rounds instead of 1.
   Fixed by redefining the cohort predicate in Required Change 3 as
   `work_item == "AD_HOC"` plus a non-empty `rerun_of` back-link, per
   `references/review-response-workflow.md:38-43`, and recorded the
   verified example in a new Risk Note.

Nothing was skipped.

# Validation

- `scripts/version tools` — Black 26.3.1, Ruff 0.15.12 confirmed (LRH env
  bin prefixed on PATH; base conda env's Black 25.11.0 otherwise shadows
  it)
- `scripts/format --check --diff` — 179 files unchanged (no Python files
  touched)
- `scripts/lint` — all checks passed
- `scripts/test` — 796 tests OK
- `lrh validate` — 0 errors, 0 warnings

# Follow-up

- A future work item could add a structured `verdict:` frontmatter field
  to `_CONFIRM.md` execution records so confirm-fixes cleanliness is
  machine-readable — explicitly out of scope for
  WI-EVIDENCE-WORKBOOKS-DIRECTORY (see its Non-Goals).
- Suggest `/lrh-confirm-fixes` next to verify these fixes against the
  current diff before merge.
