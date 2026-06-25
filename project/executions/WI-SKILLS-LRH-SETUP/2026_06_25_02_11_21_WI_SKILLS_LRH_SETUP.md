---
execution_id: 2026_06_25_02_11_21_WI_SKILLS_LRH_SETUP
prompt_id: PROMPT(WI-SKILLS-LRH-SETUP:WI_SKILLS_LRH_SETUP)[2026-06-25T01:46:25-04:00]
work_item: WI-SKILLS-LRH-SETUP
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/325
commit: 983b282c3082a8867b07b2ca2999ce8e430cd3e1
created_at: 2026-06-25T02:11:21-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SKILLS-LRH-SETUP.md
session_transcript: claude-app:3e4d8973-d1eb-4439-93e3-01c8db5efc98
---

# Summary

Implement `lrh setup` (Stage 2 of `WS-SKILLS`): a CLI subcommand that copies
all LRH skills from the installed `lrh` package (`src/lrh/skills/`) to
`~/.claude/skills/`, making them globally available in any Claude Code project.

# Result

PR #325 opened: https://github.com/xenotaur/logical_robotics_harness/pull/325

Changes:

- `src/lrh/skills/installer.py` — core install logic using
  `importlib.resources.files("lrh.skills")` to walk the package, compare
  installed files against the package version with file-by-file content
  comparison, and copy with configurable `dry_run` / `force` flags. Reports
  `INSTALLED`, `UP_TO_DATE`, `USER_MODIFIED`, or `FORCED` per skill. Prints
  restart reminder if `~/.claude/skills/` is newly created.
- `src/lrh/cli/main.py` — `lrh setup` top-level subcommand with `--dry-run`
  and `--force` flags wired to `lrh.skills.installer`.
- `tests/skills_installer_test.py` — 13 unit tests covering install,
  idempotency, dry-run, user-modified skip, and force-overwrite behaviors.

# Validation

- `scripts/version tools` — Black 26.3.1, Ruff 0.15.12
- `scripts/format --check --diff` — 173 files unchanged
- `scripts/lint` — all checks passed
- `scripts/test` — 679 tests OK
- `lrh validate` — 0 errors, 0 warnings
- `lrh setup --dry-run` smoke test output:
  ```
    would install: lrh-create-skill
    would install: lrh-implement
    would install: lrh-review-response
    would install: lrh-work-item
  ```

# Follow-up

- Update `session_transcript: pending` to `claude-app:<session-id>` after
  the session ends
- Merge PR #325 and update this record to `landed`
- Move `WI-SKILLS-LRH-SETUP` to `resolved/` once PR lands
