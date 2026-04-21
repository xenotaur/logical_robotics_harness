# LRH Meta-Control Plane MVP Spec

## 1. Scope

This spec defines an MVP **workspace-level catalog and coordination layer** for multiple LRH-compatible repositories.

The meta-control layer is intentionally secondary to each project repository's local control plane.

This MVP defines:
- dashboard/workspace repository layout
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

## 3. Repository layout

```
<dashboard-root>/
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

---

## 4. Storage classes

### `projects/`
Durable, shareable catalog metadata about registered LRH-compatible repositories.

### `.lrh/`
LRH runtime/tool configuration for the dashboard workspace.

### `private/`
Ignored local runtime/scratch state (logs, chat traces, caches, transient state, local secrets). This state is explicitly non-authoritative.

### Never stored in committed metadata
Secrets, tokens, sensitive logs, unnecessary PII.

---

## 5. Freshness and derived data

Any project summary, focus blurb, latest-work-item pointer, or status summary stored in the dashboard may become stale relative to the source project repository.

Unless explicitly designated otherwise, dashboard summaries and pointers should be treated as derived/informative views of project-local artifacts.

---

## 6. CLI commands (MVP)

- `lrh meta init`
- `lrh meta register`
- `lrh meta deregister`
- `lrh meta list`
- `lrh meta inspect`

---

## 7. Example project entry

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

## 8. Design rules

1. Keep project-local `project/` directories authoritative.
2. Use `projects/` for durable shareable catalog metadata.
3. Use `.lrh/` for workspace runtime/tool configuration.
4. Use `private/` for ignored non-authoritative local runtime state.
5. Keep CLI and any dashboard view aligned to the same meta model.
