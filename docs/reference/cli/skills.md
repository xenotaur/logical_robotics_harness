# `lrh skills`

`lrh skills` installs and inspects LRH agent skills rendered from a canonical
skill source. Installed target directories are generated outputs; the canonical
source remains `src/lrh/skills/`, the packaged LRH skills tree, or an explicit
source path.

## Subcommands

```bash
lrh skills install [options]
lrh skills status [options]
lrh skills check [options]
```

| Subcommand | Behavior |
|---|---|
| `install` | Writes missing or forced target files and reports what changed. |
| `status` | Reports installed target state without writing files. |
| `check` | Reports installed target drift and compatibility issues without writing files; exits non-zero when any inspected item is missing, modified, or has reported issues. |

## Target Selection

`--target` selects which assistant install format to use:

| Target | User-scope output | Project-scope output |
|---|---|---|
| `claude` | `~/.claude/skills/` | `./.claude/skills/` |
| `codex` | `~/.agents/skills/` | `./.agents/skills/` |
| `antigravity` | `~/.gemini/config/plugins/lrh/skills/` plus `~/.gemini/config/plugins/lrh/plugin.json` | `./.gemini/plugins/lrh/skills/` plus `./.gemini/plugins/lrh/plugin.json` |
| `all` | all user-scope targets above | all project-scope targets above |

When `--target` is omitted, LRH uses `project/agent_skills.yaml` if present;
otherwise it defaults to `claude`.

## Scope Selection

`--scope user` writes or inspects the user-global target directory. `--scope
project` writes or inspects the target directory under the current working
directory.

`--local` is a shortcut for `--scope project` and cannot be combined with
`--scope user`.

When scope is omitted, LRH uses `project/agent_skills.yaml` if present;
otherwise it defaults to user scope.

## Source Selection

`--source` selects the canonical skill source:

| Source | Behavior |
|---|---|
| `lrh-package` | Use packaged LRH skills. |
| `current-repo` | Use `./src/lrh/skills/` from the current repository. |
| filesystem path | Use that directory as the canonical skill tree. |

When `--source` is omitted, LRH uses `project/agent_skills.yaml` if present;
otherwise it defaults to `lrh-package`.

## Install Options

`lrh skills install` accepts:

| Option | Behavior |
|---|---|
| `--dry-run` | Preview missing or forced writes without changing files. |
| `--force` | Overwrite target files that differ from the selected source. |
| `--diff` | Print unified diffs for skipped locally modified target files. |

Without `--force`, locally modified target files are preserved and reported as
warnings. This protection also applies to Antigravity's generated
`plugin.json`.

## Status Values

Install output uses:

| Status | Meaning |
|---|---|
| `installed` / `would install` | Target item is missing and was written, or would be written in dry-run mode. |
| `up to date` | Target item matches the selected source/rendered artifact. |
| `warning: ... has local modifications` | Target item differs and was skipped because `--force` was not supplied. |
| `overwritten` / `would overwrite` | Target item differs and `--force` overwrote it, or would overwrite it in dry-run mode. |

Inspection output uses:

| Status | Meaning |
|---|---|
| `missing` | Target item does not exist. |
| `up to date` | Target item matches the selected source/rendered artifact. |
| `modified` | Target item differs from the selected source/rendered artifact. |
| `source error` | The selected source cannot be rendered or inspected. |

For Antigravity, `plugin.json` is reported alongside skill names by
`install`, `status`, and `check`.

## Rendering Behavior

Claude installs preserve canonical skill bytes.

Codex installs render skills for `.agents/skills/` by stripping Claude-only
frontmatter and translating `disable-model-invocation: true` into Codex
invocation policy in `agents/openai.yaml`.

Antigravity installs render plugin trees under `.gemini/.../plugins/lrh/`,
strip Claude-only frontmatter, and generate `plugin.json` at the plugin root.

## Related Docs

- [Keep skills up to date](../../how-to/keep-skills-up-to-date.md)
- [Use LRH with AI Agent Assistants](../../how-to/use-lrh-with-agent-assistants.md)
- [Agent skills config schema](../schemas/agent-skills-config.md)
