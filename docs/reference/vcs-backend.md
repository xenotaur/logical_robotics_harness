# VCS backend interface

LRH skills perform a small set of stereotyped version-control actions after
their own gates have passed. `lrh.vcs` separates each *action* (what is done,
and the checks that make it safe) from the *backend* (the forge it is done on),
so a different forge can be supported without redoing the checks.

The CLI surface is [`lrh vcs`](cli/vcs.md). The audit that chose which actions
to cover is `project/audits/2026-09-28-vcs-mutation-operations-audit.md`.

## Layers

```text
skill human gate            decides whether to act (unchanged)
  -> lrh vcs merge          src/lrh/cli/vcs.py        argument parsing, exit codes
    -> merge_pull_request_locked   src/lrh/vcs/backend.py   the action's safety checks
      -> VcsBackend          src/lrh/vcs/backend.py    the interface a forge implements
        -> GitHubBackend     src/lrh/vcs/github_backend.py   `gh` calls
```

## Actions

| Action | Status |
|---|---|
| SHA-locked pull-request merge | Implemented: `merge_pull_request_locked`. |
| `create_branch`, `push_branch`, `open_pull_request`, `resolve_review_thread` | Planned vocabulary only. No code exists for them; each would be added as its own action plus the backend methods it needs. The audit lists where skills perform them today. |

Only the merge is implemented so that the interface is shaped by one real case
and not by guesses about the others.

## The interface

`VcsBackend` is a `typing.Protocol` with two methods and a `name`:

| Member | Contract |
|---|---|
| `name` | Registry key, for example `"github"`. |
| `get_pull_request(pr)` | Return a `PullRequestInfo`: `url`, `state` (upper-case `OPEN`, `MERGED` or `CLOSED`), `head_sha` (full 40-character SHA), and `merge_commit` (or `None`). Raise `VcsError` on any failure. |
| `merge_pull_request(pr, *, mode, match_head_commit)` | Merge `pr` using `mode` (`merge`, `squash` or `rebase`) only if its head is still `match_head_commit`. Raise `VcsError` on any failure. |

### Safety invariants of the locked merge

`merge_pull_request_locked(backend, pr, *, mode, match_head_commit)` holds
these for every backend:

- Arguments are validated before any backend call: `pr` is non-empty and not
  option-shaped, `mode` is one of the three methods, the SHA is 40 lowercase hex
  characters.
- The merge is refused unless the pull request is `OPEN` and its head equals
  the verified SHA, so a commit that landed after verification is never merged.
- The merge is issued at most once. A failure is never retried.
- The pull request is read back so a queued merge (`queued`, state `OPEN`) is
  never reported as `merged`.
- If the merge call itself fails, the error also reports the pull request's
  state read back afterwards, because a call can fail after the forge accepted
  it. That read is a single read, never a second merge.
- If the read-back fails after the merge was issued, or shows a state other
  than `MERGED` or `OPEN`, `MergeVerificationError` says so explicitly, so a
  caller does not assume nothing happened.
- Any exception a backend raises that is not already a `VcsError` is reported
  as a backend error that names the exception type. Before the merge, the
  message says no merge was issued. A `VcsError` keeps its own message and gets
  neither the type name nor that wording. After the merge call, every
  exception, `VcsError` included, gets issued-merge wording: a failed merge
  call reports the pull request's state, and a failed read-back says the merge
  was issued. No exception escapes as a traceback, because its exit code `1`
  would read as `queued`.

## Error scope

The backend and action can only report what they observe. That is narrower than
everything that can go wrong around a merge.

| Failure | Visible to `lrh.vcs`? | Who reports it |
|---|---|---|
| A refused precondition: bad arguments, PR not open, head moved (`MergeRefusedError`) | Yes | `lrh vcs merge`, exit `2` |
| `gh` exits non-zero, cannot be launched, or prints unusable output (`VcsError`) | Yes | `lrh vcs merge`, exit `2`, with `gh`'s message and, for a failed merge call, the pull request's state afterwards |
| The merge issued but its final state could not be read (`MergeVerificationError`) | Yes | `lrh vcs merge`, exit `2` |
| The harness or permission layer refuses to launch the command before any LRH code runs | **No** | The calling skill or session: report it plainly, hand the exact command to the human, do not retry it another way |
| A deterministic project `permissions.deny` match | **No** | The calling session, same as above |
| The permission classifier returning no verdict | **No** | The calling session |

This is why `lrh vcs merge` is a narrower, more legible command and not a way
around host-level decisions: it cannot detect or influence them.

## Adding a backend

1. Create `src/lrh/vcs/<name>_backend.py` with a class that has a `name`, a
   `get_pull_request` and a `merge_pull_request` matching the contract above.
   Wrap every failure the underlying tool reports in `VcsError`, keeping its
   message. Do not retry, and do not delete branches.
2. Register it in `src/lrh/vcs/registry.py` by adding one entry to `_FACTORIES`.
   `--backend` choices and the unknown-backend error are generated from the
   registry.
3. Add tests alongside `tests/vcs_backend_test.py`: payload parsing, the exact
   command it builds, and error wrapping.
4. Describe any backend-specific behavior in this document.

The action's safety checks live in `merge_pull_request_locked` and are shared;
a new backend should not reimplement them.

## Relationship to gates and permissions

`lrh vcs merge` changes what command a skill presents, not who authorizes it.
`/lrh-land` Step 6 and `/lrh-confirm-fixes` Step 8 still present the command and
wait for authorization as before. Project permission settings are unchanged:
see [Claude Code permissions](../how-to/project-setup/claude-code-permissions.md)
for how merge commands are treated.
