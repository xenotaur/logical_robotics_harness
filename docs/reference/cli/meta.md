# `lrh meta`

## Command purpose

`lrh meta` manages LRH meta workspaces and the file-based project registry inside a resolved workspace. It initializes workspace paths, reports active workspace resolution, registers project records, lists records, and inspects a single record.

Workspace resolution precedence is: explicit flags, `LRH_CONFIG`, `LRH_WORKSPACE`, local discovery, then global discovery/defaults.

## Canonical invocation patterns

```bash
lrh meta init --mode hybrid
lrh meta init --mode local --workspace-root /path/to/workspace
lrh meta init --mode global
lrh meta where
lrh meta where --json
lrh meta list
lrh meta register /path/to/project-repo
lrh meta register https://github.com/xenotaur/taurworks/tree/master/project
lrh meta inspect example
python -m lrh.cli.main meta where --json
```

Use workspace-resolution flags on `list`, `where`, `register`, and `inspect` when needed:

```bash
lrh meta where --workspace /path/to/workspace
lrh meta list --config /path/to/.lrh/config.toml
lrh meta register /path/to/project-repo --mode local
lrh meta inspect example --workspace /path/to/workspace
```

## Important options and arguments

Top-level subcommands:

- `init`: initialize LRH meta workspace directories and config.
- `where`: show the active workspace and how it was resolved.
- `list`: list registered projects from the active workspace registry.
- `register`: register one project repository in the workspace registry.
- `inspect`: inspect one registered project with workspace context.

`meta init` options:

- `--name NAME`: workspace display name for generated README/config. Defaults to `LRH Workspace`.
- `--mode {hybrid,global,local}`: initialization mode. Defaults to `hybrid`.
- `workspace_root`: optional workspace/catalog root directory for hybrid mode.
- `--workspace-root WORKSPACE_ROOT`: explicit workspace/catalog root directory.
- `--force`: replace incompatible managed paths/content when safe.

Workspace-resolution options for `list`, `where`, `register`, and `inspect`:

- `--workspace`, `--workspace-root`: explicit workspace/catalog root containing `.lrh/config.toml`.
- `--config CONFIG`: explicit workspace `config.toml` path.
- `--mode {hybrid,local,global}`: workspace mode override for resolution.

`meta where` option:

- `--json`: emit machine-readable JSON for the active workspace.

`meta register` arguments and options:

- `repo_locator`: required repository locator string, such as a local path, URL, or other stable locator.
- `--project-dir PROJECT_DIR`: project control directory relative to repo root. Defaults to inferred values for supported URL patterns or `project` otherwise.
- `--directory-name DIRECTORY_NAME`: registry directory name under `projects/`.
- `--short-name SHORT_NAME`: short display label.
- `--display-name DISPLAY_NAME`: human-readable project name.
- `--force`: allow deliberate duplicates and overwrite existing target records.

`meta inspect` argument:

- `project`: project selector. It may be an exact project ID, short name, or registry name.

## Current behavior and limitations

- `hybrid` is the default initialization mode. It uses a local/shareable catalog root with global user config/state/cache defaults.
- When XDG variables are unset, global defaults are `~/.config/lrh/config.toml`, `~/.local/state/lrh/`, and `~/.cache/lrh/`.
- `meta register` is offline and writes registry files in the resolved workspace.
- Supported GitHub tree locators are normalized by default so `repo_locator` stores the repository/ref locator and `project_dir` stores the tail path such as `project`.
- `meta list` prints `No registered projects found under projects/.` when the registry is empty.
- `meta inspect` performs derived local path existence checks when applicable; remote locators may not have local path checks.

## Related how-to pages

- [Register a project with an LRH meta workspace](../../how-to/register-a-project-with-meta.md)
- [Inspect workspace state](../../how-to/inspect-workspace-state.md)
- [Use the developer sandbox](../../how-to/use-the-developer-sandbox.md)
