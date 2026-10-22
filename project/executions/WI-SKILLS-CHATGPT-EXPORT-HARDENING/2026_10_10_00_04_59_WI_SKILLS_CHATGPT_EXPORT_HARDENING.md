---
execution_id: 2026_10_10_00_04_59_WI_SKILLS_CHATGPT_EXPORT_HARDENING
prompt_id: PROMPT(WI-SKILLS-CHATGPT-EXPORT-HARDENING:WI_SKILLS_CHATGPT_EXPORT_HARDENING)[2026-10-09T05:49:46+00:00]
work_item: WI-SKILLS-CHATGPT-EXPORT-HARDENING
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/810
commit: 4e97f0e57215d41b12c5ae8427d9007b67adc4d5
created_at: 2026-10-10T00:04:59+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SKILLS-CHATGPT-EXPORT-HARDENING.md
session_transcript: claude-app:9a96d262-76e5-4e8e-92e0-0e30d7776fbf
---

# Summary

Implement `WI-SKILLS-CHATGPT-EXPORT-HARDENING` via `/lrh-execute` (inline
`/lrh-implement`), on branch
`xenotaur/feat/wi-skills-chatgpt-export-hardening-impl` from `0a6e8454`. The
four implementer notes in
`2026_10_08_05_48_36_WI_SKILLS_CHATGPT_EXPORT_HARDENING_CLOSEOUT_NOTE` were
applied; note 4 (section after the first H1) supersedes the WI's "immediately
after the frontmatter" wording.

# Result

- `src/lrh/skills/installer.py`: `SkillSource.skill_names()` skips
  dot-prefixed top-level directories after the existing symlink refusal, so
  `install`, `status`, `check`, and `export` ignore `.git/` and similar.
- `src/lrh/skills/exporter.py`:
  - a present `disable-model-invocation` / `policy.allow_implicit_invocation`
    must be `true` or `false` (a blank value fails with a fix hint); absent
    keys still mean "not manual-only";
  - `compatibility` must not be empty or whitespace-only (spec bound 1-500
    cited in a comment); `when_to_use` must be a non-blank string (note 2);
  - `when_to_use` is folded into `description` with one space when the
    stripped result fits in 1024 characters (note 1), otherwise added as a
    generated `## When to use` section after the body's first H1 (note 4),
    with a `when_to_use_section` notice; it is never reported as stripped;
  - section placement follows CommonMark fences and ATX H1 indent and keeps
    the body's line endings;
  - the capability notice no longer claims instructions are "exported
    unchanged".
- Tests and docs pinning the old behavior were updated (note 3):
  `tests/skills_exporter_test.py`, `tests/skills_installer_test.py`,
  `docs/reference/cli/skills.md`,
  `docs/how-to/use-lrh-with-agent-assistants.md`.
- Canonical sources and the Codex/Antigravity renderers are unchanged. The
  section path applies to `lrh-export-claude` (1480), `lrh-config-gates`
  (1357; the WI's 1143 predates PR #780), and `lrh-work-remains` (1155).

Pre-push diff-mode self-review:
`project/executions/AD_HOC/2026_10_10_00_03_47_WI_SKILLS_CHATGPT_EXPORT_HARDENING_IMPL_SELFREVIEW.md`
(no P1/P2; verified P3s fixed before the first push).

# Validation

- `scripts/version tools`: Python 3.11.15, ruff 0.15.12 (LRH conda env).
- `scripts/format --check --diff`: clean.
- `scripts/lint`: exit 0.
- `scripts/test`: 2185 tests, OK.
- `lrh validate`: 0 errors, 0 warnings.
- `lrh skills export --target chatgpt --source current-repo --out <tmp>`:
  20 exported, 5 manual-only skipped (codex-export, confirm-fixes, execute,
  land, self-review), `when_to_use_section` on exactly the 3 skills above.
- `lrh skills install --dry-run --local --source <tmp with demo-skill/ and
  .git/>`: only `demo-skill` would install.
- New regression tests fail against the pre-change source (`git archive HEAD
  src`); the hidden-symlink invariant test passes on both.

# Follow-up

- Run `/lrh-land` for PR #810; resolve the WI at closeout.
