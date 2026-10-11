# `lrh skills`

`lrh skills` installs, inspects, and exports LRH agent skills rendered from a
canonical skill source. Installed target directories and exported bundles are
generated outputs; the canonical source remains `src/lrh/skills/`, the packaged
LRH skills tree, or an explicit source path.

## Subcommands

```bash
lrh skills install [options]
lrh skills status [options]
lrh skills check [options]
lrh skills export --target chatgpt --out <directory> [options]
```

| Subcommand | Behavior |
|---|---|
| `install` | Writes missing or forced target files and reports what changed. |
| `status` | Reports installed target state without writing files. |
| `check` | Reports installed target drift and compatibility issues without writing files; exits non-zero when any inspected item is missing, modified, or has reported issues. |
| `export` | Writes one upload bundle (ZIP) per skill for a hosted assistant; see [Export](#export). |

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

Each top-level directory in the source is a skill, except directories whose
names start with `_` (shared support files) or `.` (tool metadata such as
`.git/` or `.vscode/`). `install`, `status`, `check`, and `export` all skip
those directories. A symlinked top-level entry is still refused, even when its
name starts with `.`.

## Install Options

`lrh skills install` accepts:

| Option | Behavior |
|---|---|
| `--dry-run` | Preview missing or forced writes without changing files. |
| `--force` | Overwrite target files that differ from the selected source. |
| `--diff` | Preview without writing files (implies `--dry-run`) and print unified diffs for locally modified target files, including those `--force` would overwrite. |

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

## Export

`lrh skills export` packages skills for hosted assistants that take uploads
instead of discovering skills on disk. ChatGPT online is the only export
target; it is not an `install` target.

```bash
lrh skills export --target chatgpt --out ./chatgpt-skills
lrh skills export --target chatgpt --out ./chatgpt-skills --skill lrh-design --skill lrh-work-item
```

| Option | Behavior |
|---|---|
| `--target chatgpt` | Required. The hosted assistant to export for. |
| `--out <directory>` | Required. Where `<skill-name>.zip` bundles are written; created if missing. |
| `--source` | Canonical skill source, as for `install` (repo config, then `lrh-package`). |
| `--skill <name>` | Repeatable. Export only the named skills; an unknown name is an error. |

`export` does not accept `--local` or `--scope`: hosted bundles have no install
scope.

**Selection.** Without `--skill`, every public skill is exported except
manual-only skills (`disable-model-invocation: true` in `SKILL.md`, or
`policy.allow_implicit_invocation: false` in `agents/openai.yaml`), which are
reported as `skipped (manual-only)`. A manual-only skill is exported only when
named with `--skill`, with a notice that ChatGPT may select it automatically.

**Bundle contents.** Each ZIP contains one top-level `<skill-name>/` folder
with `SKILL.md` and any `references/`, `scripts/`, and `assets/`. `agents/` is
never bundled. Other top-level entries, hidden files, and Python caches are
skipped and reported. `SKILL.md` frontmatter keeps only `name`, `description`,
`license`, `compatibility`, and `metadata`; other keys are dropped and
reported, except `when_to_use`, whose guidance is carried into the bundle:

- if `description`, one space, and `when_to_use` (each with surrounding
  whitespace stripped) fit in 1024 characters, the bundled `description`
  becomes that combined text;
- otherwise `description` is kept unchanged and the guidance is added as a
  generated `## When to use` section after the body's `#` (H1) title when
  that title is the body's first non-blank line, or at the top of the body
  otherwise, with a notice.

Existing skill body text is never rewritten; the generated section is the only
addition.

**Determinism.** Archive entries are sorted, with fixed timestamps
(1980-01-01), permissions, and compression settings, so identical sources
produce byte-identical ZIPs on the same machine and toolchain (compressed bytes
can vary between zlib builds).

**Validation.** Before anything is written, every selected skill is checked:

- `SKILL.md` must exist and begin with valid YAML frontmatter;
- `name` must match the directory name, use lowercase letters, digits, and
  single hyphens, and be at most 64 characters;
- `description` must be a non-empty string of at most 1024 characters;
- optional `license` must be a string, `compatibility` a string of 1 to 500
  characters (the Agent Skills specification's bound) that is not only
  whitespace, and `metadata` a mapping of string keys to string values;
- optional `when_to_use` must be a non-blank string;
- manual-only markers (`disable-model-invocation`,
  `policy.allow_implicit_invocation`), when present, must be `true` or
  `false`, so a quoted `"true"` or an empty value fails rather than silently
  exporting a manual-only skill; an absent key means the skill is not
  manual-only. Both markers are checked even when one already marks the
  skill manual-only, so a manual-only skill with a malformed or unreadable
  `agents/openai.yaml` fails validation (and stops the export) instead of
  being skipped;
- source symlinks are rejected, never followed;
- archive paths must be safe and relative, with no case-insensitive duplicates;
- bundles must stay within the upload limits documented by the OpenAI Skills
  API guide (50 MB per ZIP, 500 files, 25 MB per uncompressed file).

If any selected skill fails, no bundles are written and the command exits 1.
Usage errors and unusable output locations (for example `--out` inside the
source, or a directory at a destination path) exit 2 with an error message.

`--out` must not be a symlink, and must not be the skill source directory or
lie inside it (checked by file identity, so symlinks and letter case cannot get
around it). Bundles are staged to temporary files and published only after
every one was written, so a failure while writing leaves nothing published. An
existing directory at a destination `<skill-name>.zip` path stops the export
before anything is written.

**Notices** are non-blocking and printed per skill: dropped frontmatter keys,
`when_to_use` guidance moved into a generated section, skipped entries,
manual-only status, an earlier bundle for a skipped manual-only skill still
present in `--out`, and workflows that use local `git`, the
GitHub `gh` CLI, the `lrh` CLI, or shell commands, which ChatGPT online cannot
run against your local repository or machine.

Exported output uses:

| Status | Meaning |
|---|---|
| `exported` | The bundle was written. |
| `not written` | The skill validated, but another selected skill failed, so nothing was written. |
| `skipped (manual-only)` | Manual-only skill left out of a default export. |
| `error` | The skill failed validation. |

## Related Docs

- [Keep skills up to date](../../how-to/keep-skills-up-to-date.md)
- [Use LRH with AI Agent Assistants](../../how-to/use-lrh-with-agent-assistants.md) — including ChatGPT upload and invocation
- [Agent skills config schema](../schemas/agent-skills-config.md)
