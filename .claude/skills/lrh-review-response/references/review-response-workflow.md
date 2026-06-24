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
Merge PR + closeout (human)         ← update records to landed, resolve WI
```

---

## Execution record convention for review responses

Review response executions use `AD_HOC` as the work item bucket (not the
original `WI-*` ID). This keeps the work item's execution directory clean —
one primary execution entry — while the `rerun_of` field links the review
response back to the original.

**`rerun_of` population:**

Search for the original execution ID. Convert the branch slug (without the
`-review` suffix) to upper-underscore form before searching:

```bash
UPPER_SLUG=$(echo "<branch-slug>" | tr '-' '_' | tr '[:lower:]' '[:upper:]')
find project/executions/ -name "*${UPPER_SLUG}*.md" | grep -v "_REVIEW"
```

Example: branch `xenotaur/feat/wi-skills-lrh-review-response` →
slug `wi-skills-lrh-review-response` → `UPPER_SLUG=WI_SKILLS_LRH_REVIEW_RESPONSE` →
search for `*WI_SKILLS_LRH_REVIEW_RESPONSE*.md`, exclude files containing
`_REVIEW`.

If the original record is found, set:

```yaml
rerun_of: <execution_id-from-the-original-record>
```

If not found (PR was created outside `/lrh-implement`, or the record is in a
non-standard location), leave `rerun_of:` empty and note this in the
execution record body.

**Slug derivation for the review response prompt ID:**

Strip `<username>/<type>/` from the current branch name, then append
`-review`:

```
xenotaur/feat/wi-skills-lrh-setup → wi-skills-lrh-setup-review
xenotaur/chore/update-readme       → update-readme-review
```

For a second review round on the same branch, the idempotence check
(`lrh prompt check-execution`) will surface the first review response record.
Stop and report; the user can request a rerun explicitly, which will create a
new slug (e.g., `wi-skills-lrh-setup-review-r2` if supplied manually).

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
