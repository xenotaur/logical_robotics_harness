# Generate a context snapshot

## Purpose

Use `lrh snapshot` to render Markdown context packets from LRH project control files. Snapshots are useful when handing project state to an assistant or saving a bounded view of current project context.

The command is read-only. It can print to stdout, write to a file, or do both.

## Prerequisites

- Run in or near a repository with a `project/` control directory, or pass `--project-root`.
- Know the snapshot scope you need: `project`, `current_focus`, or one `work_item`.

## Commands

Generate a project-wide snapshot to stdout:

```bash
lrh snapshot project
```

Generate current-focus context:

```bash
lrh snapshot current_focus
```

Generate context for one work item:

```bash
lrh snapshot work_item WI-EXAMPLE
```

Write a snapshot to a file:

```bash
lrh snapshot project --output /tmp/lrh-project-snapshot.md
```

Write to a file and also print to stdout:

```bash
lrh snapshot current_focus --output /tmp/lrh-focus.md --stdout
```

Include optional sections when the corresponding project files exist:

```bash
lrh snapshot project --include-status --include-guardrails --include-design
```

Use module invocation when needed:

```bash
python -m lrh.cli.main snapshot work_item WI-EXAMPLE --project-root .
```

## Expected output or success criteria

- Exit code `0` means the requested snapshot was rendered.
- With no `--output`, the Markdown packet is printed to stdout.
- With `--output`, LRH creates parent directories as needed and writes the packet to that path.
- Exit code `2` is used for command usage problems or missing project files.

## Common troubleshooting notes

- `--project-root` may be a repository root or the project control directory. LRH resolves the control directory from that input.
- `work_item` requires a work-item identifier argument.
- Optional include flags are additive and only include content that exists; missing optional files are not created.

## Related reference

- [CLI reference: `snapshot`](../reference/cli/snapshot.md)
- [How to validate a project](validate-a-project.md)
