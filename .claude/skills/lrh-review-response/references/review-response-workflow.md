# lrh-review-response Workflow Context

Where `/lrh-review-response` sits in the LRH lifecycle, how execution records
link to originals, and how to handle edge cases. Read this before Step 7
(create execution record and report).

---

## Lifecycle placement

```
/lrh-implement WI-<ID>              ← opens the PR
    │
    ▼
PR review (Codex, Copilot, human)   ← reviewers post comments
    │
    ▼
/lrh-review-response <pr-url>       ← THIS SKILL
    │  Fetches comments via lrh request review_response
    │  Triages, fixes, validates, pushes to open PR
    │  Creates AD_HOC execution record with rerun_of link
    │
    ▼
(repeat if further review rounds)
    │
    ▼
/lrh-confirm-fixes <pr-url>         ← fresh-eyes verification against the
    │  current diff (never against this skill's report); resolves threads
    │  the diff plainly satisfies; surfaces exceptions; ends at a
    │  merge-readiness verdict + gh pr merge one-liner
    │
    ▼
Merge PR (human, or agent given         ← update records to landed, resolve WI
  unambiguous authorization) + closeout
```

---

## Execution record convention for review responses

Review response executions use `AD_HOC` as the work item bucket (not the
original `WI-*` ID). This keeps the work item's execution directory clean —
one primary execution entry — while the `rerun_of` field links the review
response record to a prior one.

**`rerun_of` population — two candidate targets, in precedence order:**

1. **A prior review-response record found at Step 3.** Step 3's own
   idempotence search (trailing-segment match against `-review`-suffixed
   slugs in `project/executions/AD_HOC/`) already looks for an existing
   review-response record on this branch before minting. If it found one
   — blocking (`in_progress`/`landed`, with an explicit user-confirmed
   rerun) or summarized (`failed`/`reverted`/`superseded`) — use its
   `execution_id` here. This takes precedence: it's the more specific,
   immediate lineage (this exact invocation's own prior attempt).
2. **The primary implementation record, only if Step 3 found nothing.**
   Convert the branch slug (without the `-review` suffix) to
   upper-underscore form (`UPPER_SLUG`), then verify whether a genuine
   primary record with exactly that slug exists — not a bare
   filename-suffix exclusion (misclassifies a primary record whose own
   slug happens to end in "review," e.g. `WI-SKILLS-LRH-SELF-REVIEW`'s own
   `execution_id` ends in `_SELF_REVIEW`) and not a uniform
   substring/trailing-exact glob applied to every candidate alike (both
   were tried in this project's own history and both broke — a bare
   substring glob can match an unrelated longer slug; a trailing-exact
   glob structurally excludes a genuine sibling whenever `UPPER_SLUG`
   itself ends in a reserved suffix, since the sibling's slug is always
   `UPPER_SLUG` plus more). See
   `/lrh-land/references/land-workflow.md` § A separate, narrower
   algorithm for the two slug-based `rerun_of` searches for the full
   algorithm and why the two simpler attempts each failed:

   ```bash
   UPPER_SLUG=$(echo "<branch-slug>" | tr '-' '_' | tr '[:lower:]' '[:upper:]')
   ```

   Run the target-verification algorithm from that section against
   `UPPER_SLUG` to get `$primary`.

   Example: branch `xenotaur/feat/wi-skills-lrh-review-response` →
   slug `wi-skills-lrh-review-response` → `UPPER_SLUG=WI_SKILLS_LRH_REVIEW_RESPONSE`.
   The algorithm gathers candidates broadly (a substring glob, so a
   genuine sibling is never excluded from the evidence pool even when
   `UPPER_SLUG` itself ends in a reserved word), but only ever classifies
   the one candidate whose slug exactly equals `UPPER_SLUG` — an unrelated
   longer-slug candidate pulled in by the broad glob can only ever serve
   as sibling evidence, never become `$primary` itself.

   If found, set:

   ```yaml
   rerun_of: <execution_id-from-the-original-record>
   ```

If neither yields a match (PR created outside `/lrh-implement`, or the
record is in a non-standard location), leave `rerun_of:` empty and note
this in the execution record body.

**Slug derivation for the review response prompt ID:**

Strip `<username>/<type>/` from the current branch name, then append
`-review`:

```
xenotaur/feat/wi-skills-lrh-setup → wi-skills-lrh-setup-review
xenotaur/chore/update-readme       → update-readme-review
```

**The slug is always this one form — do not mint a variant like
`-review-r2` for a second round.** For a second review round on the same
branch, Step 3's own idempotence search surfaces the first review-response
record by this same slug. If its status blocks (`in_progress`/`landed`),
stop and report unless the user explicitly asks for a rerun; if they do,
continue with the *same* slug and link `rerun_of` to that matched record
(precedence 1 above) — do not mint a differently-named slug to route
around the block.

---

## Edge cases

### No open comments

`lrh request review_response` outputs `Nothing to resolve: no unresolved
review threads found for <repo>#<N>` when there are no open comments. The
skill detects this at Step 2 and exits cleanly without touching any files or
minting a prompt ID.

### Closed or merged PR

Detected at Step 1 via `gh pr view --json state`. If `state` is not `OPEN`,
stop immediately — a merged PR cannot receive new commits, and a closed PR
may no longer be the right target.

### Comment conflicts with an intentional design decision

The embedded triage protocol handles this via the Validity check. When a
comment conflicts with a documented design decision (e.g., a Non-Goal in the
work item, a decision in the governing proposal, or a trade-off discussed in
the session), record it as "skipped — intentional design decision" with a
brief explanation. This gives reviewers a clear audit trail without silently
ignoring the comment.

The user may also pre-emptively direct specific skips at the Step 4 confirm
gate ("skip comment X, that's intentional"). Record these as "skipped — user
directive."

### Invoked in a fresh session (without design context)

The skill works mechanically in any session, but design-decision triage
benefits from context about why things were built a certain way. If invoked
in a fresh session:

1. Read the governing work item (`project/work_items/`) and any referenced
   design proposals before triaging.
2. If a comment's validity is ambiguous without design context, surface the
   ambiguity to the user before skipping or fixing — do not guess.

---

## After all review rounds land

Once the PR is merged:

1. Update each review response execution record: set `status: landed`,
   populate `pr:` and `commit:` with the merge metadata.
2. Update the primary execution record (the one from `/lrh-implement`) the
   same way.
3. Move the work item to `project/work_items/resolved/` with
   `status: resolved` and a non-null `resolution` value.
4. Run `lrh validate` after all edits.
