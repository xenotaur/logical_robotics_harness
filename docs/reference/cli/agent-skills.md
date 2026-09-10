# `lrh agent-skills`

`lrh agent-skills` reports on `project/agent_skills.yaml`, the optional
repository-local configuration file that supplies default `source`,
`target`, and `scope` values for `lrh skills install` (see [`skills`](skills.md)
and the [agent skills config schema](../schemas/agent-skills-config.md)).

## Subcommands

```bash
lrh agent-skills status [options]
```

| Subcommand | Behavior |
|---|---|
| `status` | Reports whether `project/agent_skills.yaml` exists and each field's current state without writing files. |

## `status`

```bash
lrh agent-skills status [--project-root PROJECT_ROOT] [--format {text,json}]
```

| Option | Behavior |
|---|---|
| `--project-root` | Target repository root (default: current directory). |
| `--format` | `text` (default) or `json`. |

Reports:

- **`profile_exists`** — whether `project/agent_skills.yaml` exists at
  `--project-root`.
- **`sources`, `targets`, `scope`** — each field's effective, resolved
  value and its provenance: `from-config` (the file supplied this value)
  or `conventional-default` (no file, or the file didn't set this key).
  Resolution reuses the same CLI-over-config-over-default precedence
  `lrh skills install` applies.
- **`install.overwrite`** — the field's raw configured value, or `null`
  (`None` in text output) meaning "not set." Unlike the three fields
  above, this field has no documented conventional default, so its
  status is never resolved to a default value — only reported as set or
  not set. This is a read-only report; `lrh agent-skills status` never
  writes `project/agent_skills.yaml`.

### Example

```bash
$ lrh agent-skills status
project/agent_skills.yaml exists: False
Editable fields (effective value, provenance):
  sources: 'lrh-package' (conventional-default)
  targets: 'claude' (conventional-default)
  scope: 'user' (conventional-default)
Read-only field (no conventional default; raw configured value):
  install.overwrite: None
```

### Errors

Exits `2` with an `error: ...` message on stderr for a malformed
`project/agent_skills.yaml` (invalid YAML, wrong shape, an unreadable or
non-UTF-8 file) — never a raw traceback.

## Related

- [`skills`](skills.md) — install and inspect rendered agent skills; consumes
  the same configuration this command reports on.
- [Agent skills config schema](../schemas/agent-skills-config.md) — full
  field reference, precedence rules, and destinations.
