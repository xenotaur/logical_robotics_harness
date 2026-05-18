# CLI Reference

CLI reference documents exact behavior for LRH command-line entrypoints.

## What belongs here

- Stable command syntax, options, arguments, outputs, and exit behavior.
- Command-specific notes that must remain synchronized with implemented CLI behavior.
- Links from task-oriented guides to the exact command facts they rely on.

## What does not belong here

- Broad operational playbooks that happen to call CLI commands.
- Beginner tutorials that introduce the CLI through a full learning path.
- Internal implementation notes that are not user-facing command behavior.
- Project-control state copied from [`../../../project/`](../../../project/).

## How to decide whether to add content here

Add content here when the reader already knows which command they need and wants exact details. If the document tells a reader which commands to choose for a task, it probably belongs in [how-to guides](../../how-to/README.md) and should link back here for command specifics.

## Currently relevant docs

- [`validate`](validate.md) — validate LRH project control files.
- [`snapshot`](snapshot.md) — generate Markdown context packets from project control files.
- [`survey`](survey.md) — survey Python source trees for assist planning workflows.
- [`request`](request.md) — render request prompts and inspect request-template resolution.
- [`work-items`](work-items.md) — validate, audit, and diagnose prompt-readiness for work-item files.
- [`meta`](meta.md) — manage LRH meta workspaces and project registry records.
