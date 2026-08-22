---
execution_id: 2026_08_22_00_00_21_WI_FRONTMATTER_PARSER_CONSOLIDATION
prompt_id: PROMPT(AD_HOC:WI_FRONTMATTER_PARSER_CONSOLIDATION)[2026-08-21T06:33:55+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/595
commit: 
created_at: 2026-08-22T00:00:21+00:00
agent: claude_app
instruction_source: project/design/proposals/proposed/lrh-frontmatter-parser/00_proposal.md
session_transcript: "claude-app:494c3b1f-14c8-46bf-a4e3-0b6e8df119e8"
---

# Summary

Files the two implementation work items for `PROP-LRH-FRONTMATTER-PARSER`
(PR #531) under `WS-LRH-FRONTMATTER-PARSER`, in a single PR per the
user's request: `WI-FRONTMATTER-PARSER-CONSOLIDATION` (prompt ID above)
and `WI-FRONTMATTER-MIGRATION-LINT-GUARD` (prompt ID
`PROMPT(AD_HOC:WI_FRONTMATTER_MIGRATION_LINT_GUARD)[2026-08-21T06:33:55+00:00]`,
minted at the same time; this one record covers both, matching the
single-PR filing).

# Result

Drafted both work items following the proposal's Implementation Plan.
Split the plan's 5 items into 2 WIs at natural atomic-PR boundaries: WI-1
(parser/validator consolidation, datetime consumer patches, and content
fixes — interdependent, can't ship the parser swap without all three) and
WI-2 (migration tool + lint guard, which share one detector per the
proposal's Decision 4, so building them separately would duplicate the
detector). WI-2 depends_on WI-1.

Before writing, discovered `WS-LRH-FRONTMATTER-PARSER` had `work_items:
[]` still — no other session had filed related work in the meantime.
User then asked "is this still relevant and valid" given how much
concurrent activity landed on `main` since the proposal merged (51+
commits). Re-verified rather than assumed: confirmed the narrow crash
fix (commit `2e1af28d`, closed out via PR #574) doesn't reduce this
scope; re-ran the old-parser-vs-`yaml.safe_load` audit against the
current tree and found the "27 files" count had drifted to 30 (20
syntax-error + 10 colon-collapse) — updated both WIs and the workstream
to describe this as re-locate-at-implementation-time rather than a
frozen number, since it will keep drifting; added `WI-PARSER-HARDENING`
to the workstream's "closed as superseded" exit criterion (it didn't
exist yet when that criterion was first written); checked for and found
no colliding open PR.

# Validation

- `lrh validate` — 0 errors, 0 warnings (re-run after the re-verification
  fixes, on the current `main` tip)
- No open PR targets the same file paths (checked via `gh pr list`)

# Follow-up

- File a follow-up WI for the migration tool's allow-list fallback mode
  (for repos without LRH's lenient-parser lineage) if a downstream repo
  ever needs it — deliberately deferred per the proposal's Open
  Questions.
