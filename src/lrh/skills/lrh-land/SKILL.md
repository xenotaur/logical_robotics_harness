---
name: lrh-land
description: >
  Land an open PR end-to-end: chain authorization gate, review-response,
  confirm-fixes, merge gate, and closeout, with all five glue-logic rules
  from PROP-LRH-LAND-EXECUTE Decision 3 encoded as explicit algorithmic
  steps. Use when the user wants to drive an open PR through the complete
  terminal lifecycle chain in a single traceable session.
when_to_use: >
  Invoke only when the user explicitly asks to land a specific open PR, or
  when /lrh-execute reaches its landing phase for the PR it just opened. The
  chain-authorization gate must still run before review-response, confirm-fixes,
  merge, or closeout actions.
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

**Inlined invocation, by design, not as an interim step:** Steps 4–7 inline
the sub-skill workflows (read target `SKILL.md` steps and execute them
directly) rather than calling them via the `Skill` tool.
`WI-DELIBERATE-MODEL-INVOCATION` resolved this as a permanent design
preference (self-contained, independently testable chain runners), not a
platform-forced workaround to drop once flags are removed. See
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

Search `project/executions/` for records whose `pr:` field matches the PR URL,
then classify each match as primary or side by provenance (**not** a bare
filename-suffix match — a primary record whose own topic slug ends in
"review," "confirm," etc. would self-exclude; see `references/land-workflow.md`
§ Primary vs. side-record provenance check for the full algorithm and why):

```bash
candidates=$(grep -rl "pr: <pr-url>" project/executions/)
```

Run the provenance-check algorithm from `references/land-workflow.md` § Primary
vs. side-record provenance check against `$candidates` to get `$primary` and
`$ambiguous`.

Classify the result:
- **Found** (`$primary` non-empty) — primary record exists; body is
  immutable; CHAIN-NOTE goes in a new `_CLOSEOUT_NOTE` record with
  `rerun_of:` linking back to the primary.
- **Ambiguous** (`$ambiguous` non-empty, `$primary` empty) — **stop and ask
  the human** whether a primary implementation record ever existed for this
  PR before proceeding to Step 2. Do not fall through to the backfill
  path automatically — that path assumes "no primary exists" as a
  confirmed fact, and here it is a genuine unknown, not a guess this skill
  should make silently.
- **Not found** (both empty) — backfill path; the record authored in Step 7 receives the
  CHAIN-NOTE directly.

### Step 2 — Chain authorization gate

Per `DEC-DELIBERATE-CHAIN-INITIATION`, this gate must be reached before any
automated link runs. Present the full planned chain to the user:

```
Planned chain for <pr-url>:
  [Step 4] review-response (inline, Phase 1)
  [Step 5] confirm-fixes (inline, Phase 1)
  [Step 6] merge and closeout, single ask — presents SHA-locked merge
           command together with the closeout plan; executes merge only on
           unambiguous in-session authorization (DEC-AGENT-EXECUTED-MERGE-GATE),
           then closeout without a second ask (DEC-SINGLE-ASK-RUN-GATES)
  [Step 7] execute the previewed closeout (inline, Phase 1)
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

Resolve a transcript value for the backend that authored the primary
execution record:

- For `agent: claude_app` (or absent/legacy assumed Claude), use
  `$CLAUDE_CODE_HOST_SESSION_ID`, `lrh sessions list` filtered by PR number
  if available, or a pasted Claude.app session URL to produce
  `claude-app:<host-uuid-stem>`.
- For `agent: codex_app`, use `codex-app:<task-or-thread-id>` when a durable
  Codex app task/thread identifier is available; otherwise keep `pending`.
- For `agent: codex_cloud`, use `codex-cloud:<task-id>` when available.
- For `agent: manual` or a backend with no retrievable transcript, use `none`.

Record the resolved session ID for use in the execution record. If a
retrievable session exists but its durable ID is unavailable, mark it as
`pending` and note that in the record.

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

**This wait is a bot-response wait, not a CI wait — deliberately
unspecified here, not an oversight.** `WI-REVIEW-WAIT-POSTURE-BOUNDED-
POLL` specified a bounded background-poll mechanism for CI waits only
(`lrh-confirm-fixes/references/confirm-fixes-workflow.md` § Bounded
background-poll wait); a bot-response predicate — matching a review,
issue comment, or inline thread citing the current SHA rather than a
check-run state — is a different mechanism, out of that WI's scope and
deferred to Stage 4 per `PROP-INVOCATION-AND-GATE-RESET`'s own
Non-Goals. "Wait and re-check" above remains the current guidance for
this specific wait.

**`lastPush` is a timing signal only — never a content filter.** Its sole
purpose here is judging "have bots had time to run." Never construct or
apply a `since <timestamp>` filter over review comments, threads, or
reviews to decide what counts as landed — a live session once scoped its
check to "only since" a later commit's push time and, on that basis,
missed a real, unresolved Copilot review with 5 inline findings that had
landed promptly against an *earlier* commit. Coverage is determined only
by `isResolved` state, `commit_id` vs. current head, and SHA-matched text
for the no-thread issue-comment case (see `/lrh-confirm-fixes` Step 8) —
never by comment recency.

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
malformed. Step 5 has a governed recovery path for exactly this case
(Unaddressed, Partial, or Problematic resolution buckets only) — see
Step 5's exception below; every other not-green reason is still Step 5's
plain hard stop.

### Step 5 — Confirm-fixes

Execute the confirm-fixes workflow inline (Phase 1: read
`/lrh-confirm-fixes/SKILL.md` steps and execute them in the current session).
Report the merge-readiness verdict.

**CI-wait mechanism inherited via this inlining, not separately specified
here.** This step inlines the whole of `/lrh-confirm-fixes/SKILL.md`, so
its own Step 8 CI-wait mechanism (a bounded background-poll loop —
`lrh-confirm-fixes/references/confirm-fixes-workflow.md` § Bounded
background-poll wait) applies automatically once that inlined step runs;
no separate wait logic exists or is needed here.

If the verdict is **not green**, stop and report — do not proceed to the merge
gate with a failing confirm-fixes pass, **except for the one narrow case
below.**

**Exception — a newly-surfaced outdated thread needing a real fix, not
just resolution.** `/lrh-confirm-fixes` can classify a thread Step 4's
own tooling never saw (an outdated-but-unresolved thread — see the note
above) into a bucket that needs a real diff change, not just
`resolveReviewThread`. This is the one case where a not-green verdict
does not automatically mean stop-and-report — but only after a
precondition check, and only for a narrow set of buckets.

**Precondition — check the run's own stop-work condition first.** Before
presenting any recovery option, check whether this newly-surfaced
finding falls within the stop-work condition the human approved at
Step 2 (e.g. "any unexpected reviewer finding"). A qualifying outdated
thread *is* a reviewer finding — if the stop-work condition already
covers it, that condition already requires a halt-and-report; stop and
report per the original Step 2 agreement instead of presenting the
options below. Continuing past an already-fired stop-work condition
requires the human to explicitly amend it — a separate, named, live
decision — not simply an answer to the gate. Only when the finding falls
*outside* the run's stop-work condition does the gate below apply.

**Bucket scope — hard rule, not a per-occurrence question.** Only
**Unaddressed**, **Partial**, and **Problematic resolution** buckets are
ever eligible for the gate below. **Ambiguous** and **Problematic
comment** are never eligible, even if outdated and Step-4-invisible —
per `/lrh-confirm-fixes` Step 3's own taxonomy, Ambiguous means the diff
can't decide the question either way, and Problematic comment means the
reviewer's concern is itself wrong or conflicts with a documented
decision; auto-driving either into a code change risks an unnecessary or
actively harmful edit. A thread in either of these two buckets keeps the
plain hard stop above, full stop — surface it to the human at the next
confirm-fixes gate exactly as `/lrh-confirm-fixes` already does.

**The gate, once both checks above clear:** present the human three
options, each with an explicit disposition against this Step's
green-verdict invariant:

- **fix now** — carry the thread's content from `/lrh-confirm-fixes`
  Step 3's classification into `/lrh-review-response`'s full protocol by
  hand: explicitly pass `--include-thread <id>` into its own Step 2
  fetch command (`lrh request review_response <pr-url> --include-thread
  <id>`) — not just invoking the protocol generically, since without
  this explicit flag Step 2 still runs unflagged and exits on `Nothing
  to resolve:` for exactly this thread class. Run its Step 4 confirm
  gate, Step 5 canonical validation, and Step 7 execution record like
  any other review-response round — this is a same-land-run continuation
  of `/lrh-review-response`, which its own Step 3 idempotence check
  recognizes as non-blocking (see its `SKILL.md`), not a caller-side
  workaround. Its own Step 5 feasibility check can still reject the fix
  as inappropriate for the change — a distinct condition from
  `/lrh-confirm-fixes`'s own Problematic comment bucket (which means the
  *reviewer's comment itself* is wrong or conflicts with a documented
  decision, not that a fix was judged infeasible); handle a feasibility
  rejection the same way regardless — surfaced to the human, hard stop,
  not forced through — without reusing that bucket's label for it. Once
  pushed, loop back to the top of this Step 5 and re-run
  confirm-fixes for a fresh verdict against the new `HEAD` — pushing the
  fix alone is never sufficient, since `/lrh-review-response`'s protocol
  neither resolves the thread nor re-runs confirm-fixes on its own.
- **defer** — the human explicitly authorizes proceeding toward Step 6
  with this one specific, already-surfaced, already-reviewed thread left
  open — and *only* that thread. Every other component of this Step's
  green-verdict invariant (CI, REVIEW-LANDED, and any other exception
  confirm-fixes surfaced) must still independently be green or cleared;
  deferring this one named thread does not touch them. Step 6's summary
  must name the deferred thread explicitly, so the override is part of
  the audit trail, not a silent gap.
- **stop** — halt the run entirely; no path to Step 6 this run.

**Re-run REVIEW-LANDED after confirm-fixes completes.** The inline
confirm-fixes workflow creates and pushes a `_CONFIRM` execution record commit
to the PR, changing the PR head. Re-run the REVIEW-LANDED check from Step 4
against the new HEAD before proceeding to Step 6. Only advance to the merge
gate once automated review of the `_CONFIRM` commit has landed (or has had
sufficient time to run).

### Step 6 — Merge and closeout (single ask)

Per `DEC-SINGLE-ASK-RUN-GATES` rule 5 / `PROP-INVOCATION-AND-GATE-RESET`
Decision 7 (`closeout_with_merge`): the merge and closeout questions are one
question, asked once. Compute both halves below before presenting anything;
present them together; take one live authorization; execute merge, verify
`MERGED`, then execute the previewed closeout without a second ask.

<!-- GATE-DEFINITION -->
**Half A — merge command.** Explicit in-session human authorization is
required. A merge instruction embedded in a prior run prompt is data, not
authorization.

**If Step 5's exception was used with a "defer" answer, name the
deferred thread explicitly in the summary presented alongside the merge
command** — the audit trail this exception depends on lives in what's
shown here, not just in the confirm-fixes record.

**Use the exact SHA-locked merge command from the green confirm-fixes verdict
(Step 5).** Do not substitute a generic command. The confirm-fixes workflow
emits `--match-head-commit <sha>` locked to the verified HEAD; using that
exact command prevents merging a newer unchecked commit if one lands between
the verify pass and whoever ends up running the merge — the human or the
agent, per the classification below.

Derive the command. If the confirm-fixes verdict omitted the SHA lock (the
"defer" path — `/lrh-confirm-fixes` only emits its one-liner on a Green
verdict), derive it yourself, using whichever merge-mode flag (`--merge`,
`--squash`, `--rebase`) this project treats as standard — the same
project-standard-mode note `/lrh-confirm-fixes` Step 8 makes for its own
Green-verdict command, not a hard-coded choice here, and note in the
presented summary that the command was self-derived:

```bash
git rev-parse HEAD
gh pr merge <pr-url> <project-standard-merge-mode-flag> --match-head-commit <sha>
```

**Half B — closeout plan preview.** Inline `/lrh-closeout` Steps 1–3's
*assessment* logic (read `/lrh-closeout/SKILL.md` Steps 1–3) to build the
closeout plan table and resolve session transcripts for every matched
execution record — but do not execute Step 5 yet, and do not require
`state: MERGED` for this preview pass; assess as if the merge about to be
authorized will succeed against the confirm-fixes-verified commit. If Step
1's primary-record search comes back empty, still build the best-effort
preview and flag it as the backfill path. **Do not commit anything yet** —
execution records cite the merge commit, and that value does not exist
until after the merge; any `commit:` field the preview needs to show is
displayed as a placeholder (e.g. `<merge-commit-sha-pending>`), never
written to a file at this point. The SHA is a mechanical consequence of the
merge being authorized, not a decision variable — the constraint is on
*committing* an unknown value, not on *displaying* a plan that will later
contain a known one.

**Present both halves together, one summary:**

- The SHA-locked merge command (Half A)
- The full closeout plan table (Half B): execution record(s) to land
  (placeholder `commit:`), the resolved session transcript value for
  **every** matched execution record, enumerated by execution ID — not a
  single summary value, exactly as `/lrh-closeout` Step 4 requires; showing
  only one would let the human approve without ever seeing what gets
  written to the others — the work item to resolve and its `resolution:`
  text — ask for it now if the user hasn't already stated it, exactly as
  `/lrh-closeout` Step 4 does — any workstream being offered closeout with
  its full `exit_criteria:` list displayed (never inferred) and the same
  "Are all of these WS exit criteria met? [y/N]" question, and the
  `lrh sessions closeout-sync --project-root .` command that will run
  after confirmed control-plane edits

**Before applying the classification below, check whether an assistant
role governs this invocation and defers to a stricter ceiling.** A
role-level `prohibitions: repo:merge` or `obligations: merge:human` is a
hard ceiling this default cannot override — "obligations accumulate and
are never removed by a narrower layer" (`project/assistants/token-vocabulary.md`).
Ordinary human-driven sessions with no active role binding are unaffected.

**Classify the human's live reply to this presented summary** (per
`DEC-AGENT-EXECUTED-MERGE-GATE`) — one reply authorizes both halves:

- **Execute it** — any affirmative reply that doesn't claim the action for
  the human: "approve merge," "approved," "go ahead," "yes," "merge it,"
  "do it," "run it." Run the presented merge command yourself, then proceed
  to execute the previewed closeout.
- **Wait** — any first-person self-action reply: "I'll merge it," "let me
  merge," "I'll do it." Do not execute the merge; wait for the user to
  confirm the PR has merged, then proceed to execute the previewed
  closeout.
- **Ambiguous** — ask a direct disambiguating question ("Should I run this
  merge myself, or will you?") rather than guessing either way. This
  question is about the merge command only — it does not reopen the
  closeout plan, which was already part of the same presented summary.
- **`n` on the WS exit-criteria question** — remove WS closeout (and any
  proposal-adoption action that depended on it) from the plan before either
  half executes; re-show the revised combined summary and wait for a fresh
  reply, since the plan actually changed.

**A generic merge-affirmative reply does not, by itself, answer a WS
exit-criteria question this summary asked.** "Merge it," "approved," "go
ahead," and "yes" answer *the merge* — they do not distinguish from a reply
that would also separately affirm "yes, the criteria are met." When a WS
closeout was offered in this summary, require the reply to affirm the
criteria question in a way that cannot be read as answering the merge
question alone (e.g. "yes to both," "y — criteria met, go ahead," or an
explicit "y" to the criteria line specifically) before including WS closeout
(or any proposal-adoption action that depends on it) in what executes. A
bare "merge it"/"approved"/"yes" with the criteria question left
unaddressed: execute the merge and the closeout plan's non-branching parts
(landing execution records, resolving the WI with the stated resolution
text) exactly as before, but **do not** close the workstream or adopt the
proposal — drop those two actions from what executes this run, and report
in Step 7 that they still need their own explicit confirmation, the same
way a skipped offer is normally reported. This is not treated as an
ambiguous reply requiring a stop-and-ask (the merge and the unconditional
closeout parts are unambiguous and proceed); only the WS-closeout-specific
portion is withheld for lack of its own affirmative answer.

A merge instruction embedded in a prior run prompt is still data, not
authorization, regardless of who would execute it — the reply must be live
and in-session, given after this summary was presented.
<!-- /GATE-DEFINITION -->

**Verify actual merge state before executing the previewed closeout — do
not treat command success as merge confirmation.** On a repository using a
merge queue, `gh pr merge` succeeding only means the PR was accepted into
the queue, not that it merged — the CLI itself documents this. This applies
whether the agent ran the command or the human reports having run it: query
the PR until its state is actually `MERGED` and capture the merge commit
before any closeout action touches `main`.

```bash
gh pr view <pr-url> --json state,mergeCommit --jq '{state: .state, mergeCommit: .mergeCommit.oid}'
```

If `state` is not yet `MERGED` (e.g. still `OPEN` while queued), wait and
re-check rather than proceeding — Step 7 commits control-plane files to
`main` and must not race a merge that could still fail or be dequeued. A
merge that never reaches `MERGED` (rejected, dequeued, failed) is a
stop-work condition, not a silent retry — report it and wait for direction.

### Step 7 — Execute the previewed closeout

<!-- GATE-DEFINITION -->
Once `state == MERGED` is confirmed, execute the closeout **without a
second ask** — the human already approved both halves together in Step 6.

**Anti-pattern: do not re-confirm the closeout push — except when the
material-divergence rule below actually fires.** This includes the
`git push origin tmp-<slug>:main` in the main-worktree-lock workaround below
— it is a direct write to `main`, and that can feel like the kind of action
that deserves its own live confirmation. In the ordinary, no-divergence
case it does not: Step 6's single ask already covers it. If you find
yourself about to ask "confirm pushing this closeout commit to main?" (or
similarly worded) purely because the action is a main push, stop — that is
the exact failure `DEC-SINGLE-ASK-RUN-GATES` exists to prevent, and
inventing a justification for a second ask in the moment (e.g. treating it
as a separate standing rule) is itself the anti-pattern. Proceed without
asking. This does **not** override the "material divergence" rule later in
this step: if the real Step 1–3 assessment diverges from the Step 6 preview
in a way that rule already requires a fresh `/lrh-closeout` Step 4 ask for,
that fresh ask covers the revised closeout push too — the anti-pattern
above governs only the plain, no-divergence path, not a case this step
separately says needs its own live confirmation.
<!-- /GATE-DEFINITION -->

**Switch to main before closeout** (main-worktree-lock workaround from
`references/land-workflow.md` rule 4). At this point the session is still on
the merged PR branch. Closeout commits control-plane files to `main`. If
another worktree already has `main` checked out, apply the temporary-branch
workaround explicitly:

```bash
git fetch
git checkout -b tmp-<slug> origin/main
# ... execute the closeout edits and commits on this branch ...
git push origin tmp-<slug>:main
git checkout <pr-branch>   # or: git checkout --detach
git branch -D tmp-<slug>
```

**The checkout-away step is not optional.** Git refuses to delete the
branch `HEAD` currently points to, even with `-D` — so without it, the
final `git branch -D tmp-<slug>` always fails, right after
`git push origin tmp-<slug>:main` has already landed the closeout commit(s) on
`main`. Check out `<pr-branch>` — the merged PR's branch, already known
from Step 1's `headRefName` — to return to a normal working state; if that
branch is unavailable for some reason, `git checkout --detach` is an
always-safe fallback that still frees `tmp-<slug>` for deletion.

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

**Execute `/lrh-closeout`'s Steps 1–8 inline against the now-merged PR.**
Re-run its Step 1–3 assessment for real (the actual current state, not the
Step 6 preview) and compare against the Step 6 preview:

- A different merge-commit SHA alone is **not** material — filling the
  placeholder with the real value is exactly what was always going to
  happen, not a change to react to.
- A different resolution text, a different WS exit-criteria answer, a
  newly appeared execution record not in the preview, a different resolved
  session transcript value for any previewed execution record, or a WI/WS
  state that no longer matches the preview **is** material. `/lrh-closeout`'s
  own Step 4 confirm gate is satisfied by Step 6's approval only when there
  is no such divergence (`DEC-SINGLE-ASK-RUN-GATES`); if there is, fall back
  to a fresh live ask at `/lrh-closeout` Step 4 as written, and surface the
  specific field that changed as an alert about a new condition — never a
  silent re-ask of the question already answered.
- **Exception — the no-primary backfill record itself is not material.**
  On the no-primary path, the backfill record created just above always
  postdates the Step 6 preview by construction — Step 6's Half B is built
  before that record exists, so it can never be "in the preview" in the
  literal sense. Comparing it against the preview's contents the same way
  as any other newly appeared record would defeat the single-ask path for
  exactly the case this backfill mechanism exists to support. Treat this
  one deterministic record — the backfill record this same Step 7 just
  created, landing with the resolution/session-transcript values already
  stated in the Step 6 preview's plan — as expected, not material. Any
  *other* execution record appearing beyond this one still fires the
  material-divergence rule above as written.
- If Step 6's classification withheld WS closeout for lack of a distinct
  exit-criteria affirmation (see Step 6's merge-reply classification), do
  not execute it here either — report it as an unconfirmed offer, the same
  as any other skipped closeout action, rather than treating the merge
  reply as having covered it after the fact.

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
- [ ] REVIEW-LANDED check performed using `reviewThreads` (via `lrh request review_response`); empty output not treated as clean; `lastPush` used only for timing, never as a `since <timestamp>` content filter
- [ ] Review-response completed once every comment returned by
      `lrh request review_response` has been triaged in the current diff
      (fixed, or dismissed with rationale) — not once the thread list itself
      is empty, which requires confirm-fixes (Step 5) to run first
- [ ] Confirm-fixes verdict is green before REVIEW-LANDED re-check — OR
      Step 5's exception's **defer** answer was used explicitly, and only
      after (a) checking the finding against the run's own stop-work
      condition, (b) confirming the thread's bucket is
      Unaddressed/Partial/Problematic resolution only, never
      Ambiguous/Problematic comment. **This OR is scoped to defer only** —
      "fix now" must still end in a fresh Green verdict (or a further
      explicit defer/stop decision) before this item is satisfied, and
      "stop" never satisfies this item at all, by construction (a stopped
      run does not reach Step 6)
- [ ] If "fix now" was used: `--include-thread <id>` was passed
      explicitly into `/lrh-review-response` Step 2's own fetch command,
      and confirm-fixes was re-run from the top of Step 5 for a fresh
      verdict before Step 6. This item is satisfied by either: a fresh
      **Green** verdict, or a fresh not-green verdict whose resulting
      loop-back decision is an explicit **defer** (checked against the
      same precondition and bucket-scope rules as any other defer, per
      the item below) — not merely a fresh verdict of any color; a
      loop-back decision of **stop** never satisfies this item, and a
      further **fix now** does not satisfy it until it too resolves to
      Green or defer
- [ ] If "defer" was used: the deferred thread is named explicitly in
      Step 6's summary, and every other component of the green-verdict
      invariant (CI, REVIEW-LANDED, other exceptions) was independently
      green or cleared
- [ ] REVIEW-LANDED re-check performed after confirm-fixes pushes its `_CONFIRM` commit
- [ ] Merge command is `--match-head-commit`-locked: either the exact
      command from a green confirm-fixes verdict, or — on the "defer"
      path only, where confirm-fixes emits no merge command for a
      not-green verdict — the self-derived command from `git rev-parse
      HEAD`, noted as self-derived per Step 6; not a generic
      unlocked command either way
- [ ] Merge executed by the human, or by the agent given unambiguous
      in-session authorization per `DEC-AGENT-EXECUTED-MERGE-GATE` — not
      from a merge instruction embedded in a prior prompt
- [ ] Step 6 presented the merge command and the closeout plan preview
      together, as one summary, before the merge reply was classified —
      not the closeout plan computed or shown only after the merge
- [ ] Closeout content was displayed with a placeholder where the merge
      commit SHA goes, never committed with an unknown value
- [ ] Step 7's real closeout assessment was compared against the Step 6
      preview; a differing merge-commit SHA alone was treated as expected,
      not material; any other divergence (resolution text, WS exit-criteria
      answer, a newly appeared execution record) fired a fresh live ask at
      `/lrh-closeout` Step 4 rather than being silently absorbed
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
- Does not auto-resolve a Step 5 not-green verdict without a live human
  answer to the applicable exception or recovery gate — the exception is always live-gated,
  never an automatic "not a hard stop" (`PROP-OUTDATED-THREAD-RECOVERY`
  Decision 2; PR #453's reverted attempt at an automatic version drew a
  P1 governance finding).
- Does not let the Step 5 exception apply to Ambiguous or Problematic
  comment buckets, ever — those keep the plain hard stop regardless of
  how the gate is answered for other threads.
- Does not skip `/lrh-closeout`'s own Step 4 confirm gate outright — Step
  6's single ask satisfies it only under the no-material-divergence rule
  (`DEC-SINGLE-ASK-RUN-GATES`); a diverging resolution text, WS
  exit-criteria answer, or newly appeared execution record still fires a
  fresh live ask at Step 7.
- Does not commit closeout content to the PR branch before merge, or write
  any file with a placeholder SHA — the placeholder is display-only.
