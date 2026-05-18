# `lrh snapshot`

## Command purpose

`lrh snapshot` generates Markdown context packets from LRH project control files. It is intended for bounded assistant context and human review, and it is read-only except for an optional output file.

## Canonical invocation patterns

```bash
lrh snapshot project
lrh snapshot current_focus
lrh snapshot work_item WI-EXAMPLE
lrh snapshot project --project-root /path/to/repo
lrh snapshot project --output /tmp/lrh-project.md
lrh snapshot current_focus --output /tmp/lrh-focus.md --stdout
python -m lrh.cli.main snapshot work_item WI-EXAMPLE --project-root .
```

## Important options and arguments

- Scope argument, required:
  - `project`: generate project-wide context.
  - `current_focus`: generate current-focus context.
  - `work_item`: generate context for a specific work item.
- `work_item_id`: required positional argument after `work_item`.
- `--project-root PROJECT_ROOT`: repository root or project directory. Defaults to the current directory.
- `--output OUTPUT`: write the generated packet to this file path.
- `--stdout`: also print generated context to stdout. Without `--output`, stdout is already used.
- `--include-status`: include `project/status/current_status.md` when it exists.
- `--include-guardrails`: include summaries from `project/guardrails/` when files exist.
- `--include-design`: include `project/design/design.md` when it exists.

## Current behavior and limitations

- The output format is Markdown.
- Parent directories for `--output` are created as needed.
- Exit code `0` means the requested packet was rendered.
- Exit code `2` is used when required project files cannot be found.
- Optional include flags do not create missing files.
- The command currently supports the implemented scopes only: `project`, `current_focus`, and `work_item`.

## Related how-to pages

- [Generate a context snapshot](../../how-to/generate-a-snapshot.md)
- [Validate a project control directory](../../how-to/validate-a-project.md)
