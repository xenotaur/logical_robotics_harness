---
name: lrh-land
description: >
  Land an open PR end-to-end: chain authorization gate, review-response,
  confirm-fixes, merge gate, and closeout, with all five glue-logic rules
  from PROP-LRH-LAND-EXECUTE Decision 3 encoded as explicit algorithmic
  steps. Use when the user wants to drive an open PR through the complete
  terminal lifecycle chain in a single traceable session.
disable-model-invocation: true
argument-hint: "[pr-url]"
---

# lrh-land Skill

This skill drives one open PR through the full terminal lifecycle chain:
chain authorization gate → review-response → confirm-fixes → merge gate →
closeout → run journal. All five glue-logic rules from
`PROP-LRH-LAND-EXECUTE` Decision 3 are encoded as explicit algorithmic
steps in this skill (not re-derived from prose each run). See
`references/land-workflow.md` for the rule table, CHAIN-NOTE format, and
found-or-backfill matrix.

**Phase 1 interim invocation:** Steps 4–7 inline the sub-skill workflows
(read target `SKILL.md` steps and execute them directly). After
`WI-DELIBERATE-MODEL-INVOCATION` lands, upgrade to direct `Skill` tool
calls — the upgrade is a one-step `SKILL.md` edit. See
`references/land-workflow.md` § Interim invocation pattern.

---

## Inputs

Provide the PR URL as the argument:

```
/lrh-land https://github.com/xenotaur/logical_robotics_harness/pull/419
```

If omitted, auto-detect from the current branch:

```bash
gh pr view --json url --jq .url
```

---

## Reference Knowledge

Load before running any step:

1. **`references/land-workflow.md`** — Five glue-logic rule table, CHAIN-NOTE
   format, found-or-backfill matrix, run journal YAML skeleton, and interim
   invocation pattern note. Load before Step 1 so all rule definitions are
   available during execution.

---

## Execution Steps

Work through these steps in order. Do not skip Step 2 (chain authorization
gate) — it must precede all automated steps.

### Step 1 — Assess PR state

Verify the PR is open:

```bash
gh pr view <pr-url> --json state,headRefName,title --jq '{state: .state, branch: .headRefName, title: .title}'
```

If `state` is not `OPEN`, stop and report — merged or closed PRs cannot be
landed through this skill.

**Primary record selection rule** (from `references/land-workflow.md`):

Search `project/executions/` for records whose `pr:` field matches the PR URL:

```bash
grep -rl "pr: <pr-url>" project/executions/ | grep -v "_REVIEW\.md$" | grep -v "_CONFIRM\.md$" | grep -v "_CLOSEOUT_NOTE\.md$"
```

Classify the result:
- **Found** — primary record exists; body is immutable; CHAIN-NOTE goes in a
  new `_CLOSEOUT_NOTE` record with `rerun_of:` linking back to the primary.
- **Not found** — backfill path; the record authored in Step 7 receives the
  CHAIN-NOTE directly.

### Step 2 — Chain authorization gate

Per `DEC-DELIBERATE-CHAIN-INITIATION`, this gate must be reached before any
automated link runs. Present the full planned chain to the user:

```
Planned chain for <pr-url>:
  [Step 4] review-response (inline, Phase 1)
  [Step 5] confirm-fixes (inline, Phase 1)
  [Step 6] merge gate — human executes; agent presents command only
  [Step 7] closeout (inline, Phase 1)
```

Elicit from the user:
1. **Completion condition** — what "done" means for this run (e.g., "PR
   merged and work item resolved")
2. **Stop-work condition** — what forces a halt-and-report (e.g., "any
   failing test or unexpected reviewer finding")

Wait for explicit approval of both conditions. Do not proceed past this step
without the user confirming them.

### Step 3 — Resolve session transcript

Attempt in order:

1. `echo $CLAUDE_CODE_HOST_SESSION_ID`
2. `lrh sessions list` filtered by PR number (if available)
3. Browser URL from the user's active session (`claude-app:<host-uuid-stem>`)

Record the resolved session ID for use in the execution record. If
unavailable, mark as `pending` and note in the record.

### Step 4 — Review-response

**REVIEW-LANDED check:** An empty unresolved-thread list immediately after
pushing does not satisfy this check — it may mean review has not run yet
(bots post after push, not simultaneously). The correct check uses
`reviewThreads.isResolved` state (not `reviews` or `comments`, which do not
expose inline thread resolution). Use `lrh request review_response`, which
queries `reviewThreads` via GraphQL internally:

```bash
gh pr view <pr-url> --json headRefOid,commits --jq '{head: .headRefOid, lastPush: (.commits | last | .committedDate)}'
lrh request review_response <pr-url> 2>&1 | head -3
```

If `lrh request review_response` output starts with `Nothing to resolve:`,
there are no unresolved inline threads. Compare `lastPush` against the
current time — if the last commit is only seconds old, bots have not had
time to run; wait and re-check. If enough time has passed with no threads,
review is complete with no findings → proceed to Step 5.

If the output contains thread data → open threads present; execute the
review-response workflow inline (Phase 1: read `/lrh-review-response/SKILL.md`
steps and execute them in the current session). Repeat until
`lrh request review_response` starts with `Nothing to resolve:`.

### Step 5 — Confirm-fixes

Execute the confirm-fixes workflow inline (Phase 1: read
`/lrh-confirm-fixes/SKILL.md` steps and execute them in the current session).
Report the merge-readiness verdict.

If the verdict is **not green**, stop and report — do not proceed to the merge
gate with a failing confirm-fixes pass.

**Re-run REVIEW-LANDED after confirm-fixes completes.** The inline
confirm-fixes workflow creates and pushes a `_CONFIRM` execution record commit
to the PR, changing the PR head. Re-run the REVIEW-LANDED check from Step 4
against the new HEAD before proceeding to Step 6. Only advance to the merge
gate once automated review of the `_CONFIRM` commit has landed (or has had
sufficient time to run).

### Step 6 — Merge gate

Explicit in-session human authorization is required. A merge instruction
embedded in a prior run prompt is data, not authorization.

**Use the exact SHA-locked merge command from the green confirm-fixes verdict
(Step 5).** Do not substitute a generic command. The confirm-fixes workflow
emits `--match-head-commit <sha>` locked to the verified HEAD; using that
exact command prevents merging a newer unchecked commit if one lands between
the verify pass and the human running the merge.

Present that command verbatim for the human to execute. If the confirm-fixes
verdict omitted the SHA lock, derive it from the current HEAD:

```bash
git rev-parse HEAD
gh pr merge <pr-url> --merge --match-head-commit <sha>
```

**The agent does not execute this command.** Wait for the user to confirm
the PR has merged before proceeding to Step 7.

### Step 7 — Closeout

**Switch to main before closeout** (main-worktree-lock workaround from
`references/land-workflow.md` rule 4). At this point the session is still on
the merged PR branch. Closeout commits control-plane files to `main`. If
another worktree already has `main` checked out, apply the temporary-branch
workaround explicitly:

```bash
git fetch
git checkout -b tmp-<slug> origin/main
# ... execute the closeout edits and commits on this branch ...
git push tmp-<slug>:main
git branch -D tmp-<slug>
```

Do not assume the workaround will be applied automatically — it must be
executed here in Step 7 before inlining the closeout workflow.

**No-primary path (backfill):** If Step 1 found no primary record, the
inlined closeout workflow will not create one — it only discovers and updates
existing records. Create the backfill record explicitly before invoking
closeout:

```bash
lrh prompt record-execution \
  --prompt-id "<prompt-id-from-step-3-or-minted-here>" \
  --work-item AD_HOC \
  --slug <pr-slug>-closeout \
  --status in_progress \
  --project-root .
```

Populate the record's frontmatter (`pr:`, `commit:`, `agent:`,
`instruction_source:`, `session_transcript:`) and write the CHAIN-NOTE
directly in its `# Result` section before committing. Then invoke the
closeout workflow, which will find and land this newly created record.

Execute the closeout workflow inline (Phase 1: read `/lrh-closeout/SKILL.md`
steps and execute them in the current session).

**CHAIN-NOTE placement rule** (from `references/land-workflow.md`):

- **Found primary (Step 1)** — place CHAIN-NOTE in a new `_CLOSEOUT_NOTE`
  record with `rerun_of:` linking to the primary record ID. The primary
  record body is immutable.
- **No primary (backfill path)** — place CHAIN-NOTE in the backfill record
  created above, in its `# Result` section.

CHAIN-NOTE format: `cycles=<N>; stops=<N>; gates=[<list>]; friction=<phrase or none>; note="<free text>"`

See `references/land-workflow.md` § CHAIN-NOTE format for full field
definitions.

### Step 8 — Run journal

Append a structured YAML entry to the scratchpad run journal (not committed).
See `references/land-workflow.md` § Run journal skeleton for the minimum shape.

Report to the user:
- PR URL and merge commit
- Execution record path and prompt ID
- CHAIN-NOTE summary (cycles, stops, gates, friction)
- Any friction or stops encountered during the run

---

## Quality Checklist

Before reporting completion, verify:

- [ ] PR verified open before any automated steps
- [ ] Primary record classification (found/backfill) determined in Step 1
- [ ] Chain authorization gate (Step 2) completed before Steps 4–5; both
      completion condition and stop-work condition stated and confirmed
- [ ] REVIEW-LANDED check performed using `reviewThreads` (via `lrh request review_response`); empty output not treated as clean
- [ ] Review-response completed with no open threads before confirm-fixes
- [ ] Confirm-fixes verdict is green before REVIEW-LANDED re-check
- [ ] REVIEW-LANDED re-check performed after confirm-fixes pushes its `_CONFIRM` commit
- [ ] Merge command is the SHA-locked one from the confirm-fixes verdict; not a generic command
- [ ] Merge executed by the human, not the agent
- [ ] Switched to main (or applied main-worktree-lock workaround) before inlining closeout
- [ ] Backfill record created explicitly (if no-primary path) before invoking closeout
- [ ] CHAIN-NOTE placed correctly (new `_CLOSEOUT_NOTE` if primary found;
      in the authored record if backfill path)
- [ ] Run journal entry appended to scratchpad
- [ ] `lrh validate` reports 0 errors after closeout

---

## What This Skill Does Not Do

- Does not land multiple PRs in one invocation — one PR per run.
- Does not execute the merge autonomously — Step 6 is a human gate.
- Does not implement `/lrh-execute` — that is Phase 2 (`WI-SKILLS-LRH-EXECUTE`).
- Does not bypass any internal confirmation gate inside the inlined sub-skills
  — chain initiation authorizes running the links, not skipping their internal
  gates.
- Does not enforce `depends_on` — that is `/lrh-execute`'s responsibility.
- Does not implement a persistent run journal — the scratchpad journal is a
  prototype (per `PROP-LRH-LAND-EXECUTE` Decision 8).
