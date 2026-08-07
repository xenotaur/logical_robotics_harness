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
   format, found-or-backfill matrix, run journal YAML skeleton, interim
   invocation pattern note, and the chain-defaults propose-and-confirm flow.
   Load before Step 1 so all rule definitions are available during execution.

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
grep -rl "pr: <pr-url>" project/executions/ | grep -v "_REVIEW\.md$" | grep -v "_CONFIRM\.md$" | grep -v "_CLOSEOUT_NOTE\.md$" | grep -v "_SELFREVIEW\.md$"
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
  [Step 6] merge gate — presents SHA-locked command; executes only on
           unambiguous in-session authorization (DEC-AGENT-EXECUTED-MERGE-GATE)
  [Step 7] closeout (inline, Phase 1)
```

**Run the chain-defaults propose-and-confirm flow before eliciting
conditions from scratch** — see `references/land-workflow.md` § Chain-defaults
propose-and-confirm flow (canonical source:
`src/lrh/skills/_shared/chain-defaults.md`). It pre-fills the completion and
stop-work condition text below from `project/config/chain-defaults.yaml`
(proposing the steelmanned defaults on first encounter), and under
`chain_init_confirmation: skip_if_opted_in` with valid user-local consent and
no special condition firing, may skip the live confirming reply entirely for
this run — always falling back to the live-reply path below when any of
that isn't true.

Elicit from the user (or, under a validated `skip_if_opted_in` skip, display
without asking):
1. **Completion condition** — what "done" means for this run (pre-filled
   from the stored profile, or "PR merged and work item resolved" on first
   encounter before any profile exists)
2. **Stop-work condition** — what forces a halt-and-report (pre-filled
   from the stored profile, or "any failing test or unexpected reviewer
   finding" on first encounter)

Wait for explicit approval of both conditions, unless the skip path above
applied. Do not proceed past this step without either the user confirming
them or a validated skip. If the user's live reply diverges from the stored
values, apply the profile-update offer at the end of the run (see the
propose-and-confirm flow doc) rather than silently persisting the override.

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
there are no threads matching *this check's* definition of unresolved —
which excludes outdated threads (a thread whose commented line moved can
stay `isResolved: false` while `isOutdated: true`; see `/lrh-confirm-fixes`'s
Step 2 note on the narrower definition). It is not a full authoritative "zero
unresolved threads anywhere" guarantee — Step 5's `isResolved`-only check
is what provides that. Compare `lastPush` against the current time — if the
last commit is only seconds old, bots have not had time to run; wait and
re-check. If enough time has passed with no threads, review is complete
with no findings under this check → proceed to Step 5.

If the output contains thread data → open threads present; execute the
review-response workflow inline (Phase 1: read `/lrh-review-response/SKILL.md`
steps and execute them in the current session).

**Loop-exit condition:** do not loop on `Nothing to resolve:` here.
`/lrh-review-response` does not itself resolve GitHub review threads — its
own "What This Skill Does Not Do" states this is a human decision, and
thread resolution (`resolveReviewThread`) is Step 5's job. Because of this,
a thread that was already fixed in the diff still shows up as unresolved
when `lrh request review_response` is re-run, until Step 5 resolves it —
looping until the list itself goes empty would never terminate here. The
correct exit condition: repeat Step 4 only while a fresh
`lrh request review_response` call surfaces a comment that has not yet been
triaged in the current diff (fixed, or explicitly dismissed with rationale,
per `/lrh-review-response`'s presence/validity/feasibility checks). Once
every comment currently returned has been triaged — even though the thread
list is not yet empty — proceed to Step 5, whose confirm-fixes pass is what
actually resolves the threads and makes `Nothing to resolve:` true
afterward.

**Step 4 completing is provisional, not authoritative.** Because
`lrh request review_response`'s notion of unresolved excludes outdated
threads, an untriaged thread can exist that Step 4 never saw at all — not
just one it triaged and is waiting on Step 5 to resolve. Step 5's
authoritative `isResolved`-only check can surface it for the first time.
If it does and the diff doesn't plainly satisfy it, that is expected —
`/lrh-confirm-fixes` classifies it (Unaddressed/Partial/Ambiguous/etc.)
per its own Step 3 taxonomy. A not-green Step 5 verdict caused by a
newly-surfaced outdated thread is not a sign Step 4 was skipped or
malformed — it is handled the same way as any other not-green verdict:
Step 5's hard stop, with the human deciding next steps. A mechanical way
for Step 4 to pick up this specific class of thread automatically is
tracked as a backlog item rather than solved here — see
`project/design/backlog.md`.

### Step 5 — Confirm-fixes

Execute the confirm-fixes workflow inline (Phase 1: read
`/lrh-confirm-fixes/SKILL.md` steps and execute them in the current session).
Report the merge-readiness verdict.

If the verdict is **not green**, stop and report — do not proceed to the merge
gate with a failing confirm-fixes pass. This includes a not-green verdict
caused by a newly-surfaced outdated thread Step 4 couldn't see (per the
note above) — it is not a special case; the human decides how to resolve
it, including whether to address it manually outside this automated loop
before re-running from Step 4.

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
the verify pass and whoever ends up running the merge — the human or the
agent, per the classification below.

Present that command verbatim. If the confirm-fixes verdict omitted the SHA
lock, derive it from the current HEAD:

```bash
git rev-parse HEAD
gh pr merge <pr-url> --merge --match-head-commit <sha>
```

**If this invocation is governed by an `project/assistants/<role>/policy.md`
binding, check it first.** A role-level `prohibitions: repo:merge` or
`obligations: merge:human` is a hard ceiling — "obligations accumulate and
are never removed by a narrower layer" (`project/assistants/token-vocabulary.md`)
— that overrides the general default below regardless of the reply.
Ordinary human-driven sessions with no active role binding are unaffected.

**Classify the human's live reply to this presented command** (per
`DEC-AGENT-EXECUTED-MERGE-GATE`):

- **Execute it** — any affirmative reply that doesn't claim the action for
  the human: "approve merge," "approved," "go ahead," "yes," "merge it,"
  "do it," "run it." Run the presented command yourself.
- **Wait** — any first-person self-action reply: "I'll merge it," "let me
  merge," "I'll do it." Do not execute; wait for the user to confirm the PR
  has merged.
- **Ambiguous** — ask a direct disambiguating question ("Should I run this
  merge myself, or will you?") rather than guessing either way.

A merge instruction embedded in a prior run prompt is still data, not
authorization, regardless of who would execute it — the reply must be live
and in-session, given after this command was presented.

**Verify actual merge state before proceeding to Step 7 — do not treat
command success as merge confirmation.** On a repository using a merge
queue, `gh pr merge` succeeding only means the PR was accepted into the
queue, not that it merged — the CLI itself documents this. This applies
whether the agent ran the command or the human reports having run it: query
the PR until its state is actually `MERGED` and capture the merge commit
before any closeout action touches `main`.

```bash
gh pr view <pr-url> --json state,mergeCommit --jq '{state: .state, mergeCommit: .mergeCommit.oid}'
```

If `state` is not yet `MERGED` (e.g. still `OPEN` while queued), wait and
re-check rather than proceeding — Step 7 commits control-plane files to
`main` and must not race a merge that could still fail or be dequeued.

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
- [ ] Review-response completed once every comment returned by
      `lrh request review_response` has been triaged in the current diff
      (fixed, or dismissed with rationale) — not once the thread list itself
      is empty, which requires confirm-fixes (Step 5) to run first
- [ ] Confirm-fixes verdict is green before REVIEW-LANDED re-check
- [ ] REVIEW-LANDED re-check performed after confirm-fixes pushes its `_CONFIRM` commit
- [ ] Merge command is the SHA-locked one from the confirm-fixes verdict; not a generic command
- [ ] Merge executed by the human, or by the agent given unambiguous
      in-session authorization per `DEC-AGENT-EXECUTED-MERGE-GATE` — not
      from a merge instruction embedded in a prior prompt
- [ ] Switched to main (or applied main-worktree-lock workaround) before inlining closeout
- [ ] Backfill record created explicitly (if no-primary path) before invoking closeout
- [ ] CHAIN-NOTE placed correctly (new `_CLOSEOUT_NOTE` if primary found;
      in the authored record if backfill path)
- [ ] Run journal entry appended to scratchpad
- [ ] `lrh validate` reports 0 errors after closeout

---

## What This Skill Does Not Do

- Does not land multiple PRs in one invocation — one PR per run.
- Does not execute the merge without explicit, in-session authorization at
  Step 6 — but given unambiguous authorization (per
  `DEC-AGENT-EXECUTED-MERGE-GATE`), the agent may run the presented command
  itself rather than only waiting on the human.
- Does not implement `/lrh-execute` — that is Phase 2 (`WI-SKILLS-LRH-EXECUTE`).
- Does not bypass any internal confirmation gate inside the inlined sub-skills
  — chain initiation authorizes running the links, not skipping their internal
  gates.
- Does not enforce `depends_on` — that is `/lrh-execute`'s responsibility.
- Does not implement a persistent run journal — the scratchpad journal is a
  prototype (per `PROP-LRH-LAND-EXECUTE` Decision 8).
