# Keep skills up to date

## Purpose

Use this guide when Claude Code or Codex does not offer an `/lrh-*` skill you expect to see (for example, a skill that was added to LRH recently). LRH skills are installed into each agent's skills directory as a copy; upgrading the `lrh` package does not automatically update that copy. This guide shows how to check for and apply skill updates.

## Prerequisites

- LRH installed so the `lrh` command is available.
- Claude Code configured to read skills from `~/.claude/skills/` (global) or `./.claude/skills/` (per-repository, via `--local`), or Codex configured to read skills from `~/.agents/skills/` (global) or `./.agents/skills/` (per-repository, via `--local --target codex`).

## Check whether installed skills are current

Run this from the repository root when using `--local` — the target directory is resolved relative to the current working directory, so running it from a subdirectory installs into that subdirectory's `.claude/skills/` or `.agents/skills/` instead of the repository's.

Preview what an install would change without writing any files:

```bash
lrh skills install --dry-run
```

By default, `lrh skills install` targets Claude Code for backward
compatibility. The explicit target options are:

| Command | Target directory |
|---|---|
| `lrh skills install` or `lrh skills install --target claude` | `~/.claude/skills/` |
| `lrh skills install --local` or `lrh skills install --local --target claude` | `./.claude/skills/` |
| `lrh skills install --target codex` | `~/.agents/skills/` |
| `lrh skills install --local --target codex` | `./.agents/skills/` |
| `lrh skills install --target all` | both Claude and Codex user-scope directories |
| `lrh skills install --local --target all` | both Claude and Codex project-scope directories |

By default, skills are copied from the packaged LRH skill source. Use
`--source` when you need to install from a different canonical source:

| Command | Source |
|---|---|
| `lrh skills install` or `lrh skills install --source lrh-package` | packaged LRH skills |
| `lrh skills install --source current-repo` | `./src/lrh/skills/` from the current repository |
| `lrh skills install --source ./path/to/skills` | explicit filesystem skill source |

The source directory is the canonical skill tree to copy from; target
directories such as `.claude/skills/` and `.agents/skills/` remain generated
install destinations. Existing safety behavior still applies for every source:
locally modified target copies are skipped unless `--force` is passed, and
`--diff` compares the installed copy against the selected source.

Repositories may also define optional defaults in `project/agent_skills.yaml`.
When that file is present, `lrh skills install` uses its configured source,
target, and scope unless the corresponding CLI flag is supplied. CLI flags take
precedence over repo config, and repo config takes precedence over the
conventional defaults. See the [agent skills config reference](../reference/schemas/agent-skills-config.md)
for the full schema.

Each skill is reported as one of:

- `up to date` — the installed copy already matches the selected source; no action needed.
- `would install` — the skill is missing from the target directory entirely.
- `warning: <name> has local modifications — skipped (use --force to overwrite)` — the installed copy exists but differs from the selected source (for example, an update to a skill you already have installed). A plain `lrh skills install` will **not** update this skill; see [Apply the update](#apply-the-update).

Add `--local` to check the per-repository skills directory instead of the global one:

```bash
lrh skills install --dry-run --local
```

`--local` is a shortcut for project scope. When a repository config sets a
scope default, use `--scope user` or `--scope project` to override it for a
single command.

For a project-local Codex install, use:

```bash
lrh skills install --dry-run --local --target codex
```

To preview what `--force` would change for a skill reported as locally modified, combine it with `--dry-run`:

```bash
lrh skills install --dry-run --force
```

This reports `would overwrite` for any skill that differs from the selected source. `would overwrite` only ever appears when `--force` is passed — a plain dry run never shows it.

## Apply the update

Install skills that are missing entirely (reported as `would install`):

```bash
lrh skills install
```

This does **not** touch skills reported as locally modified in the dry run — those are left untouched with the same warning. To pick up an updated skill whose installed copy already exists and differs from the selected source (commonly the packaged version after upgrading `lrh`), you must pass `--force`:

```bash
lrh skills install --force
```

`--force` overwrites any skill that differs from the selected source (reported as `overwritten`) in addition to installing missing skills as normal (reported as `installed`).

Use `--local` if you are installing into a single repository rather than globally:

```bash
lrh skills install --force --local
```

For Codex, choose the Codex target explicitly:

```bash
lrh skills install --force --target codex
lrh skills install --force --local --target codex
```

## Codex render-adapter behavior

Codex installs are rendered for `.agents/skills/` rather than copied byte for
byte. The renderer strips Claude-only frontmatter such as `argument-hint` and
translates `disable-model-invocation: true` into Codex invocation policy in a
sibling `agents/openai.yaml` file. If a canonical skill already supplies
`agents/openai.yaml`, authored values are preserved and generated policy values
only fill missing defaults.

Some skill body prose may still mention Claude Code or slash-command
conventions. Treat those references as an interim wording caveat until later
body-prose neutralization work produces fully agent-neutral skill bodies.

## Common troubleshooting notes

- A newly created `/lrh-*` skill in the LRH source tree does not appear in Claude Code or Codex until `lrh skills install` (or `lrh skills install --local` with the relevant `--target`) has been run in the target environment. This is expected: skill installation is a deliberate, explicit step, not something that happens implicitly on every `lrh` invocation.
- If a skill reports the `has local modifications` warning, LRH has detected that the installed copy differs from the selected source and will not silently overwrite it — whether that difference is your own edit or simply an unapplied upstream update. Review the installed copy before deciding whether to re-run with `--force`.
- If you maintain multiple repositories, remember that global (`~/.claude/skills/` or `~/.agents/skills/`) and per-repository (`./.claude/skills/` or `./.agents/skills/` via `--local`) installs are independent. Updating one does not update the other.

## Related reference

- [Your first LRH project](../tutorials/first-lrh-project.md)
