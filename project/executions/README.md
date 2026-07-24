# Execution Records

Execution records provide lightweight traceability for meaningful prompt-driven
work. They record which prompt ran, the associated work item or `AD_HOC`
bucket, current status, and concise evidence or follow-up notes from the run.

## Directory layout

```text
project/executions/
  README.md
  AD_HOC/
  <WORK_ITEM_ID>/
    YYYY_MM_DD_HH_MM_SS_SLUG.md
```

- Use work-item IDs as the primary grouping mechanism when a matching work item exists.
- Use `AD_HOC/` when no work item applies.

This directory is intentionally lightweight. It is not a workflow engine and does not introduce formal workstreams.

## Front matter schema

Execution records should include these front-matter fields:

- `execution_id`: `YYYY_MM_DD_HH_MM_SS_<SLUG_UPPER_UNDERSCORE>`
- `prompt_id`: full prompt identifier
- `work_item`: work-item ID or `AD_HOC`
- `status`: one of the status values below
- `rerun_of`: optional prior execution ID
- `pr`: optional PR identifier
- `commit`: optional commit SHA
- `created_at`: ISO8601 timestamp with timezone offset

These optional fields come from `PROP-LRH-EXECUTION-SESSIONS`. They are
backward-compatible; records without them remain valid:

- `agent`: execution backend — `claude_app`, `codex_cloud`, `manual`, or
  another named backend
- `instruction_source`: the instruction-phase artifact (a repo-relative path,
  a short description, or a scheme-prefixed reference such as
  `promptspace:<relative-path>` for an archive outside the repository)
- `session_transcript`: pointer to the agent session that produced the work

### `session_transcript` values

The value is a scheme-prefixed scalar `<backend>:<id>`, or one of two
sentinels. See the 2026-07-23 "Backend-Agnostic Session Pointer Grammar"
entry in `project/memory/decision_log.md`.

| Value | Meaning |
|---|---|
| `claude-app:<host-uuid-stem>` | Claude.app session, host id, `local_` prefix stripped |
| `codex-cloud:<task-id>` | Codex Cloud task |
| `chatgpt:<conversation-id>` | ChatGPT conversation |
| `pending` | A retrievable session exists; its ID is not yet recorded. **A to-do.** |
| `none` | This backend produced no retrievable transcript. **Terminal, not a backlog item.** |

Never write an absolute path (`~/.claude/...`, `/Users/...`) — it leaks local
workspace layout to everyone who clones the repository. Session transcripts
themselves are never committed; the repository stores only the pointer.

A sequence of these scalars is reserved for executions that genuinely span
multiple backends; single-backend records stay scalar.

## Status values

Allowed status values:

- `planned`
- `in_progress`
- `landed`
- `failed`
- `reverted`
- `superseded`

## Soft idempotence guidance

Before executing a prompt-driven PR, check `project/executions/` for the
prompt ID. Exact matches against the front-matter `prompt_id` field are
authoritative for deciding whether a prompt ID has already been executed.

Use the lookup commands by role:

- `lrh prompt check-execution --prompt-id ...` is the authoritative exact
  structured lookup for soft idempotence when the prompt ID is already
  available.
- `lrh match executions <prompt-file>` is a human-friendly convenience layer
  when starting from a prompt file; it extracts full prompt IDs and delegates to
  the same exact lookup.
- `lrh search executions <query>` is exploratory local substring search across
  execution-record frontmatter and body text for discovery, auditing, and
  debugging. Search results are useful context, but they are not authoritative
  for rerun or idempotence decisions.

Examples:

```bash
lrh prompt check-execution --prompt-id "$PROMPT_ID" --project-root .
lrh match executions prompts/my_prompt.md --project-root .
lrh search executions "PROMPT_EXECUTION_SEARCH" --project-root .
lrh search executions "release smoke" --project-root .
lrh search executions "AD_HOC" --project-root .
lrh search executions "PROMPT(" --status landed --work-item AD_HOC --project-root .
```

For recent-prompt dogfooding, first run the exact `prompt_id` lookup. Then use
`lrh match executions <prompt-file>` if the prompt was saved to a file, and use
`lrh search executions "<distinctive prompt text>"` only for surrounding context
such as related validation notes, failed attempts, or other `AD_HOC` records.
Exploratory search results are not authoritative soft-idempotence evidence.

If future heuristic or fuzzy matching is added, it must be clearly labeled
non-authoritative unless later design work explicitly changes this rule.

If a prior exact record exists:

- `landed` or `in_progress`: stop and report unless the prompt explicitly says rerun.
- `failed`, `reverted`, or `superseded`: summarize the prior run and continue only if the prompt indicates rerun or follow-up.
- unknown or ambiguous status: stop and report ambiguity.

## Notes

- Work-item linkage is optional.
- Keep records concise and useful.
- Prompt records are encouraged for meaningful work, not required for every tiny change.

## Important Rules

- Prompts should only manipulate execution records related to them.
- Previous execution records for other prompts should NOT be modified.

For example, a cleanup prompt that was removing a variable or folder from the documentation
should NOT remove references to the directory in previous completed execution records.
This applies to all updates to execution records and especially to cleanup work items.

The exception is **limited frontmatter backfills and corrections** to a
record's own provenance metadata — for example a closeout populating
`status`, `pr`, `commit`, or `session_transcript`, or a schema-alignment pass
adding `agent`/`instruction_source` to historical records. These are allowed
(and are normal closeout workflow) because they record what actually
happened. The narrative body (`# Summary`, `# Result`, `# Validation`,
`# Follow-up`) and any unrelated context must remain immutable, even where it
has since gone stale — annotate in a later record rather than rewriting it.
