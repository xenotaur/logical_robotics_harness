# Your first prompt-driven change

This tutorial walks through LRH's lightweight prompt workflow: choose a prompt ID, make a small meaningful change, check for prior execution, and record what happened.

Prompt workflow is traceability, not ceremony. Use it for meaningful prompt-driven work where future readers should know what was requested, what ran, and what validation supported the result.

## When to use prompt IDs and execution records

Use a prompt ID and execution record when a change is meaningfully driven by a prompt, especially when it:

- implements or advances a work item;
- changes project policy, documentation, behavior, or release process;
- may be rerun by an agent later;
- needs durable validation notes for review.

Skip execution records for tiny exploratory edits or obvious typo fixes unless a maintainer asks for one.

The authoritative workflow is [`PROMPTS.md`](../../PROMPTS.md). Execution-record schema details live in [`project/executions/README.md`](../../project/executions/README.md).

## Step 1: Choose a prompt ID

A prompt ID has this form:

```text
PROMPT(<WORK_ITEM_OR_AD_HOC>:<SLUG_UPPER_UNDERSCORE>)[<ISO8601_TIMESTAMP_WITH_OFFSET>]
```

Use a work-item ID when the prompt directly advances a work item. Use `AD_HOC` when no work item applies.

For an ad hoc documentation change, you can ask LRH to generate a prompt label:

```bash
scripts/prompts/label-prompt --slug improve-docs-example
```

The output includes a `prompt_id` and a suggested execution-record path. Keep the full prompt ID with the prompt text you submit to a human or agent.

For this tutorial, examples use a placeholder:

```bash
PROMPT_ID='PROMPT(AD_HOC:IMPROVE_DOCS_EXAMPLE)[2026-05-18T12:00:00-04:00]'
```

When doing real work, use the actual generated timestamp instead of copying this placeholder unchanged.

## Step 2: Check soft idempotence before changing files

Before starting meaningful prompt-driven work, check whether the exact prompt ID already has an execution record:

```bash
lrh prompt check-execution --prompt-id "$PROMPT_ID" --project-root .
```

If no record exists, continue.

If an exact prior record exists:

- `landed` or `in_progress`: stop unless your prompt explicitly says this is a rerun.
- `failed`, `reverted`, or `superseded`: summarize the prior run and continue only if this is clearly a rerun or follow-up.
- unknown or ambiguous status: stop and ask for clarification.

Exact matches against execution-record frontmatter are authoritative for these soft idempotence decisions. Exploratory search can help you understand surrounding history, but it should not override the exact check:

```bash
lrh search executions "IMPROVE_DOCS_EXAMPLE" --project-root .
```

## Step 3: Make a small meaningful change

Pick a change that is easy to review. For example, add a sentence to a local documentation draft or create a short note under a project-specific docs directory.

Keep the prompt nearby in your PR or task description. A useful prompt says:

- what should change;
- what should not change;
- what validation should run;
- whether this is a rerun or follow-up;
- which work item applies, or that the work is `AD_HOC`.

Do not invent LRH behavior in the change. If a workflow is not implemented yet, document it as future or out of scope rather than presenting it as runnable.

## Step 4: Validate the change

Run checks appropriate to the change. In the LRH repository, start with the tool version report during task-phase validation:

```bash
scripts/version tools
```

For typical code or documentation changes in this repository, the recommended checks are:

```bash
scripts/lint
scripts/test
```

For documentation-only changes, also manually inspect copy-paste commands and links where practical. If an environment limitation prevents a check, record exactly what was and was not run.

## Step 5: Record execution

After the work and validation, create an execution record for the prompt. Use `AD_HOC` when no work item applies:

```bash
scripts/prompts/record-execution \
  --prompt-id "$PROMPT_ID" \
  --work-item AD_HOC \
  --slug improve-docs-example \
  --status in_progress
```

The helper writes a Markdown file under `project/executions/AD_HOC/`. Use the generated file to summarize:

- what changed;
- the result;
- validation commands and outcomes;
- follow-up, if any.

If you already know the PR or commit reference, pass `--pr` or `--commit`. Otherwise, leave those fields empty and keep the record concise.

## Step 6: Apply rerun rules later

If the same prompt returns later, repeat the exact check first:

```bash
lrh prompt check-execution --prompt-id "$PROMPT_ID" --project-root .
```

Then apply the status rules from `PROMPTS.md` and `project/executions/README.md`. If the new run is intentionally a rerun of a prior failed, reverted, or superseded execution, pass `--rerun-of` when recording the new execution:

```bash
scripts/prompts/record-execution \
  --prompt-id "$PROMPT_ID" \
  --work-item AD_HOC \
  --slug improve-docs-example-rerun \
  --status in_progress \
  --rerun-of 2026_05_18_120000_IMPROVE_DOCS_EXAMPLE
```

Use the actual prior `execution_id` from the existing record.

## What success looks like

You have succeeded when:

- the prompt has a stable ID;
- the exact soft-idempotence check was considered before the change;
- the change is small and reviewable;
- relevant validation was run or explicitly noted as not run;
- a matching execution record exists under `project/executions/`.

## Where to go next

- Read [`PROMPTS.md`](../../PROMPTS.md) for canonical prompt ID and rerun rules.
- Read [`project/executions/README.md`](../../project/executions/README.md) for execution-record fields and allowed statuses.
- Read the explanation of the [prompt-driven workflow](../explanations/prompt-driven-workflow.md) for the rationale behind this lightweight traceability layer.
