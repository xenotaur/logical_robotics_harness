---
execution_id: 2026_08_31_02_01_40_DOC_WORK_WI_SKILLS_LRH_CONFIG_GATES_AND_SKILLS
prompt_id: PROMPT(AD_HOC:DOC_WORK_WI_SKILLS_LRH_CONFIG_GATES_AND_SKILLS)[2026-08-30T16:06:53+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
agent: claude_app
instruction_source: WI-SKILLS-LRH-CONFIG-GATES,WI-SKILLS-LRH-CONFIG-SKILLS
session_transcript: claude-app:81eca1c8-36fa-493d-b0e5-08c0501ec1d0
created_at: 2026-08-31T02:01:40+00:00
---

# Summary

`/lrh-doc-work` run updating documentation to reflect
`WI-SKILLS-LRH-CONFIG-GATES` (PR #636) and `WI-SKILLS-LRH-CONFIG-SKILLS`
(PR #652) together, as a deliberate, user-confirmed exception to
`doc-work-scope.md`'s one-work-reference-per-invocation rule -- the two
WIs are a matched sibling pair (same Option C pattern, same session,
one built directly on the other), and covering them in one PR avoids two
near-duplicate documentation changes.

# Result

- `docs/reference/cli/agent-skills.md` (new): CLI reference for
  `lrh agent-skills status`.
- `docs/reference/cli/chain-defaults.md` (new): CLI reference for
  `lrh chain-defaults status` and `check-staleness`. `status` is this
  WI's own new subcommand; `check-staleness` predates it (an earlier
  session's increment) but was never documented either -- included here
  since a reference page covering only one of two subcommands in the
  same group would be misleadingly incomplete, not scope creep into an
  unrelated feature.
- `docs/reference/cli/README.md`: added index entries for both new pages.
- `docs/reference/schemas/agent-skills-config.md`: added a short
  cross-reference to `lrh agent-skills status` / `/lrh-config-skills` as
  the way to inspect or edit `sources`/`targets`/`scope`, alongside
  manual editing.
- `docs/how-to/use-lrh-with-agent-assistants.md`: its own Prerequisites
  bullet already mentioned `project/agent_skills.yaml`; added a pointer
  to `/lrh-config-skills` for setting it up.

Not touched (explicitly out of scope, confirmed with the user before
starting): no new Tutorial or Explanation doc -- neither WI introduces a
new concept beyond what the existing Precedence section and the skills'
own internal docs already cover. `docs/how-to/keep-skills-up-to-date.md`
is about the skill-install mechanism, a different concern, and isn't
stale from this work.

# Validation

- `scripts/version tools`: all pinned tool versions matched
  (`black==26.3.1`, `ruff==0.15.12`).
- `scripts/format --check --diff`: clean, 247 files unchanged.
- `scripts/lint`: clean (ruff + black).
- `scripts/test`: environment-broken in this worktree, same pre-existing
  gap noted in this session's earlier execution records -- it discovers
  `lrh` from a separate, stale installed clone rather than this
  worktree's `src/`. `PYTHONPATH=src python3 -m pytest tests/ -q` (the
  correct in-repo check) run instead: full suite, 1529 passed, 0 failed
  -- confirming this docs-only change didn't break anything, even though
  no source files changed.
- `lrh validate`: 0 errors, 1 pre-existing warning unrelated to this
  change.
- All relative Markdown links in the new/edited files verified to
  resolve to real files via a direct filesystem check (not just visual
  inspection).

# Follow-up

None deferred.
