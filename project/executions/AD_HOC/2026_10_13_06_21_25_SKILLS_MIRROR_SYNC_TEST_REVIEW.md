---
execution_id: 2026_10_13_06_21_25_SKILLS_MIRROR_SYNC_TEST_REVIEW
prompt_id: PROMPT(AD_HOC:SKILLS_MIRROR_SYNC_TEST_REVIEW)[2026-10-13T02:22:13+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_10_12_00_54_38_SKILLS_MIRROR_SYNC_TEST
pr: https://github.com/xenotaur/logical_robotics_harness/pull/831
commit: ddeb3b78a9a4519cc604ada484041a5af2dc7dc9
created_at: 2026-10-13T06:21:25+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/831
session_transcript: claude-app:a5ff4b4b-5afd-495b-9eee-87ba975572ba
---

# Summary

Review-response round 1 for PR #831, run inline from `/lrh-land`. It addressed
7 open review threads on HEAD `dcc59d30`: 5 from Copilot and 2 from Codex.

# Result

All 7 threads were valid, and all were fixed in `1c740bf3`,
which was pushed directly. The threads fell into four themes:

A. **Forced regeneration was "previewed" with `--dry-run`.** This is Copilot
   on `CONTRIBUTING.md:244`.
   - *Problem:* `--dry-run` without `--force` only prints a per-skill "local
     modifications" warning. But `--force` `shutil.rmtree`s each differing
     skill directory before rewriting it (`installer.py:897-901`), so
     local-only files would be lost.
   - *Fix:* CONTRIBUTING, including the one-skill command, now previews with
     `--force --diff`. That has been read-only since #820 and prints a unified
     diff. It also states the deletion semantics.

B. **The sync test's failure hint pointed straight at a repo-wide `--force`.**
   This is Copilot on `skills_mirror_sync_test.py:38`.
   - *Fix:* the module docstring and `REGEN_HINT` now say to preview with
     `--force --diff` first, then rerun without `--diff`.

C. **The test was run as `python -m unittest ...` instead of `scripts/test`.**
   This is Copilot and Codex P1 on `lrh-create-skill/SKILL.md:229`, and
   Copilot on `canonical-validation.md:69`.
   - *Why it matters:* `AGENTS.md:177` mandates the canonical runner, and
     `scripts/test:6` sets `PYTHONPATH=<repo>/src`.
   - *Fix:* both files now use
     `scripts/test tests/packaging_tests/skills_mirror_sync_test.py`.
     `scripts/test:44-48` maps a file path to a module, and this form was
     verified: 3 tests, OK.

D. **The regeneration command was missing `--source current-repo`.** This is
   Copilot and Codex P2 on `canonical-validation.md:74`.
   - *Problem:* without the flag, the command defaults to `lrh-package`.
   - *Fix:* the flag was added.

Both edited skills were then regenerated into `.claude`, `.agents` and
`.gemini` from a one-skill scratch source, previewed with `--force --diff`.
Nothing was skipped.

# Validation

Run in the per-worktree conda env `LrhGeminiSkillsSync` (ruff 0.15.12, black
26.3.1):

- `scripts/format --check --diff`: clean.
- `scripts/lint`: clean.
- `scripts/test`: 2288 tests, OK.
- `scripts/test tests/packaging_tests/skills_mirror_sync_test.py`: 3 tests,
  OK.
- `lrh validate`: 0 errors.
- `lrh skills install --local --target all --source current-repo --dry-run`:
  all up to date.
- `lrh chain-defaults status`: not stale.

# Follow-up

None.
