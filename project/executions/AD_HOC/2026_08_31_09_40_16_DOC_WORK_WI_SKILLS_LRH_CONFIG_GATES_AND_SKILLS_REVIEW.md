---
execution_id: 2026_08_31_09_40_16_DOC_WORK_WI_SKILLS_LRH_CONFIG_GATES_AND_SKILLS_REVIEW
prompt_id: PROMPT(AD_HOC:DOC_WORK_WI_SKILLS_LRH_CONFIG_GATES_AND_SKILLS_REVIEW)[2026-08-31T09:40:08+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/657
commit: 
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/657
session_transcript: claude-app:81eca1c8-36fa-493d-b0e5-08c0501ec1d0
created_at: 2026-08-31T09:40:16+00:00
---

# Summary

`/lrh-review-response` round for PR #657, inlined from `/lrh-land` Step 4.

# Result

5 findings, all present, valid, and feasible (3 from
`copilot-pull-request-reviewer`, 2 from `chatgpt-codex-connector`, P2 each):

1. **(copilot)** `agent-skills-config.md`'s intro used singular "skill
   source, install target" while the rest of the page (and the schema
   itself) uses plural `sources`/`targets`. Fixed: pluralized to match.
2. **(copilot)** The same doc's new cross-reference paragraph presented
   `lrh agent-skills status` and `/lrh-config-skills` as interchangeable
   for "create/edit," but `status` is read-only (verified directly:
   `agent_skills_status.py`'s CLI dispatch only calls `compute_status()`
   and never writes). Fixed: attributed inspection to `status`, creation/
   editing solely to `/lrh-config-skills`.
3. **(copilot)** Same conflation in `use-lrh-with-agent-assistants.md`'s
   Prerequisites bullet ("set this file up" attributed to both
   commands). Fixed: attributed setup solely to `/lrh-config-skills`.
4. **(codex, P2)** `chain-defaults.md`'s staleness description claimed
   marker-scoped diffing unconditionally, but `gate_staleness.py`
   (verified directly, `WatchTarget`/`resolve_watch_targets`) has a
   second, distinct mechanism for user-scope installed targets with no
   git history: a persisted whole-file SHA-256 fingerprint comparison,
   where *any* content change counts as stale, not just
   `GATE-DEFINITION` region changes. This mechanism (PR #649, merged
   2026-08-29) already existed when this doc-work PR was written
   (2026-08-30) -- checked via `git log -S"FINGERPRINT_PATH"` and
   confirmed with commit timestamps; this was a research gap on my part
   at Steps 4-5, not code that changed after the doc was written. Fixed:
   qualified both the `status` and `check-staleness` sections to
   describe both mechanisms and when each applies.
5. **(codex, P2)** Same root conflation as findings 2/3, stated more
   precisely: the schema doc's wording let "either" command be read as
   able to mutate the config. Fixed by the same edit as finding 2.

All 5 fixed directly in `docs/reference/schemas/agent-skills-config.md`,
`docs/how-to/use-lrh-with-agent-assistants.md`, and
`docs/reference/cli/chain-defaults.md`.

# Validation

- `lrh validate`: 0 errors, 1 pre-existing warning unrelated to this
  change.
- Identity verified before triage: `gh pr view` `headRefOid` matched
  local `HEAD` (`53810aef...`) exactly.
- Finding 4 verified directly by reading
  `src/lrh/gate_staleness.py`'s `WatchTarget`/`resolve_watch_targets`
  and confirming via `git log -S"FINGERPRINT_PATH"` plus commit
  timestamps that the fingerprint mechanism (PR #649, 2026-08-29)
  predates this doc-work PR (2026-08-30) -- a research gap in Steps 4-5
  of this run, not code that changed after the doc was written.
- All relative Markdown links in the edited files re-verified to resolve
  via a direct filesystem check after the edits.

# Follow-up

None deferred -- all 5 findings fixed in this round.
