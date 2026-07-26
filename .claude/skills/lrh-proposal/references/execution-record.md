# Execution Record Reference

Practical facts from `PROP-LRH-EXECUTION-SESSIONS` needed when running
`/lrh-proposal`. Read this before Step 4 (instruction phase) and Step 10
(execution record).

Creating a proposal is itself a planning action worth recording: without
an execution record for the PR that files the proposal, later `_REVIEW`/
`_CONFIRM` records created by `/lrh-review-response` and `/lrh-confirm-fixes`
against that PR have no primary record to set `rerun_of` against, and
`/lrh-closeout` has to reconstruct one by hand.

---

## Mint a prompt ID

```bash
lrh prompt label --slug <slug> --work-item <PROP-ID>
```

`<slug>` is the same lowercase-kebab slug given as this skill's argument.
`<PROP-ID>` is the `id:` value decided in Step 2 — conventionally
`PROP-<SLUG-UPPER>` (e.g. slug `lrh-doc-skills` → `PROP-LRH-DOC-SKILLS`).

The command outputs a `prompt_id` in the form:

```
PROMPT(<PROP-ID>:<SLUG_UPPER_UNDERSCORE>)[<ISO8601-TIMESTAMP>]
```

## Check for prior execution

```bash
lrh prompt check-execution --prompt-id "<id>" --project-root .
```

If this returns a `landed` or `in_progress` record, stop and report to the
user — do not proceed without explicit instruction to rerun.

## Create the execution record

```bash
lrh prompt record-execution \
  --prompt-id "<id>" \
  --work-item <PROP-ID> \
  --slug <slug> \
  --status in_progress \
  --project-root .
```

This creates a new file at:
`project/executions/<PROP-ID>/<timestamp>_<SLUG_UPPER_UNDERSCORE>.md`

Immediately edit the generated file to add the three optional fields:

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
