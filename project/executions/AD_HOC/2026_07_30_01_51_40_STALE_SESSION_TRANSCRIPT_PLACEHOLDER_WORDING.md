---
execution_id: 2026_07_30_01_51_40_STALE_SESSION_TRANSCRIPT_PLACEHOLDER_WORDING
prompt_id: PROMPT(AD_HOC:STALE_SESSION_TRANSCRIPT_PLACEHOLDER_WORDING)[2026-07-30T01:51:22-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
agent: claude_app
instruction_source: follow-up item #4 from PR #438's final report
session_transcript: claude-app:3fcab22f-9ebe-4392-bf31-2103fce507f2
created_at: 2026-07-30T01:51:40-04:00
---

# Summary

Fix the last 5 remaining instances of the stale `claude-app:<session-id>`
session-transcript placeholder wording under `src/lrh/skills/` (the active
skill sources and their `.claude/skills/` mirrors), left out of scope in
PR #438 since review there didn't flag them (only files PR #438 actually
touched got fixed): `lrh-confirm-fixes/SKILL.md`,
`lrh-doc-organize/references/organize-workflow.md`,
`lrh-implement/references/lrh-implement-workflow.md`, `lrh-implement/SKILL.md`,
`lrh-review-response/SKILL.md`. Historical execution records and design
proposals elsewhere in the repo still contain the old string as immutable
narrative prose — out of scope here, not touched.

# Result

Updated all 5 to `claude-app:<host-uuid-stem>`, matching the canonical form
documented in `lrh-closeout/references/closeout-workflow.md` (the host
session id, `local_` prefix stripped — not the child SDK id). Mirrored into
`.claude/skills/` (`diff -r` clean). Confirmed no remaining instances of
the stale form anywhere under `src/lrh/skills/`.

# Validation

- `grep -rn "claude-app:<session-id>" src/lrh/skills/` — no matches after
  the fix
- `lrh validate` — 0 errors, 1 pre-existing unrelated warning
  (`WS-LRH-ASSISTANTS` no actionable leaf)
- `scripts/format --check --diff`, `scripts/lint` — clean
- `diff -r` clean between `src/lrh/skills/<skill>` and `.claude/skills/<skill>`
  for all 4 skills touched

# Follow-up

None — this closes out the last item from PR #438's follow-up list.
