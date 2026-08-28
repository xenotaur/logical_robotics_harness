---
execution_id: 2026_08_28_07_02_18_FRONTMATTER_MIGRATION_LINT_GUARD_SELFREVIEW
prompt_id: PROMPT(AD_HOC:FRONTMATTER_MIGRATION_LINT_GUARD_SELFREVIEW)[2026-08-28T07:02:12+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/642
commit: 02b0a327324ed121ac561f3c2fe5c34889320581
created_at: 2026-08-28T07:02:18+00:00
agent: claude_app
instruction_source: 'command lrh-self-review (diff-mode), run before xenotaur/feat/wi-frontmatter-migration-lint-guards first PR push, per fleet policy'
session_transcript: claude-app:494c3b1f-14c8-46bf-a4e3-0b6e8df119e8
---

# Summary

Diff-mode substitute self-review of the uncommitted-then-committed diff on
`xenotaur/feat/wi-frontmatter-migration-lint-guard` (`git diff main` at
HEAD `b02211af06fea79ec1008f8b7cc5870fcc33a9f2`, before this branch's
first PR was opened), implementing `WI-FRONTMATTER-MIGRATION-LINT-GUARD`.
Dispatched a cold `general-purpose` subagent with the diff and work-item
orientation; the invoking session independently re-verified the top
finding.

# Result

One real, medium-severity finding, independently re-verified and fixed
before opening the PR: `lrh project doctor --fix-frontmatter` scanned the
entire repository tree (`project_root.glob("**/*.md")` with
`project_root` = repo root, per `lrh project doctor`'s own convention)
instead of being scoped to `project/` as the WI's Required Change 4 and
Acceptance Criteria specify. No unsafe scalars exist outside `project/`
today, so this caused no visible harm yet, but it would have silently
rewritten `src/lrh/skills/`, `.claude/skills/`, and `.agents/skills/`
frontmatter on a future `--apply` run with no mirror-propagation logic --
desyncing the very three mirrors this same WI keeps in sync. Fixed by
passing `project_root / "project"` to `frontmatter_migration.fix_project()`
in `src/lrh/cli/main.py`, verified against a scratch fixture with unsafe
content both inside and outside `project/`.

Two low-severity, non-blocking findings, left as documented limitations
rather than expanding scope further:
1. No test exercised the CLI wiring itself (`--fix-frontmatter`,
   `--apply`, exit codes). Fixed by adding
   `tests/cli_tests/project_doctor_test.py` coverage (including a
   regression test for the scope-boundary fix above), rather than left
   as a gap.
2. The detector doesn't scan unquoted plain-scalar line-fold
   continuations (a value that wraps onto an indented next line with no
   `- ` marker and no `>`/`|` block-scalar indicator) -- independently
   reproduced as a genuine `yaml.safe_load` syntax error. No such
   construct currently exists in `project/`'s frontmatter (repo-wide
   scan), and it falls within the detector's own documented "not a
   closed enumeration" caveat, so left undocumented-but-real rather than
   expanding the four confirmed categories in this same pass.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `scripts/test` / full `pytest`: 1465 tests, all pass (up from 1461
  before the CLI-wiring tests were added).
- `scripts/lint`, `scripts/format --check --diff`: clean.
- Manually verified the scope fix against a scratch fixture with unsafe
  frontmatter both inside and outside a `project/` subdirectory.

# Follow-up

- The plain-scalar line-fold continuation gap (finding 2 above) is not
  tracked as its own work item; if a real instance is ever found, the
  detector's line-walk in `iter_unsafe_scalars` would need to also check
  continuation lines that lack a `- ` marker, not just skip them as
  presumed block-scalar body text.
