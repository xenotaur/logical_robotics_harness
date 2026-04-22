# LRH Meta-Control Plane MVP Spec

## 1. Scope

This spec defines an MVP **workspace-level catalog and coordination layer** for multiple LRH-compatible repositories.

The meta-control layer is intentionally secondary to each project repository's local control plane.

This MVP defines:
- dashboard/workspace repository layout
- workspace-context resolution model
- CLI subcommands for meta operations
- storage boundaries
- project registration format

This MVP does **not** define:
- agent orchestration
- background workflow execution
- deep integrations
- remote multi-user server behavior

---

## 2. Authority model

### 2.1 Project-local authority remains primary
For any project, that repository's `project/` directory remains authoritative.

### 2.2 Meta layer is informative/coordinating
The dashboard/workspace repository catalogs and coordinates across repos, but project summaries and pointers are informative by default.

### 2.3 Dashboard authority boundary
The dashboard is authoritative only for its own workspace registry/catalog records (for example, project registration metadata under `projects/`).

### 2.4 No precedence override
The dashboard/meta layer does not override, replace, or participate in a project's internal LRH precedence hierarchy.

---

## 3. Workspace layout

### 3.1 Local workspace layout

```
<workspace-root>/
  .gitignore
  README.md
  .lrh/
    config.toml
  projects/
  private/
    logs/
    chats/
    cache/
    state/
    tmp/
    secrets/
```

Local workspaces are rooted at an explicit directory and identified by `.lrh/config.toml`.

### 3.2 Global workspace layout (XDG-style)

Global/user-level workspace defaults should use XDG-style storage classes rather than an ad hoc `~/.lrh` monolith:

- config (for durable user/workspace configuration)
- state (for durable local state)
- cache (for disposable caches)

Exact path wiring can evolve during implementation, but the design contract is explicit separation of config/state/cache concerns.

---

## 4. Workspace-context resolution

`lrh meta` commands operate against a resolved workspace context. Resolution precedence is:

1. explicit CLI flags (for example `--workspace`, `--config`, `--mode`)
2. `LRH_CONFIG`
3. `LRH_WORKSPACE`
4. local workspace auto-discovery
5. global workspace auto-discovery
6. built-in defaults

Rationale:
- predictable precedence is easier to explain and debug
- explicit user intent should win over inferred defaults
- user-level defaults and project-local defaults are distinct concepts

The selected workspace/config should be rendered or inspectable in command output so behavior is visible rather than surprising.

---

## 5. Storage classes

### `projects/`
Durable, shareable catalog metadata about registered LRH-compatible repositories.

### `.lrh/`
LRH runtime/tool configuration for the workspace.

### `private/`
Ignored local runtime/scratch state (logs, chat traces, caches, transient state, local secrets). This state is explicitly non-authoritative.

### Never stored in committed metadata
Secrets, tokens, sensitive logs, unnecessary PII.

---

## 6. Freshness and derived data

Any project summary, focus blurb, latest-work-item pointer, or status summary stored in the workspace may become stale relative to the source project repository.

Unless explicitly designated otherwise, workspace summaries and pointers should be treated as derived/informative views of project-local artifacts.

---

## 7. CLI commands (MVP)

- `lrh meta init`
- `lrh meta register`
- `lrh meta deregister`
- `lrh meta list`
- `lrh meta inspect`

### 7.1 Prompting behavior

Interactive prompts in `lrh meta init` should only be used when stdin/stdout are TTY-appropriate. Non-interactive flows must remain automation-safe, with prompts bypassable via `--yes`.

---

## 8. Example project entry

```
projects/lcats/project.toml
```

```toml
schema_version = "0.1"

[project]
slug = "lcats"
display_name = "LCATS"
status = "active"

[identity]
canonical_url = "https://github.com/xenotaur/LCATS/tree/main/project"

[summary]
focus = "Working on style guide consolidation"
```

---

## 9. Design rules

1. Keep project-local `project/` directories authoritative.
2. Resolve an explicit workspace context using documented precedence.
3. Keep workspace resolution visible and inspectable in CLI behavior.
4. Use XDG-style config/state/cache separation for global defaults.
5. Use `projects/` for durable shareable catalog metadata.
6. Use `.lrh/` for workspace runtime/tool configuration in local mode.
7. Use `private/` for ignored non-authoritative local runtime state.
8. Keep CLI and any dashboard view aligned to the same meta model.
