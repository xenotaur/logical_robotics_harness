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

After your PR is generated, run `record-execution` so the record can capture PR/commit metadata.
