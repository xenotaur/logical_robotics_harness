# LRH Prompt Workflow

This guide defines a lightweight prompt workflow for meaningful prompt-driven changes.

## Why prompt IDs and execution records exist

Prompt IDs and execution records make prompt-driven work easier to trace, search, and review.
They help answer:

- what prompt drove a change
- whether a prompt has already been executed
- what happened during the execution

This workflow is intentionally lightweight and should not become process overhead.

## When to use this workflow

Use prompt IDs and execution records for meaningful prompt-driven changes, especially when changes affect:

- design
- roadmap
- work items
- implementation
- tests
- project-control artifacts

## When not to use this workflow

Do not require prompt records for:

- casual discussion
- exploratory analysis
- small obvious fixes

If traceability helps anyway, you may still create one record.

## Prompt ID format

Use this shape:

```text
PROMPT(<WORK_ITEM_OR_AD_HOC>:<SLUG_UPPER_UNDERSCORE>)[<ISO8601_TIMESTAMP_WITH_OFFSET>]
```

Examples:

```text
PROMPT(WI-META-CLI-MVP:REGISTER_IMPLEMENTATION)[2026-04-24T16:24:13-04:00]
PROMPT(AD_HOC:REGISTER_AUDIT)[2026-04-24T16:30:00-04:00]
```

## Execution record format

Execution records live under `project/executions/` and include YAML-style front matter plus brief sections:

- Summary
- Result
- Validation
- Follow-up

See `project/executions/README.md` for canonical layout and schema guidance.

WARNING: Prompts should only manipulate execution records related to them. Previous execution
records for other prompts should not be modified. This is to prevent the loss of important
information - for example, a cleanup prompt that was removing a variable or folder from the
documentation should not remove references to the directory in previous completed execution
records. This applies to all updates to execution records and especially to cleanup work items.

## Rerun, revert, and supersession handling

Use status values from `project/executions/README.md`: `planned`, `in_progress`, `landed`, `failed`, `reverted`, `superseded`.

When rerunning a prompt, create a new execution record and link prior execution via `rerun_of`.

If work is reverted or superseded, preserve prior records and set status accordingly rather than deleting history.

## Soft idempotence before execution

Before starting prompt-driven PR work, perform an exact structured lookup for
the prompt ID in `project/executions/`. Exact `prompt_id` matches are
authoritative for deciding whether a prompt has already been executed.

Preferred command when the prompt ID is already available:

```bash
lrh prompt check-execution --prompt-id "$PROMPT_ID" --project-root .
```

If a prior exact record exists:

- `landed` or `in_progress`: stop and report unless prompt explicitly requests rerun.
- `failed`, `reverted`, or `superseded`: summarize prior run and continue only if prompt is a rerun or follow-up.
- unknown or ambiguous status: stop and report ambiguity.

Exploratory search results can provide useful context for discovery, auditing,
and debugging, but they should not by themselves drive blocking or rerun
decisions. If future heuristic or fuzzy matching is added, it must be clearly
labeled non-authoritative unless later design work explicitly changes this rule.

## Codex Cloud prompt requirements

For meaningful prompt-driven implementation in Codex Cloud:

1. include an explicit prompt ID in the prompt text
2. keep work-item linkage optional (`AD_HOC` is valid)
3. generate one execution record per meaningful prompt run
4. keep process lightweight and non-blocking for tiny fixes

## Work-item to Codex prompt flow

For work-item-driven implementation, use this sequence:

```text
Work item Markdown
  -> lrh request codex-prompt-from-work-item
  -> Codex Cloud prompt
  -> PR
  -> execution record
```

Suggested command flow:

```bash
lrh request codex-prompt-from-work-item \
  --work-item project/work_items/active/WI-EXAMPLE.md \
  --slug implement-wi-example \
  --out /tmp/codex_prompt.md

# Submit /tmp/codex_prompt.md to Codex Cloud and open a PR.

scripts/prompts/record-execution \
  --prompt-id "PROMPT(WI-EXAMPLE:IMPLEMENT_WI_EXAMPLE)[2026-04-24T20:15:00-04:00]" \
  --work-item WI-EXAMPLE \
  --slug implement-wi-example \
  --status in_progress
```

Notes:

- `codex-prompt-from-work-item` is the preferred structured command for work-item input.
- Pass `--work-item <WORK_ITEM_ID>` to `record-execution` for work-item-driven
  runs so records are written under that work-item directory instead of the
  `AD_HOC` default.
- Record execution after generating the PR so the record can include final PR/commit references.
- Keep this workflow lightweight: skip extra ceremony for tiny exploratory edits.

## Installed CLI commands (preferred)

When LRH is installed, prefer package-owned commands that support explicit target roots:

```bash
lrh prompt label --work-item WI-EXAMPLE --slug implement-example --project-root /path/to/client-repo
lrh prompt check-execution --prompt-id "PROMPT(WI-EXAMPLE:IMPLEMENT_EXAMPLE)[2026-04-24T20:15:00-04:00]" --project-root /path/to/client-repo
lrh match executions /path/to/prompt-file.md --project-root /path/to/client-repo
lrh search executions "validation command" --project-root /path/to/client-repo
lrh search executions "PROMPT(" --status planned --work-item AD_HOC --project-root /path/to/client-repo
lrh prompt record-execution --prompt-id "PROMPT(WI-EXAMPLE:IMPLEMENT_EXAMPLE)[2026-04-24T20:15:00-04:00]" --work-item WI-EXAMPLE --slug implement-example --project-root /path/to/client-repo --status in_progress
```

Use the commands by role:

- `lrh prompt check-execution --prompt-id ...` is the authoritative exact
  structured lookup for soft idempotence. Use it before meaningful prompt-driven
  PR work when the prompt ID is available.
- `lrh match executions <prompt-file>` is a human-friendly convenience layer
  for prompt files. It extracts full prompt IDs from the file and delegates each
  ID to the same exact execution-record lookup. It does not perform fuzzy
  matching or make rerun recommendations for unmatched IDs.
- `lrh search executions <query>` is exploratory local substring search across
  execution-record frontmatter and body text. Use it for discovery, auditing,
  and debugging; do not treat search results as authoritative for
  soft-idempotence decisions.

These commands preserve the same prompt ID and execution-record formats as the repository-local helper scripts.

## Helper scripts

### `scripts/prompts/label-prompt`

Generates a prompt ID and suggested execution record path.

```bash
scripts/prompts/label-prompt --work-item WI-META-CLI-MVP --slug register-implementation
scripts/prompts/label-prompt --slug register-audit
```

Outputs include:

- `prompt_id`
- `execution_dir`
- `suggested_execution_file`

`--work-item` must be a safe ID (letters/numbers plus `_` or `-`) so paths stay scoped to execution-record directories.

### `scripts/prompts/record-execution`

Generates an execution-record Markdown file.

```bash
scripts/prompts/record-execution \
  --prompt-id "PROMPT(WI-META-CLI-MVP:REGISTER_IMPLEMENTATION)[2026-04-24T16:24:13-04:00]" \
  --work-item WI-META-CLI-MVP \
  --slug register-implementation \
  --status planned
```

Use `--dry-run` to preview output without writing files.
