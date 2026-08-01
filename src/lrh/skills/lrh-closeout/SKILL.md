---
name: lrh-closeout
description: >
  Automate the post-execution closeout workflow for an LRH session. Given a PR
  URL, WI ID, WS ID, or auto-detected from in-progress execution records, the
  skill assesses all artifact states, resolves the session transcript, presents
  a full closeout plan at a human gate, executes confirmed actions (landing
  execution records via lrh prompt update-execution, resolving work items,
  closing workstreams, adopting proposals), validates, prompts for session
  reflection, and reports.
disable-model-invocation: true
argument-hint: "[pr-url | WI-ID | WS-ID]"
---

# lrh-closeout Skill

This skill automates the post-execution closeout workflow that completes every
LRH session: updating execution records to `landed`, resolving work items,
closing workstreams, and adopting governing proposals. It assesses all artifact
states before touching any files, presents a full closeout plan at a human
confirm gate, and executes only what the user approves.

This is the missing complement to `/lrh-implement` and `/lrh-review-response`
in the LRH execution lifecycle. See `PROP-LRH-CLOSEOUT` for the design.

---

## Inputs

Provide one of:

```
/lrh-closeout https://github.com/xenotaur/logical_robotics_harness/pull/342
/lrh-closeout WI-SKILLS-LRH-CLOSEOUT
/lrh-closeout WS-SKILLS-CLOSEOUT
/lrh-closeout
```

Omitting the argument triggers auto-detection from in-progress execution
records. If multiple candidates are found, they are listed for the user to
choose. See Step 1 for full auto-detection behavior.

---

## Reference Knowledge

Load this before running any step:

1. **`references/closeout-workflow.md`** — Full decision matrix (artifact →
   condition → action), execution record update protocol (field values, valid
   transitions, `pending`/`none` conventions), WI resolution protocol
   (`mv` commands, frontmatter fields), WS closeout protocol, proposal
   adoption protocol, and session-transcript resolution (host-id env var →
   `list_sessions` → View > Copy URL, `claude-app:<host-uuid-stem>` format,
   `pending`/`none` sentinels). Read this before Step 2 and Step 5.

---

## Execution Steps

Work through these steps in order. Do not skip Step 4 (confirm gate).

### Step 1 — Parse input

**If a PR URL was provided:**
Use it directly as the target. Proceed to Step 2 with this URL.

**If a WI ID was provided:**
Locate the execution record for this WI:
```bash
find project/executions/<WI-ID>/ -name "*.md" 2>/dev/null
```
If found, read the `pr:` field for the PR URL. If not found, warn and ask.

**If a WS ID was provided:**
Read the workstream file to find its `work_items:` list, then find execution
records for each WI as above.

**If no argument was provided (auto-detect):**
```bash
grep -rl '^status: in_progress' project/executions/ --include='*.md'
```

For each candidate returned, read its `pr:` field. If exactly one candidate
has a non-empty `pr:` field, use it. If multiple candidates match, list them
and ask the user to select one. If none has a `pr:` field, list all candidates
and ask the user to identify the target.

### Step 2 — Assess state → build closeout plan

Apply the decision matrix from `references/closeout-workflow.md` to all
discovered artifacts. Assess in this order:

**1. PR state:**
```bash
gh pr view <pr-url> --json state,mergeCommit \
  --jq '{state: .state, commit: .mergeCommit.oid}'
```
- `MERGED` → proceed; record the commit SHA
- `OPEN` or `CLOSED` without merge → **abort** and report; do not proceed
  past this point

**2. Execution record(s):**
Find all execution records linked to this PR by `pr:` field:
```bash
grep -rl "^pr: <pr-url>" project/executions/ --include='*.md'
```
If no records are found (common when `/lrh-implement` left `pr:` blank), fall
back to listing all in-progress records:
```bash
grep -rl '^status: in_progress' project/executions/ --include='*.md'
```
Present the fallback candidates to the user and ask which one(s) belong to
this PR. For each matched record: check `status:` field. See decision matrix
in `references/closeout-workflow.md` for `in_progress` / `landed` / missing
actions.

**3. Work item(s):**
```bash
find project/work_items/ -name "<WI-ID>.md"
```
Check which bucket (`proposed/` vs. `resolved/`) the file is in. See
decision matrix for actions.

**4. Workstream (if linked from WI):**
Read the `related_workstreams:` field of the WI. For each workstream:
- Read `work_items:` from the WS file
- Check whether every listed WI will be resolved after this closeout. Treat
  WIs already marked `resolve and move` in the current plan as resolved —
  assess WS readiness from the **post-plan state**, not the current on-disk
  state. Check disk only for WIs not mentioned in the current plan.
- If all WIs resolve (on disk or planned) AND WS is in `workstreams/proposed/`
  or `workstreams/active/`:
  - Also read `exit_criteria:` from the WS file
  - Include the criteria list in the plan output as a sub-list below the WS
    row — the user must see the criteria at assessment time
  - Mark the WS as "offer closeout — exit criteria confirmation required at
    Step 4"
- If any WI would remain unresolved after this closeout → skip (not ready)

**5. Proposal (if WS would be closed):**
Read `related_design:` from the WS file; identify any proposals in
`project/design/proposals/proposed/`. If the WS would close AND the proposal
is still in `proposed/` → offer adoption.

Present the full plan as a table:

| Artifact | Current state | Intended action |
|---|---|---|
| PR #N | MERGED, commit `<sha>` | record commit |
| Execution record `<id>` | `in_progress` | update to `landed` |
| WI `<WI-ID>` | in `proposed/` | resolve and move |
| WS `<WS-ID>` | in `proposed/`, 1/2 WIs resolved | skip — not all WIs resolved |
| WS `<WS-ID>` | in `active/`, all WIs resolved | offer closeout — exit criteria confirmation required |
| PROP-`<slug>` | in `proposed/` | skip — governing WS not closing |

### Step 3 — Resolve session transcript

**Resolve a transcript value separately for each execution record matched in
Step 2** — a single PR can carry records from different backends (e.g. a
`codex_cloud` implementation record plus Claude-authored review-response/
confirm-fixes records), and stamping one resolved value onto every record
would misattribute provenance on whichever records don't share that backend.
Repeat the branch-and-resolve procedure below once per matched record, keyed
off that record's own `agent` field, and keep each record's resolved value
separate for Step 5.

**First, branch on the execution record's `agent`** — the pointer scheme is
backend-specific, and running closeout from Claude must not associate the
current Claude window with work another backend produced:

- **Non-Claude backend** (`agent: codex_cloud`, `manual`, or any other
  value): the Claude env var and Claude session URL are the *wrong* session —
  do **not** use them. Resolve the backend's own scheme-prefixed id if one is
  retrievable (e.g. `codex-cloud:<task-id>` from the Codex run, per
  `project/executions/README.md`); otherwise use `none`. Skip the
  Claude-specific steps below.
- **Claude.app** (`agent: claude_app`, or absent/assumed Claude): resolve the
  host id with the steps below.

For a Claude.app session the canonical stored value is
`claude-app:<host-uuid-stem>` — the **host** session id (`local_<uuid>`,
`local_` stripped), not the child SDK id that names the JSONL file. Do **not**
use JSONL-filename auto-detection: on Claude.app sessions it returns the child
id, which differs from the host id on resumed/continued sessions and produces
a pointer that session-management tools cannot resolve. Resolve in this order,
stopping at the first that yields a confident value:

1. **Same session — env var (preferred).** Read the host id directly:

   ```bash
   echo "$CLAUDE_CODE_HOST_SESSION_ID"   # e.g. local_4c3d03d6-...
   ```

   Strip the `local_` prefix and propose `claude-app:<host-uuid-stem>`.

   **Confirm before storing — the env var tracks the *current* window.**
   `CLAUDE_CODE_HOST_SESSION_ID` reflects the session window you are in right
   now, and the host id **rotates when a session is resumed or continued**.
   On a long or resumed session it can therefore differ from the session that
   actually authored the work. So: show the value and ask the user to confirm
   it, e.g. "In-session host id is `claude-app:<stem>` — is this the session
   for this work?" If the user's **View > Copy URL** disagrees with the env
   var, the browser URL wins (case 3). When they agree, store the env-var
   value.

2. **Cross-session — `list_sessions` by PR number.** When closing out on
   `main` after merge from a *different* session than the one that did the
   work, the env var is not the right session. Use the session-management
   `list_sessions` tool and match the target session by its `prNumber`
   (it returns other sessions with `sessionId`, `prNumber`, `branch`); take
   that session's `sessionId` (host id), strip `local_`, and store
   `claude-app:<host-uuid-stem>`. Confirm the match with the user if more than
   one session references the PR.

3. **Manual — View > Copy URL.** If neither above yields a confident id, ask:
   "Paste View > Copy URL for the session (e.g. `local_6f9b846e-...` from
   `claude.ai/.../local_<uuid>`), or confirm `none`/`pending`." Store the
   pasted id as `claude-app:<uuid>` (strip any `local_` prefix; UUID stem
   only). The browser URL is authoritative over the env var when they differ.

4. **Sentinels — `none` vs `pending` (distinct, not interchangeable).**
   - `none`: the backend produced **no retrievable transcript** (e.g. a
     `codex_cloud` or `manual` execution). This is a **terminal** value — do
     not add a "update it later" reminder.
   - `pending`: a transcript exists but its id is **not yet known**. This is a
     **to-do** — include the Step 8 reminder to update it before archiving.

   Use `none` (not `pending`) whenever the backend simply has no session URL
   to resolve, so a finished record is never left looking like unfinished
   work. See the 2026-07-23 "Backend-Agnostic Session Pointer Grammar"
   decision-log entry and `project/executions/README.md`.

### Step 4 — Confirm gate (human gate)

Before touching any files, show the user:

- PR URL, state (`MERGED`), and commit SHA
- The full closeout plan table (from Step 2)
- Resolved session transcript value for **every** matched execution record
  from Step 3, enumerated by execution ID — not a single summary value.
  Step 3 resolves a value per record (Step 5 writes each to its own
  record), so showing only one here would let the user confirm without
  ever seeing what gets written to the others.
- For any WI being resolved: the `resolution:` text to be written. If the
  user has not already stated it, ask: "What should the `resolution:` note
  say for `<WI-ID>`?" (one-line summary; e.g., `"Implemented and merged in PR #342 (commit abc1234)"`)

**WS exit criteria confirmation:** for any WS where closeout is being offered,
display the full `exit_criteria:` list (already shown at Step 2, repeated here
for the gate) and ask:

> "Are all of these WS exit criteria met? [y/N]"

Only include the WS closeout action in the confirmed plan if the user answers
`y`. If the user answers `n` or expresses doubt about any criteria, remove WS
closeout from the plan — and also remove any proposal-adoption action whose
offer depended on that WS closing — then note which criteria blocked it. Show
the revised plan before asking for final confirmation.

**Wait for explicit confirmation before touching any files.** If the user
redirects, updates the resolution text, or asks to skip an action, adjust the
plan and show it again.

### Step 5 — Execute confirmed actions

Execute all confirmed actions. Abort on any error rather than partially completing.

**Execution records** (for each record marked `update to landed`):

Call the CLI to update all four fields atomically, using **that record's own**
resolved transcript value from Step 3 — not a value resolved for a different
record on the same PR:

```bash
lrh prompt update-execution \
  --execution-id <execution-id> \
  --status landed \
  --pr <pr-url> \
  --commit <merge-commit-sha> \
  --session-transcript <this-record's-resolved-value-from-step-3> \
  --project-root .
```

The `--execution-id` is the `execution_id:` field value from the record
(e.g. `2026_06_28_11_30_26_WI_PROMPT_CLI_CLOSEOUT`). The command finds the
record by scanning `project/executions/**/*.md`, updates the four frontmatter
fields in-place, and prints `updated: <path>` on success.

See `references/closeout-workflow.md` for valid field values and the
`session_transcript:` `pending` convention.

**Work items** (for each WI marked `resolve and move`):

Edit the frontmatter in-place:
- `status: proposed` → `status: resolved`
- `resolution:` → set to the confirmed resolution text

Then move the file:
```bash
mv project/work_items/proposed/<WI-ID>.md project/work_items/resolved/<WI-ID>.md
```

Do not use `cp` — a copy in both locations triggers `WORK_ITEM_ID_DUPLICATE`
in `lrh validate`.

**Workstream** (if offered closeout and user confirmed):

Edit the frontmatter in-place:
- `stage:` → `stage: closed`
- `status:` → `status: resolved`

Then move from whichever bucket the WS was found in at Step 2 (`proposed/` or
`active/`):
```bash
mv project/workstreams/<current-bucket>/<WS-ID>.md project/workstreams/resolved/<WS-ID>.md
```

**Proposal** (if offered adoption and user confirmed):

Edit the frontmatter in-place:
- `status: proposed` → `status: adopted`
- `implementation_status: not_started` → `implementation_status: implemented`
- `implemented_by:` → set to the list of implementing WI IDs (e.g., `[WI-SKILLS-LRH-CLOSEOUT]`)

Then move the entire proposal directory:
```bash
mv project/design/proposals/proposed/<slug>/ project/design/proposals/adopted/<slug>/
```

### Step 6 — Validate

```bash
lrh validate
```

If any errors are reported: stop, report each error to the user, and ask how
to proceed. Do not commit with `lrh validate` errors.

If clean (0 errors, 0 warnings): proceed to Step 7.

### Step 7 — Session reflection

Before asking the user anything, review this session's actual changes and
decisions — corrected assumptions, discovered conventions or gotchas,
design decisions and their rationale, anything a fresh session would have
no way to re-derive from code or git history alone. Apply the same bar the
auto-memory system already uses: surprising, non-obvious, durable, and not
already fully captured by an existing memory or derivable by reading the
current project state.

Draft 0-3 candidate suggestions from that review. Each candidate is one
line naming the rule or fact, plus one line of why it matters. If nothing
in the session clears that bar, say so explicitly — do not silently skip
straight to asking.

Then present the candidates (or the explicit "nothing stands out" finding)
and ask: "Does this look right — anything to add, edit, or drop?"

If candidates were presented and the user confirms, adds, or edits: write
the resulting content using the auto-memory system
(`~/.claude/projects/<project-slug>/memory/`). Update `MEMORY.md` with a
pointer. See the session memory instructions for file format.

If the user declines all candidates, or confirms the "nothing stands out"
finding with no additions: proceed to Step 8 without writing anything.
Confirming that nothing stands out is not itself content to persist — only
write when there is an actual candidate or user-supplied fact to record.

### Step 8 — Report and commit

Commit all closeout changes to `main`:

```bash
git add -p   # or stage specific files
git commit -m "chore(closeout): <summary of actions> (PR #N)"
```

Report to the user:

- Each action taken (file edited, file moved, validation result)
- Commit SHA on `main`
- If `session_transcript` is still `pending`: remind to update it before
  archiving the session (the host id is `$CLAUDE_CODE_HOST_SESSION_ID` or the
  `local_<uuid>` in View > Copy URL, `local_` stripped). Do **not** add this
  reminder for `none` — that value is terminal.
- Offer to run `/export` to archive the session transcript locally

**Memory written (Step 7 outcome):** state explicitly whether memory was
written this session. If yes: include a one-line summary of each memory
persisted (e.g., "Memory written: feedback on WS premature closure —
`feedback_closeout_ws_exit_criteria.md`"). If no: "Memory: nothing written
this session."

**Pending offers:** re-state any action that was offered during the skill run
but was not included in the confirmed plan. For each skipped action, give a
one-line reason:
- "WS `<WS-ID>` closeout: skipped — `<WI-ID>` and `<WI-ID>` still unresolved"
- "Proposal `<slug>` adoption: skipped — governing WS not closing"
- Any offer the user deferred at Step 4

If no offers were skipped, omit this section.

---

## Quality Checklist

Before reporting completion, verify:

- [ ] PR state verified as `MERGED` before any files were touched
- [ ] Decision matrix applied to all discovered artifacts
- [ ] Session transcript value resolved (or `pending` confirmed)
- [ ] User confirmed at Step 4 before any files were touched
- [ ] Each file read before editing; no partial edits
- [ ] `mv` used for WI/WS/proposal moves (not `cp`)
- [ ] `lrh validate` reports 0 errors before commit
- [ ] Committed to `main` (not a feature branch)
- [ ] `session_transcript: pending` reminder included in report if applicable

---

## What This Skill Does Not Do

- Does not close GitHub PRs — the skill records an already-merged PR; closing
  is a human action.
- Does not automatically write memories — Step 7 prompts the user; writing
  is always opt-in.
- Does not enforce WS exit criteria programmatically — prose criteria are
  human-authored and cannot be machine-checked. The skill surfaces them at
  Step 2 and requires human confirmation at Step 4, but the judgment is the
  user's.
- Does not automate the `resolution:` prose — the one-line summary is
  human-authored and confirmed at Step 4.
- Does not handle the design or instruction phases — those remain
  `/lrh-design`, `/lrh-proposal`, and `/lrh-implement`.
- Does not handle abandoned WIs (WI with no PR ever opened) — warns and
  leaves for human resolution.
- Does not open a new branch or PR — closeout commits go directly to `main`.
