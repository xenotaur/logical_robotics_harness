---
execution_id: 2026_11_09_05_05_30_WI_EXPORT_SKILL_FAMILY_RENAME
prompt_id: PROMPT(WI-EXPORT-SKILL-FAMILY-RENAME:WI_EXPORT_SKILL_FAMILY_RENAME)[2026-10-28T07:41:27+00:00]
work_item: WI-EXPORT-SKILL-FAMILY-RENAME
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/865
commit:
created_at: 2026-11-09T05:05:30+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-EXPORT-SKILL-FAMILY-RENAME.md
session_transcript: pending
---

# Summary

Implemented `WI-EXPORT-SKILL-FAMILY-RENAME` via `/lrh-execute
WS-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES`, which resolved to this work item
as the workstream's first ready one. The run renamed `lrh-codex-export` to
`lrh-export-codex` and `lrh-antigravity-export` to
`lrh-export-antigravity`, and left the old names as deprecated stubs.

# Result

- **New skills:** `src/lrh/skills/lrh-export-codex/` (with its unchanged
  `agents/openai.yaml`) and `src/lrh/skills/lrh-export-antigravity/`. Only
  the name, heading, usage examples and self-references differ from the
  old skills.
- **Stubs:** the two old `SKILL.md` files now:
  - keep the old `name:`;
  - set `disable-model-invocation: true`;
  - have a "Deprecated: use … Do not select" description;
  - hand off with the same arguments.

  Each stub has `agents/openai.yaml` with `allow_implicit_invocation:
  false`. The Antigravity stub's file is new.
- **Antigravity invocation control:** Antigravity documents only the
  `name` and `description` frontmatter fields (checked during #790), so
  `AntigravitySkillRenderer` has no field to map the flag onto. The stub
  relies on its description, and the renderer is unchanged.
- **Copies:** rendered one skill at a time to `.claude/skills/`,
  `.agents/skills/` and `.gemini/plugins/lrh/skills/` without `--force`.
  `lrh-export-antigravity` is now present on the Antigravity target.
- **Plugin tree:** `origin/main` gained a committed Claude plugin tree in
  PR #859 while this run was paused. After merging `main` (`7474615c`,
  clean), the plugin tree (`plugins/lrh/`) was regenerated with `lrh skills
  export --target claude-plugin --source current-repo --out .`.
- **References updated:**
  - `lrh-session-id-codex` (3 lines, plus all its copies);
  - `CLAUDE.md`;
  - five docs pages;
  - experimental READMEs and the `codexexportlib.py` docstring;
  - `WI-CODEX-EXPORT-RESCUE-CANONICAL-DEST`;
  - one `WS-LRH-GITHUB-EXECUTION-RESILIENCE` line;
  - the portability test.
- **Left unchanged:**
  - the `lrh-codex-export-<timestamp>` artifact prefix;
  - adopted and resolved documents, the decision log and execution
    records;
  - the backlog;
  - rename-describing passages;
  - one historical `codex_export.md` line.
- **Commits:** `d2fedcf3` (rename), `7474615c` (merge of `main`) and
  `e8860145` (plugin regeneration and docstring).

# Validation

- `scripts/version tools`: OK.
- `lrh validate`: 0 errors, 0 warnings.
- `scripts/format --check --diff`: clean.
- `scripts/lint`: passes.
- `scripts/test --log`: passes, including
  `skills_claude_plugin_sync_test`.
- `lrh skills check --target claude --local`, and `lrh skills status
  --target codex|antigravity --local --source current-repo`: all up to
  date.
- `diff -r src/lrh/skills/lrh-export-codex
  .claude/skills/lrh-export-codex`: identical.
- `grep -rln 'lrh-codex-export\|lrh-antigravity-export' src/lrh/skills`:
  only the two stubs.

# Follow-up

- The run paused for about 11 days mid-implementation; the work resumed
  intact.
- **Optional:** the backlog entry about `CLAUDE.md` missing the export
  skills is stale. `WI-EXPORT-SESSION-ID-DOCS` covers backlog cleanup.
- **Optional:** add "(now `/lrh-export-codex`)" to the historical
  `codex_export.md:149` line.
- Removing the stubs is a later follow-up.
