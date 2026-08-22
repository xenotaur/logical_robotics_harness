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
  `git show`, `git branch` (list form), `git rev-parse`, `git ls-remote`,
  `find`, `grep`, `ls`, `cat`. These carry no risk of changing repository or
  filesystem state. `git fetch` is deliberately **not** in this category —
  it does write to the local repository (it downloads objects and updates
  remote-tracking refs) even though it never touches the working tree — so
  it is grouped with the write commands below instead.
- **Routine write commands LRH skills run under their own human confirm
  gates** — `git fetch`, `git add`, `git commit`, `git push`,
  `git checkout -b`, `git pull`, `gh pr view/list/create/diff`, and the
  `lrh` subcommands (`validate`, `prompt`, `skills`, `work-items`,
  `request`, `snapshot`, `survey`). Every LRH skill that reaches these
  commands does so only after its own Step 4-style confirm gate has
  already been answered by a human (see any `SKILL.md`'s "human gate"
  steps) — this allowlist removes a second, redundant shell-level prompt
  for the same already-approved action, not the approval itself.
- **`gh api`, narrowly** — only the two exact forms this repo's skills
  actually issue (`gh api user`, `gh api user --jq .login`, used to look
  up the current GitHub username for branch naming). `gh api` is
  deliberately **not** wildcarded (`gh api *`) the way the commands above
  are: the caller chooses both the endpoint and the HTTP method, so a
  wildcard would also pre-approve a mutating call like
  `gh api -X PUT repos/<owner>/<repo>/pulls/<n>/merge` — silently merging
  a PR through a path that bypasses the `gh pr merge` handling described
  below entirely. Any other `gh api` invocation is intentionally left
  unmatched, so it prompts.

## What is deliberately still denied

`.claude/settings.json`'s `permissions.deny` list names the destructive or
irreversible operations that must keep prompting even though a
similarly-named safe command is allowed above. `deny` entries take
precedence over `allow` entries, so these fire even though the broader
`git push *` / `find *` allow rules above would otherwise match them too:

- `git push --force` / `-f`, in the flag-first, flag-last, and
  flag-in-the-middle argument orders (`git push origin main --force` is
  just as much a force push as `git push --force origin main`), plus
  `--force-with-lease` / `--force-if-includes`. This is deliberately
  redundant coverage rather than one clever pattern, because the
  underlying permission match is a simple wildcard, not a full command
  parser — it cannot express "the `--force` flag, wherever it appears" as
  a single rule. **Known residual gap:** a bundled short-flag form (e.g.
  `-uf` for `-u -f` in one token) is not covered by any of these
  patterns and would still fall through to the broad `git push *` allow.
  If a new push variant is added to the allowlist, prefer an exact,
  non-wildcarded entry over widening `git push *` further.
- `git reset --hard`
- `git checkout .` / `git checkout -- <path>` / `git restore` (discards
  uncommitted changes)
- `git branch -D` / `-d` (deletes a branch)
- `git clean`
- `find ... -delete` / `-exec` / `-execdir` / `-ok` / `-okdir` /
  `-fprint` / `-fprintf` — `find`'s read-only reputation only holds for
  its search predicates; these actions can modify or delete files
  (`find --help` documents them as GNU extensions, not part of a POSIX
  read-only search) and are excluded from the broad `find *` allow above.
- `rm -rf`

`gh pr merge` is **not** in this deny list, even though merging is
exactly the kind of irreversible action this list otherwise exists to
gate. `permissions.deny` is a hard, unconditional block — it has no
"prompt every time" mode — so putting `gh pr merge` here would stop even
an agent that has already received unambiguous, live, in-session merge
authorization from running the command at all, which is precisely the
agent-executes-merge path `DEC-AGENT-EXECUTED-MERGE-GATE` establishes as
this repository's normal behavior. Leaving it out of both `allow` and
`deny` gives the correct behavior instead: every invocation prompts,
and an approved prompt still executes.

Merge authority specifically is documented in `AGENTS.md`'s "Pull
requests and merge authority" section. The broader shape here — pre-approve
broad, low-risk commands; keep anything that can lose work, rewrite
history, or merge code gated behind a live prompt — is not itself named
by a canonical repo document; it is simply the posture this allowlist
applies consistently.

## Extending the allowlist

Add new entries to `.claude/settings.json` directly (it is a normal
tracked file) rather than relying on personal, untracked
`.claude/settings.local.json` files, so the benefit is shared across
sessions and reviewable in a PR like any other change. Keep new entries as
narrow as the underlying command allows — prefer a specific subcommand form
(`git checkout -b *`) over a broad wildcard (`git checkout *`) that could
also match a destructive variant of the same base command, and prefer an
exact, non-wildcarded entry (like the `gh api user` forms above) whenever
a command's danger comes from which flag follows it rather than from the
base command itself.
