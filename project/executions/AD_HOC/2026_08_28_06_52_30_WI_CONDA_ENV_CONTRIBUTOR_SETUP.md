---
execution_id: 2026_08_28_06_52_30_WI_CONDA_ENV_CONTRIBUTOR_SETUP
prompt_id: PROMPT(AD_HOC:WI_CONDA_ENV_CONTRIBUTOR_SETUP)[2026-08-28T06:50:55+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/641
commit: 2374647c5b078fea8df8036be4f626f34b3b7aab
created_at: 2026-08-28T06:52:30+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-CONDA-ENV-CONTRIBUTOR-SETUP.md
session_transcript: claude-app:17bd90a6-1e4a-4b7b-8883-fc13d0d8a192
---

# Summary

Created `WI-CONDA-ENV-CONTRIBUTOR-SETUP`: a design investigation into how
a new human contributor sets up their own working conda environment for
this repo, and what to do about `environment.yml`'s stale dual-pin
(`lrh` vs. its prior name `logical-robotics-harness`) -- the item this
session's `/lrh-work-remains` follow-up work surfaced but explicitly
deferred as its own separate design discussion, per the user's request.

# Result

Ran the prior-art check before drafting: found `PROP-DEV-TOOLCHAIN-ENV-RESOLUTION`
(adopted), an existing proposal that already frames and decides the
adjacent question of environment *resolution* (Option C: LRH-native
version guardrails mandatory; Taurworks activation optional/detected,
never a hard dependency). Surfaced this to the user before finalizing,
then scoped the new work item to explicitly reconcile with that adopted
decision rather than duplicate or re-decide it -- added
`forbidden_actions: implement_taurworks_detection_contract` and a
matching Non-Goals entry, since that proposal's own Taurworks-contract
follow-on is deliberately deferred pending a sibling repo's producer-side
work.

Created `project/work_items/proposed/WI-CONDA-ENV-CONTRIBUTOR-SETUP.md`
with full frontmatter and body (Summary, Problem/Context with duplication
and demand search verdicts, Scope, Required Changes, Non-Goals,
Acceptance Criteria, Validation, Risk Notes). Opened
[PR #641](https://github.com/xenotaur/logical_robotics_harness/pull/641).

Also updated (in the same conversation, prior turn) the handoff prompt
originally drafted for a fresh design session on this topic to reference
this new work item by ID, so the new session has a tracked control-plane
anchor rather than only free-text context.

# Validation

- `lrh validate`: 0 errors. 80 pre-existing warnings surfaced from a
  newly-landed, unrelated lint rule (`FRONTMATTER_LINT_UNSAFE_SCALAR`)
  across many other files in the repo; none reference this new file.

# Follow-up

- `session_transcript` left `pending` -- update with the durable
  Claude.app session pointer when available.
- The actual design work (running `/lrh-design` against this item) is
  intentionally not done here -- per the user's own framing, this is a
  separate design discussion meant for a fresh session, not a
  continuation of this worktree's already-closed PR work.
