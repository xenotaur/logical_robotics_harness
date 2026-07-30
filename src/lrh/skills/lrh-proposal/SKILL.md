---
name: lrh-proposal
description: >
  Create a new LRH design proposal at project/design/proposals/proposed/<slug>/00_proposal.md.
  Use when the user wants to capture a design decision, architecture choice, or feature direction
  as a formal proposal artifact. Interviews the user, researches existing proposals, proposes
  complete frontmatter and body sections, and writes the file only after explicit confirmation.
  Validates with lrh validate.
when_to_use: >
  Invoke only when explicitly creating a new LRH design proposal planning
  artifact in project/design/proposals/proposed/. Do not invoke when the
  user is discussing, reading, or querying proposals. Suitable for
  orchestration from /lrh-design when it needs to create a companion
  proposal as part of a design-capture workflow.
argument-hint: [slug]
---

# lrh-proposal Skill

This skill creates a new LRH design proposal at
`project/design/proposals/proposed/<slug>/00_proposal.md`
following the LRH proposal schema and body conventions. It interviews the
user, researches related design context, proposes a complete proposal for
review, and writes the file only after explicit confirmation. All output is
shown to the user before any files are written.

---

## Inputs

The user provides a slug as the argument:

```
/lrh-proposal lrh-doc-skills
```

The slug becomes the proposal-set directory name and informs the `id:` field.
If not provided, ask for one before proceeding. Use lowercase-kebab-case.

---

## Reference Knowledge

Load these before running any step:

1. **`references/proposal-schema.md`** — Full YAML frontmatter field reference:
   required fields, valid status values, `implementation_status` vocabulary,
   and optional traceability fields (`implemented_by`, `supersedes`,
   `superseded_by`, `evidence`). Read this to produce valid frontmatter.

2. **`references/proposal-body-guide.md`** — Section-by-section authoring
   guide for the proposal body: what goes in Summary, Background/Motivation,
   Prior Art Check, Design Decisions, Non-Goals, Implementation Plan, and
   cross-references. Read this to produce a body that follows LRH proposal
   conventions.

3. **`references/prior-art-check.md`** — Prior art / build-vs-buy check
   procedure (duplication search + demand search). Run this during Step 3
   (research) and record both verdicts in the `## Prior Art Check` body
   section before drafting Design Decisions.

4. **`references/execution-record.md`** — `lrh prompt label` and
   `lrh prompt check-execution` command syntax, execution record field
   descriptions (`agent`, `instruction_source`, `session_transcript`). Read
   before Step 4 (instruction phase) and Step 10 (execution record).

---

## Execution Steps

Work through these steps in order. Do not skip the confirmation gate (Step 5).

### 1. Check for existing proposal

Search for a file matching the slug under `project/design/proposals/`:

```bash
find project/design/proposals/ -name "00_proposal.md" -path "*<slug>*"
```

Also check for an `id:` conflict in existing proposals:

```bash
grep -r "^id: " project/design/proposals/ | grep -i "<slug>"
```

If found:
- Report the file path and its current `status` and `implementation_status`.
- Ask whether to overwrite, extend, or abort.
- Do not silently overwrite existing work.

### 2. Interview

Ask all questions at once to avoid multiple round-trips. Collect all
answers before proposing anything.

1. **Proposal title and summary:**
   - **Title:** A short one-line title for the `title:` frontmatter field.
   - **Summary:** What design decision, architecture choice, or feature
     direction does this proposal address? One to two sentences suitable
     for the `## Summary` section.

2. **Background / motivation:** What problem or gap motivates this proposal?
   What context does a reader need to evaluate the design? Reference any
   related workstreams, design docs, or prior proposals.

3. **Design decision(s):** What is being decided? List the key options that
   were considered and which option was chosen. This becomes the
   `## Design Decisions` section.

4. **Non-goals:** What is explicitly out of scope? What should a reader not
   assume this proposal addresses?

5. **Implementation scope:** How big is the resulting implementation?
   - One PR worth of work → suggest `/lrh-work-item`
   - Multiple PRs, novel decisions, or uncertain scope → suggest
     `/lrh-workstream` ± `/lrh-work-item`
   - Complex multi-stage → suggest `/lrh-workstream` first, work items later
   This informs the `## Implementation Plan` section and Step 11 follow-on offer.

6. **Related design docs:** Any existing workstream files, design docs, or
   prior proposals that this proposal relates to? Used for `related_design:`.

### 3. Research the project

Before proposing, read:

- `project/design/proposals/README.md` — to understand ID conventions
  (`PROP-*`), lifecycle vocabulary, and proposal-set structure.
- A few similar existing proposals (from `project/design/proposals/`) — to
  follow naming, depth, and cross-reference conventions established in this
  project.
- The related workstream file (if identified) — to understand the broader
  delivery context.

Then propose the complete proposal: frontmatter (all fields) and body
(all required sections with content). Show it to the user before writing.

### 4. Instruction phase (mint prompt ID + idempotence check)

**Before minting, search for an existing record by stable slug — the
current checkout and any open PRs.** `lrh prompt label` always mints a
fresh timestamped prompt ID, so `check-execution` alone cannot detect a
rerun — the ID it receives is brand new every time it's called. Derive
`<SLUG_UPPER_UNDERSCORE>` from `<slug>` by replacing `-` with `_` and
uppercasing (e.g. `lrh-doc-skills` → `LRH_DOC_SKILLS`), then match the
complete trailing filename segment — not a bare substring, which would
also match an unrelated longer slug that happens to contain this one
(e.g. `..._LRH_DOC_SKILLS_REVIEW.md`):

```bash
find project/executions/AD_HOC/ -name "*_<SLUG_UPPER_UNDERSCORE>.md" 2>/dev/null | sort
```

`AD_HOC/` may not exist yet in a freshly bootstrapped project — no record
has been written there yet — so a nonzero exit with no output here means
no prior record, not a failure; do not treat it as one. `sort` here is for
deterministic *ordering*, not chronological correctness — see below for
why filename order alone can't be trusted to mean "most recent."

This only searches the current checkout. A prior record can exist on a
branch not fetched locally yet — e.g. an earlier attempt still open as its
own PR, possibly from a fork. Fetch and check open PRs by number using
GitHub's `refs/pull/<N>/head` — a ref the base repository always exposes
for every open PR regardless of whether the head branch lives in this
repo or a fork, so this works even when `origin/<branch>` would not exist
or would silently resolve to the wrong commit. Force the fetch (`+refs/...`)
so a previously-scanned PR that was later force-pushed still updates the
local ref instead of silently keeping the stale one. Request every open
PR, not just the CLI's default first page (`--limit`), so an older PR
isn't silently omitted in a repo with many open PRs.

Exclude any remote match that this PR didn't actually introduce — a
bare-path match in the current checkout, or a file already present at
this PR's own merge-base with its declared base ref, is inherited, not
new. The merge-base check specifically covers stacked PRs (PR B branched
from still-open PR A): without it, both A's and B's pull refs contain the
same file, and picking the "most recent" match by sort order could pick
B — which only inherited the record — over A, which actually introduced
it:

```bash
LOCAL_MATCHES=$(find project/executions/AD_HOC/ -name "*_<SLUG_UPPER_UNDERSCORE>.md" 2>/dev/null)
{
  echo "$LOCAL_MATCHES"
  gh pr list --state open --limit 1000 --json number,baseRefName \
    --jq '.[] | "\(.number)\t\(.baseRefName)"' | while IFS=$'\t' read -r pr base; do
    git fetch origin "+refs/pull/$pr/head:refs/remotes/pr/$pr" --quiet 2>/dev/null
    git fetch origin "$base" --quiet 2>/dev/null
    merge_base=$(git merge-base "refs/remotes/pr/$pr" "origin/$base" 2>/dev/null)
    git ls-tree -r "refs/remotes/pr/$pr" --name-only -- project/executions/AD_HOC/ 2>/dev/null \
      | grep -i "_<SLUG_UPPER_UNDERSCORE>\.md\$" \
      | grep -vxFf <(echo "$LOCAL_MATCHES") \
      | while read -r path; do
          if [ -n "$merge_base" ] && git cat-file -e "$merge_base:$path" 2>/dev/null; then
            continue
          fi
          printf '%s\tPR#%s\n' "$path" "$pr"
        done
  done
} | sort
```

If the base-ref fetch or merge-base lookup fails (e.g. a fork base this
session can't reach), the match is kept rather than silently dropped —
failing to *prove* a match is inherited is not the same as proving it
isn't.

Each line is either a bare path (a match already in the current checkout)
or `<path><TAB>PR#<N>` (a match found only on an open PR, fetched above
into the local `refs/remotes/pr/<N>` ref). If there is more than one
match, **do not** assume the filename that sorts last is the most
recent — execution-record timestamps embed the creating machine's *local*
time, not UTC (see `project/design/backlog.md`'s "Execution-record
filename timestamps use local time, not UTC"), so filename order can be
wrong across machines in different timezones. Instead, read every
surviving match's `created_at:` frontmatter field (for a bare path, read
the file directly; for a `<path><TAB>PR#<N>` match, read it without
checking out via `git show "refs/remotes/pr/$N:$path"`), normalize each to
an absolute instant before comparing — e.g.
`python3 -c "import datetime,sys; print(datetime.datetime.fromisoformat(sys.argv[1]).timestamp())" "$created_at"`
for a comparable epoch value (portable across GNU/BSD; `date -d` is
GNU-only and fails on macOS) — since the raw ISO8601 strings carry their
own UTC offsets and don't sort correctly as plain text either — and base
the decision below only on the one with the truly latest timestamp; older
matches are historical context, not separately actionable. (Recency, not
asking the user to disambiguate, resolves multiple matches
deterministically.)

Having identified that match, read its `status:` frontmatter field
(already fetched above) before deciding. Per
`PROMPTS.md`'s status-handling rule (`DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT`),
a matched filename is discovery, not by itself a block:
- `in_progress` or `landed`: **stop and report** — do not continue unless
  the user explicitly asks for a rerun. If they do, see Step 6 for how to
  resume the match's branch (`<username>/<type>/<slug>`) whether it's
  local, remote-only, or gone. Either way, keep the match's
  `execution_id` to pass as `--rerun-of` in Step 10.
- `failed`, `reverted`, or `superseded`: not a blocking prior run —
  summarize it and continue, but keep its `execution_id` to pass as
  `--rerun-of` in Step 10 (per `PROMPTS.md:136`, a rerun must link back to
  the prior attempt it supersedes).
- unknown or ambiguous status: **stop and report** the ambiguity.

Then mint the prompt ID and run the secondary check (see
`references/execution-record.md` for full syntax):

```bash
lrh prompt label --slug <slug>
lrh prompt check-execution --prompt-id "<id>" --project-root .
```

`<PROP-ID>` (the `id:` value decided in Step 2, `PROP-<SLUG-UPPER>`) is not
passed to `--work-item` here — this record documents the proposal's
*creation*, so it stays in the `AD_HOC` bucket (the `lrh prompt label`
default). See `references/execution-record.md`.

If `check-execution` reports a `landed` or `in_progress` record, **stop and
report** — do not continue unless the user explicitly asks for a rerun.

### 5. User confirms

Show the user the complete proposed proposal — frontmatter and full body —
in a readable block.

Wait for explicit confirmation before writing any files.

If the user redirects or declines, adjust the proposal and show it again.
Do not skip this gate — it prevents incorrectly-scoped proposals from
being committed to the control plane.

### 6. Create branch from main

If Step 4 found a blocked match and the user asked for a rerun, resume its
branch rather than creating a duplicate. Check local first, then the
remote — the common case is that the branch only exists as
`origin/<branch-name>` (the match came from the cross-PR search, not the
current checkout), not locally yet:

This same check covers the no-prior-match case too — if the branch exists
nowhere (no rerun, or the match's branch was already cleaned up), the
`else` clause creates it fresh from `main`, same as always.

If the match came from the cross-PR search (tagged `PR#<N>` in Step 4),
check whether it's a fork PR before assuming reuse is possible:
`gh pr view <N> --json isCrossRepository`. A fork PR's branch lives in a
repository you don't have push access to — stop and ask the user how to
proceed (e.g. they push further commits themselves, or this becomes a
fresh attempt) rather than silently trying to continue it. Otherwise (the
normal same-repo case), get the branch name (`gh pr view <N> --json
headRefName`) and reuse it as below:

```bash
if git rev-parse --verify <branch-name> >/dev/null 2>&1; then
  git checkout <branch-name>
  git pull
elif git ls-remote --exit-code --heads origin <branch-name> >/dev/null 2>&1; then
  git fetch origin <branch-name>
  git checkout -b <branch-name> --track "origin/<branch-name>"
else
  git checkout main && git pull
  git checkout -b <branch-name>
fi
```

Branch naming: `<username>/<type>/<slug>`. Get the username:

```bash
gh api user --jq .login
```

Proposals are documentation artifacts; use `feat` as the branch type:

```
xenotaur/feat/lrh-doc-skills
```

### 7. Write files

Re-check that the proposal directory does not already exist on the freshly
pulled main — the Step 1 check may be stale if main advanced since the
session started:

```bash
find project/design/proposals/ -name "00_proposal.md" -path "*<slug>*"
```

If found, stop and report — ask the user to overwrite, extend, or abort
before proceeding.

Create the directory and file:

```
project/design/proposals/proposed/<slug>/00_proposal.md
```

Set `status: proposed`, `implementation_status: not_started`.
The `project/design/proposals/proposed/` directory already exists; do not
recreate it. Create only the `<slug>/` subdirectory and `00_proposal.md`.

### 8. Validate

Run:

```bash
lrh validate
```

Fix any errors before proceeding. Common failures: missing required field
(`id`, `status`, `type`), `status` bucket mismatch (`status: proposed` file
must be under `proposed/`), `type: design_proposal` missing or misspelled.

### 9. Commit and open PR

```bash
git add project/design/proposals/proposed/<slug>/
git commit -m "Add design proposal <PROP-ID>: <title>"
git push -u origin <branch-name>
gh pr create --title "Add design proposal <PROP-ID>: <title>" --body "..."
```

Include in the PR body: the proposal summary, status, `id`, and the prompt
ID minted in Step 4 — it is the traceability link between the PR and the
execution record.

### 10. Create execution record

```bash
lrh prompt record-execution \
  --prompt-id "<id>" \
  --work-item AD_HOC \
  --slug <slug> \
  --status in_progress \
  --project-root .
```

If Step 4 found a prior matching record — whether summarized
(`failed`/`reverted`/`superseded`) or explicitly overridden by the user
(`in_progress`/`landed`) — add `--rerun-of <its-execution_id>` to the
command above so the new record links back to it, per `PROMPTS.md:136`.

Use `AD_HOC`, not `<PROP-ID>` — see the note in Step 4. This creates the
record under `project/executions/AD_HOC/`, not `project/executions/<PROP-ID>/`.

Immediately edit the generated file to populate the three optional fields
(see `references/execution-record.md`):

```yaml
agent: claude_app
instruction_source: project/design/proposals/proposed/<slug>/00_proposal.md
session_transcript: pending
```

Then replace the generated `TODO` placeholders in `# Summary`, `# Result`,
`# Validation`, and `# Follow-up` with real content grounded in what this
run actually did (per `AGENTS.md`'s evidence policy) — `/lrh-closeout` later
only touches frontmatter, so an unedited TODO body would ship as `landed`
with no narrative evidence.

Commit the execution record and push it as an additional commit to the
already-open PR.

### 11. Offer follow-on and report

**Follow-on artifacts (offer, not automatic):**

Based on the implementation scope assessed in Step 2, offer the user the
appropriate next step:

- **Small scope (one PR):** offer to invoke `/lrh-work-item` to create a
  companion work item.
- **Medium scope (multiple PRs):** check whether `/lrh-workstream` is listed
  in `CLAUDE.md ## Skills`. If it is, offer to invoke it followed by
  `/lrh-work-item` for each immediate task. If it is not yet available,
  direct the user to create a workstream manually at
  `project/workstreams/proposed/<WS-ID>.md` following the workstream schema,
  then offer `/lrh-work-item` for each immediate task.
- **Large scope (multi-stage):** check whether `/lrh-workstream` is listed
  in `CLAUDE.md ## Skills`. If it is, offer to invoke it first; defer
  individual work items until workstream scope is defined. If it is not yet
  available, direct the user to the manual workstream path and defer work
  items.

Do not automatically invoke any skill — offer and wait for the user to confirm.

**Report to the user:**

- The file created and its path.
- The `lrh validate` outcome.
- The PR URL.
- The minted prompt ID and execution record path.
- Which fields were inferred vs. directly from user answers.
- Suggested next steps per the scope assessment above.
- A reminder that `session_transcript: pending` in the execution record
  should be updated to `claude-app:<host-uuid-stem>` after the session ends.
- Next steps for the PR itself: run `/lrh-review-response <pr-url>` to
  address reviewer comments (repeat as needed), then
  `/lrh-confirm-fixes <pr-url>` to verify the fixes against the current diff
  and resolve the review threads before merge. After merging, run
  `/lrh-closeout <pr-url>` to land this skill's execution record — and any
  additional `_REVIEW`/`_CONFIRM` records the review rounds created — and to
  update the record's status to `landed`.

---

## Quality Checklist

Before reporting completion, verify:

- [ ] Prompt ID minted (Step 4) before the confirm gate (Step 5)
- [ ] Idempotence check passed (no prior landed/in_progress record)
- [ ] Branch created from a fresh `git pull` of main
- [ ] `project/design/proposals/proposed/<slug>/00_proposal.md` exists
- [ ] `id`, `type: design_proposal`, `title`, `status`, `implementation_status`
      all present in frontmatter
- [ ] `status: proposed` and file is in `proposed/` directory bucket
- [ ] `implementation_status: not_started`
- [ ] Body contains all required sections: Summary, Background/Motivation,
      Design Decisions, Non-Goals, Implementation Plan
- [ ] `lrh validate` reports 0 errors
- [ ] The confirm-before-write gate (Step 5) was honoured
- [ ] PR opened and URL reported to the user
- [ ] Execution record exists under `project/executions/AD_HOC/` (not
      `<PROP-ID>/` — see Step 4) with `agent`, `instruction_source`,
      `session_transcript` populated, and `# Summary`/`# Result`/
      `# Validation`/`# Follow-up` filled in with real content, not TODOs
- [ ] Execution record was pushed to the open PR

---

## What This Skill Does Not Do

- Does not create work items or workstreams — use `/lrh-work-item` or
  `/lrh-workstream` for those.
- Does not adopt or supersede proposals — status changes are human decisions.
- Does not implement the design — the skill creates the planning artifact only.
- Does not create sub-proposals or appendices (`01_*.md`) — the umbrella
  `00_proposal.md` only; sub-proposals are added manually or in follow-on work.
- Does not update `project/design/design.md` or `architecture.md` — those
  edits follow adoption and are separate tasks.
- Does not land the execution record it creates for this PR, or mark it
  `landed` — that happens at `/lrh-closeout` after the PR merges.
