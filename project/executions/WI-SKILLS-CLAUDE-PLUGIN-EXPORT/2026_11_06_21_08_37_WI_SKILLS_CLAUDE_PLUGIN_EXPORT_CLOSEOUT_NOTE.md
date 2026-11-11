---
execution_id: 2026_11_06_21_08_37_WI_SKILLS_CLAUDE_PLUGIN_EXPORT_CLOSEOUT_NOTE
prompt_id: PROMPT(WI-SKILLS-CLAUDE-PLUGIN-EXPORT:WI_SKILLS_CLAUDE_PLUGIN_EXPORT_CLOSEOUT_NOTE)[2026-11-06T21:08:37+00:00]
work_item: WI-SKILLS-CLAUDE-PLUGIN-EXPORT
status: landed
rerun_of: 2026_10_29_01_13_43_WI_SKILLS_CLAUDE_PLUGIN_EXPORT
pr: https://github.com/xenotaur/logical_robotics_harness/pull/859
commit: 216c451b4dac1b775c8f245734dfb51423ad172c
created_at: 2026-11-06T21:08:37+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/859
session_transcript: claude-app:b45207bd-f56d-4b2d-a182-23126acc88a6
---

# Summary

`/lrh-land` closeout note for PR #859, the implementation of
`WI-SKILLS-CLAUDE-PLUGIN-EXPORT`, run inline from `/lrh-execute`. A primary
record was found, so this note carries the CHAIN-NOTE (`rerun_of` links to the
primary) and leaves the primary record's body untouched.

# Result

PR #859 merged as `216c451b` via `lrh vcs merge ... --merge
--match-head-commit 799dc7bb`, after the human's "Approve merge" reply to the
merge-and-closeout plan. `gh pr view` independently confirmed `MERGED`.
The agent ran the merge as an explicit, human-approved override of the work
item's `merge_pr` forbidden action, as `/lrh-execute` provides.

At the chain gate the human chose to run the cloud dogfood after merge. The
run paused there; the results are in
`2026_11_06_21_08_36_WI_SKILLS_CLAUDE_PLUGIN_EXPORT_DOGFOOD`. The dogfood
succeeded, so this closeout:
- lands ten execution records: primary, diff-mode `_SELFREVIEW`, three
  `_CONFIRM`, three PR-mode `_SELFREVIEW`, `_DOGFOOD`, and this note;
- carries the round-3 `_SELFREVIEW` onto `main` in this commit, not on the PR
  branch, so the merge's SHA lock stayed on the reviewed head;
- resolves the work item.

No workstream or proposal is linked.

CHAIN-NOTE: `cycles=3; stops=2; gates=[chain-init, merge, dogfood]; friction=review-nit-loop; self_review_rounds=3; note="Implementation run via /lrh-execute. A diff-mode self-review before the first push gave 5 fixes. Hosted review runs only on PR open, so each later head got a PR-mode substitute self-review. Round 1 found a false manual-only claim in the docs and fixed it. Round 2 found that the skill-authoring docs omitted the export step, which would fail CI for anyone adding a skill, plus an overstated versioning claim; both fixed. Round 3 was clean. Stop 1: an interruption mid-run; a land-gate re-confirm question was rejected, and the human said to resume on the execute-gate conditions, since the execute gate already covered landing. Stop 2: the round-2 finding halted under the stored stop condition; the human chose to fix it and amended the stop condition to halt only on blocking or unverifiable findings. One amendment typed as a reply-button message was dropped, so the stored condition held until the human repeated it. The dogfood paused the run after merge as agreed. On claude.ai/code, the empty pre-session composer menu first looked like a load failure; a started session showed lrh@synced loaded."`

## Non-blocking findings carried to closeout

1. `_publish_plugin_tree` writes with `target.write_bytes(content)`
   (`src/lrh/skills/exporter.py`), so file modes are not preserved. No file
   under `src/lrh/skills` is executable today. The drift test compares bytes
   only and would not notice.
2. A SIGKILL or other non-`OSError` interrupt mid-export can leave
   `plugins/.lrh-staging-*` or `plugins/.lrh-previous-*` behind, and hidden
   entries removed with the old `skills/` folder are not reported.
3. The top-level `bin/` limit check cannot fire for the current renderer,
   which never emits `bin/`. It is defensive only.
4. Skills that are manual-only only through Codex's `agents/openai.yaml`
   (`lrh-land`, `lrh-execute`, `lrh-confirm-fixes`, `lrh-self-review`,
   `lrh-codex-export`) can be started by Claude on its own from the plugin.
   This is the same as a local Claude install, and the docs say so. The work
   item's premise that the plugin keeps skills manual-only holds only for the
   `disable-model-invocation` frontmatter.
5. The primary record says 21 exporter unit tests; there are 22. The primary
   body is immutable, so the correction is recorded here.
6. How claude.ai versions a plugin without `version` is partly answered: it
   labels it `v1`. Whether updates bump that label is untested.

# Validation

- Merge verified with `gh pr view` (state `MERGED`, merge commit `216c451b`).
- PR head `799dc7bb`: CI passed. `scripts/test` gave 2404 tests OK, and
  format, lint, `lrh validate`, and `claude plugin validate` for the
  marketplace and the plugin all passed.
- `lrh validate` and `lrh sessions closeout-sync` ran before this closeout
  commit.

# Follow-up

- Update the how-to §5 with the dogfood results (see the `_DOGFOOD` record's
  Follow-up).
- Optional exporter hardening: preserve file modes, and sweep leftover
  `.lrh-staging-*` and `.lrh-previous-*` entries on the next run.
- Decide whether the Codex-only manual skills should also carry
  `disable-model-invocation: true`.
- The human can delete the two probe plugins and the probe skill from
  claude.ai once they're no longer needed.
- Test marketplace re-sync on push the next time a skill change merges.
