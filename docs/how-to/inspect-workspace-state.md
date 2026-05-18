# Inspect workspace state

## Purpose

Use `lrh meta where`, `list`, and `inspect` to understand which LRH meta workspace is active, where its files live, and what project records it contains.

This is the safest first step before registering projects or debugging meta-workspace behavior because the commands are read-only.

## Prerequisites

- An initialized meta workspace, or enough context for workspace discovery to find one.
- If discovery is ambiguous, know the intended `--workspace`, `--config`, or `--mode` value.

## Commands

Show human-readable active workspace diagnostics:

```bash
lrh meta where
```

Show machine-readable workspace diagnostics:

```bash
lrh meta where --json
```

Resolve a specific workspace root:

```bash
lrh meta where --workspace /path/to/lrh-workspace
```

List project registry records:

```bash
lrh meta list
```

Inspect one project by exact project ID, short name, or registry directory name:

```bash
lrh meta inspect example
```

Use module invocation when needed:

```bash
python -m lrh.cli.main meta where --json
```

## Expected output or success criteria

- `lrh meta where` prints `Active LRH meta workspace`, LRH version, mode, resolution source, config path, catalog root, projects directory, state directory, cache directory, and runtime scope notes.
- `lrh meta where --json` prints the same workspace facts as deterministic JSON.
- `lrh meta list` prints one block per registered project, or an explicit empty-registry message.
- `lrh meta inspect` prints workspace context, project record fields, and derived local path checks.

## Common troubleshooting notes

- If no workspace can be resolved, run `lrh meta init --mode hybrid`, `lrh meta init --mode local`, or point commands at an existing workspace with `--workspace`.
- Use `--mode local`, `--mode hybrid`, or `--mode global` to make mode assumptions explicit when debugging discovery.
- `where`, `list`, and `inspect` do not register projects or mutate registry records.

## Related reference

- [CLI reference: `meta`](../reference/cli/meta.md)
- [How to register a project with meta](register-a-project-with-meta.md)
