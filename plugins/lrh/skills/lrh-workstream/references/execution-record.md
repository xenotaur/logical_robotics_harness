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

Search by stable slug *before* minting, across the current checkout and
open PRs — `lrh prompt label` always mints a fresh timestamped ID, so
`check-execution --prompt-id` alone cannot catch a rerun. Use the
slug-based mode, the mechanism `DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT`
describes and `WI-SLUG-IDEMPOTENCE-CLI-TOOLING` implements:

```bash
lrh prompt check-execution --slug <slug> --work-item AD_HOC --project-root .
```

This matches the complete trailing filename segment (not a bare
substring), searches the local checkout and every open PR (including
forks) via `refs/pull/<N>/head`, excludes matches a PR only *inherited*
via `git merge-base` against its declared base ref (so a stacked PR never
shadows the PR that actually introduced the record), and selects the
truly most recent match by parsed `created_at:` rather than filename
order (execution-record filename timestamps are not reliably
chronological across machines — see `project/design/backlog.md`'s
"Execution-record filename timestamps use local time, not UTC").

Interpret the exit code: `1` is a blocking match — either
`landed`/`in_progress` (the default) or a `planned`/unrecognized status
(unresolved outcomes block too), or any match whose recency can't be
established (a missing/malformed `created_at`) even if every status is
otherwise terminal — stop and report unless the user explicitly asks for
a rerun (see SKILL.md Step 6 for resuming the match's branch whether
local, remote-only, or gone; keep the printed `execution_id` for
`--rerun-of` below). `0` with a match printed means
only `failed`/`reverted`/`superseded` — summarize and continue, keeping
its `execution_id` for `--rerun-of` below. `0` with no match printed
means no prior record. `3` means the check itself failed (a `gh`/`git`
error) — stop and report the error; this is not the same as "no prior
record." `2` means malformed input (argparse rejected the derived
`<slug>`/work-item value, or both/neither of `--slug`/`--prompt-id` were
given) — a usage error, not a slug-check result; stop and report. Only
after that search comes up empty or clears, mint the ID and run the
secondary check:

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
agent: <agent-backend>
instruction_source: project/workstreams/proposed/<WS-ID>.md
session_transcript: pending
```

### `agent`

| Value | Use when |
|---|---|
| `claude_app` | Created in a Claude Code (Claude.app) session |
| `codex_app` | Created in a Codex desktop app task |
| `codex_cloud` | Submitted to and executed by Codex Cloud |
| `manual` | Created manually without an AI backend |

### `instruction_source`

The path to the workstream file this PR creates, e.g.
`project/workstreams/proposed/WS-DOC-SKILLS.md`.

### `session_transcript`

Scheme-prefixed scalar `<backend>:<id>`, or `pending` if the session exists
but the durable ID is not yet known. Use the scheme that matches the selected
agent backend:

| Backend | Session transcript form |
|---|---|
| Claude.app | `claude-app:<host-uuid-stem>` (host id with `local_` stripped, when `CLAUDE_CODE_HOST_SESSION_ID` is available) |
| Codex app | `codex-app:<task-or-thread-id>` when available; otherwise `pending` |
| Codex Cloud | `codex-cloud:<task-id>` |
| Manual/no retrievable session | `none` |

Never commit an absolute path or the transcript itself.

---

## Landing the record

Turning `in_progress` into `landed` is `/lrh-closeout`'s job, run against
the merged PR — not something this skill does. See
`lrh prompt update-execution --help` if closeout is unavailable and the
transition must be done by hand.
