# `lrh vcs`

`lrh vcs` runs backend-neutral version-control actions that LRH skills perform
after their own human gates have passed. Today it has one subcommand, `merge`,
the SHA-locked pull-request merge that `/lrh-land` and `/lrh-confirm-fixes`
present. The interface behind it, and how to add another backend, are in
[VCS backend interface](../vcs-backend.md).

## Subcommands

```bash
lrh vcs merge <pr-url> (--merge | --squash | --rebase) --match-head-commit <sha> [options]
```

| Subcommand | Behavior |
|---|---|
| `merge` | Merge a pull request only if it is open and its head is exactly `--match-head-commit`; issue the merge once; read the pull request back to report the result. |

## `merge`

| Argument or option | Behavior |
|---|---|
| `pr` | Pull request URL (required). A value that starts with `-` is refused, and the `github` backend refuses anything that is not an `https://<host>/<owner>/<repo>/pull/<number>` URL. |
| `--merge`, `--squash`, `--rebase` | Merge method; exactly one is required. |
| `--match-head-commit SHA` | The full 40-character lowercase hex head SHA the merge must apply to (required). Short or uppercase SHAs are refused. |
| `--backend` | VCS backend (default: `github`). |
| `--format` | `text` (default) or `json`. |

In order, `merge`:

1. Validates the arguments. Nothing leaves the process if they are malformed.
2. Reads the pull request and refuses unless its state is `OPEN`.
3. Refuses unless the pull request's head SHA equals `--match-head-commit`.
4. Issues the merge once. It never retries.
5. Reads the pull request back. `MERGED` is reported as merged and `OPEN` as
   queued; any other state is reported as an error, since a merge that was
   issued should not leave the pull request closed.

It never deletes the branch, never edits the pull request, and decides nothing
about whether a merge is authorized. Authorization stays in the calling skill's
human gate (`DEC-AGENT-EXECUTED-MERGE-GATE`); this command only refuses to act
on a commit other than the one that gate verified.

### Exit codes

| Code | Meaning | Output |
|---|---|---|
| `0` | The pull request is confirmed `MERGED`. | stdout: `merged: <merge commit>` |
| `1` | The merge was accepted but the pull request is not `MERGED` yet, for example it is queued. Re-check its state before proceeding. | stdout: `queued: ...` |
| `2` | Refused or failed. A refusal (`refused: ...`) means no merge command was issued. A failure (`error: ...`) carries the backend's own message. If the merge command itself failed, the message ends with the pull request's state read back afterwards (for example `the pull request is now OPEN`), because a command can fail after the forge accepted it; if that read also failed, the message says to check the pull request. The same applies when the merge was issued but its final state could not be read, or was neither `MERGED` nor `OPEN`. An unexpected exception of any type from the backend is reported the same way, with its type name, and never as a traceback (whose exit code `1` would read as "queued"). | stderr |

### JSON output

```bash
lrh vcs merge <pr-url> --merge --match-head-commit <sha> --format json
```

Prints one object on stdout with `status` (`merged` or `queued`), `state`,
`merge_commit` (or `null`), `backend`, and `pr`. Errors still go to stderr with
exit code `2`, so stdout is valid JSON or empty.

## What this command cannot report

`lrh vcs merge` can only report failures that occur once it is running. If the
host (for example an agent harness's permission layer) refuses to launch the
command at all, no LRH code runs and nothing here can observe it. The calling
skill or session reports that case. See
[Error scope](../vcs-backend.md#error-scope).
