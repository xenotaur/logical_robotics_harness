---
execution_id: 2026_11_28_18_14_39_LRH_PR_EXPLAIN_SELFREVIEW
prompt_id: PROMPT(AD_HOC:LRH_PR_EXPLAIN_SELFREVIEW)[2026-11-28T18:14:39+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/878
commit: a0d2dd0864e759799b16656c586e35f4472eb857
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/878
session_transcript: claude-app:dc7ab054-6d76-4d02-a27c-408367a4cb6b
created_at: 2026-11-28T18:14:39+00:00
---

# Summary

PR-mode `/lrh-self-review` pass on PR 878 at `fda75d04`, used as the
substitute review signal for `/lrh-confirm-fixes` Step 8 inside `/lrh-land`.
The hosted reviewers in this repository review only when a PR opens, so they
never looked at `27d4aafc` (the review fixes) or `fda75d04` (the `_CONFIRM`
record). This record is committed with the closeout on `main`, not on the
PR, so the reviewed head stayed the merge head.

# Result

A cold-context `general-purpose` subagent, given only the PR URL, head SHA,
checkout path and PR history, reviewed the full diff. Verdict: safe to merge
as-is. It confirmed the packaging (built a wheel from `git archive HEAD`;
`lrh/pr_brief/templates/briefing.html` is included), mirror sync, HTML
escaping, and that all six earlier review findings are fixed.

Findings (all non-blocking; recorded, not fixed, per the run's stop-work
condition):

1. should-fix — some malformed narrative fields still raise `TypeError`
   instead of a field error: a list-valued `review_notes[].severity` or
   `confidence` crashes `validate()`; a non-iterable `summary`,
   `review_notes[].body`, `files[path].points` or `tests.gaps` passes
   `--check` and then crashes `render`.
2. minor — when the base-tip lookup fails and no `--repo-dir` is given,
   `pr.base_sha` holds the possibly stale `baseRefOid` with no
   `status.conflicts.error`, and the footer shows it as the current base.
3. minor — `SKILL.md` and the `--repo-dir` help say the trial merge changes
   no refs, but `git fetch` writes `FETCH_HEAD` (the CLI reference doc says
   this correctly).
4. minor — `pr.url` scheme is not checked before use in `href`, and a
   boolean `behind_by` renders as "True commit behind".

Top finding re-verified directly by the invoking session: probes against
`sample_data()` reproduced `TypeError: unhashable type: 'list'` for a list
severity and `'int' object is not iterable` for `summary = 5` and
`tests.gaps = 3`.

Findings routed to `/lrh-confirm-fixes`: classified non-blocking; none
reopened a thread. Fixes applied: none (PR-mode is report-only).

`rerun_of` is empty: no primary execution record exists for this PR (opened
through `/lrh-create-skill`); the `/lrh-land` backfill record is
`2026_11_28_18_14_40_LRH_PR_EXPLAIN_CLOSEOUT`.

# Validation

- Subagent ran the targeted `pr_brief` tests (42), the skills tests, ruff,
  black and `lrh validate` from source; all clean.
- CI on `fda75d04`: coverage, installed-wheel-smoke, lint, Check workflow
  files and tests all pass.

# Follow-up

- Harden `validate()` against the item 1 shapes (or catch `TypeError` in the
  CLI), and fix items 2–4, in a follow-up PR.
