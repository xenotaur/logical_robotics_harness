---
execution_id: 2026_08_02_15_20_28_SLUG_IDEMPOTENCE_CLI_AND_UTC_TIMESTAMPS_REVIEW
prompt_id: PROMPT(AD_HOC:SLUG_IDEMPOTENCE_CLI_AND_UTC_TIMESTAMPS_REVIEW)[2026-08-02T15:20:11+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_08_02_15_03_56_SLUG_IDEMPOTENCE_CLI_AND_UTC_TIMESTAMPS_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/443
commit: 7a2209a132e9c5069ac46b4721b36e8daa8d0e32
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/443
session_transcript: claude-app:3fcab22f-9ebe-4392-bf31-2103fce507f2
created_at: 2026-08-02T15:20:28+00:00
---

# Summary

Round 12 review response for PR #443. Codex and Copilot both reviewed at
commit `6e7ecb6`. 3 new genuine findings (2 code, 1 doc), one reported
independently by both reviewers; remaining threads are stale duplicates
of already-fixed prior-round issues.

# Result

- **Codex: "Include uppercase Markdown extensions in local slug checks"**
  (valid, fixed): `find_local_matches` used `bucket.glob("*.md")` before
  applying the trailing-segment regex. Verified empirically that
  `pathlib`'s glob matching is case-sensitive regardless of the
  underlying filesystem's own case-sensitivity (confirmed directly: it
  does not match a `.MD`-suffixed file even on this sandbox's
  case-insensitive-by-default filesystem) -- so round 9's fix making the
  *slug* regex case-insensitive never mattered for an uppercase-extension
  file, since the glob filtered it out first. Fixed: replaced the glob
  with `bucket.iterdir()` plus an `is_file()` check, letting the regex
  (already requiring `.md$` case-insensitively) do all the filtering
  itself, with no redundant case-sensitive pre-filter. Test:
  `test_uppercase_md_extension_is_still_matched`.
- **Codex + Copilot (same root cause, reported independently by both):
  absolute `--output-root` breaks remote discovery.** Codex: "Relativize
  absolute output roots before remote tree searches." Copilot (suppressed
  comment): flagged the identical issue in `prompt_workflow.py`'s CLI
  wiring. Verified: `find_local_matches` handles an absolute
  `output_root` fine (an absolute `Path` operand replaces the prefix via
  normal `pathlib` semantics), but `find_remote_matches` fed that same
  absolute string into `git ls-tree`'s pathspec, which git always treats
  as a path *within the tree*, never a filesystem path -- an absolute
  pathspec matches nothing, silently producing zero candidates for every
  open PR (a false "no prior record," exit 0). Fixed: added
  `_relative_output_root(project_root, output_root)`, used by both
  `find_local_matches` (for its `path` field) and `find_remote_matches`
  (for the git pathspec) -- relativizes an absolute `output_root` against
  `project_root` when it's a genuine subpath, and raises
  `SlugCheckError` (not a silent wrong answer, and not a raw `ValueError`)
  when it isn't, since there's no sensible git pathspec for a foreign
  absolute path. This also fixes a latent local/remote de-duplication
  bug neither reviewer flagged directly: before this fix, an absolute
  `output_root` would have made local matches' `path` field absolute
  while remote matches' stayed relative, breaking the `local_paths`
  exclusion set's string equality even for the identical file. Test:
  `test_absolute_output_root_outside_project_root_raises`.
- **Copilot: ambiguous doc wording in `lrh-confirm-fixes/SKILL.md`**
  (valid, fixed): the instruction "the output is not \"No prior execution
  record found for this slug.\"" is ambiguous if read as a full-output
  equality check -- the CLI always prints `slug:`/`work_item:` header
  lines first, so that string is never the *entire* output even in the
  true no-match case, meaning a literal-equality implementation would
  always be false regardless of whether a match exists. Reworded to
  explicitly say "check the output for a match line — one containing
  `\tstatus=`" per Copilot's suggestion, and to spell out why the
  original phrasing was ambiguous rather than just changing the words
  with no explanation. Mirror synced (`diff -r` clean).
- **Not new work — stale/duplicate threads, left alone:** the remaining
  visible threads are findings from prior rounds already fixed in code in
  earlier commits on this branch, still open only because
  `/lrh-confirm-fixes` (not `/lrh-review-response`) resolves GitHub
  review threads.

# Validation

- `pytest tests/` — 841 passed (up from 839; +2 new tests), same 1
  pre-existing unrelated failure as before this PR
  (`version_integration_test.py`).
- `pytest tests/assist_tests/prompt_workflow_slug_test.py` — 27 passed.
- `scripts/format --check` / `scripts/lint` — clean.
- `lrh validate` — 0 errors, 1 pre-existing unrelated warning.

# Follow-up

None beyond what the primary record already tracks.
