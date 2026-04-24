# Execution Records

Execution records provide lightweight traceability for meaningful prompt-driven work.

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

Before executing a prompt-driven PR, search `project/executions/` for the prompt ID.

If a prior record exists:

- `landed` or `in_progress`: stop and report unless the prompt explicitly says rerun.
- `failed`, `reverted`, or `superseded`: summarize the prior run and continue only if the prompt indicates rerun or follow-up.
- unknown or ambiguous status: stop and report ambiguity.

## Notes

- Work-item linkage is optional.
- Keep records concise and useful.
- Prompt records are encouraged for meaningful work, not required for every tiny change.
