---
execution_id: 2026_09_28_06_14_17_WI_SKILLS_CHATGPT_EXPORT_IMPL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_SKILLS_CHATGPT_EXPORT_IMPL_REVIEW)[2026-09-28T04:40:59+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_09_27_17_54_52_WI_SKILLS_CHATGPT_EXPORT
pr: https://github.com/xenotaur/logical_robotics_harness/pull/747
commit:
created_at: 2026-09-28T06:14:17+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/747
session_transcript: pending
---

# Summary

Review-response round 1 for PR #747 (`WI-SKILLS-CHATGPT-EXPORT`
implementation), run inline from `/lrh-land` Step 4. Codex and Copilot
reviewed the opening commit `9e6fe990` and left 7 inline threads. The user
confirmed the triage at the review-response gate.

`rerun_of` note: no prior `_REVIEW` record exists for this branch. The
branch-slug search for a primary (`WI_SKILLS_CHATGPT_EXPORT_IMPL`) finds no
exact match, because the branch carries an `-impl` suffix to avoid colliding
with planning PR #720's records. The primary
`2026_09_27_17_54_52_WI_SKILLS_CHATGPT_EXPORT` was identified unambiguously
by `/lrh-land` Step 1's `pr:`-field provenance check, so it is linked here.

# Result

Fix commit: `cde9cc06b74815efe3ff4fe548cbc67bd0f01875`.

- **Copilot, symlinked `--out` followed (fixed):** `_check_output_dir`
  rejects a symlinked output directory before any preparation or write.
- **Copilot, non-string frontmatter key → `TypeError` (fixed):** stripped
  keys are sorted by string form; a `1: one` key is reported as stripped and
  the skill still exports.
- **Copilot, `[]` in `agents/openai.yaml` read as no policy (fixed):** only
  an empty file (`None`) means no policy; any other non-mapping root fails
  the skill safe.
- **Codex P2, `--out` inside the canonical source (fixed):** an `--out` equal
  to or inside a filesystem source root (including an on-disk package root)
  is rejected.
- **Codex P2, partial batch on filesystem error (fixed):** `_publish_archives`
  refuses a directory at any destination path, stages every archive to a
  temporary file, removes all staged temporaries if any staging fails, and
  promotes with `os.replace` only after every archive staged. The CLI also
  converts write-time `OSError` into a clean error.
- **Copilot and Codex P1, dogfood evidence missing (no longer present):** both
  threads predate commits `4a276f2a` and `c623c934`, which record a real
  ChatGPT upload plus `@` invocation of `lrh-design` in the implementation
  execution record. Replied on both threads citing that evidence; no code
  change.

Regression tests were added for each code fix: symlinked output, output inside
the source (three variants), directory at a destination, staging-failure
cleanup, non-string key, non-mapping and empty `openai.yaml`. The CLI
reference was updated to describe the `--out` rules and the staged,
all-or-nothing publish.

# Validation

- `scripts/format --check --diff`: clean. `scripts/lint`: exit 0.
- `scripts/test` (with `PYTHONPATH=<checkout>/src`): 1859 tests OK.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

`/lrh-land` Step 5: confirm-fixes resolves the threads this diff satisfies,
then checks CI and REVIEW-LANDED on the `_CONFIRM` head.
