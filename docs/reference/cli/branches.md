# `lrh branches`

## Command purpose

`lrh branches survey` classifies every local git branch in a checkout into a documented class. It is report-only: it never deletes, renames, or otherwise modifies any branch or ref. It exists to give a human a reviewable picture of local branch clutter without automating the one part of cleanup (deletion) that LRH deliberately does not let an agent do on its own.

## Canonical invocation patterns

```bash
lrh branches survey
lrh branches survey --format json
lrh branches survey --write-delete-commands /tmp/branch-cleanup.sh
lrh branches survey --project-root /path/to/repo
```

## Important options and arguments

- `--format {md,json}`: report output format. Defaults to `md`.
- `--write-delete-commands PATH`: write a reviewable shell file of `git branch` delete commands to `PATH`. The command itself never runs them; a human reviews the file and runs it themselves.
- `--project-root PROJECT_ROOT`: repository root to survey. Defaults to the current directory.
- `-h`, `--help`: print command help.

## Branch classes

Each branch receives exactly one class, in this fixed precedence order:

1. `default` — the repository's discovered default branch (via `origin/HEAD`). Never delete-eligible, and never appears in `--write-delete-commands` output at all, not even as a comment — this holds even when the default branch is an ancestor of the branch currently checked out.
2. `in_worktree` — checked out in any local worktree, including the primary checkout.
3. `open_pr` — has at least one open pull request.
4. `merged_or_empty` — an ancestor of the default branch; nothing unique. Delete-eligible with `-d`.
5. `squash_merged` — the branch's own tip exactly matches the head commit of a merged pull request with the same branch name. `git branch --merged` alone cannot detect this, since a squash merge breaks direct ancestry. Delete-eligible with `-D`.
6. `review_first` — ambiguous or unknown: never pushed with no PR, or pushed with PR history that is neither open nor a tip-matching merge. Never delete-eligible.
7. `unique_work` — pushed, ahead of the default branch, with no associated PR at all. Never delete-eligible.

A branch that could match more than one class always receives the earliest-checked class above — for example, a branch that is both checked out in a worktree and an ancestor of the default branch is `in_worktree`, not `merged_or_empty`.

## Generated delete commands

`--write-delete-commands` renders one line per non-default branch:

- `merged_or_empty` and `squash_merged` branches get a live, ready-to-run `git branch <flag> -- <name>` line.
- Every other class gets the same line, commented out, for review.
- The default branch never appears in the file at all.

Every branch name is shell-quoted with an explicit `--` option terminator before the name. Valid git ref names can contain shell metacharacters (for example `$(...)` or `;`) that are not forbidden by git's own ref-name rules, so unquoted interpolation into a file a human later runs would risk executing arbitrary shell syntax.

## Current behavior and limitations

- This command never deletes, renames, or modifies a branch or ref. Deletion is a human action — see `docs/how-to/project-setup/claude-code-permissions.md` for why `git branch -d`/`-D` are denied to agents in this project.
- Requires a configured `origin` remote with `origin/HEAD` set (`git remote set-head origin -a`, or as set automatically by `git clone`). Without it, the command reports an error rather than guessing a default branch name.
- Requires the `gh` CLI to be authenticated against the repository, to look up open and merged pull requests by branch name.
- Scoped to local branches only; it does not enumerate or clean up remote branches.
