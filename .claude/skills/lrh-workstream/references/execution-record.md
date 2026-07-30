# Execution Record Reference

Practical facts from `PROP-LRH-EXECUTION-SESSIONS` needed when running
`/lrh-workstream`. Read this before Step 4 (instruction phase) and Step 10
(execution record).

Creating a workstream is itself a planning action worth recording: without
an execution record for the PR that files the workstream, later
`_REVIEW`/`_CONFIRM` records created by `/lrh-review-response` and
`/lrh-confirm-fixes` against that PR have no primary record to set
`rerun_of` against, and `/lrh-closeout` has to reconstruct one by hand.

**Bucket this record under `AD_HOC`, not the new workstream's own ID.**
`/lrh-closeout`'s Step 2.3 looks up a work item by the execution record's
`work_item:` bucket (`find project/work_items/ -name "<work_item>.md"`). A
`WS-*` bucket won't match any work item file, so closeout would surface a
spurious "not found — how do you want to proceed?" prompt on every closeout
of this PR. `AD_HOC` is the bucket the decision matrix explicitly recognizes
as "no WI to resolve" — see `project/executions/README.md` and
`.claude/skills/lrh-closeout/references/closeout-workflow.md`.

---

## Mint a prompt ID

```bash
lrh prompt label --slug <slug>
```

`<slug>` is lower-kebab, derived from the workstream ID:
`WS-DOC-SKILLS` → `ws-doc-skills`. Omit `--work-item` — it defaults to
`AD_HOC`.

The command outputs a `prompt_id` in the form:

```
PROMPT(AD_HOC:<SLUG_UPPER_UNDERSCORE>)[<ISO8601-TIMESTAMP>]
```

## Check for prior execution

Search by stable slug *before* minting — `lrh prompt label` always mints a
fresh timestamped ID, so `check-execution` alone cannot catch a rerun.
Derive `<SLUG_UPPER_UNDERSCORE>` from `<slug>` by replacing `-` with `_` and
uppercasing, then match the complete trailing filename segment — not a bare
substring, which would also match an unrelated longer slug that happens to
contain this one:

```bash
find project/executions/AD_HOC/ -name "*_<SLUG_UPPER_UNDERSCORE>.md" 2>/dev/null
```

`AD_HOC/` may not exist yet in a freshly bootstrapped project — suppress the
not-found error rather than treating it as a failure.

The glob can return more than one match — a prior rerun mints a new
timestamped file with the same trailing slug. Read the `status:`
frontmatter field of every match before deciding — per `PROMPTS.md`'s
status-handling rule, a matched filename is discovery, not by itself a
block: any match `in_progress`/`landed` stop and report (if more than one,
name them all and ask the user which is being rerun — do not guess; unless
the user explicitly asks for a rerun, in which case keep the confirmed
match's `execution_id`, the most recent if undistinguished, for
`--rerun-of` below); all matches
`failed`/`reverted`/`superseded` summarize the most recent and continue
(keeping its `execution_id` for `--rerun-of` below); disagreeing or
unrecognized statuses stop and report the ambiguity. Only after that
search comes up empty or clears, mint the ID and run the secondary check:

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
instruction_source: project/workstreams/proposed/<WS-ID>.md
session_transcript: pending
```

### `agent`

| Value | Use when |
|---|---|
| `claude_app` | Created in a Claude Code (Claude.app) session |
| `codex_cloud` | Submitted to and executed by Codex Cloud |
| `manual` | Created manually without an AI backend |

### `instruction_source`

The path to the workstream file this PR creates, e.g.
`project/workstreams/proposed/WS-DOC-SKILLS.md`.

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
