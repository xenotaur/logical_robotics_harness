# Writing the briefing

The reader is a maintainer deciding how to review, and whether to land, a PR
they did not write. They want an accurate picture fast. Every section answers
one question; if you have nothing true and useful to say for a section, leave
it empty and the renderer drops it.

## Voice

- Plain, direct sentences in the active voice. Short beats clever.
- Name things the way the project's users and maintainers do: commands,
  config keys, file names.
- No hedging filler ("it is worth noting", "it seems that"). State what you
  found and how sure you are, using the confidence field.
- No praise or blame. Describe the change and its effects.
- Use `` `code` `` for commands, paths, identifiers, and config; use
  `**bold**` sparingly for the one or two terms a skimmer must catch.

## Evidence

- Facts come from `data.json` and the diff, never from the PR description or
  commit messages alone. If the description claims something the diff does
  not show, say so in a review note.
- Each review note names where it applies (`where`) and what you checked.
- `confirmed`: verified against code you read, the trial merge, or a command
  you ran. `likely`: follows from reading the code but you did not run it.
  `unverified`: a question worth asking, with no evidence either way.
- If tests were not run, say so in `tests.note`, `footer_note`, and chat.

## Section by section

### `headline_summary` (the header paragraph)

At most four sentences: what the PR lets someone do, the main design move,
and where it stands. It must read on its own.

Example (taurworks PR 113):

> Lets a Taurworks project run inside a **Dev Container**. With
> `type = "devcontainer"` in its config, `tw activate` starts the container
> through the official `devcontainer` CLI and opens a shell inside it, and
> `taurworks dev` commands run there too. Conda and Dev Containers now share
> one new provider interface. The PR comes with substantial tests, but
> before merging it needs a rebase to fix one conflict, and two behaviors
> need checking.

### `summary` and `at_a_glance`

Two or three paragraphs: the before state, what the PR adds, and the
secondary changes that ride along. The side box is five or so label/value
pairs; "To land" lists the concrete steps left (rebase, fix N conflicts, run
CI, check named behaviors).

### `behavior_changes`

What a current user notices after merge, especially changes that land even
for people who never use the headline feature: changed defaults, stricter
validation, new environment variables, changed output, new commands.

Example rows from PR 113:

| what | before | after |
|---|---|---|
| Leaving a Conda project for a plain one | The old Conda env stayed active. | `tw activate` runs `conda deactivate`, but only if Taurworks activated it. |
| `[activation.environment]` validation | Extra keys were ignored. | Unknown keys are rejected. |

### `files`

- `gist`: one sentence on the file's role in this PR.
- `points`: 2 to 6 for files that carry real logic; none for one-line edits.
  Each point is a fact a reviewer would otherwise have to dig for: a new
  function and what it guarantees, a fallback, a path that duplicates
  logic elsewhere.
- `snippet`: only when a few lines show the shape better than prose (an
  interface, a config example, the key branch). Keep it under 10 lines.

Example gist and point (PR 113, `environments.py`):

- gist: "The heart of the PR. Defines the provider interface and the three
  providers, plus a registry that picks one by type."
- point: "`prepare` runs `devcontainer up`, reads the JSON line with
  `outcome` and `remoteWorkspaceFolder`, then checks the mapped directory
  exists with `exec test -d`."

### `tests`

Rows map behaviors to where they are tested and how (unit, mocked CLI, real
shell, opt-in integration). `gaps` lists behaviors the PR adds that no test
exercises, especially the ones your review notes are about.

### `review_notes`

Order by effect on landing: blockers first, then things to check, then
information. Typical content:

- `blocker`: merge conflicts (name the files and how to resolve), failing
  CI, a bug that breaks the headline feature.
- `check`: interactions with base-branch commits since the merge base,
  likely bugs, missing CI or reviews, security-relevant behavior.
- `info`: compatibility notes for release notes, design drift from the
  project's stated design, naming, performance, housekeeping (misleading
  commit messages, unrelated changes, typos).

Example (PR 113, `check`, label "Likely bug", confidence `likely`):

> **A normal exit can look like a failed entry.** `enter()` returns the
> interactive shell's exit status. If the last command you ran in the
> container failed and you then type `exit`, that status is non-zero.
> `tw activate` then prints "Dev Container shell entry failed" and skips the
> return-to-host step.

### `footer_note`

One line: what the briefing is based on (full diff, trial merge against
`<base>` at `<sha>`) and what was not done (tests not run).
