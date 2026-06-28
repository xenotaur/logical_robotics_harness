---
resolution: "Implemented and merged in PR #343 (commit fa0bf60)"
blocked_reason: null
blocked: false
id: WI-SKILLS-CLOSEOUT-GATE-FIX
title: Improve /lrh-closeout confirm gate to surface WS exit criteria
type: deliverable
status: resolved
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-SKILLS-CLOSEOUT
related_design:
  - project/design/proposals/adopted/lrh-closeout/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
acceptance: []
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected: []
---

## Summary

Update `/lrh-closeout` Step 2 (assess state) and Step 4 (confirm gate) to
display the full `exit_criteria:` list from the workstream file and require
explicit human confirmation that each criterion is met before offering WS
closeout. The current structural check (`work_items:` all resolved) is
necessary but not sufficient.

## Problem

`WS-SKILLS-CLOSEOUT` was closed prematurely on 2026-06-27 because the
structural check passed — all IDs in `work_items:` were resolved on disk.
However, the WS `exit_criteria:` included items that were not satisfied
(e.g., `/lrh-closeout confirm gate surfaces full WS exit_criteria list`,
`WI-PROMPT-CLI-CLOSEOUT resolved in project/work_items/resolved/`) because
those WIs did not yet exist and could not be in `work_items:`.

The confirm gate showed the structural check result but never enumerated
or required per-criterion confirmation of the `exit_criteria:` list. The
user accepted without friction.

Root issue: `SKILL.md` Step 2 reads `work_items:` but never reads
`exit_criteria:`. Step 4 shows the plan table but has no block for WS
exit criteria. `closeout-workflow.md` readiness check section says nothing
about `exit_criteria:`.

## Scope

- `src/lrh/skills/lrh-closeout/SKILL.md` — Step 2 (WS assessment block),
  Step 4 (confirm gate), and "What This Skill Does Not Do"
- `src/lrh/skills/lrh-closeout/references/closeout-workflow.md` — WS
  Closeout Protocol → Readiness Check section
- `.claude/skills/lrh-closeout/SKILL.md` and
  `.claude/skills/lrh-closeout/references/closeout-workflow.md` — mirrors
  of the above (byte-for-byte identical)

## Out of Scope

- Does not add machine-parseable enforcement of exit criteria — prose
  criteria are human-authored and cannot be checked by tooling
- Does not change the `work_items:` structural check — it remains a
  necessary precondition; exit criteria confirmation is additive
- Does not modify any skill other than `/lrh-closeout`
- Does not change the WS file format or the `exit_criteria:` field schema

## Required Changes

1. **`SKILL.md` Step 2 — WS assessment block**: after determining that
   all `work_items:` are resolved (post-plan state check), read
   `exit_criteria:` from the WS file and include the list in the plan
   output — as a sub-list below the plan table row for the WS. The user
   must see the criteria at assessment time, not only at the confirm gate.

2. **`SKILL.md` Step 4 — confirm gate**: add a WS exit criteria block.
   When WS closeout is being offered, enumerate each `exit_criteria:` item
   and ask: "Are all of these criteria met? [y/N]". Only include the WS
   closeout action in the confirmed plan if the user confirms all criteria
   are met.

3. **`SKILL.md` "What This Skill Does Not Do"**: update the bullet "Does
   not replace human judgment on WS exit criteria — the skill checks
   structural completeness (all listed WIs resolved), not semantic
   completeness." to reflect the new behavior: the skill now also surfaces
   `exit_criteria:` and requires human confirmation, though it still cannot
   enforce prose criteria programmatically.

4. **`references/closeout-workflow.md` — WS Closeout Protocol → Readiness
   Check section**: add a note that after confirming structural readiness
   (`work_items:` all resolved), the skill must also surface the WS
   `exit_criteria:` list and require human confirmation at Step 4. The
   structural check is necessary but not sufficient.

5. Mirror all changes byte-for-byte to `.claude/skills/lrh-closeout/`.

## Likely Files

- `src/lrh/skills/lrh-closeout/SKILL.md`
- `src/lrh/skills/lrh-closeout/references/closeout-workflow.md`
- `.claude/skills/lrh-closeout/SKILL.md` (mirror)
- `.claude/skills/lrh-closeout/references/closeout-workflow.md` (mirror)

## Acceptance Criteria

- `/lrh-closeout` Step 2 reads `exit_criteria:` from the WS file when the
  structural check passes and includes the criteria list in the plan output.
- `/lrh-closeout` Step 4 confirm gate enumerates each `exit_criteria:` item
  when WS closeout is being offered and requires explicit user confirmation
  before including WS closeout in the confirmed plan.
- `closeout-workflow.md` WS Closeout Protocol readiness check section
  explicitly states that `exit_criteria:` must be surfaced and confirmed at
  Step 4, not only the structural `work_items:` check.
- `diff -r src/lrh/skills/lrh-closeout/ .claude/skills/lrh-closeout/`
  reports no differences.
- `lrh validate` reports 0 errors.

## Validation

- `lrh validate`
- `diff -r src/lrh/skills/lrh-closeout/ .claude/skills/lrh-closeout/`

## Open Questions

- Should per-criterion confirmation be a single "y for all" prompt or
  per-item y/n? Reasonable default: show the full list, ask "Are all of
  these criteria met? [y/N]" — minimal friction while ensuring the list
  is seen. Implementation may choose per-item if preferred.
