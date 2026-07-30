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

### Complete example

A landed execution record with all three optional fields populated:

```yaml
---
execution_id: 2026_07_25_04_01_32_WI_EXEC_SESSIONS_SCHEMA
prompt_id: PROMPT(WI-EXEC-SESSIONS-SCHEMA:WI_EXEC_SESSIONS_SCHEMA)[2026-07-25T02:19:37-04:00]
work_item: WI-EXEC-SESSIONS-SCHEMA
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/421
commit: e7d7a0eb1a74ab21e0245f58798e8afbe54b2424
created_at: 2026-07-25T04:01:32-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-EXEC-SESSIONS-SCHEMA.md
session_transcript: claude-app:4c3d03d6-6ebd-418a-86b2-6f4041feb9db
---
```

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

### Pre-mint duplicate detection by slug (a second authoritative case)

`lrh prompt label` mints a fresh, timestamped prompt ID on every call, so
there is no existing ID to check with `check-execution` before a skill's
own instruction phase has run once already — the exact-lookup mechanism
above cannot answer "has this same logical slug already produced a
record?" because no ID for it exists yet to look up. When a skill needs to
detect that before minting (e.g. a review-response run keyed to the
current branch, or a proposal/work-item/workstream keyed to its own
stable slug), a filename search against the relevant bucket (typically
`project/executions/AD_HOC/`) for the exact trailing slug segment is
authoritative for this narrower question — it is not the same thing as
the exploratory/fuzzy search above.

Match the complete trailing filename segment, not a bare substring — a
longer, unrelated slug that happens to contain this one as a substring
must not count as a match. Status handling on a match found this way is
similar to exact-ID lookup, with one deliberate difference: `landed`/
`in_progress` blocks (unless the prompt explicitly asks for a rerun, which
then requires linking `rerun_of` to the matched record); `failed`/
`reverted`/`superseded` is non-blocking and continues unconditionally
(also linking `rerun_of`) — it does not require the prompt to
independently declare itself a rerun or follow-up, the way the exact-ID
rule above does, since no such declaration mechanism exists before a
slug's own history is even known. Unknown/ambiguous status, or matches
that disagree with each other, stop and report either way. See
`PROMPTS.md` "Pre-mint duplicate detection by slug" for the canonical
statement of this rule.

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
