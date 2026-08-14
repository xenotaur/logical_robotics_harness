# Claude Code permission allowlist

This repository ships a project-level `.claude/settings.json` with a
permission allowlist for Claude Code. It exists to reduce repeated
approval prompts for the routine, low-risk commands LRH skills run
constantly (`git status`, `git commit`, `gh pr create`, `lrh validate`,
`lrh prompt`, and similar), without weakening the actual safety gates
those skills already enforce.

## Why this exists

Claude Code scopes its permission allowlist to the directory a session is
**launched** in, not to the nearest enclosing git repository. A session
launched one level above this repo builds up its own, separate
`.claude/settings.local.json` in that outer directory — approvals don't
carry over, so the same commands get re-prompted every session. Committing
a project-level `.claude/settings.json` here means any session actually
launched from this repository's root inherits the same baseline allowlist,
regardless of who is running it or how many prior sessions happened.

If prompts still feel unusually frequent, check that the session's working
directory is this repository itself, not a parent directory — see
`docs/how-to/use-lrh-with-agent-assistants.md` for install/launch paths.

## What is allowed

`.claude/settings.json`'s `permissions.allow` list covers two categories:

- **Read-only / inspection commands** — `git status`, `git diff`, `git log`,
  `git show`, `git branch` (list form), `git rev-parse`, `git fetch`,
  `git ls-remote`, `find`, `grep`, `ls`, `cat`. These carry no risk of
  changing repository or filesystem state.
- **Routine write commands LRH skills run under their own human confirm
  gates** — `git add`, `git commit`, `git push`, `git checkout -b`,
  `git pull`, `gh pr view/list/create/diff`, `gh api`, and the `lrh`
  subcommands (`validate`, `prompt`, `skills`, `work-items`, `request`,
  `snapshot`, `survey`). Every LRH skill that reaches these commands does
  so only after its own Step 4-style confirm gate has already been
  answered by a human (see any `SKILL.md`'s "human gate" steps) — this
  allowlist removes a second, redundant shell-level prompt for the same
  already-approved action, not the approval itself.

## What is deliberately still denied

`.claude/settings.json`'s `permissions.deny` list names the destructive or
irreversible operations that must keep prompting even though a
similarly-named safe command is allowed above:

- `git push --force` / `-f`
- `git reset --hard`
- `git checkout .` / `git checkout -- <path>` / `git restore` (discards
  uncommitted changes)
- `git branch -D` / `-d` (deletes a branch)
- `git clean`
- `gh pr merge` — per `DEC-AGENT-EXECUTED-MERGE-GATE`, merge authorization
  requires explicit in-session approval every time; this is intentionally
  never pre-approved
- `rm -rf`

This mirrors this project's own Git Safety Protocol: broad, low-risk
commands are pre-approved; anything that can lose work, rewrite history,
or merge code stays gated.

## Extending the allowlist

Add new entries to `.claude/settings.json` directly (it is a normal
tracked file) rather than relying on personal, untracked
`.claude/settings.local.json` files, so the benefit is shared across
sessions and reviewable in a PR like any other change. Keep new entries as
narrow as the underlying command allows — prefer a specific subcommand form
(`git checkout -b *`) over a broad wildcard (`git checkout *`) that could
also match a destructive variant of the same base command.
