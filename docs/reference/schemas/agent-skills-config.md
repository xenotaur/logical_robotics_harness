# Agent Skills Config

`project/agent_skills.yaml` is an optional repository-local configuration file
for `lrh skills install`. When present, it supplies project defaults for the
canonical skill source, install target, and install scope.

To inspect the currently resolved values without hand-parsing this file, or
to create/edit `sources`, `targets`, and `scope` through a confirmed
gate, use [`lrh agent-skills status`](../cli/agent-skills.md) or the `/lrh-config-skills`
LRH skill. `install.overwrite` is not editable through either — it stays a
manual edit to this file, per the non-destructive-only rule below.

## Precedence

Install planning uses this precedence, from highest to lowest:

1. CLI flags supplied to `lrh skills install`
2. Values in `project/agent_skills.yaml`
3. Conventional defaults

The conventional defaults remain backward compatible:

- source: `lrh-package`
- target: `claude`
- scope: `user`

`--force` is intentionally CLI-only. Checked-in repository config cannot enable
destructive overwrite behavior for ordinary installs.

## Schema

```yaml
schema_version: 1
sources:
  - current-repo
targets:
  - codex
scope: project
install:
  overwrite: skip
```

Fields:

| Field | Required | Values | Behavior |
|---|---:|---|---|
| `schema_version` | no | `1` | Omitted version defaults to `1`. Other versions are rejected. |
| `sources` | no | one list item: `lrh-package`, `current-repo`, or a filesystem path | Selects the canonical skill source when `--source` is absent. This installer stage supports exactly one configured source. |
| `targets` | no | `all`, or one or more of `claude`, `codex`, `antigravity` | Selects install targets when `--target` is absent. Listing all concrete targets is equivalent to `all`; smaller explicit lists install only those targets. |
| `scope` | no | `user` or `project` | Selects user-scope or project-local install destinations when `--scope` and `--local` are absent. |
| `install.overwrite` | no | `false`, `skip`, or `preserve` | Documents non-destructive overwrite policy. Any value that attempts to enable force or overwrite is rejected. |

Relative filesystem paths in `sources` are resolved from the repository root
that contains `project/agent_skills.yaml`. Relative paths supplied to the
`--source` CLI flag remain shell-relative.

## Destinations

User scope:

| Target | Directory |
|---|---|
| `claude` | `~/.claude/skills/` |
| `codex` | `~/.agents/skills/` |
| `antigravity` | `~/.gemini/config/plugins/lrh/skills/` plus `~/.gemini/config/plugins/lrh/plugin.json` |

Project scope:

| Target | Directory |
|---|---|
| `claude` | `./.claude/skills/` |
| `codex` | `./.agents/skills/` |
| `antigravity` | `./.gemini/plugins/lrh/skills/` plus `./.gemini/plugins/lrh/plugin.json` |

## Example

Use LRH skills from the current checkout as the canonical source and install
them into all project-local agent targets:

```yaml
schema_version: 1
sources:
  - current-repo
targets:
  - claude
  - codex
  - antigravity
scope: project
install:
  overwrite: skip
```

From the repository root:

```bash
lrh skills install --dry-run
lrh skills install
```

To override the configured target for one command:

```bash
lrh skills install --target claude
```

To override the configured scope for one command:

```bash
lrh skills install --scope user
lrh skills install --scope project
```

`--local` remains a shortcut for `--scope project` and cannot be combined with
`--scope user`.

To overwrite locally modified installed skills, pass the explicit CLI force
flag:

```bash
lrh skills install --force
```
