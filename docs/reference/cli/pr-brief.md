# `lrh pr-brief`

`lrh pr-brief` builds a visual briefing of one GitHub pull request in two
steps. `gather` collects the facts into `data.json`; a person or the
`/lrh-pr-explain` skill writes the narrative into that file's `briefing`
section; `render` turns the whole file into one HTML page. Neither subcommand
changes the pull request.

## Subcommands

```bash
lrh pr-brief gather <target> [number] --out DIR [--repo-dir DIR] [--force]
lrh pr-brief render <data.json> [--out PATH] [--format artifact|standalone] [--check]
```

| Subcommand | Behavior |
|---|---|
| `gather` | Write `DIR/data.json` (facts plus an empty `briefing` skeleton) and `DIR/pr.diff`. |
| `render` | Validate `data.json` and write the HTML briefing. |

## `gather`

| Argument or option | Behavior |
|---|---|
| `target` | A pull request URL, `OWNER/REPO` followed by `number`, or a bare number resolved against the current directory's GitHub repository. |
| `--out DIR` | Output directory (required). Created if missing. |
| `--repo-dir DIR` | A git directory (a checkout or a bare repository) used for a trial merge. `gather` fetches the base-branch tip and the PR head by SHA from `https://github.com/OWNER/REPO.git` (objects only, no ref changes beyond `FETCH_HEAD`) and runs `git merge-tree --write-tree`, which writes no working-tree or index state. Without it, conflicts are reported as not checked. |
| `--force` | Overwrite an existing `data.json`. Without it, `gather` refuses, because the file may hold written narrative. |

`gather` reads through the `gh` CLI: `gh pr view`, the pull request files
API, the compare API (for `ahead_by`, `behind_by`, and the merge base), the
base branch's current tip, and `gh pr diff`. When GitHub refuses a very large
diff, `pr.diff` is assembled from the per-file patches instead.

Exit status: `0` on success, `1` when `data.json` exists and `--force` was not
given, `2` for an invalid target, an unusable `--repo-dir`, or a `gh` failure.

## `render`

| Argument or option | Behavior |
|---|---|
| `data` | Path to `data.json`. |
| `--out PATH` | Output path. Default: `briefing.html` next to `data.json`. |
| `--format` | `artifact` (default) writes the page body for a claude.ai Artifact publish, with no doctype wrapper. `standalone` wraps it in a complete HTML document to open directly. |
| `--check` | Validate only; print warnings and errors without writing HTML. |

Validation errors (an unknown category, severity, confidence, or tone; a
figure id that is malformed, duplicated, or reserved; an empty figure) stop
the render with exit status `1`. Warnings (an empty headline summary, a file
without a gist, narrative for a path not in the PR) are printed to stderr and
do not stop it. Exit status `2` means `data.json` could not be read.

Text fields are HTML-escaped, then `` `code` `` and `**bold**` are applied.
`briefing.figures[].html` is inserted as written. The field-by-field schema is
in the skill's `references/data-schema.md`
(`src/lrh/skills/lrh-pr-explain/references/data-schema.md`).
