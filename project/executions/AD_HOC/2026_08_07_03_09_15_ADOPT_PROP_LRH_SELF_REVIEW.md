---
execution_id: 2026_08_07_03_09_15_ADOPT_PROP_LRH_SELF_REVIEW
prompt_id: PROMPT(AD_HOC:ADOPT_PROP_LRH_SELF_REVIEW)[2026-08-07T03:06:42+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/501
commit: 5578815965b90ab8e043a584040679239ebe7dc0
created_at: 2026-08-07T03:09:15+00:00
agent: claude_app
instruction_source: chat (user request following a codebase survey that found PROP-LRH-SELF-REVIEW's frontmatter stale relative to its actual shipped state)
session_transcript: claude-app:f7e2dee6-84cf-4396-bc1e-fc9c23261c9c
---

# Summary

Adopt `PROP-LRH-SELF-REVIEW`: its governing WI (`WI-SKILLS-LRH-SELF-REVIEW`)
shipped and was resolved (PR #467), but the proposal's own frontmatter
still read `status: proposed`, `implementation_status: not_started`. No
workstream ever governed it (`WI-SKILLS-LRH-SELF-REVIEW`'s own
`related_workstreams: []` confirms the planned `WS-SKILLS-SELF-REVIEW`
governance home was never created), so `/lrh-closeout`'s
WS-triggered proposal-adoption path never fired — this fixes it directly.

# Result

- `project/design/proposals/proposed/lrh-self-review/00_proposal.md` →
  `project/design/proposals/adopted/lrh-self-review/00_proposal.md`
  (`git mv`), frontmatter updated to `status: adopted`,
  `implementation_status: implemented`,
  `implemented_by: [WI-SKILLS-LRH-SELF-REVIEW]`, `updated_on: 2026-08-07`
  — matching the exact field shape of the precedent this proposal's own
  Decision 7 named (`PROP-LRH-CONFIRM-FIXES`, verified directly).
- Updated the 3 files that cited the stale `proposed/` path:
  `src/lrh/skills/lrh-self-review/SKILL.md`,
  `.claude/skills/lrh-self-review/SKILL.md` (both mirrors — `diff -r`
  reconfirmed clean), and `WI-SKILLS-LRH-SELF-REVIEW.md`'s
  `related_design:` field.
- Deliberately did **not** edit
  `project/executions/AD_HOC/2026_08_02_16_34_11_WI_SKILLS_LRH_SELF_REVIEW_IMPL_CONFIRM.md`,
  which also cites the old path — that citation is in its landed `#
  Result` narrative, describing what was true at the time that round ran;
  execution-record narrative bodies are immutable once landed.
- Also found `project/design/backlog.md`'s "Self-review-first tier..."
  entry still states "Not yet filed as a proposal or work item" — also
  stale, but a different file with no established "mark as shipped"
  convention found in it, and outside this fix's requested scope. Left
  as a follow-up rather than editing without direction.

# Validation

- `lrh validate`: 0 errors, 0 warnings
- `diff -r src/lrh/skills/lrh-self-review/ .claude/skills/lrh-self-review/`:
  clean
- `scripts/format`/`scripts/lint`: blocked by a pre-existing environment
  tool-version mismatch (black `26.3.1` required vs. `25.11.0` installed,
  `pyright` not installed) — unrelated to this change, which touches only
  Markdown files, no Python.

# Follow-up

- `project/design/backlog.md`'s "Self-review-first tier for reducing
  GitHub bot-review credit consumption" entry (line ~796) still says the
  idea is "not yet filed" — stale given `PROP-LRH-SELF-REVIEW` and
  `WI-SKILLS-LRH-SELF-REVIEW` both now show adopted/resolved. Flagged for
  the human to decide how to handle (no existing convention in that file
  for marking an entry shipped).
- `WI-REVIEW-LANDED-CANONICAL-CHECK` (a separate, unrelated item from an
  earlier session) remains `proposed`/unimplemented — not addressed here.
