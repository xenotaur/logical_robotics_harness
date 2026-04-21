# LRH Meta-Control Plane MVP Spec

## 1. Scope

This spec defines the first version of the **LRH meta-control plane**, a lightweight catalog and status surface for multiple LRH-managed projects.

It does **not** yet define:

- agent orchestration
- background workflow execution
- budget tracking
- durable chat semantics
- remote multi-user server behavior

This MVP does define:

- dashboard repository layout
- CLI subcommands for meta operations
- configuration precedence
- storage boundaries
- project registration format
- minimum localhost web view behavior

---

## 2. Core concepts

### 2.1 Project control pane
A **project control pane** is the existing LRH `project/` directory within a single repository.

### 2.2 Meta-control pane
A **meta-control pane** is a separate dashboard repository that tracks multiple active projects.

### 2.3 Dashboard repository
A **dashboard repository** is a Git repository created by `lrh meta init`.

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

## 4. Storage boundaries

### projects/
Durable, shareable, human-readable metadata.

### .lrh/
LRH runtime configuration only.

### private/
Ignored local operational data (logs, chats, cache, etc).

### Never stored
Secrets, tokens, sensitive logs, unnecessary PII.

---

## 5. CLI commands

- `lrh meta init`
- `lrh meta register`
- `lrh meta deregister`
- `lrh meta list`
- `lrh meta inspect`

---

## 6. Configuration precedence

1. CLI flags  
2. CLI config file  
3. Environment variables  
4. Env config file  
5. `.lrh/config.toml`  
6. Defaults  

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

1. `projects/` = durable catalog  
2. `.lrh/` = tool config  
3. `private/` = ignored runtime state  
4. No secrets in committed files  
5. CLI and web share same model  

---

## 9. Implementation phases

Phase 1:
- init, register, list, inspect

Phase 2:
- deregister, JSON output, web view

Phase 3:
- REPL, summaries, enhancements

---

## 10. Notes

This MVP is intentionally minimal and focused on establishing:

- a clean control-plane model
- safe storage boundaries
- extensibility toward future orchestration
