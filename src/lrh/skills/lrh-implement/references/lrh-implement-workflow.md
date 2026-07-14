# lrh-implement Workflow Context

Where `/lrh-implement` sits in the LRH lifecycle, and what to do after it
completes. Read this before Step 10 (report and offer closeout).

---

## Lifecycle placement

```
/lrh-work-item WI-<ID>              ← create planning artifact
    │
    ▼
lrh work-items readiness <WI-ID>    ← check prompt-readiness
lrh request ready-work-item <ID>    ← refine if thin
    │
    ▼
/lrh-implement WI-<ID>              ← THIS SKILL
    │  Instruction phase: mint prompt ID, idempotence check, confirm plan
    │  Execution phase: branch → implement → validate → PR → record
    │
    ▼
project/executions/<WI-ID>/         ← execution record (in_progress)
    │
    ▼
/lrh-review-response <PR-URL>       ← address reviewer comments (repeat as needed)
    │
    ▼
Merge PR + closeout (human)         ← update record to landed, resolve WI
```

The PR is rarely mergeable the moment it opens — expect at least one round of
`/lrh-review-response` before it lands. Do not offer "merge PR" as the next
step without first accounting for outstanding review comments.

---

## Relationship to adjacent tools

### `lrh work-items readiness <WI-ID>`

Run before `/lrh-implement` to confirm the work item has the sections
(`Required Changes`, `Acceptance Criteria`, `Validation`) needed to drive a
bounded implementation. The skill runs this automatically at Step 1 and warns
if the item is not ready, but does not hard-block. An expert user may override.

### `lrh request ready-work-item <WI-ID>`

Use before `/lrh-implement` when the work item is thin. `ready-work-item`
proposes a patch to fill missing sections; apply it manually and re-run
`lrh work-items readiness` before proceeding.

### `lrh request prompt-from-work-item`

Not called by this skill. `prompt-from-work-item` generates a prompt file for
submission to Codex Cloud. In a Claude.app session, Claude reads the work item
directly — a rendered prompt file adds a step with no benefit.

### `lrh skills install`

`lrh skills install` installs LRH skills globally to `~/.claude/skills/`, making
`/lrh-implement` available in any project on the machine. Use `--local` to install
to `./.claude/skills/` for a project-scoped installation instead.

### `/lrh-review-response <PR-URL>`

Run after `/lrh-implement` opens a PR, once reviewer comments arrive — not
called by this skill directly, but it is the expected next step before
merging. Fetches open comments, triages each (presence / validity /
feasibility), applies fixes, and pushes them as additional commits to the
same PR with a linked `AD_HOC` execution record. Repeat for further rounds
of comments; only proceed to "After the PR lands" once the PR is clean.

---

## After the PR lands

1. **Update the execution record** — edit the file under
   `project/executions/<WI-ID>/` to set:
   - `status: landed`
   - `pr: <PR-URL>`
   - `commit: <merge-SHA>`
   - `session_transcript: claude-app:<session-id>` (if still `pending`)

2. **Resolve the work item** — move the file from
   `project/work_items/proposed/` to `project/work_items/resolved/` and set:
   - `status: resolved`
   - `resolution: <one-line description of what was delivered>`

3. **Validate** — run `lrh validate` after both edits to confirm the file is
   in the correct bucket and all references are intact.

4. **Audit traceability** — optionally run:

   ```bash
   lrh work-items audit --format md
   ```

   to confirm the work item appears in the audit with correct evidence links.

---

## Workstream closeout (offer, not automatic)

If the work item belongs to a workstream (`related_workstreams`), check
whether it is already listed in the workstream's `work_items:` frontmatter.
If not, offer to add it and re-run `lrh validate`.

Workstream stage or `exit_criteria` changes are human decisions — the skill
does not update them automatically.
