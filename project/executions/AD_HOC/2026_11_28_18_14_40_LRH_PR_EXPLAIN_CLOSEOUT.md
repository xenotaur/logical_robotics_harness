---
execution_id: 2026_11_28_18_14_40_LRH_PR_EXPLAIN_CLOSEOUT
prompt_id: PROMPT(AD_HOC:LRH_PR_EXPLAIN_CLOSEOUT)[2026-11-28T18:14:40+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/878
commit: a0d2dd0864e759799b16656c586e35f4472eb857
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/878
session_transcript: claude-app:dc7ab054-6d76-4d02-a27c-408367a4cb6b
created_at: 2026-11-28T18:14:40+00:00
---

# Summary

Backfill record for PR 878, which adds the `/lrh-pr-explain` skill (a visual
HTML briefing of a pull request) and the `lrh pr-brief gather|render`
tooling behind it. The PR was built through `/lrh-create-skill`, which
writes no execution record, so `/lrh-land` took its backfill path and this
record carries the CHAIN-NOTE.

# Result

CHAIN-NOTE: cycles=1; stops=0; gates=[chain-init, merge]; friction=none; self_review_rounds=1; note="Backfill path (PR from /lrh-create-skill, no primary record). Codex and Copilot reviewed only on open (0f35c55a); their 6 findings were fixed in 27d4aafc by an Auto-fix pass in this session, then replied to and resolved. Confirm-fixes took the empty-thread path (autopilot routine). Substitute self-review of fda75d04: safe to merge, 4 non-blocking findings recorded here and in the _SELFREVIEW record; _SELFREVIEW committed with closeout on main to avoid a review loop. Chain-init asked live: skip consent not granted in this clone."

What landed:

- `src/lrh/pr_brief/` (`gather.py`, `render.py`, `templates/briefing.html`)
  and `lrh pr-brief` in `src/lrh/cli/`; package data in `pyproject.toml`.
- `src/lrh/skills/lrh-pr-explain/` with `references/data-schema.md`,
  `briefing-content.md` and `diagram-kit.md`, mirrored to all four skill
  locations; CLAUDE.md index line; `docs/reference/cli/pr-brief.md`.
- 42 `pr_brief` tests.

Merged with `lrh vcs merge --merge --match-head-commit fda75d04…` as
`a0d2dd08`.

Non-blocking findings carried forward (from the substitute self-review):

1. Malformed narrative field types (list `severity`/`confidence`;
   non-iterable `summary`, note `body`, file `points`, `tests.gaps`) raise
   `TypeError` instead of field errors.
2. Stale `baseRefOid` can appear as `pr.base_sha` without a caveat when the
   tip lookup fails and no `--repo-dir` is given.
3. "Changes no refs" wording ignores `FETCH_HEAD` in `SKILL.md` and the CLI
   help.
4. `pr.url` scheme unchecked in `href`; boolean `behind_by` renders as
   "True commit behind".

# Validation

- CI on `fda75d04`: coverage, installed-wheel-smoke, lint, Check workflow
  files, tests — all pass.
- Local before the `27d4aafc` push: `scripts/test` (2,478 tests),
  `scripts/lint`, `scripts/format --check`, `lrh validate` — clean.
- `lrh validate` after closeout edits — 0 errors.

# Follow-up

- Follow-up PR for the four non-blocking findings above.
- Run `lrh skills install` to pick up `/lrh-pr-explain` in new sessions.
