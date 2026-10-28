---
execution_id: 2026_10_22_18_05_13_WI_LRH_CONSOLE_SESSION_LINK_RENDER_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_SESSION_LINK_RENDER_REVIEW)[2026-10-15T05:38:59+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_10_13_01_00_23_WI_LRH_CONSOLE_SESSION_LINK_RENDER
pr: https://github.com/xenotaur/logical_robotics_harness/pull/839
commit:
created_at: 2026-10-22T18:05:13+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/839
session_transcript: pending
---

# Summary

Address the six open review threads on PR #839 (two Codex P2, four Copilot) at head 5cdccdd8. All are on the work item file; they collapse to five fixes because two threads (Codex and Copilot) raise the same non-allowlisted click-check problem.

# Result

- PRRT_kwDOR7l1D86rrB5a (Codex P2): valid. The planning tree builds work-item edges only from parent_id, so the item has to be in the workstream's work_items list; that was already done in 5cdccdd8, after the review ran. The remaining defect was the workstream's non-goal "does not render links on work-item ... pages", which contradicted the new item. Reworded the non-goal to carve out rendering on the project work-item page through WI-LRH-CONSOLE-SESSION-LINK-RENDER, and added that rendering to the workstream's Scope.
- PRRT_kwDOR7l1D86rrB5g (Codex P2) and PRRT_kwDOR7l1D86rrCNS (Copilot): valid. A non-allowlisted pointer renders as plain text, so there is nothing to click and a "click does nothing" check would not exercise LinkHandoff::offer. The check is now: a non-allowlisted pointer in the fixture is shown to be plain text with no anchor, in the page and its HTML; the shell's refusal stays covered by the Rust tests from PR #833. Updated the acceptance frontmatter, Required Changes item 4, the Acceptance Criteria and the Risk Notes.
- PRRT_kwDOR7l1D86rrCMz (Copilot): valid, a real security point. Escaping does not make an untrusted pr: value safe as an href (pr: javascript:...). Required Changes now say the PR renders as a link only for an http or https URL with a host and no credentials, otherwise as escaped plain text, with a hostile-PR test (javascript:, data:, credentials, markup); the acceptance criteria say the same.
- PRRT_kwDOR7l1D86rrCNf (Copilot): valid. Record membership was left as an open question. Decided: a record belongs to the item when its work_item is the item's id, its rerun_of is the execution id of such a record, or its instruction_source is the item's own file path (the creation record); stated consistently in Required Changes, the tests and the acceptance criteria, and the open question removed.
- PRRT_kwDOR7l1D86rrCNx (Copilot): valid. Added `scripts/version tools` as the first Validation bullet, per AGENTS.md's validation guidance.
- Skipped: none.

# Validation

lrh validate reported 0 errors and 0 warnings; lrh work-items readiness still reports prompt_ready: yes with no blocking items. Only planning files changed (the work item and the workstream), so canonical code validation does not apply.

# Follow-up

Thread resolution and the substitute --pr self-review for the new head are handled by /lrh-confirm-fixes. session_transcript is pending until closeout.
