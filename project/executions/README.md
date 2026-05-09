# Execution Records

Execution records provide lightweight traceability for meaningful prompt-driven
work. They record which prompt ran, the associated work item or `AD_HOC`
bucket, current status, and concise evidence or follow-up notes from the run.

## Directory layout

```text
project/executions/
  README.md
  AD_HOC/
  <WORK_ITEM_ID>/
    YYYY_MM_DD_HH_MM_SS_SLUG.md
```

- Use work-item IDs as the primary grouping mechanism when a matching work item exists.
- Use `AD_HOC/` when no work item applies.

This directory is intentionally lightweight. It is not a workflow engine and does not introduce formal workstreams.

## Front matter schema

Execution records should include these front-matter fields:

- `execution_id`: `YYYY_MM_DD_HH_MM_SS_<SLUG_UPPER_UNDERSCORE>`
- `prompt_id`: full prompt identifier
- `work_item`: work-item ID or `AD_HOC`
- `status`: one of the status values below
- `rerun_of`: optional prior execution ID
- `pr`: optional PR identifier
- `commit`: optional commit SHA
- `created_at`: ISO8601 timestamp with timezone offset

## Status values

Allowed status values:

- `planned`
- `in_progress`
- `landed`
- `failed`
- `reverted`
- `superseded`

## Soft idempotence guidance

Before executing a prompt-driven PR, check `project/executions/` for the
prompt ID. Exact matches against the front-matter `prompt_id` field are
authoritative for deciding whether a prompt ID has already been executed.

Use the lookup commands by role:

- `lrh prompt check-execution --prompt-id ...` is the authoritative exact
  structured lookup for soft idempotence when the prompt ID is already
  available.
- `lrh match executions <prompt-file>` is a human-friendly convenience layer
  when starting from a prompt file; it extracts full prompt IDs and delegates to
  the same exact lookup.
- `lrh search executions <query>` is exploratory local substring search across
  execution-record frontmatter and body text for discovery, auditing, and
  debugging. Search results are useful context, but they are not authoritative
  for rerun or idempotence decisions.

Examples:

```bash
lrh prompt check-execution --prompt-id "$PROMPT_ID" --project-root .
lrh match executions prompts/my_prompt.md --project-root .
lrh search executions "PROMPT_EXECUTION_SEARCH" --project-root .
lrh search executions "release smoke" --project-root .
lrh search executions "AD_HOC" --project-root .
lrh search executions "PROMPT(" --status landed --work-item AD_HOC --project-root .
```

For recent-prompt dogfooding, first run the exact `prompt_id` lookup. Then use
`lrh match executions <prompt-file>` if the prompt was saved to a file, and use
`lrh search executions "<distinctive prompt text>"` only for surrounding context
such as related validation notes, failed attempts, or other `AD_HOC` records.
Exploratory search results are not authoritative soft-idempotence evidence.

If future heuristic or fuzzy matching is added, it must be clearly labeled
non-authoritative unless later design work explicitly changes this rule.

If a prior exact record exists:

- `landed` or `in_progress`: stop and report unless the prompt explicitly says rerun.
- `failed`, `reverted`, or `superseded`: summarize the prior run and continue only if the prompt indicates rerun or follow-up.
- unknown or ambiguous status: stop and report ambiguity.

## Notes

- Work-item linkage is optional.
- Keep records concise and useful.
- Prompt records are encouraged for meaningful work, not required for every tiny change.

## Important Rules

- Prompts should only manipulate execution records related to them.
- Previous execution records for other prompts should NOT be modified.

For example, a cleanup prompt that was removing a variable or folder from the documentation
should NOT remove references to the directory in previous completed execution records.
This applies to all updates to execution records and especially to cleanup work items.
