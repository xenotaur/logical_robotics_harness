---
execution_id: 2026_10_08_05_55_38_WI_SESSION_ID_CODEX_SKILL_RENAME
prompt_id: PROMPT(WI-SESSION-ID-CODEX-SKILL-RENAME:WI_SESSION_ID_CODEX_SKILL_RENAME)[2026-10-08T02:03:53+00:00]
work_item: WI-SESSION-ID-CODEX-SKILL-RENAME
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/790
commit:
created_at: 2026-10-08T05:55:38+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SESSION-ID-CODEX-SKILL-RENAME.md
session_transcript: pending
---

# Summary

Implemented `WI-SESSION-ID-CODEX-SKILL-RENAME` via `/lrh-execute` (with
`/lrh-implement` inlined). `lrh-codex-session` is renamed to
`lrh-session-id-codex`, and a deprecated stub is kept under the old name,
per `PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES` Decisions 1 and 3.

# Result

PR #790, branch `xenotaur/feat/wi-session-id-codex-skill-rename` (from
`origin/main` at `b559d362`), commit `8902cdf3`.

- **New skill:** `src/lrh/skills/lrh-session-id-codex/` is the old skill
  with only its name, H1, and usage example changed (3 lines).
  `agents/openai.yaml` is unchanged.
- **Stub:** `lrh-codex-session` sets `disable-model-invocation: true`, has
  the description "Deprecated: use /lrh-session-id-codex. Do not select
  this skill…", and hands off with the same arguments.
  - **Finding:** `CodexSkillRenderer._render_openai_yaml` uses
    `setdefault`, so a source `allow_implicit_invocation: true` survives
    rendering. The stub therefore ships an explicit `false`; the rendered
    `.agents` copy confirms it.
- **Antigravity invocation control (checked, as the WI requires):** Google's
  Antigravity skills codelab documents only `name` and `description`, with
  no invocation-control field. So there is no renderer change, and the
  stub's description carries the protection.
- **References updated:** `lrh-codex-export`, `lrh-session-id-claude`,
  `CLAUDE.md`, `docs/conversations/codex_export.md`, and
  `docs/reference/cli/conversation.md`.
  - Outside `artifacts_expected`: `lrh-session-id-claude/SKILL.md` (covered
    by the "every current skill" criterion), and the portability test's
    `AFFECTED_SKILLS` entry, moved to the skill that holds the content.
  - Unchanged on purpose: the rename-planning docs, resolved/adopted docs
    (including `WI-SKILLS-LRH-CLAUDE-SESSION`, now resolved), and execution
    records.
- **Mirrors:** all four touched skills were rendered to all three targets
  one skill at a time, with no `--force`. The `.gemini` copy of
  `lrh-session-id-claude` also caught up with a section already in source.

Deviations:

- The branch was created from `origin/main` directly, because `main` is
  checked out in the primary worktree.
- Format and lint ran under the `LRH` conda env.
- The canonical `main` versions of the chain skills were followed, because
  the installed copies lag.

# Validation

- `scripts/format --check --diff`: exit 0.
- `scripts/lint`: exit 0.
- `scripts/test`: 1976 tests OK.
- `lrh validate`: 0 errors, 0 warnings.
- `lrh skills check --target claude --local --source current-repo`: clean.
- `lrh skills status --target codex|antigravity --local --source
  current-repo`: all four touched skills are up to date.
- `lrh chain-defaults status`: `stale: False`.
- `git grep -ln lrh-codex-session -- src/lrh/skills`: only the stub, plus
  the "formerly" note.

# Follow-up

- `/lrh-land` for PR #790, then closeout, which resolves the WI. That
  leaves `WI-LRH-SESSION-ID-DISPATCHER` with all three dependencies
  resolved.
- `WI-EXPORT-SKILL-FAMILY-RENAME` updates the `/lrh-codex-export`
  reference in `lrh-session-id-codex`, per its Risk Notes.
