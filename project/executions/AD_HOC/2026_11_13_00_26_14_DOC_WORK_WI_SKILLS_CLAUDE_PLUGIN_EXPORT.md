---
execution_id: 2026_11_13_00_26_14_DOC_WORK_WI_SKILLS_CLAUDE_PLUGIN_EXPORT
prompt_id: PROMPT(AD_HOC:DOC_WORK_WI_SKILLS_CLAUDE_PLUGIN_EXPORT)[2026-11-13T00:15:44+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/871
commit:
created_at: 2026-11-13T00:26:14+00:00
agent: claude_app
instruction_source: WI-SKILLS-CLAUDE-PLUGIN-EXPORT
session_transcript: pending
---

# Summary

`/lrh-doc-work` for `WI-SKILLS-CLAUDE-PLUGIN-EXPORT` (PR #859) and its
follow-ups (PRs #861, #862, #864), at the human's request to document the
session's recent changes if needed. The main docs (`docs/reference/cli/skills.md`
and `docs/how-to/use-lrh-with-agent-assistants.md` §5) were already
updated in those PRs. This run updates the two index lines that still
described the old state.

# Result

Confirmed at the Step 7 gate ("Make both edits"):

| Path | Action | Diataxis | Reason |
|---|---|---|---|
| `docs/reference/cli/README.md` | update | Reference | The `skills` entry listed only ChatGPT export; it now also names the Claude plugin marketplace. |
| `docs/README.md` | update | How-to index | The agent-assistants guide entry now mentions Claude Code cloud sessions on claude.ai. |

Checked, no change:
- `docs/reference/cli/chain-defaults.md` and
  `src/lrh/skills/_shared/chain-defaults.md` quote the stricter stop
  condition as the first-encounter default and as example output. Both
  are still accurate; only this repository's stored value changed
  (`b4cd0dbe`).
- The PR #864 backlog entry and the config change are control-plane files,
  not user docs.

Flagged, out of scope: the `docs/README.md` entry also omits ChatGPT,
which the guide has covered since before this work.

PR: https://github.com/xenotaur/logical_robotics_harness/pull/871

# Validation

- `scripts/version tools`, `scripts/format --check --diff`, `scripts/lint`:
  clean.
- `scripts/test`: 2410 tests, OK.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- Land PR #871, then run closeout to land this record.
- Optional: add ChatGPT to the `docs/README.md` guide entry in a later
  docs touch.
