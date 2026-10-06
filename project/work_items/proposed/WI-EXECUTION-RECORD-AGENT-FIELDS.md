---
resolution: null
blocked_reason: null
blocked: false
id: WI-EXECUTION-RECORD-AGENT-FIELDS
title: Investigate agent/instruction_source/session_transcript gap in record-execution field population
type: investigation
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design: []
depends_on: []
blocked_by: []
expected_actions:
  - create_report
  - edit_file
  - add_cli_command
forbidden_actions:
  - force_push
  - delete_branch
  - modify_ci_pipeline
acceptance:
  - A documented recommendation exists for each of the three investigation questions (record-execution flags and default, update-execution extension, intentional-vs-oversight verdict)
  - If the verdict is oversight and a fix is warranted, record-execution and/or update-execution are extended accordingly with lrh validate and the relevant tests passing
  - If the verdict is intentional design, the conclusion and its rationale are recorded in closeout evidence with no speculative code change made
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - Investigation findings recorded in this work item or its execution record
  - Possible changes to src/lrh/prompt_workflow.py (record-execution and update-execution argument parsing, render_execution_content)
  - Possible changes to src/lrh/prompt_workflow_records.py if field parsing needs updating
  - Possible test updates for the prompt workflow CLI
---

# WI-EXECUTION-RECORD-AGENT-FIELDS

## Summary

Investigate why `lrh prompt record-execution` never populates `agent:`,
`instruction_source:`, and `session_transcript:` in generated execution-record
frontmatter (they are omitted entirely, not blank), despite downstream
conventions (e.g. LCATS's `project/executions/README.md`) documenting them as
expected on every record. Decide whether the CLI should gain flags/defaults to
close the gap, whether `update-execution` should be extended to set them after
creation, or whether the current "calling skill fills them in by hand" design is
intentional.

## Problem / Context

Reported from a downstream consumer repo (LCATS), not discovered by working in
this repo directly. During a `/lrh-execute WI-SEGMENT-0102` run there, six
execution records (implementation, review-response, three substitute
self-review rounds, confirm-fixes) were created without these fields; the gap
was only caught at `/lrh-closeout` time and each record was hand-edited
retroactively. A LCATS-side work item for this was mistakenly created and then
closed unmerged (LCATS PR #429) once it was clear the fix belongs here.

Reproduction: `lrh prompt record-execution --prompt-id <id> --work-item AD_HOC
--slug <slug> --status in_progress --project-root .` in any LRH-managed
project; the resulting file has no `agent:`, `instruction_source:`, or
`session_transcript:` line.

Source confirmation: `render_execution_content` in
`src/lrh/prompt_workflow.py` hard-codes exactly
`execution_id/prompt_id/work_item/status/rerun_of/pr/commit/created_at`.
`update-execution` in the same file only edits `status`/`pr`/`commit`/
`session_transcript`, so a record missing `agent:`/`instruction_source:` has no
CLI-driven way to gain them. This repo's own skills (e.g. `lrh-implement`
Step 9, `lrh-work-item` Step 10) instead carry an "immediately edit the
generated file" instruction, and `project/design/backlog.md` (the entry on
`lrh-implement` never passing `--pr`) records the same pattern, which suggests
the manual-edit design may be deliberate. This investigation must decide
whether that is a sufficient design or a gap, noting that non-LRH-skill callers
(such as downstream repos) have no such instruction to follow.

### Duplication search
- In-repo: No existing implementation found (grep over `src/`, `project/design/proposals/`, `project/workstreams/`, `project/work_items/`, `.claude/skills/` for these field names surfaces only unrelated resolved session/frontmatter items and the backlog note above)
- Sibling repos: LCATS (reporting repo) has the downstream convention doc but no code fix
- External libraries: None identified; this is LRH-specific CLI/schema behavior
- Recommendation: Proceed

### Demand search
- Work items: None found
- Proposals: None found
- Backlog: Related but not a duplicate: the `lrh-implement` missing-`--pr` entry (same subsystem and "immediately edit" pattern, different missing instruction)
- Recommendation: No action

## Scope

- Investigate whether `record-execution` should accept `--agent` and `--instruction-source` flags, and what `--agent` default (e.g. `claude_app`) is sensible when omitted
- Investigate whether `update-execution` should be able to set `agent:` and `instruction_source:` after creation
- Reach and document a verdict: intentional design or oversight
- Implement the resulting fix in this repo if, and only if, the verdict calls for one

## Required Changes

1. Read `src/lrh/prompt_workflow.py`, `src/lrh/prompt_workflow_records.py`, and each skill reference that instructs manually editing these three fields (`lrh-implement`, `lrh-work-item`, `lrh-review-response`, `lrh-confirm-fixes`, `lrh-self-review`).
2. Determine design intent: deliberate (e.g. a correct `agent`/`instruction_source` cannot be known CLI-side) or an oversight from when the schema grew after the CLI shipped.
3. Record the verdict and rationale in this work item or its execution record.
4. If a fix is warranted, add flags to `record-execution` and/or extend `update-execution` in `src/lrh/prompt_workflow.py`, update `render_execution_content`, and update skill reference docs to stop instructing manual edits for fields the CLI now sets.
5. Add or update tests covering any new or changed CLI behavior.

## Non-Goals

- Do not make any LCATS-side change.
- Do not change the existing `update-execution --session-transcript` path; only `agent`/`instruction_source` and creation-time defaults are in scope.
- Do not retroactively backfill existing execution records in this repo.

## Acceptance Criteria

- A documented recommendation exists for each of the three investigation questions.
- If the verdict calls for a fix, `record-execution`/`update-execution` are extended accordingly, `lrh validate` passes, and the relevant tests pass.
- If the verdict is "intentional design", that conclusion and its rationale are recorded with no speculative code change.

## Validation

- `lrh validate`
- `scripts/test`

## Risk Notes

- A CLI-baked default `--agent` value could be wrong when invoked from a backend other than Claude Code; weigh a required flag against a default.
- Changing the frontmatter shape of `render_execution_content` must stay compatible with `parse_front_matter_fields` and downstream parsers, including LCATS's.
