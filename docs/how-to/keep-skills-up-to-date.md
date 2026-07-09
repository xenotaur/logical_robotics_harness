# Keep skills up to date

## Purpose

Use this guide when Claude Code does not offer a `/lrh-*` skill you expect to see (for example, a skill that was added to LRH recently). LRH skills are installed into Claude Code's skills directory as a copy; upgrading the `lrh` package does not automatically update that copy. This guide shows how to check for and apply skill updates.

## Prerequisites

- LRH installed so the `lrh` command is available.
- Claude Code configured to read skills from `~/.claude/skills/` (global) or `./.claude/skills/` (per-repository, via `--local`).

## Check whether installed skills are current

Run this from the repository root when using `--local` — the target directory is resolved relative to the current working directory, so running it from a subdirectory installs into that subdirectory's `.claude/skills/` instead of the repository's.

Preview what an install would change without writing any files:

```bash
lrh skills install --dry-run
```

Each skill is reported as one of:

- `up to date` — the installed copy already matches the packaged skill; no action needed.
- `would install` — the skill is missing from the target directory entirely.
- `warning: <name> has local modifications — skipped (use --force to overwrite)` — the installed copy exists but differs from the packaged skill (for example, an update to a skill you already have installed). A plain `lrh skills install` will **not** update this skill; see [Apply the update](#apply-the-update).

Add `--local` to check the per-repository skills directory (`./.claude/skills/`) instead of the global one (`~/.claude/skills/`):

```bash
lrh skills install --dry-run --local
```

To preview what `--force` would change for a skill reported as locally modified, combine it with `--dry-run`:

```bash
lrh skills install --dry-run --force
```

This reports `would overwrite` for any skill that differs from the packaged version. `would overwrite` only ever appears when `--force` is passed — a plain dry run never shows it.

## Apply the update

Install skills that are missing entirely (reported as `would install`):

```bash
lrh skills install
```

This does **not** touch skills reported as locally modified in the dry run — those are left untouched with the same warning. To pick up an updated skill whose installed copy already exists and differs from the packaged version (the common case after upgrading `lrh`), you must pass `--force`:

```bash
lrh skills install --force
```

`--force` overwrites any skill that differs from the packaged version (reported as `overwritten`) in addition to installing missing skills as normal (reported as `installed`).

Use `--local` if you are installing into a single repository rather than globally:

```bash
lrh skills install --force --local
```

## Common troubleshooting notes

- A newly created `/lrh-*` skill in the LRH source tree does not appear in Claude Code until `lrh skills install` (or `lrh skills install --local`) has been run in the target environment. This is expected: skill installation is a deliberate, explicit step, not something that happens implicitly on every `lrh` invocation.
- If a skill reports the `has local modifications` warning, LRH has detected that the installed copy differs from the packaged skill and will not silently overwrite it — whether that difference is your own edit or simply an unapplied upstream update. Review the installed copy before deciding whether to re-run with `--force`.
- If you maintain multiple repositories, remember that global (`~/.claude/skills/`) and per-repository (`./.claude/skills/` via `--local`) installs are independent. Updating one does not update the other.

## Related reference

- [Your first LRH project](../tutorials/first-lrh-project.md)
