---
execution_id: 2026_10_29_01_13_43_WI_SKILLS_CLAUDE_PLUGIN_EXPORT
prompt_id: PROMPT(WI-SKILLS-CLAUDE-PLUGIN-EXPORT:WI_SKILLS_CLAUDE_PLUGIN_EXPORT)[2026-10-29T00:53:34+00:00]
work_item: WI-SKILLS-CLAUDE-PLUGIN-EXPORT
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/859
commit:
created_at: 2026-10-29T01:13:43+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SKILLS-CLAUDE-PLUGIN-EXPORT.md
session_transcript: pending
---

# Summary

Implemented WI-SKILLS-CLAUDE-PLUGIN-EXPORT through `/lrh-execute`. The user
approved the chain with the stored completion and stop-work conditions, and
chose to run the cloud-session dogfood after merge, before closeout resolves
the work item. Branch: `xenotaur/feat/wi-skills-claude-plugin-export-impl`;
the `-impl` suffix avoids the merged planning branch's name.

# Result

- `src/lrh/skills/exporter.py`:
  - added `ExportTarget.CLAUDE_PLUGIN`, `ClaudePluginSkillRenderer`, and
    `render_claude_plugin_tree`;
  - added plugin limits (5,000 files, 200 MB) and `bin/` rejection;
  - added destination guards, including the source-overlap checks;
  - added a stage-and-swap publish that removes stale skills, restores the
    previous tree on failure, and writes only
    `.claude-plugin/marketplace.json` and `plugins/lrh/` under `--out`.
- `src/lrh/cli/main.py`: added the `claude-plugin` choice and target-aware
  help.
- Generated and committed `.claude-plugin/marketplace.json` and
  `plugins/lrh/`: 27 skills, 66 plugin files, with no `version`.
- Tests:
  - 21 exporter unit tests and 3 CLI tests;
  - a new drift test, `tests/packaging_tests/skills_claude_plugin_sync_test.py`;
  - `plugins/lrh/skills` added to the portability test's targets.
- Docs:
  - a Claude plugin section in `docs/reference/cli/skills.md`;
  - a new "Claude Code Cloud Sessions (claude.ai)" section in
    `docs/how-to/use-lrh-with-agent-assistants.md`.
- Pre-push self-review: no blocking findings. The verified non-blocking
  fixes are recorded in
  `project/executions/AD_HOC/2026_10_29_01_09_06_WI_SKILLS_CLAUDE_PLUGIN_EXPORT_SELFREVIEW.md`.
- Prior-art check: present in the work item. No duplicate or competing
  open PR was found.

# Validation

- `scripts/version tools`: recorded; pyright is not installed locally.
- `scripts/format --check --diff`: 300 files unchanged. `scripts/lint`:
  all checks passed.
- `scripts/test`: 2404 tests, OK.
- `lrh validate` (this branch's code): 0 errors, 0 warnings.
- `lrh skills export --target claude-plugin --source current-repo --out
  <tmpdir>`: `diff -r` against the committed `.claude-plugin/` and
  `plugins/lrh/` is empty.
- `claude plugin validate`, Claude Code 2.1.309:
  - `.` (marketplace): "Validation passed with warnings". The one warning
    is that `plugins[0]` has no `version`, which is intended.
  - `plugins/lrh` (plugin): "Validation passed with warnings". The warning
    is no `version` (intended), plus one plugin-directory warning, no icon
    (`ICON_MISSING`).
  - Earlier warnings about the marketplace description and the plugin
    author were fixed by adding both.

# Follow-up

- **After merge, before closeout:** run the manual dogfood.
  1. Add `xenotaur/logical_robotics_harness` as a marketplace on claude.ai,
     with Sync automatically.
  2. Invoke an instruction-centric skill in a new claude.ai/code session.
  3. Record the skill, the invocation form, and the outcome here.
  4. Record answers to the Open Questions: short-name resolution,
     `_shared/` citations, duplicate loading in LRH sessions, auto-sync on
     push, and repo-attached sessions.
- Replace `session_transcript: pending` at closeout.
