---
execution_id: 2026_07_05_02_51_26_WI_DECISION_RECORD_CONVENTIONS
prompt_id: PROMPT(WI-DECISION-RECORD-CONVENTIONS:WI_DECISION_RECORD_CONVENTIONS)[2026-07-05T02:43:23-04:00]
work_item: WI-DECISION-RECORD-CONVENTIONS
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/374
commit: 560c096
created_at: 2026-07-05T02:51:26-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-DECISION-RECORD-CONVENTIONS.md
session_transcript: pending
---

# Summary

Implement `WI-DECISION-RECORD-CONVENTIONS`: document LRH's two-tier
decision-recording model in `design.md` and retrofit a `DEC-*` id onto the
existing promoted decision file, `precedence_semantics.md`.

# Result

- Added a new subsection under `design.md` §14 (Revision Policy) explaining
  the two-tier model: `decision_log.md` is the default landing spot for
  routine decisions; `project/memory/decisions/<slug>.md` is for decisions
  promoted out of the log when other documents need to cite them
  independently and repeatedly. States the `DEC-*` id convention, scoped to
  the promoted tier only (not applied to `decision_log.md` entries).
- Added a YAML frontmatter block to
  `project/memory/decisions/precedence_semantics.md`
  (`id: DEC-PRECEDENCE-SEMANTICS`, `status: accepted`, `date: 2026-04-22`).
  Existing body content (including section anchors cited by other docs) was
  left untouched.
- All five acceptance criteria satisfied; nothing skipped.

# Validation

- `scripts/version tools` — lrh 0.2.5.dev673+g111f7ab13, Python 3.11.8, Ruff 0.15.12, Black 26.3.1
- `scripts/format --check --diff` — 175 files unchanged
- `scripts/lint` — all checks passed
- `scripts/test` — 696 tests OK
- `lrh validate` — 0 errors, 0 warnings
- `grep -n "id:" project/memory/decisions/precedence_semantics.md` — `id: DEC-PRECEDENCE-SEMANTICS`
- `git diff --stat project/memory/decision_log.md` — no output (unmodified, confirmed)
- `python3 -c "import yaml; ..."` — frontmatter parses as `{'id': 'DEC-PRECEDENCE-SEMANTICS', 'status': 'accepted', 'date': date(2026, 4, 22)}`

# Follow-up

- `session_transcript: pending` should be updated to `claude-app:<session-id>` after this session ends.
- Future promotions of `decision_log.md` entries into their own `decisions/<slug>.md` files should follow the `DEC-*` convention documented here — this WI intentionally did not fabricate a second promoted file.
