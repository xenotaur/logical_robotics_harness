---
execution_id: 2026_04_27_05_11_53_RELEASE_DOCS_INTEGRATION
prompt_id: PROMPT(AD_HOC:RELEASE_DOCS_INTEGRATION)[2026-04-27T00:10:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: make_pr:docs-document-release-workflow-and-record-execution
commit: a867576
created_at: 2026-04-27T05:11:53+00:00
---

# Summary

Document the LRH release workflow with actionable setuptools-scm tag, build, and isolated wheel-install smoke-test instructions.

# Result

Updated the top-level `README.md` release section to include the required command sequence, key concepts, expected outputs, and safety/idempotence notes.

# Validation

- Reviewed rendered Markdown structure and command sequence in `README.md`.
- Verified prompt execution record creation with `scripts/prompts/record-execution`.

# Follow-up

Optionally add CI automation for this documented manual workflow when release automation scope is approved.
