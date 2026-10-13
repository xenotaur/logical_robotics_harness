---
execution_id: 2026_10_13_01_18_28_LRH_CONSOLE_READINESS_VOCABULARY
prompt_id: PROMPT(WI-LRH-CONSOLE-READINESS-VOCABULARY:LRH_CONSOLE_READINESS_VOCABULARY)[2026-10-13T00:57:24+00:00]
work_item: WI-LRH-CONSOLE-READINESS-VOCABULARY
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/840
commit:
created_at: 2026-10-13T01:18:28+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/840
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
---

# Summary

This record covers the implementation of `WI-LRH-CONSOLE-READINESS-VOCABULARY` under `/lrh-execute`, with the run plan approved by the owner. LRH Console now names each readiness check instead of showing plain "ready" or "not ready". Only labels change; no check's computation or gating does.

# Result

The labels below are from the implementation round. Review-response round 1 renamed "Execution-ready" to "Execution-ready flag" and "Leaves flagged execution-ready" (see the `_REVIEW` record).


- **Work-item page** (`render_project_work_item_page`, `src/lrh/serve.py`): the unqualified "Readiness state" is replaced by three named checks.
  - **Prompt-ready:** `parse_work_item_markdown` and `evaluate_prompt_readiness` run on the item's own file. This is the check behind `lrh work-items readiness` and the map, and the page shows the blocking reasons when the answer is No. Closed items show "Not applicable (closed)".
  - **Execution-ready (run packets):** Yes, No, or "Not declared".
  - **Authorization.**
  - **Run-packet fields:** these say "not declared" instead of "missing". Required evidence shows the item's own field.
  - **Copy button:** gated as before, with a note on when it becomes available.
- **Statusboard and project pages:** "Execution-ready leaves" and "Leaves not execution-ready". The next action now says "N work items are execution-ready". The counts are unchanged.
- **Visual-language proposal:** a "Readiness vocabulary" section records the four terms and where each appears.
- **Speed:** a first version scanned every work item for one item's prompt-readiness, which took about 0.45 s. Checking the one file takes about 0.1 s.
- **Browser check:**
  - `WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT` shows Prompt-ready Yes and Execution-ready Not declared.
  - The Statusboard and the LRH project page show the new labels.
- **Pre-push self-review:** 2 Medium and several Low findings, fixed in the second commit. See the `AD_HOC` `_SELFREVIEW` record.
- **Pending:** the owner's check in LRH Console.

# Validation

- `scripts/format --check --diff`: clean.
- `scripts/lint`: clean.
- `scripts/test`: one test failed in the first full run, and that test was then fixed. After review-response round 1, the complete `scripts/test` run passed on the final code: 2312 tests, OK.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- Land through `/lrh-land`, after the owner's check.
