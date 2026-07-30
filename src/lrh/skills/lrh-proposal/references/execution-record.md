# Execution Record Reference

Practical facts from `PROP-LRH-EXECUTION-SESSIONS` needed when running
`/lrh-proposal`. Read this before Step 4 (instruction phase) and Step 10
(execution record).

Creating a proposal is itself a planning action worth recording: without
an execution record for the PR that files the proposal, later `_REVIEW`/
`_CONFIRM` records created by `/lrh-review-response` and `/lrh-confirm-fixes`
against that PR have no primary record to set `rerun_of` against, and
`/lrh-closeout` has to reconstruct one by hand.

**Bucket this record under `AD_HOC`, not the new proposal's own `PROP-*`
ID.** `/lrh-closeout`'s Step 2.3 looks up a work item by the execution
record's `work_item:` bucket (`find project/work_items/ -name
"<work_item>.md"`). A `PROP-*` bucket won't match any work item file, so
closeout would surface a spurious "not found — how do you want to proceed?"
prompt on every closeout of this PR. `AD_HOC` is the bucket the decision
matrix explicitly recognizes as "no WI to resolve" — see
`project/executions/README.md` and
`.claude/skills/lrh-closeout/references/closeout-workflow.md`.

---

## Mint a prompt ID

```bash
lrh prompt label --slug <slug>
```

`<slug>` is the same lowercase-kebab slug given as this skill's argument.
Omit `--work-item` — it defaults to `AD_HOC`. `<PROP-ID>` (the `id:` value
decided in Step 2, conventionally `PROP-<SLUG-UPPER>`, e.g. slug
`lrh-doc-skills` → `PROP-LRH-DOC-SKILLS`) is not passed here.

The command outputs a `prompt_id` in the form:

```
PROMPT(AD_HOC:<SLUG_UPPER_UNDERSCORE>)[<ISO8601-TIMESTAMP>]
```

## Check for prior execution

Search by stable slug *before* minting, across the current checkout and
open PRs — `lrh prompt label` always mints a fresh timestamped ID, so
`check-execution` alone cannot catch a rerun. Derive
`<SLUG_UPPER_UNDERSCORE>` from `<slug>` by replacing `-` with `_` and
uppercasing, then match the complete trailing filename segment — not a bare
substring, which would also match an unrelated longer slug that happens to
contain this one:

```bash
find project/executions/AD_HOC/ -name "*_<SLUG_UPPER_UNDERSCORE>.md" 2>/dev/null | sort
```

`AD_HOC/` may not exist yet in a freshly bootstrapped project — a nonzero
exit with no output here means no prior record, not a failure. `sort`
makes multiple matches deterministic (timestamp-prefixed filenames sort
chronologically). This only searches the current checkout — also check
open PRs:

```bash
gh pr list --state open --json headRefName --jq '.[].headRefName' | while read -r branch; do
  git ls-tree -r "origin/$branch" --name-only -- project/executions/AD_HOC/ 2>/dev/null \
    | grep -i "_<SLUG_UPPER_UNDERSCORE>\.md$"
done
```

Combine matches from both searches; if more than one, take the single most
recent by filename timestamp and decide based only on that one — older
matches are historical context, not separately actionable. Read that
match's `status:` frontmatter field before deciding — per `PROMPTS.md`'s
status-handling rule (`DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT`), a matched
filename is discovery, not by itself a block: `in_progress`/`landed` stop
and report (unless the user explicitly asks for a rerun, in which case
check whether the match's branch still exists and reuse it if so — see
SKILL.md Step 6 — and keep the match's `execution_id` for `--rerun-of`
below); `failed`/`reverted`/`superseded` summarize and continue (keeping
its `execution_id` for `--rerun-of` below); unknown or ambiguous status
stops and reports the ambiguity. Only after that search comes up empty or
clears, mint the ID and run the secondary check:

```bash
lrh prompt check-execution --prompt-id "<id>" --project-root .
```

If this returns a `landed` or `in_progress` record, stop and report to the
user — do not proceed without explicit instruction to rerun.

## Create the execution record

```bash
lrh prompt record-execution \
  --prompt-id "<id>" \
  --work-item AD_HOC \
  --slug <slug> \
  --status in_progress \
  --project-root .
```

If the prior-execution check above found a matching record — whether
summarized (`failed`/`reverted`/`superseded`) or explicitly overridden by
the user (`in_progress`/`landed`) — add `--rerun-of <its-execution_id>` so
the new record links back to it, per `PROMPTS.md:136`.

This creates a new file at:
`project/executions/AD_HOC/<timestamp>_<SLUG_UPPER_UNDERSCORE>.md`

Immediately edit the generated file to add the three optional fields, then
replace the generated `# Summary`/`# Result`/`# Validation`/`# Follow-up`
TODO placeholders with real content — `/lrh-closeout` only edits frontmatter
when landing, so an un-narrated record ships as `landed` with no evidence
(see `AGENTS.md`'s evidence policy):

```yaml
agent: claude_app
instruction_source: project/design/proposals/proposed/<slug>/00_proposal.md
session_transcript: pending
```

### `agent`

| Value | Use when |
|---|---|
| `claude_app` | Created in a Claude Code (Claude.app) session |
| `codex_cloud` | Submitted to and executed by Codex Cloud |
| `manual` | Created manually without an AI backend |

### `instruction_source`

The path to the proposal file this PR creates, e.g.
`project/design/proposals/proposed/lrh-doc-skills/00_proposal.md`.

### `session_transcript`

Scheme-prefixed scalar `<backend>:<id>`, or `pending` if the session ID is
not yet known. For Claude.app, use `claude-app:<host-uuid-stem>` (the host
session id with the `local_` prefix stripped — see
`CLAUDE_CODE_HOST_SESSION_ID`). Never commit an absolute path or the
transcript itself.

---

## Landing the record

Turning `in_progress` into `landed` is `/lrh-closeout`'s job, run against
the merged PR — not something this skill does. See
`lrh prompt update-execution --help` if closeout is unavailable and the
transition must be done by hand.
