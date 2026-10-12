---
execution_id: 2026_10_11_05_34_32_NORMALIZE_CLAUDE_APP_AGENT_FIELD
prompt_id: PROMPT(AD_HOC:NORMALIZE_CLAUDE_APP_AGENT_FIELD)[2026-10-11T04:29:03+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/828
commit:
created_at: 2026-10-11T05:34:32+00:00
agent: claude_app
instruction_source: "ad-hoc: normalize agent: claude-app to claude_app in the 18 execution records from PRs 793, 804, 808"
session_transcript: pending
---

# Summary

Ad-hoc normalization, at the user's request ("Please normalize the
records"): `agent: claude-app` becomes `agent: claude_app` in the 18
execution records from PRs #793, #804 and #808 that used the hyphenated
form. Only the frontmatter `agent:` line changes. The
`session_transcript: claude-app:<id>` prefixes are correct and were left
unchanged.

# Result

- PR #828, implementation commit on branch
  `xenotaur/chore/normalize-claude-app-agent-field`: 18 files, 18 one-line
  swaps.
- No `^agent: claude-app` remains under `project/`.
- PR #816's two records were already normalized in its closeout.
- No code depends on the hyphenated agent value (verified by grep and the
  diff-mode self-review).

# Validation

Python 3.11.17, Ruff 0.15.12, Black 26.3.1 (`LrhMain` env,
`PYTHONPATH=src`):

- `scripts/format --check --diff`: clean
- `scripts/lint`: clean
- `scripts/test`: 2256 tests, OK
- `lrh validate`: 0 errors, 0 warnings
- diff check: exactly 18 `-agent: claude-app` / `+agent: claude_app` line
  pairs
- self-review: 0 findings

# Follow-up

None.
