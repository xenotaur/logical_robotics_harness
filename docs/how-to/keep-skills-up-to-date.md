# Keep skills up to date

## Purpose

Use this guide when Claude Code does not offer a `/lrh-*` skill you expect to see (for example, a skill that was added to LRH recently). LRH skills are installed into Claude Code's skills directory as a copy; upgrading the `lrh` package does not automatically update that copy. This guide shows how to check for and apply skill updates.

## Prerequisites

- LRH installed so the `lrh` command is available.
- Claude Code configured to read skills from `~/.claude/skills/` (global) or `./.claude/skills/` (per-repository, via `--local`).

## Check whether installed skills are current

Preview what an install would change without writing any files:

```bash
lrh skills install --dry-run
```

Each skill is reported as one of:

- `up to date` — no action needed.
- `would install` — new or changed skill content is available.
- `would overwrite` — the skill was modified locally and `--force` would be needed to apply the update.

Add `--local` to check the per-repository skills directory (`./.claude/skills/`) instead of the global one (`~/.claude/skills/`):

```bash
lrh skills install --dry-run --local
```

## Apply the update

Once you have reviewed the dry run, install for real:

```bash
lrh skills install
```

Use `--local` if you are installing into a single repository rather than globally:

```bash
lrh skills install --local
```

## Common troubleshooting notes

- A newly created `/lrh-*` skill in the LRH source tree does not appear in Claude Code until `lrh skills install` (or `lrh skills install --local`) has been run in the target environment. This is expected: skill installation is a deliberate, explicit step, not something that happens implicitly on every `lrh` invocation.
- If a skill reports `would overwrite` instead of `would install`, LRH has detected local modifications to that skill and will not silently discard them. Review the local changes before deciding whether to re-run with `--force`.
- If you maintain multiple repositories, remember that global (`~/.claude/skills/`) and per-repository (`./.claude/skills/` via `--local`) installs are independent. Updating one does not update the other.

## Related reference

- [Your first LRH project](../tutorials/first-lrh-project.md)
