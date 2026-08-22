---
execution_id: 2026_08_22_05_04_40_WI_CODEX_EXPORT_INVOCATION_FLAG_REMOVAL_IMPL
prompt_id: PROMPT(WI-CODEX-EXPORT-INVOCATION-FLAG-REMOVAL:WI_CODEX_EXPORT_INVOCATION_FLAG_REMOVAL_IMPL)[2026-08-21T23:59:33+00:00]
work_item: WI-CODEX-EXPORT-INVOCATION-FLAG-REMOVAL
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/601
commit: 834ac0a9d780342a0e26e0c0f27ac476f7a2cea2
agent: claude_code
instruction_source: project/work_items/proposed/WI-CODEX-EXPORT-INVOCATION-FLAG-REMOVAL.md
session_transcript: claude-app:local_dd7df709-1e50-4e78-a5bf-802d06e31d50
created_at: 2026-08-22T05:04:40+00:00
---

# Summary

Implemented `WI-CODEX-EXPORT-INVOCATION-FLAG-REMOVAL`: assessed and removed
`lrh-codex-export`'s orphaned `disable-model-invocation` flag, re-checked
against the skill's current text (post-PR-#579's durable-archive-by-default
rewrite) rather than the WI's original drafting-time assumptions.

# Result

- Assessment: no platform-enforced guard needed — single-shot CLI wrapper,
  no subagent dispatch, no chain-authorization gate; none of the three gap
  categories that justified retaining the flag on the other 4 skills apply.
- `disable-model-invocation` removed; `when_to_use` added, naming the
  durable-archive-by-default consequence explicitly (PR #579 changed the
  default from ephemeral `/tmp` to a permanent archive).
- Persistent `src/lrh/skills/lrh-codex-export/agents/openai.yaml` committed
  — required per PR #571's own review; verified directly against
  `installer.py:190-214` that it survives the Codex-target render cycle
  unmodified once the flag is absent.
- Propagated to all corpora (repo-local + user-scope, Claude/Codex/
  Antigravity) via `lrh skills install`; verified `up to date` for all
  three targets.
- Decision recorded in `project/memory/decision_log.md`.
- Diff-mode `/lrh-self-review` ran before push (see
  `2026_08_22_05_03_11_WI_CODEX_EXPORT_INVOCATION_FLAG_REMOVAL_IMPL_SELFREVIEW.md`)
  — clean pass, every claim independently verified against actual file/code
  content.
- Opened as PR #601.

# Validation

- `scripts/version tools`
- `scripts/format --check --diff` — clean
- `scripts/lint` — clean
- `PYTHONPATH=src PATH=/Users/centaur/anaconda3/envs/LRH/bin:$PATH python -m lrh.cli.main validate` — 0 errors, 0 warnings
- `PYTHONPATH=src PATH=/Users/centaur/anaconda3/envs/LRH/bin:$PATH python -m lrh.cli.main skills check --target all --local` — `lrh-codex-export` up to date on all 3 targets
- Diff-mode `/lrh-self-review` (see linked `_SELFREVIEW` record)

# Follow-up

None outstanding for this item. Continuing to `/lrh-land` for PR #601
(review-response, confirm-fixes, merge gate, closeout).
