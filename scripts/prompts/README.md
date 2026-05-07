# Prompt Workflow Helpers

This directory contains lightweight helper scripts for LRH prompt workflows.

- `label-prompt`: generate a prompt ID and suggested execution-record path.
- `record-execution`: generate an execution-record Markdown document.

See `PROMPTS.md` for workflow guidance and `project/executions/README.md` for execution-record schema details.

For safety, both scripts validate `--work-item` against a simple ID pattern (`^[A-Za-z0-9][A-Za-z0-9_-]*$`) so execution paths remain scoped under the selected output root.


## Recommended work-item workflow

Use these helpers with the structured request command:

```text
Work item Markdown
  -> lrh request codex-prompt-from-work-item
  -> Codex Cloud prompt
  -> PR
  -> execution record
```

After your PR is generated, run `record-execution --work-item <WORK_ITEM_ID>`
so the record can capture PR/commit metadata and be written under the
correct work-item folder instead of the default `AD_HOC` location.


Once LRH is installed in a target repository, prefer the installed commands:

```bash
lrh prompt label ...
lrh prompt check-execution --prompt-id "$PROMPT_ID" --project-root .
lrh match executions prompts/my_prompt.md --project-root .
lrh search executions "release smoke" --project-root .
lrh prompt record-execution ...
```

Use `lrh prompt check-execution --prompt-id ...` as the authoritative exact
lookup for soft idempotence decisions. Use `lrh match executions <prompt-file>`
only as a convenience layer that extracts prompt IDs from a file and delegates
exact matching. Use `lrh search executions <query>` for exploratory discovery,
auditing, and debugging; search results are not authoritative for blocking or
rerun decisions.

The repository-local scripts are compatibility wrappers that first run the
repository checkout CLI via `python -m lrh.cli.main prompt ...` for deterministic
local behavior; they fall back to installed `lrh prompt ...` only when the
checkout module cannot be resolved. Use installed `lrh prompt ...`,
`lrh match ...`, and `lrh search ...` commands as the portable interface for
client repositories.
