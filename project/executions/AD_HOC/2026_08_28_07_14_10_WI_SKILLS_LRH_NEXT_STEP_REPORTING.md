---
execution_id: 2026_08_28_07_14_10_WI_SKILLS_LRH_NEXT_STEP_REPORTING
prompt_id: PROMPT(AD_HOC:WI_SKILLS_LRH_NEXT_STEP_REPORTING)[2026-08-28T07:12:21+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/643
commit: fd25f20dcd5662ea21c42889da096e0d7d5cb37b
agent: claude_app
instruction_source: project/work_items/proposed/WI-SKILLS-LRH-NEXT-STEP-REPORTING.md
session_transcript: claude-app:81eca1c8-36fa-493d-b0e5-08c0501ec1d0
created_at: 2026-08-28T07:14:10+00:00
---

# Summary

Filed `WI-SKILLS-LRH-NEXT-STEP-REPORTING`: fixes a recurring, user-flagged
reporting failure (agents naming `/lrh-implement`/`/lrh-execute` as a
"next step" while a WI's own filing PR is unmerged), scoped deliberately
as investigation-first rather than pre-deciding the fix -- the user
explicitly rejected an earlier draft's premature Non-Goals/Risk-Notes
closure of a mechanical CLI-computed-oracle option.

# Result

- `project/work_items/proposed/WI-SKILLS-LRH-NEXT-STEP-REPORTING.md`
  created: requires the executing session to produce a repo-grounded
  decision matrix (covering at minimum an AGENTS.md-rule option and a
  CLI-computed-next-step option) before implementing, and to read/account
  for PR #602 (a related-but-non-obviating prior fix, verified by this
  session via `gh pr view 602 --json files` -- it fixed a downstream
  execution-safety consequence in `/lrh-implement` Step 5, not the
  reporting-accuracy problem here) before proposing anything.
- PR #643 opened.

# Validation

- Checked PR #602 does not obviate this work: its file list (`gh pr view
  602 --json files`) touches only `lrh-implement/SKILL.md`,
  `lrh-implement/references/lrh-implement-workflow.md`, and
  `lrh-work-item/references/lrh-work-item-workflow.md` -- never
  `AGENTS.md`, `lrh-work-item/SKILL.md`'s Step 11, `lrh-proposal`,
  `lrh-workstream`, or `lrh-work-remains`.
- Prior-art check: `git grep -liE "next-step-reporting|next step reporting"`
  over `project/work_items`, `project/design/backlog.md`,
  `project/design/proposals` returned no matches.
- `lrh validate`: 0 errors, 80 pre-existing warnings unrelated to this
  file (all `FRONTMATTER_LINT_UNSAFE_SCALAR` on already-resolved WIs/
  workstreams elsewhere in the repo -- confirmed none reference this new
  file).

# Follow-up

- A parallel backlog entry is being added in a follow-up commit on this
  same PR so the gap isn't lost if this WI isn't picked up immediately.
- A handoff prompt (rendered via `lrh request prompt-from-work-item`) is
  being produced separately for a fresh session to pick this up, since
  the filing session is mid-task on unrelated work.
- Implementation not started -- explicitly deferred to whichever session
  executes this WI, per its own investigation-first scoping.
