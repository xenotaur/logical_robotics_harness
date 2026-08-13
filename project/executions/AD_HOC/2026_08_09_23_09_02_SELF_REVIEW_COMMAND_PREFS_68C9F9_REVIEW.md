---
execution_id: 2026_08_09_23_09_02_SELF_REVIEW_COMMAND_PREFS_68C9F9_REVIEW
prompt_id: PROMPT(AD_HOC:SELF_REVIEW_COMMAND_PREFS_68C9F9_REVIEW)[2026-08-09T21:58:14+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/535
commit: 98b128ed733a7b125a68f7d5d8db1308e6b62fd6
created_at: 2026-08-09T23:09:02+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/535
session_transcript: claude-app:3c4e404b-8420-4a62-9c3f-f5dcccfa5400
---

# Summary

Address the first review round on PR #535 — nine comments from two automated
reviewers, all verified against the repository before acting, all fixed.

`rerun_of` is empty deliberately: the branch-slug search
(`*SELF_REVIEW_COMMAND_PREFS_68C9F9*` excluding `_REVIEW`/`_CONFIRM`/`_SELFREVIEW`)
returns nothing, because this packet's execution records are named after the
artifacts they created rather than after the branch. There is no single primary
record to link to.

# Result

## Codex (chatgpt-codex-connector) — 3 comments, all confirmed and fixed

**P1 — the workstream could not enforce its own sequencing.**
`WS-INVOCATION-AND-GATE-RESET` listed `WI-DELIBERATE-MODEL-INVOCATION` in
`work_items:`, which is the executable list `/lrh-execute` selects from
(`lrh-execute/SKILL.md` Step 1). That item has `depends_on: []` and
`prompt_ready: yes`, so a chain runner would have begun **Stage 2 flag removal
before Stage 1 retrigger removal** — inverting the strict sequencing established
two rounds earlier. Verified directly before fixing.

Fixed by withholding it from `work_items:` (author-selected from four options).
The obvious fix — `depends_on: <Stage 1 item>` — is impossible because Stage 1's
work item does not exist and `depends_on:` takes work-item IDs. Ownership
remains visible through the item's own `related_workstreams:` and the workstream
body, which now records why the list is empty and when to repopulate it.

**P2 — the same hazard for the branch-fix item.**
`WI-SKILLS-WORKTREE-SAFE-BRANCH-CREATION` is in `WS-CROSS-REPO-CODE-HEALTH`'s
`work_items:` with `depends_on: []`, so C1's documented file-collision ordering
was equally unenforced. The blocker is a *workstream stage*, which `depends_on:`
cannot name at all, so this is recorded as a known weakness with an explicit
pre-dispatch check rather than presented as a control.

**P2 — our own evidence convention was violated.**
`WI-SIBLING-REPO`'s validation asserted `git grep -c | awk` returns 35/18 without
saying those are *matching lines*. `AGENTS.md`'s `### Evidence` section — added
earlier in this same session — explicitly requires distinguishing lines,
occurrences, and files. Now labelled, with a note that lines and occurrences
coincide only because the pattern is anchored.

Both P1 and P2's first finding are the live instance of what
`WI-WORK-ITEM-BLOCKED-STATE-EXPRESSIVENESS` predicts: prose ordering is not part
of readiness evaluation. That work item's motivation is now evidenced rather
than hypothesised.

## Copilot (copilot-pull-request-reviewer) — 6 comments, one issue, fixed

All six flagged artifacts written *before* `WS-CROSS-REPO-CODE-HEALTH` existed
that still stated `related_workstreams:` was left empty, while frontmatter now
reads `WS-CROSS-REPO-CODE-HEALTH`. Corrected in
`WI-SKILLS-WORKTREE-SAFE-BRANCH-CREATION`'s body and five execution records.

This is the correct disposition under this packet's own extended cascade
taxonomy (`PROP-INVOCATION-AND-GATE-RESET` Decision 6): these are assertions of
current state about still-live artifacts, not narrative about what happened.
The records are also `status: in_progress` rather than landed, so the
immutability rule does not yet apply.

# Validation

Canonical sequence, after resolving two environment problems described below:

- `scripts/format --check --diff` → PASS
- `scripts/lint` → PASS
- `scripts/test` → **1071 tests, OK** (exit 0)
- `lrh validate` → 0 errors, 1 warning (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF`
  on `WS-SESSION-ARCHIVE-SYNC`, pre-existing and unrelated)
- `git diff --cached --check` → clean

## Two environment problems diagnosed, not worked around

**1. Tool-pin drift.** `scripts/format` and `scripts/lint` failed with black
requiring `26.3.1` against a running `25.11.0`, and ruff requiring `0.15.12`
against `0.15.0`. Confirmed pre-existing by reproducing on a stashed clean tree.
Resolved with the constrained dev install
(`pip install -e ".[dev]" -c constraints-dev.txt`) rather than skipped, after
which both passed.

**2. Worktree/editable-install mismatch — the more instructive one.**
`scripts/test` reported 2 failures in `tests/skills_installer_test.py`, both
asserting `when_to_use` is stripped for the Codex target. Neither
`src/lrh/skills/installer.py` nor its test differs from `origin/main` on this
branch, and PR #535's CI reported `tests: pass`.

Root cause: the editable `lrh` install resolves to the **main checkout**, not
this worktree, and that checkout is on branch
`xenotaur/feat/wi-dual-clean-log-hygiene-and-tag-flood-prevention`, whose
`installer.py` contains **zero** occurrences of `when_to_use`. So the tests were
exercising a different branch's source. Re-running with
`PYTHONPATH="$(pwd)/src"` gives 79/79 OK for that module and 1071/1071 OK for
the full suite.

This is the documented worktree-PYTHONPATH gotcha, and it is worth recording
that it presented as a plausible code failure: two red tests naming the exact
Codex-renderer behaviour this packet's Stage 2 is about to change. Reporting
those as real would have manufactured a finding out of a local environment
artifact.

# Follow-up

Fixes pushed to PR #535 as commit `5dd50632`. No reviewer was retriggered and no
bot mention was posted, per the standing constraint — this repository is
mid-way through removing retrigger loops, and the PR body asks reviewers for a
single complete pass.

Recommended next step is `/lrh-confirm-fixes https://github.com/xenotaur/logical_robotics_harness/pull/535`
to verify these fixes against the current diff and resolve the review threads.
Note that `/lrh-confirm-fixes` still carries `disable-model-invocation` in the
installed skill corpus, so it must be typed by the author rather than invoked.

`session_transcript` is recorded; `commit:` is left empty until closeout, when
the merge commit exists.
