# Closeout Workflow Reference

Protocols and reference tables for `/lrh-closeout`. Read this before Step 2
(assess state) and Step 5 (execute confirmed actions).

---

## Decision Matrix

Apply this table to each discovered artifact at Step 2. Assess all artifacts
before touching any files.

| Artifact | Condition | Action |
|---|---|---|
| PR | `state: MERGED` | Proceed; record `mergeCommit.oid` as commit SHA |
| PR | `state: OPEN` | **Abort** — PR not yet merged; no closeout actions |
| PR | `state: CLOSED` (no merge) | **Abort** — PR was closed without merge; investigate |
| Execution record | `status: in_progress` | Update to `landed` (Step 5) |
| Execution record | `status: landed` | Skip — already closed out |
| Execution record | Missing entirely | Warn user; ask whether to proceed without it |
| Execution record | `work_item: AD_HOC` | No WI to resolve — closeout scope is execution record update only; do not search for WIs via PR diff or working tree |
| WI | Found in `proposed/` | Resolve: set `status: resolved`, write `resolution:`, `mv` to `resolved/` |
| WI | Found in `resolved/` | Skip — already resolved |
| WI | Not found anywhere | Warn user; ask how to proceed |
| WS | All listed WIs resolved (on disk or planned in this closeout) AND WS in `workstreams/proposed/` or `workstreams/active/` | Offer closeout |
| WS | Any listed WI would remain unresolved after this closeout | Skip — not all WIs resolved |
| WS | Already in `workstreams/resolved/` | Skip |
| Proposal | WS would close AND proposal in `proposals/proposed/` | Offer adoption |
| Proposal | WS not closing (or WS skipped) | Skip adoption — WS must close first |
| Proposal | Already in `proposals/adopted/` | Skip |

---

## Execution Record Update Protocol

### Fields to update

When updating an execution record from `in_progress` to `landed`, edit these
four frontmatter fields:

```yaml
status: landed
pr: https://github.com/<owner>/<repo>/pull/<N>
commit: <merge-commit-sha>
session_transcript: claude-app:<host-uuid-stem>   # or: pending / none
```

**Valid status transition:** `in_progress → landed` is the only forward
transition for closeout. Never set `status: proposed` or `status: resolved`
on an execution record — those are work item statuses, not execution record
statuses.

### `pr:` field

The full GitHub PR URL. If the field is already populated with the correct
URL, leave it unchanged. If empty, set it now.

### `commit:` field

The merge commit SHA from `gh pr view <url> --json mergeCommit --jq '.mergeCommit.oid'`.
Use the full 40-character SHA or the 7-character abbreviated form — be
consistent with the project convention (check existing landed records for
which form is used).

### `session_transcript:` field

See the Session Transcript section below.

### Locating execution records by PR

```bash
grep -rl "^pr: <pr-url>" project/executions/ --include='*.md'
```

A single PR may have multiple execution records: one primary (from
`/lrh-implement`) and one or more review-response records (from
`/lrh-review-response`). Update all of them.

---

## Work Item Resolution Protocol

### Required frontmatter changes

```yaml
status: resolved
resolution: "<one-line summary of what was implemented and where>"
```

The `resolution:` value is a human-authored one-liner, confirmed at the
Step 4 confirm gate. Convention:

```
Implemented and merged in PR #N (commit <sha>)
```

For planning-artifact PRs (where the PR contains only the WI file itself,
not the implementation), use:

```
Implemented <artifact-type> planning artifact in PR #N (commit <sha>)
```

### File move

```bash
mv project/work_items/proposed/<WI-ID>.md project/work_items/resolved/<WI-ID>.md
```

**Use `mv`, never `cp`.** A file present in both `proposed/` and `resolved/`
triggers `WORK_ITEM_ID_DUPLICATE` in `lrh validate`. The `status: resolved`
field and the `resolved/` directory bucket must always match.

### Validation after move

Run `lrh validate` after the move. The validator checks that each WI's
`status:` field matches its directory bucket.

---

## Workstream Closeout Protocol

### Readiness check

Before offering WS closeout, verify that every ID in the WS's `work_items:`
list will be resolved after this closeout. Treat WIs marked `resolve and move`
in the current closeout plan as resolved (post-plan state). For WIs not in the
plan, check disk:

```bash
# For each WI-ID not already planned for resolution:
find project/work_items/resolved/ -name "<WI-ID>.md"
```

If any WI would remain unresolved after this closeout, skip WS closeout and
note it in the closeout plan.

<!-- GATE-DEFINITION -->
**The structural check is necessary but not sufficient.** After confirming
that all `work_items:` are resolved, also read the WS `exit_criteria:` list
and include it in the Step 2 plan output. At Step 4, enumerate the criteria
and require explicit human confirmation (`y`) before including WS closeout in
the confirmed plan. The `exit_criteria:` list is the authoritative definition
of done — WIs can be resolved while prose criteria remain unmet.
<!-- /GATE-DEFINITION -->

### Required frontmatter changes

```yaml
stage: closed
status: resolved
```

### File move

Move from whichever bucket the WS was actually found in at Step 2 —
`proposed/` or `active/`:

```bash
mv project/workstreams/<current-bucket>/<WS-ID>.md project/workstreams/resolved/<WS-ID>.md
```

---

## Proposal Adoption Protocol

### When to offer adoption

Offer proposal adoption only when:
1. The governing workstream is being closed in this same closeout session
   (or is already in `workstreams/resolved/`), **and**
2. The proposal is still in `project/design/proposals/proposed/`.

Do not offer adoption if the WS is being skipped (not all WIs resolved).

### Required frontmatter changes

```yaml
status: adopted
implementation_status: implemented
implemented_by:
  - <WI-ID-1>
  - <WI-ID-2>
```

`implemented_by:` takes WI IDs, not PR URLs. List all WI IDs that delivered
the implementation.

### Directory move

Move the entire proposal directory (including any sub-files like `01_*.md`):

```bash
mv project/design/proposals/proposed/<slug>/ project/design/proposals/adopted/<slug>/
```

---

## Session Transcript Resolution

### Resolve per execution record, not once per PR

A single PR can carry execution records from different backends (e.g. a
`codex_cloud` implementation record plus Claude-authored review-response or
confirm-fixes records against the same PR). Resolve a transcript value
separately for each matched record and apply each record's own resolved
value when landing it — never reuse one record's resolved value for another.

### Branch on the backend first

The pointer scheme is backend-specific. Check the execution record's `agent`
before resolving:

- **Codex app** (`agent: codex_app`): the Claude env var and Claude session URL
  are the wrong session. Resolve `codex-app:<task-or-thread-id>` when a durable
  Codex app task/thread identifier is available; otherwise leave `pending` if
  the session should be recorded later.
- **Codex Cloud** (`agent: codex_cloud`): resolve `codex-cloud:<task-id>` from
  the Codex run when available; otherwise leave `pending` if the task id should
  be recorded later.
- **Manual/no transcript backend** (`agent: manual`, or another terminal
  non-retrievable backend): use `none`.
- **Other non-Claude backend**: resolve the backend's own scheme-prefixed id if
  retrievable; otherwise use `none`. Do not construct a `claude-app:` pointer
  for non-Claude work.
- **Claude.app** (`agent: claude_app`, or absent/assumed Claude): resolve the
  host id as below.

### What to detect (Claude.app)

The `session_transcript:` field stores the **host** session reference in the
form:

```
claude-app:<host-uuid-stem>
```

where `<host-uuid-stem>` is the host session id (`local_<uuid>`) with the
`local_` prefix stripped. Example:
`claude-app:6f9b846e-c6f9-45aa-9cf9-8c744ec57026`.

Do **not** use the child SDK id that names the `~/.claude/projects/.../<child-uuid>.jsonl`
file: on Claude.app sessions it differs from the host id after resume/continue,
producing a pointer that session-management tools cannot resolve. Never store
an absolute path (`~/.claude/...` or `/Users/...`) — it leaks the local
workspace layout to everyone who clones the repository.

### Resolution order

`/lrh-session-id-claude` owns the resolution order; run it rather than
re-deriving it here. It stops at the first path that yields a confident
value:

1. **Same session — current window.** The skill runs
   `lrh conversation current-claude-session-id` (reading
   `$CLAUDE_CODE_HOST_SESSION_ID` directly only when the installed CLI lacks
   that subcommand), strips `local_`, and reports
   `claude-app:<host-uuid-stem>` with the session's title and branch from
   `get_session` (`"self"`). **Confirm before storing:** the host id
   reflects the *current* session window, so on a long, resumed, or forked
   session it can differ from the session that authored the work. If the
   user says it is not the authoring session, continue to path 2 or 3.
2. **Cross-session — by PR number, then branch or title.**
   `/lrh-session-id-claude <pr-url>` matches the target session by
   `prNumber` via `list_sessions`, falls back to the PR's head branch and
   then its title, and asks the user to pick when several sessions match.
3. **Manual — pick from the session list.** The skill lists candidates by
   title, branch, PR, and last activity (archived sessions too when needed,
   plus the current session from `get_session`, because `list_sessions`
   excludes the calling session per that tool's own contract) and the user
   picks one. The desktop app no longer exposes View > Copy URL; a
   `local_<uuid>` the user already has is accepted as the skill's argument.
   A session picked this way gets no child-id alias.

A resolver failure, or a host id that is unavailable in this window, yields
`pending` — never a guessed pointer. If the skill is not installed, run
`lrh conversation current-claude-session-id --format json` inline under
the same rule: read `$CLAUDE_CODE_HOST_SESSION_ID` directly only when the
subcommand is unavailable (`lrh` not found, or it reports the subcommand as
an invalid choice).

### `none` vs `pending` sentinels

Both are explicit first-class values and must never block closeout; they are
**not** interchangeable (see the 2026-07-23 "Backend-Agnostic Session Pointer
Grammar" decision-log entry):

| Value | Meaning | Step 8 reminder? |
|---|---|---|
| `pending` | Transcript exists; id not yet known — a **to-do** | Yes — remind to update before archiving |
| `none` | Backend produced no retrievable transcript (e.g. `codex_cloud`, `manual`) — **terminal** | No |

Use `none`, not `pending`, whenever a backend simply has no session URL to
resolve, so a finished record never looks like unfinished work.

When the user later provides a `pending` session id (env var, or a session
picked from `list_sessions`), update with:

```bash
lrh prompt update-execution \
  --execution-id <id> \
  --status landed \
  --commit <sha> \
  --session-transcript claude-app:<uuid> \
  --project-root .
```

---

## Session identity capture

Per `PROP-LRH-SESSION-ARCHIVE-SYNC` Stage 1: `session_transcript` stores
only the host id, but transcript files are named by the child SDK id, and
these differ on resumed/continued sessions. `project/sessions/index.jsonl`
records both together so the mapping is not lost. This capture is
independent of the `session_transcript` field above — writing to it does
not change that field's grammar or validator rules.

**Always record the observation; the child-id alias is what's conditional.**
Every resolution path (1, 2, or 3) yields a real, confirmed host id and a PR
worth recording — that association is useful on its own even without a
child-id alias, so call `record-session-alias` regardless of which path
resolved the host id.

**Only pair the child id on resolution-order path 1.** Only when
`/lrh-session-id-claude` resolved the current window in Step 3 (it reports
the alias as *pairable*) and the user confirmed it does
`$CLAUDE_CODE_SESSION_ID` in this same window belong to that same session.
On path 2 (`list_sessions` by PR number) or path 3 (picked from the session
list), the resolved host id belongs to a *different* window than the one
running closeout right now — recording the current window's child
id against that host id would create a false alias. **Omit `--child-id`
entirely** (do not pass the flag, and do not pass an empty string) in those
two cases; the command still records the host id and PR. On every path,
pass `--title` whenever `/lrh-session-id-claude` reported one, and pass
`--branch` as the PR's head branch (`gh pr view <pr-url> --json
headRefName`), not the app-recorded branch, which can be stale when a
session switched branches inside its worktree.

```bash
# Path 1 (same window): pair host + child.
lrh prompt record-session-alias \
  --host-id <host-uuid-stem-from-step-3> \
  --child-id <child-id-reported-as-pairable-in-step-3> \
  --title "<title-from-step-3>" \
  --branch <pr-head-branch> \
  --pr <pr-url> \
  --project-root .

# Path 2 or 3 (cross-session / manual): host + PR only, no child-id flag.
lrh prompt record-session-alias \
  --host-id <host-uuid-stem-from-step-3> \
  --title "<title-from-step-3>" \
  --branch <pr-head-branch> \
  --pr <pr-url> \
  --project-root .
```

Each observation is additive and idempotent by host id — child ids and PRs
accumulate across repeated runs; the row is never duplicated. This file is
committed and regenerated by observation, never hand-edited.

**Recovering a pointer this closeout run left `pending`.** Stage 2
(`WI-SESSION-ARCHIVE-SYNC-RECONCILER`) adds `lrh sessions sync` (mirrors
local transcripts into a durable archive and harvests desktop-app
`session-export-*.zip` `metadata.json` for pointers that already dangle)
and `lrh sessions link` (promotes a resolved child id to its host-keyed
`session_transcript` pointer on one execution record).
Stage 4 wires closeout to run
`lrh sessions closeout-sync --project-root .`, which refreshes the private
archive as part of the closeout path; `lrh sessions link` remains a separate,
explicit command for promoting a now-resolved child id onto one execution
record. See
`src/lrh/skills/lrh-implement/references/execution-session-reference.md`'s
"`lrh sessions` — the Stage 2 archive reconciler" section for the full
command reference.
