---
execution_id: 2026_08_28_07_06_12_FRONTMATTER_MIGRATION_LINT_GUARD
prompt_id: PROMPT(WI-FRONTMATTER-MIGRATION-LINT-GUARD:FRONTMATTER_MIGRATION_LINT_GUARD)[2026-08-28T06:29:44+00:00]
work_item: WI-FRONTMATTER-MIGRATION-LINT-GUARD
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/642
commit: 02b0a327324ed121ac561f3c2fe5c34889320581
created_at: 2026-08-28T07:06:12+00:00
agent: claude_app
instruction_source: 'chat (user ran /lrh-execute WI-FRONTMATTER-MIGRATION-LINT-GUARD to implement and land the work item end-to-end)'
session_transcript: claude-app:494c3b1f-14c8-46bf-a4e3-0b6e8df119e8
---

# Summary

Implemented `WI-FRONTMATTER-MIGRATION-LINT-GUARD`: a shared raw-text
lexical detector for the four confirmed unsafe frontmatter plain-scalar
patterns, wired into both a new `lrh validate` lint category and a new
`lrh project doctor --fix-frontmatter` migration tool; ran the migration
tool against this repo's own `project/` tree; updated the five
frontmatter-authoring skills with "always quote free text" guidance.

# Result

- `src/lrh/control/frontmatter_lint.py` (new): `iter_unsafe_scalars()`
  detects unquoted colon-collapse, unquoted mid-scalar `#`
  (truncation), a reserved-indicator-leading scalar, and a known-string
  field that would implicitly resolve to a non-string YAML type.
  Deliberately excludes `created_at` (accepted datetime divergence,
  Decision 2) and flow sequences/mappings (`[]`, `{}`) from false
  positives.
- `src/lrh/control/validator.py`: new `_validate_frontmatter_lint()`
  pass, wired into `validate_project()`, reporting
  `FRONTMATTER_LINT_UNSAFE_SCALAR` as a warning (report-only, never
  fails validation on its own).
- `src/lrh/control/frontmatter_migration.py` (new): `plan_fixes()` /
  `fix_file()` / `fix_project()` re-quote exactly the flagged line's raw
  value text (never truncating or reinterpreting it), self-verifying via
  round-trip and re-scan after each fix.
- `src/lrh/cli/main.py`: new `lrh project doctor --fix-frontmatter`
  (dry-run by default) and `--apply` flags, scoped to `project_root /
  "project"` (fixed during self-review — see Follow-up).
- Ran `lrh project doctor --fix-frontmatter --apply` against this repo's
  own `project/` tree: 75 files, 80 fields fixed, all content preserved
  exactly (verified: no body changes, no value truncation, only YAML
  encoding changed).
- Updated `src/lrh/skills/{lrh-work-item,lrh-workstream,lrh-proposal,
  lrh-closeout,lrh-execute}/SKILL.md` (and their `.claude/skills/` and
  `.agents/skills/` mirrors) with the "always quote free-text frontmatter
  scalar values" guidance.
- New test coverage: `tests/control_tests/frontmatter_lint_test.py`,
  `tests/control_tests/frontmatter_migration_test.py` (including the
  acceptance-criterion test that the lint guard and migration tool agree
  on the same fixtures), `tests/cli_tests/project_doctor_test.py`
  additions for `--fix-frontmatter`/`--apply`.

# Validation

- `lrh validate`: 0 errors, 0 warnings on the full `project/` tree.
- `scripts/format --check --diff`: clean.
- `scripts/lint`: clean.
- `scripts/test`: 1465 tests, all pass.
- `lrh project doctor --fix-frontmatter` (dry-run, manually reviewed,
  then applied).

# Follow-up

- `/lrh-self-review` (diff-mode, before this PR's first push) caught a
  real medium-severity bug: `--fix-frontmatter` was scanning the whole
  repository tree instead of being scoped to `project/`, which would
  have silently rewritten skill-mirror frontmatter
  (`src/lrh/skills/`, `.claude/skills/`, `.agents/skills/`) on a future
  `--apply` run with no mirror-propagation logic. Fixed before push; see
  `project/executions/AD_HOC/2026_08_28_07_02_18_FRONTMATTER_MIGRATION_LINT_GUARD_SELFREVIEW.md`
  for the full record and two additional low-severity findings left
  documented rather than fixed (no CLI-wiring test coverage — since
  fixed; a plain-scalar line-fold continuation gap in the detector — no
  such construct currently exists in `project/`, left as a known,
  documented limitation).
- The `WS-LRH-FRONTMATTER-PARSER` workstream can close once this WI
  lands, since it was the workstream's other and final open work item.
