---
execution_id: 2026_08_01_15_52_10_OUTDATED_THREAD_RECOVERY_REVIEW
prompt_id: PROMPT(AD_HOC:OUTDATED_THREAD_RECOVERY_REVIEW)[2026-08-01T15:51:23-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_08_01_12_28_08_OUTDATED_THREAD_RECOVERY
pr: https://github.com/xenotaur/logical_robotics_harness/pull/457
commit: 4c1b856ae19ff1f0b854321bfc9ce5cf46b25239
created_at: 2026-08-01T15:52:10-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/457
session_transcript: claude-app:61881211-bfd7-40cb-8080-33938a265398
---

# Summary

Addresses the first review round on PR #457 (planning artifacts:
PROP-OUTDATED-THREAD-RECOVERY + 2 work items). Codex and Copilot together
raised 6 findings; all fixed in one batch and pushed as a single commit
to minimize retrigger rounds, per this session's own discussion about
GitHub review credit consumption.

# Result

One commit pushed to branch `xenotaur/feat/outdated-thread-recovery`:

- `4c1b856` — fixes all 6 findings plus the workstream fold.

**Issue A — Merge-gate invariant undefined for fix now/defer (Codex,
P1):** Fixed. Decision 2 didn't say how "fix now" or "defer" satisfy
`/lrh-land` Step 6's green-verdict requirement. Added explicit
disposition: "fix now" loops back through `/lrh-confirm-fixes` for a
fresh verdict before Step 6 is reachable; "defer" is a named, audited,
in-session override of the invariant, not a silent bypass. Propagated
the same language into WI-B's acceptance criteria and Required Changes.

**Issue B — Workstream traversal (Codex, P2, fabricated citation but
valid underlying claim):** Codex cited `AGENTS.md:L43-L49`, which does
not exist/say what was claimed — verified directly against
`src/lrh/control/planning_tree.py:315` instead, which confirmed the
substantive point: planning-tree traversal builds `children_by_parent_id`
from a workstream's `work_items:` list, not `related_workstreams`
(metadata-only). This reopened an earlier decision made in this same
session (leave the two WIs related-only) — surfaced the new technical
fact to the user rather than silently overriding or silently keeping the
old call. User chose to fold; added both WI IDs to
`WS-SKILLS-EXECUTE`'s `work_items:` list.

**Issues C-F — wording/terminology (Copilot x4):** Fixed. "supersedes/
closes" language in the proposal contradicted the backlog entry's own
"stays open until implemented" status (2 occurrences); normalized
"Problematic-resolution"/"Problematic-comment" to the taxonomy's actual
spelling ("Problematic resolution"/"Problematic comment", verified
against `src/lrh/skills/lrh-confirm-fixes/SKILL.md:164-165`) across
WI-B (9 occurrences); clarified WI-B's backlog-closure step timing
(link now, close only once both items are implemented).

**Round 2 (commit `3380a17`): Issue G — same closure-timing bug, missed
in WI-A (Codex P2 + Copilot suppressed, same root cause independently
caught by both):** The round-1 fix only corrected WI-B's and the
proposal's closure-timing wording; WI-A's own Demand-search section had
the identical bug ("Close the backlog entry once this item ... are
filed" — filed, not implemented). Fixed to match the same
link-now/close-on-implementation language used everywhere else.

# Validation

scripts/version tools -- Black 26.3.1, Ruff 0.15.12 confirmed
scripts/format --check --diff -- 179 files unchanged
lrh validate -- 0 errors, 1 pre-existing unrelated warning
grep -n "^def _matches_state" -A 12 src/lrh/integrations/github/formatters.py -- confirmed line 31-40 citation still accurate against current main
grep -n "Problematic" src/lrh/skills/lrh-confirm-fixes/SKILL.md -- confirmed exact taxonomy spelling before applying the fix
grep -n "work_items\|parent_id" src/lrh/control/planning_tree.py -- confirmed Codex's underlying traversal claim before triaging it as valid, independent of its fabricated citation

# Follow-up

- Retrigger both reviewers on this commit and verify all 6 threads
  resolve against the pushed diff.
- Update `session_transcript` to the final host session id if it differs
  after the session ends.
