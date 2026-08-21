---
execution_id: 2026_08_21_16_14_45_WI_CODEX_EXPORT_INVOCATION_FLAG_REMOVAL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_CODEX_EXPORT_INVOCATION_FLAG_REMOVAL_REVIEW)[2026-08-21T06:32:12+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_08_20_04_35_54_WI_CODEX_EXPORT_INVOCATION_FLAG_REMOVAL
pr: https://github.com/xenotaur/logical_robotics_harness/pull/571
commit: e27caf103ed78bbac7450028ec4ac9d594b9f8f3
agent: claude_code
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/571
session_transcript: claude-app:local_dd7df709-1e50-4e78-a5bf-802d06e31d50
created_at: 2026-08-21T16:14:45+00:00
---

# Summary

Addressed round-1 review comments on PR #571 (2 from `chatgpt-codex-connector`,
3 from `copilot-pull-request-reviewer`). No hosted GitHub review-bot
retrigger was used — these were the automatic first-push responses.

# Result

- **Fixed (P1, Codex):** the WI never required a *persistent* source copy of
  `agents/openai.yaml` for Codex's explicit-invocation policy. Verified
  directly against `src/lrh/skills/installer.py`:
  `_copy_skill_from_source` `shutil.rmtree`s the entire installed skill
  directory before rewriting it, and `CodexSkillRenderer` only regenerates
  `agents/openai.yaml` when source `disable-model-invocation` is `True` —
  confirmed today's `.agents/skills/lrh-codex-export/agents/openai.yaml`
  exists only as an installer-derived artifact, with no
  `src/lrh/skills/lrh-codex-export/agents/` source directory at all. Fixed:
  added an explicit Required Changes step and acceptance criterion
  requiring a persistent `src/lrh/skills/lrh-codex-export/agents/openai.yaml`
  (matching the precedent already committed at
  `src/lrh/skills/lrh-self-review/agents/openai.yaml`), verified to survive
  a fresh `lrh skills install --target codex`.
- **Valid but deferred (P2, Codex):** registering this WI in
  `WS-INVOCATION-AND-GATE-RESET`'s `work_items:` list. Confirmed the gap is
  real (not yet registered), but that file is concurrently owned by
  `WI-GATE-POLICY-CASCADE-STAGE3`'s implementation, open as PR #577 at the
  time of this round. Editing it here would recreate the concurrent-edit
  collision this program already hit once (PR #556). Documented the
  deferral explicitly in the WI's Non-Goals section rather than silently
  skipping it, with a named follow-up condition (once PR #577 lands).
- **Fixed (Copilot):** `related_design` held two `WI-*` file paths, which
  per `work-item-schema.md`'s own field table is for design-doc paths only
  — WI relationships belong in `depends_on`/`blocked_by`. Moved both to
  `depends_on`.
- **Fixed (Copilot):** an inline code span (the `git grep` command in the
  Prior Art Check section) was split across two lines, breaking Markdown
  rendering. Joined to one line.
- **Fixed (Copilot):** two bare `lrh-codex-export/SKILL.md` path references
  were ambiguous given the skill's four mirrored copies. Both changed to
  the canonical `src/lrh/skills/lrh-codex-export/SKILL.md`.

Every comment `lrh request review_response` returned was triaged in the
current diff; the one deferred item was recorded with explicit rationale,
not silently dismissed.

# Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `PYTHONPATH=src scripts/test` — 1104 tests, OK
- `PYTHONPATH=src PATH=/Users/centaur/anaconda3/envs/LRH/bin:$PATH python -m lrh.cli.main validate` — 0 errors, 0 warnings
- `git diff --check`

# Follow-up

Next: `/lrh-confirm-fixes` before merge, to verify these fixes against the
current diff and resolve the review threads. Separately: register this WI
in `WS-INVOCATION-AND-GATE-RESET`'s `work_items:` list once PR #577
(`WI-GATE-POLICY-CASCADE-STAGE3`) lands.
