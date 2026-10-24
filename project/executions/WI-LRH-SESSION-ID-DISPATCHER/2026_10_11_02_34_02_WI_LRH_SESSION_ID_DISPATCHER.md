---
execution_id: 2026_10_11_02_34_02_WI_LRH_SESSION_ID_DISPATCHER
prompt_id: PROMPT(WI-LRH-SESSION-ID-DISPATCHER:WI_LRH_SESSION_ID_DISPATCHER)[2026-10-10T05:43:02+00:00]
work_item: WI-LRH-SESSION-ID-DISPATCHER
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/824
commit:
created_at: 2026-10-11T02:34:02+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-SESSION-ID-DISPATCHER.md
session_transcript: pending
---

# Summary

Implemented `WI-LRH-SESSION-ID-DISPATCHER` via `/lrh-execute`, adding the
metadata-only `/lrh-session-id` dispatcher. It follows
`PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES` Decision 2. The dispatcher
selects the vendor, then carries out the matching `lrh-session-id-<vendor>`
skill's steps inline.

# Result

- Added `src/lrh/skills/lrh-session-id/SKILL.md` and
  `agents/openai.yaml`, with `allow_implicit_invocation: true`.
- **Vendor order:**
  1. An explicit first argument (`claude`, `codex` or `antigravity`).
  2. The single environment signal that is set: `CLAUDE_CODE_SESSION_ID`,
     `CODEX_THREAD_ID` or `ANTIGRAVITY_CONVERSATION_ID`.
  3. Otherwise, ask.
- **Missing variant:** checked at run time in any skills scope; reported as
  unsupported with `session_transcript: pending`, with no stub fallback.
  Antigravity is not hard-coded.
- **Other skill rules:**
  - Safety rules forbid transcript reads and exports, and
    `export_transcript`.
  - Environment variable values are never printed.
  - The pending-on-ask path has a defined report format.
- Rendered to `.claude/skills/`, `.agents/skills/` and
  `.gemini/plugins/lrh/skills/` one skill at a time, without `--force`.
- `CLAUDE.md` lists `/lrh-session-id`.
- `skills_reference_portability_test.py` adds `lrh-session-id` to
  `AFFECTED_SKILLS`.
- Commits: `0848381d` (implementation) and the pre-push self-review fix.

# Validation

- `scripts/version tools`: ran.
- `lrh validate`: 0 errors, 0 warnings.
- `scripts/format --check --diff`: clean.
- `scripts/lint`: passes.
- `scripts/test --log`: passes.
- `lrh skills check --target claude --local`: up to date.
- `lrh skills status --target codex|antigravity --local --source
  current-repo`: `lrh-session-id` up to date on both.
- Pre-push diff-mode self-review: ready to push, with three findings fixed
  before the push. See the `_SELFREVIEW` record.

# Follow-up

- Open PR #797 (`WI-ANTIGRAVITY-SESSION-ID-RESOLVER`) adds
  `lrh-session-id-antigravity`. The dispatcher picks it up without edits.
  Expect a small adjacent-line conflict in `CLAUDE.md` for whichever PR
  lands second.
- Optional wording follow-up: `lrh-session-id-claude` still says "a future
  `/lrh-session-id` dispatcher". It was left alone because changing variants
  is a non-goal.
- Out of scope: routing `/lrh-closeout`, `/lrh-land` and `/lrh-implement`
  through the dispatcher.
