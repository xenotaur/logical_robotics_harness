---
execution_id: 2026_07_30_21_01_24_SLUG_IDEMPOTENCE_CLI_AND_UTC_TIMESTAMPS
prompt_id: PROMPT(AD_HOC:SLUG_IDEMPOTENCE_CLI_AND_UTC_TIMESTAMPS)[2026-07-30T21:01:08+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
agent: claude_app
instruction_source: user request in this session (implementing WI-SLUG-IDEMPOTENCE-CLI-TOOLING and WI-PROMPT-WORKFLOW-UTC-TIMESTAMPS in one PR, per user direction)
session_transcript: pending
created_at: 2026-07-30T21:01:24+00:00
---

# Summary

Implement both `WI-SLUG-IDEMPOTENCE-CLI-TOOLING` and
`WI-PROMPT-WORKFLOW-UTC-TIMESTAMPS` in one PR, per the user's explicit
direction that they could land together (both touch
`src/lrh/prompt_workflow.py` with no functional dependency between them).

# Result

- **UTC timestamp fix** (`WI-PROMPT-WORKFLOW-UTC-TIMESTAMPS`):
  `src/lrh/prompt_workflow.py:299` no longer calls `.astimezone()` after
  `datetime.datetime.now(datetime.timezone.utc)` — the timestamp used for
  execution-record filenames and `execution_id`s is now UTC regardless of
  the host's local timezone. Added a regression test
  (`test_label_timestamp_is_utc_regardless_of_local_timezone`) that
  monkeypatches `TZ` to two different non-UTC offsets and asserts the
  minted `PROMPT(...)` ID's timestamp offset is always `+00:00`.
- **Slug idempotence CLI** (`WI-SLUG-IDEMPOTENCE-CLI-TOOLING`): added
  `src/lrh/prompt_workflow_slug.py`, a new sibling to
  `prompt_workflow_match.py`/`prompt_workflow_search.py` implementing
  `SlugMatch`/`SlugCheckResult` dataclasses, `find_local_matches`
  (trailing-segment filename search), `find_remote_matches` (cross-PR/fork
  discovery via `refs/pull/<N>/head`, force-refspec fetch, `git
  merge-base`-based stacked-PR inheritance exclusion, all raising
  `SlugCheckError` on any `gh`/`git` failure instead of silently reporting
  "no match" — closing the "doesn't fail closed on fetch errors" backlog
  gap), and `check_slug` (combined local+remote). Reused the existing
  `lrh.integrations.github.gh_client.run_gh_json` wrapper (already
  fail-loud by design) rather than inventing a second `gh` wrapper. Added
  `parse_front_matter_fields_from_text` to `prompt_workflow_records.py` so
  remote matches read via `git show <ref>:<path>` can be parsed without a
  local path. Wired `--slug`/`--work-item`/`--no-remote` into
  `lrh prompt check-execution` (mutually exclusive with `--prompt-id`;
  parser error if neither or both given); exit codes: `0` no
  match/non-blocking match, `1` blocking match
  (`landed`/`in_progress`, the default per
  `DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT`), `3` the check itself failed.
- **Skill migration**: `lrh-proposal`, `lrh-work-item`, and
  `lrh-workstream`'s Step 4 (and their `references/execution-record.md`
  mirrors) now call `lrh prompt check-execution --slug ...` instead of
  inlining the `find`/`gh pr list`/`git merge-base` shell block —
  replacing ~115 lines of duplicated shell-in-prose per skill with a
  single command call plus exit-code interpretation. `lrh-review-response`
  and `lrh-confirm-fixes` Step 3 migrated the same way with `--no-remote`
  (both already operate on an already-checked-out PR branch, so cross-PR
  discovery doesn't apply); `lrh-confirm-fixes` keeps its deliberate
  Decision-12 warning-only deviation (ignores the exit code, warns on any
  printed match regardless of status). All `src/lrh/skills/` and mirrored
  `.claude/skills/` copies updated identically (`diff -r` clean for all
  five).
- **Explicitly not touched** (per both WIs' Non-Goals): `PROMPTS.md`'s
  invariant/default text; the `lrh-review-response`/`lrh-confirm-fixes`
  `rerun_of`-attribution `find` (a different, lower-risk search, already
  flagged separately in `project/design/backlog.md`); the `planned`-status
  gap (left non-blocking by default, per code comment in
  `prompt_workflow_slug.py`).

# Validation

- `pytest tests/` — 821 passed, 1 pre-existing unrelated failure
  (`version_integration_test.py`'s installed-package-metadata check,
  confirmed present identically on a clean stash of this branch before
  any of these changes).
- `pytest tests/assist_tests/prompt_workflow_slug_test.py` — 13 passed,
  including a real local git simulation (bare-equivalent "origin" repo,
  PR#1 introducing the slug file, PR#2 stacked on PR#1 adding only an
  unrelated file) proving the merge-base check keeps PR#1's match and
  excludes PR#2's inherited one, plus fail-loud tests for both a
  simulated `gh` failure and a `git fetch` failure with no configured
  remote.
- `pytest tests/assist_tests/prompt_workflow_test.py` — 7 passed,
  including the new UTC-timestamp regression test.
- `scripts/format --check` and `scripts/lint` — clean.
- `lrh validate` — 0 errors, 1 pre-existing unrelated warning
  (`WS-LRH-ASSISTANTS` no actionable leaf).
- Manual dogfood against this actual repo: `lrh prompt check-execution
  --slug idempotence-check-refinements --no-remote --project-root .`
  correctly found and blocked on PR #441's own landed execution record;
  `--slug nonexistent-slug-smoke-test` correctly reported no match;
  omitting both `--prompt-id` and `--slug` correctly errored.

# Follow-up

- `project/design/backlog.md`'s "Idempotence cross-PR discovery doesn't
  fail closed on fetch errors" entry should be marked Resolved at
  closeout — this PR's `SlugCheckError` fail-loud behavior closes it.
- The `lrh-review-response`/`lrh-confirm-fixes` `rerun_of`-attribution
  `find` (unanchored substring, a different and lower-risk search than
  the Step 3 idempotence check this PR migrated) remains open, as
  originally flagged in PR #440's "Noticed but not fixed" note — still
  not part of this PR's scope.
- The `planned`-status gap remains centrally unresolved, per
  `DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT`'s own revisit conditions; this
  PR's default (non-blocking) is a reasonable lean, not a resolution.
