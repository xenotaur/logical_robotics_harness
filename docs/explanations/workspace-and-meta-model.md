# Workspace and meta model

LRH is designed to work across multiple repositories, but each project repository keeps its own
local authority. The workspace and meta model is the coordination layer that helps LRH find and
catalog LRH-compatible repositories without replacing their project control planes.

## Project-local authority comes first

For any project, that repository's `project/` directory remains authoritative for project state.
A workspace catalog may store summaries, pointers, or registration metadata, but those entries are
informative by default and can become stale.

This distinction prevents a dashboard or workspace from accidentally overriding a project's own
principles, focus, work items, evidence, or status.

## What the meta layer is for

The meta-control layer is meant to answer workspace-level questions such as:

- Which LRH-compatible projects are registered here?
- Where is the workspace configuration?
- Which storage mode is in use?
- Where should shareable catalog data, private state, and cache data live?

It is not an agent orchestration layer, background execution engine, or remote multi-user server.

## Workspace modes

The MVP model defines three workspace modes.

### Hybrid mode

Hybrid mode is the default. It keeps a local/shareable workspace catalog in a workspace root while
using global user locations for private runtime state and cache data.

### Local mode

Local mode keeps catalog, configuration, private runtime state, logs, cache, and temporary data
under one explicit local workspace root. Private state should remain ignored and non-authoritative.

### Global mode

Global mode uses XDG-style user locations for configuration, state, and cache. It is useful when a
user wants LRH workspace state managed from global defaults rather than a shareable local catalog
root.

## Workspace-context resolution

`lrh meta` commands operate against a resolved workspace context. The MVP resolution order is:

1. explicit CLI flags;
2. `LRH_CONFIG`;
3. `LRH_WORKSPACE`;
4. local workspace auto-discovery;
5. global workspace auto-discovery;
6. built-in defaults.

The important principle is visibility: commands should make the selected workspace/config
inspectable so users are not surprised by hidden discovery behavior. `lrh meta where` is the
primary diagnostics surface for this context.

## Storage classes

The meta model distinguishes storage by authority and portability:

- `projects/` stores durable, shareable catalog metadata about registered repositories;
- `.lrh/` stores workspace runtime/tool configuration;
- `private/` stores ignored local runtime state such as logs, chats, cache, temporary state, and
  local secrets;
- secrets, tokens, sensitive logs, and unnecessary personal data should not be committed.

## How this relates to runtime state

Workspace summaries, focus blurbs, and latest-work-item pointers are derived views unless a design
explicitly gives them authority. If they disagree with the source project's `project/` directory,
the project-local control plane wins.

## Authoritative sources

- [meta-control plane MVP spec](../../project/design/meta_control_plane_mvp_spec.md);
- [architecture design](../../project/design/architecture.md);
- [repository state versus runtime state](repository-state-vs-runtime-state.md);
- [repository specification](../../project/design/repository_spec.md).
