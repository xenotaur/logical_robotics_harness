---
execution_id: 2026_09_22_14_58_52_WI_SKILL_PATTERN_TYPED_INVOCATION_CARVEOUT
prompt_id: PROMPT(AD_HOC:WI_SKILL_PATTERN_TYPED_INVOCATION_CARVEOUT)[2026-09-22T14:57:44+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/713
commit: 6864b3b853c9012fdaefa38eb56e2e1434773eaf
created_at: 2026-09-22T14:58:52+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SKILL-PATTERN-TYPED-INVOCATION-CARVEOUT.md
session_transcript: claude-app:3278dd49-9852-4955-b978-00367552dc27
---

# Summary

Created `WI-SKILL-PATTERN-TYPED-INVOCATION-CARVEOUT` via `/lrh-work-item`, at
the user's request, to track the follow-up `km9-g` named on PR #703: the
shared `lrh-skill-pattern.md` confirm-before-write gate section has no
documented exception for a literal, user-typed slash-command invocation,
even though `WI-EXPORT-CLAUDE-SKILL-CURRENT-SESSION-DEFAULT` (merged, PR
#703) implemented exactly such an exception for `/lrh-export-claude`.

# Result

Wrote `project/work_items/proposed/WI-SKILL-PATTERN-TYPED-INVOCATION-CARVEOUT.md`
with full frontmatter and body (Summary, Problem/Context with duplication
and demand search verdicts, Scope, Required Changes, Non-Goals, Acceptance
Criteria, Validation). `type: deliverable`, `depends_on: []` (the reference
implementation is already resolved, so nothing blocks starting), `related_design`
points at the governing proposal
(`project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md`).

Duplication search found two resolved, related-but-distinct work items
(`WI-DELIBERATE-MODEL-INVOCATION`, `WI-CODEX-EXPORT-INVOCATION-FLAG-REMOVAL`)
that address the separate `disable-model-invocation` frontmatter flag, not
this gate-prose gap — no duplicate found, proceed. Demand search found no
open item and no proposal anticipating this exception — this item is the
tracking artifact.

Opened https://github.com/xenotaur/logical_robotics_harness/pull/713, planning only, no implementation.

# Validation

- `lrh validate` — 0 errors, 0 warnings.

# Follow-up

- This item is `prompt_ready` for `/lrh-implement` or `/lrh-execute` once
  the user wants it worked.
