---
execution_id: 2026_10_12_00_41_34_WI_SKILLS_OPENAI_POLICY_NULL_FAILSAFE
prompt_id: PROMPT(AD_HOC:WI_SKILLS_OPENAI_POLICY_NULL_FAILSAFE)[2026-10-11T04:44:56+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/830
commit:
created_at: 2026-10-12T00:41:34+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SKILLS-OPENAI-POLICY-NULL-FAILSAFE.md
session_transcript: pending
---

# Summary

Ran `/lrh-work-item` to capture the two deferred follow-ups from the PR #810
closeout (`WI-SKILLS-CHATGPT-EXPORT-HARDENING`). Both go in one combined
planning PR:

- follow-up 1, a blank `policy:` in `agents/openai.yaml`, became the new work
  item `WI-SKILLS-OPENAI-POLICY-NULL-FAILSAFE`;
- follow-up 2, the `## When to use` placement edge cases, became a
  design-backlog entry.

The human confirmed both drafts at the Step 5 gate.

# Result

- Created `project/work_items/proposed/WI-SKILLS-OPENAI-POLICY-NULL-FAILSAFE.md`:
  a deliverable with no workstream, depending on the resolved
  `WI-SKILLS-CHATGPT-EXPORT-HARDENING`.
- Appended "ChatGPT export: `## When to use` placement edge cases" to
  `project/design/backlog.md`.
- Opened PR #830 on `xenotaur/feat/wi-skills-openai-policy-null-failsafe`,
  branched from origin/main `52d34a03`.

Research grounding the work item, run against origin/main code:

- Five canonical skills are manual-only only through `agents/openai.yaml`.
- With `policy:` blank, `lrh-land` and `lrh-codex-export` export by default,
  with no error and no manual-only notice.
- A Codex install copies the blank file verbatim, and
  `lrh skills check --target codex` does not report it.
- The canonical export gives 20 exported and 6 manual-only skipped (including
  `lrh-codex-session`). This was rechecked on `52d34a03` before writing.
- Prior art check:
  - duplication: none found;
  - demand: found in the PR #810 closeout note.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `lrh work-items readiness WI-SKILLS-OPENAI-POLICY-NULL-FAILSAFE`: ready.

# Follow-up

- Land PR #830, then implement the WI, for example with
  `/lrh-execute WI-SKILLS-OPENAI-POLICY-NULL-FAILSAFE`, using an `-impl`
  branch suffix to avoid planning/implementation slug collisions.
