---
execution_id: 2026_10_08_06_28_43_WI_EXECUTION_RECORD_AGENT_FIELDS_IMPL
prompt_id: PROMPT(WI-EXECUTION-RECORD-AGENT-FIELDS:WI_EXECUTION_RECORD_AGENT_FIELDS_IMPL)[2026-10-08T05:54:12+00:00]
work_item: WI-EXECUTION-RECORD-AGENT-FIELDS
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/794
commit: 7d2d73632a7c4b3db46e199118d3703a983b6f4d
created_at: 2026-10-08T06:28:43+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-EXECUTION-RECORD-AGENT-FIELDS.md
session_transcript: claude-app:c5f26330-07dd-4169-bb76-4dbbf2e696e0
---

# Summary

Implemented WI-EXECUTION-RECORD-AGENT-FIELDS: investigated why `lrh prompt record-execution` omits `agent:`, `instruction_source:`, and `session_transcript:` and why `update-execution` cannot set the first two, reached a verdict, and implemented the fix. This record was itself created with the new flags, with no hand-edit of the three fields.

# Result

Verdict: the fields being optional is intentional; the missing creation-time CLI path is an oversight.
- **Intentional part:** `lrh-execution-sessions` makes all three fields optional and backward-compatible, expects `pending` when the session id is not yet known, and explicitly allows manual population. So no field is required, and the CLI assumes no default `--agent` (a wrong provenance value is worse than an absent one, and callers span Claude.app, Codex, and manual runs).
- **Oversight part:** the proposal never says how the fields get written. `/lrh-implement` was the only intended populator, and the LCATS report shows skills that say "immediately edit" still get skipped; `lrh-self-review` has no such instruction at all.

Changes (PR #794): `src/lrh/prompt_workflow.py` adds optional `--agent`, `--instruction-source`, `--session-transcript` to `record-execution` (field omitted when its flag is not passed, written after `created_at` in that order) and `--agent`, `--instruction-source` to `update-execution`. All values must be non-empty single-line; this also closes a pre-existing hole where `update-execution --session-transcript` accepted a newline and corrupted the frontmatter. Frontmatter replacement now treats backslashes literally, and a new `_set_frontmatter_field` raises rather than silently no-opping when it cannot place a field. Docs updated in `PROMPTS.md`, `project/executions/README.md`, and `scripts/prompts/README.md`. New unit and CLI tests cover flags, omission, rejection, replacement, anchors, and body text that looks like a field.

Deliberately not done: skill text still tells agents to hand-edit the fields (migration deferred to a follow-up work item, per the run plan the user approved). `update-execution` still only moves `in_progress` to `landed`, so an already-`landed` record cannot be amended this way.

# Validation

- `scripts/version tools`; `scripts/format --check --diff`: 280 files unchanged; `scripts/lint`: pass; `scripts/test`: pass (run twice, before and after the self-review fix); `lrh validate`: 0 errors, 0 warnings.
- Diff-mode self-review (`AD_HOC` record `..._IMPL_SELFREVIEW`): one substantive finding (newline in `update-execution --session-transcript`), reproduced and fixed with a regression test.

# Follow-up

- File and execute a follow-up work item migrating `lrh-implement`, `lrh-work-item`, `lrh-review-response`, `lrh-confirm-fixes`, and `lrh-self-review` (src plus rendered `.claude`/`.agents` copies) to pass the new flags.
- Consider letting `update-execution` amend records that are already `landed`.
- Optionally have `lrh validate` warn on execution records missing `agent` (the proposal's Stage 2 validator work).
