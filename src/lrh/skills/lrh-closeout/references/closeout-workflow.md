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
| WI | Found in `proposed/` | Resolve: set `status: resolved`, write `resolution:`, `mv` to `resolved/` |
| WI | Found in `resolved/` | Skip — already resolved |
| WI | Not found anywhere | Warn user; ask how to proceed |
| WS | All listed WIs in `resolved/` AND WS in `workstreams/proposed/` | Offer closeout |
| WS | Any listed WI still in `proposed/` | Skip — not all WIs resolved |
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
session_transcript: claude-app:<uuid>   # or: pending
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
list is present in `project/work_items/resolved/`:

```bash
# For each WI-ID in the workstream's work_items: list:
find project/work_items/resolved/ -name "<WI-ID>.md"
```

If any WI is still in `proposed/`, skip WS closeout and note it in the
closeout plan.

### Required frontmatter changes

```yaml
stage: closed
status: resolved
```

### File move

```bash
mv project/workstreams/proposed/<WS-ID>.md project/workstreams/resolved/<WS-ID>.md
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

## Session Transcript Auto-Detection

### What to detect

The `session_transcript:` field stores the Claude.app session reference in
the form:

```
claude-app:<uuid>
```

where `<uuid>` is the UUID stem from the JSONL session file or browser URL.
Example: `claude-app:6f9b846e-c6f9-45aa-9cf9-8c744ec57026`

Never store an absolute path (`~/.claude/...` or `/Users/...`) — it leaks
the local workspace layout to everyone who clones the repository.

### JSONL auto-detection

```bash
ls ~/.claude/projects/-Users-centaur-Workspace-LogicalRoboticsHarness-logical-robotics-harness/*.jsonl 2>/dev/null
```

The project slug is the absolute project root path with each `/` replaced
by `-`. If the project root is
`/Users/centaur/Workspace/LogicalRoboticsHarness/logical_robotics_harness`,
the slug is:
`-Users-centaur-Workspace-LogicalRoboticsHarness-logical-robotics-harness`.

### Reliable failure for web-backed sessions

In Claude.app web sessions, the JSONL filename does not match the UUID in the
browser URL — the auto-detection reliably returns no match. This is expected,
not an error. Fall through to case 2 (ask user) without alarming the user.

### 3-way resolution

| Case | What to do |
|---|---|
| One JSONL found | "Detected session `<uuid>`. Is this correct?" — confirm before using |
| Not found or ambiguous | "Could not auto-detect. Provide the UUID from your browser URL, or confirm `pending`." |
| User confirms `pending` | Set `session_transcript: pending`; add reminder to Step 8 report |

### `pending` sentinel

`pending` is an explicit first-class value. It is used when the session ID
is not yet known or cannot be auto-detected. A `pending` value must never
block the closeout workflow. Include a reminder in the Step 8 report to
update it before archiving the session.

When the user later provides the session ID (from the browser URL), update
with:

```bash
# Edit the frontmatter manually (Phase 1) or:
# lrh prompt update-execution --execution-id <id> --session-transcript claude-app:<uuid>  (Phase 2)
```
