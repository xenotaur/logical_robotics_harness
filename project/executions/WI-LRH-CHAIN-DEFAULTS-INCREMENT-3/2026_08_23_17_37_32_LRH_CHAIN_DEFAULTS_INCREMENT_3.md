---
execution_id: 2026_08_23_17_37_32_LRH_CHAIN_DEFAULTS_INCREMENT_3
prompt_id: PROMPT(WI-LRH-CHAIN-DEFAULTS-INCREMENT-3:LRH_CHAIN_DEFAULTS_INCREMENT_3)[2026-08-23T15:54:03+00:00]
work_item: WI-LRH-CHAIN-DEFAULTS-INCREMENT-3
status: landed
rerun_of: 
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-CHAIN-DEFAULTS-INCREMENT-3.md
session_transcript: claude-app:81eca1c8-36fa-493d-b0e5-08c0501ec1d0
pr: https://github.com/xenotaur/logical_robotics_harness/pull/623
commit: 2a9b3d766bdbf3574430144dba3007fe350baec3
created_at: 2026-08-23T17:37:32+00:00
---

# Summary

Implements `WI-LRH-CHAIN-DEFAULTS-INCREMENT-3`: the `closeout_with_merge`
single-ask in `/lrh-land` (merge command + closeout plan preview presented
together, one authorization, placeholder SHA until merge produces it,
closeout executed without a second ask unless the real assessment diverges
materially from the preview), and a semantic (marker-scoped) replacement
for the file-granular Decision 5 chain-defaults staleness watch, closing
both its over-watch and under-watch defects. Third and final PR in the
planned 1-2-3 sequence (housekeeping fixes -> `WI-CHAIN-DEFAULTS-ACTIVATION-STAGE3-5`
-> this).

# Result

**`closeout_with_merge`:** `/lrh-land` Step 6 rewritten to compute and
present the SHA-locked merge command together with an inline preview of
`/lrh-closeout` Steps 1-3's assessment (execution records, WI resolution
text, WS exit-criteria display), with the merge-commit SHA shown as a
placeholder wherever it would be needed pre-merge. One live reply
authorizes both; Step 7 executes merge then the previewed closeout without
a second ask, re-deriving the real assessment from scratch and comparing
against the preview -- a differing SHA alone is never material; a
differing resolution text, WS exit-criteria answer, or newly appeared
execution record is, and falls back to a fresh live ask at
`/lrh-closeout` Step 4 (whose own text now documents this satisfaction
rule). `project/config/chain-defaults.yaml` gained `closeout_with_merge:
true` as a recorded fact, not a runtime-branched toggle -- verified no
skill text branches on its value; `chain_init_confirmation` is unchanged.

**Semantic staleness watch:** replaced the raw `git diff --quiet` over
whole watched files with `<!-- GATE-DEFINITION -->`-marked regions and a
new `src/lrh/gate_staleness.py` module + `lrh chain-defaults
check-staleness` CLI command. Markers added to the actual gate-defining
prose in all ten now-watched files (the four original watched files, the
three previously under-watched inlined skills `/lrh-confirm-fixes`,
`/lrh-review-response`, `/lrh-closeout`, and three reference files with
real gate content -- `/lrh-implement`'s Step 4, the substitute-review
round cap, the WS exit-criteria gate). Two files checked and found to
carry no gate definitions of their own (`confirm-fixes-workflow.md`,
`lrh-self-review/SKILL.md`) were deliberately left unmarked and
unwatched, with the rationale recorded in the skill text.

A two-round `/lrh-self-review` diff-mode pass (this WI's own `_SELFREVIEW`
execution record has the full trail) caught a real structural gap in an
earlier version of the watch-list expansion -- 3 files with zero markers
(never stale regardless of content), 5 dropped files with genuine gate
content in 2 of them -- fixed before push.

Mirrored `src/lrh/skills/` changes into `.claude/skills/` for all five
touched skills; `land-workflow.md` kept byte-identical across `src/`,
`.claude/`, `.agents/`, and `.gemini/` mirrors.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `tests/gate_staleness_test.py`: 19/19 passing.
- `tests/cli_tests/`: 323/323 passing.
- Full suite (`tests/`, excluding `tests/smoke`): 1390/1390 passing.
- `scripts/format`/`scripts/lint`: pre-existing environment tool-version
  mismatch (black/ruff), unrelated to this change -- third time seen this
  session. Manually verified line length (<=88 chars) and ran `pylint` as
  a diagnostic (8.79/10, only missing-docstring style nits and one
  since-fixed single-letter variable name).

# Follow-up

None specific to this WI -- proceeding to `/lrh-land`.
