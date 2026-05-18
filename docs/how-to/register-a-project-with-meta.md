# Register a project with an LRH meta workspace

## Purpose

Use `lrh meta` to create or resolve an LRH meta workspace and register project repositories in its project registry. The current meta CLI is offline and file-based: it initializes workspace paths, writes registry records, lists records, and inspects stored project metadata.

## Prerequisites

- Decide where the meta workspace catalog should live.
- Choose a workspace mode:
  - `hybrid` (default): local/shareable catalog with global user config/state/cache.
  - `local`: catalog, config, state, and cache all under the local workspace root.
  - `global`: workspace and runtime paths use global XDG locations.
- Have a repository locator to register. It may be a local path, URL, or other stable locator string.

## Commands

Initialize the default hybrid workspace in the current directory:

```bash
lrh meta init --mode hybrid
```

Initialize an explicitly local workspace:

```bash
lrh meta init --mode local --workspace-root /path/to/lrh-workspace
```

Show the active workspace resolution:

```bash
lrh meta where
```

Register a local repository:

```bash
lrh meta register /path/to/project-repo
```

Register a GitHub tree URL. For supported GitHub tree locators, LRH stores the repository/ref locator separately from the relative project directory:

```bash
lrh meta register https://github.com/xenotaur/taurworks/tree/master/project
```

Override inferred registry metadata:

```bash
lrh meta register /path/to/project-repo \
  --project-dir project \
  --directory-name example-repo \
  --short-name example \
  --display-name "Example Project"
```

Allow a deliberate overwrite or duplicate target record:

```bash
lrh meta register /path/to/project-repo --force
```

List registered projects:

```bash
lrh meta list
```

Inspect one registered project:

```bash
lrh meta inspect example
```

Use module invocation when needed:

```bash
python -m lrh.cli.main meta register /path/to/project-repo
```

## Expected output or success criteria

- `lrh meta init` prints the initialized workspace mode/path and counts for created, updated, and unchanged files.
- `lrh meta register` prints the record path, project ID, and setup-state check result.
- `lrh meta list` prints each registered record, or `No registered projects found under projects/.` when the registry is empty.
- `lrh meta inspect` prints workspace context, stored project record fields, and derived local path existence checks.

## Common troubleshooting notes

- `lrh meta` resolves workspaces from explicit flags, `LRH_CONFIG`, `LRH_WORKSPACE`, local discovery, and then global discovery/defaults.
- Use `--workspace`, `--config`, or `--mode` on `list`, `where`, `register`, and `inspect` when the active workspace is ambiguous.
- Duplicate registration targets require `--force`.
- `setup_state` is a truth-first local check; remote locators may be reported as not checked.

## Related reference

- [CLI reference: `meta`](../reference/cli/meta.md)
- [How to inspect workspace state](inspect-workspace-state.md)
