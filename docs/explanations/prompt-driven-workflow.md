# Prompt-driven workflow

LRH uses prompt IDs and execution records to make meaningful AI-assisted changes traceable without
turning every small edit into ceremony.

The canonical workflow is defined in [`PROMPTS.md`](../../PROMPTS.md). This page explains the idea
for readers who are new to the project.

## Why prompt traceability exists

A prompt-driven PR often starts from a block of instructions rather than a traditional issue. If
that prompt disappears into chat history, reviewers lose important context:

- what the agent was asked to do;
- whether the same prompt already ran;
- what validation was attempted;
- whether the work landed, failed, was reverted, or was superseded;
- what follow-up remains.

Execution records make that context durable under `project/executions/`.

## Prompt IDs

A prompt ID has this shape:

```text
PROMPT(<WORK_ITEM_OR_AD_HOC>:<SLUG_UPPER_UNDERSCORE>)[<ISO8601_TIMESTAMP_WITH_OFFSET>]
```

Use a work-item ID when the prompt directly implements or advances a work item. Use `AD_HOC` when
no work item applies.

## Soft idempotence

Before meaningful prompt-driven work begins, LRH checks whether the exact prompt ID already has an
execution record. Exact matches against execution-record frontmatter are authoritative.

The preferred check is:

```bash
lrh prompt check-execution --prompt-id "$PROMPT_ID" --project-root .
```

If a prior exact record is `landed` or `in_progress`, the safe behavior is to stop unless the new
prompt explicitly says it is a rerun. If a prior record is `failed`, `reverted`, or `superseded`,
the prior result should be summarized before deciding whether the new work is a rerun or follow-up.

## Execution records

Execution records live under `project/executions/`:

```text
project/executions/
  AD_HOC/
  <WORK_ITEM_ID>/
    YYYY_MM_DD_HH_MM_SS_SLUG.md
```

A useful record includes:

- the prompt ID;
- work-item linkage or `AD_HOC`;
- status;
- concise summary;
- result;
- validation;
- follow-up.

These records support review and search. They are not a substitute for tests, evidence files, or
status updates when those are needed.

## What not to do

Prompt workflow should stay lightweight. Do not create unrelated execution records. Do not edit
old records for other prompts as part of cleanup. Do not let prompt bookkeeping become more
important than correct code, docs, validation, and evidence.

## Relationship to `project/` and `docs/`

Execution records are project-control artifacts because they record what happened during a
meaningful prompt-driven run. This explanation page is only a guide. The authoritative prompt
workflow remains `PROMPTS.md`, and the execution-record schema remains
`project/executions/README.md`.

Authoritative sources:

- [prompt workflow](../../PROMPTS.md);
- [execution records README](../../project/executions/README.md);
- [record-execution helper README](../../scripts/prompts/README.md).
