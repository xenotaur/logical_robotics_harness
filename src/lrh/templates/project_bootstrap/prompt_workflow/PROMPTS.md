# Prompt Workflow (starter stub)

Use prompt IDs to track meaningful prompt-driven implementation work.

See `project/executions/README.md` for execution-record schema and status conventions.

Use `lrh prompt check-execution --prompt-id ...` as the authoritative exact
lookup for soft idempotence decisions. Use `lrh match executions <prompt-file>`
when a prompt file contains the ID and you want the command to extract it before
applying exact matching. Use `lrh search executions <query>` only for
exploratory local substring search over execution records. Search results are
useful context for discovery, auditing, and debugging, but they are not
authoritative for blocking or rerun decisions.

**Exception — pre-mint duplicate detection by slug:** before a prompt ID
exists to check (a fresh `lrh prompt label` call always mints a new
timestamped ID, so `check-execution` can't catch a rerun of the same slug
yet), a filename search against the relevant execution bucket for the
exact trailing slug segment (not a bare substring) is authoritative for
that narrower question — not the same thing as the general exploratory
search above. On a match: `landed`/`in_progress` blocks unless the prompt
explicitly asks for a rerun; `failed`/`reverted`/`superseded` is
non-blocking and continues; ambiguous or disagreeing statuses stop and
report. Whenever a new record is actually created after a match (an
explicit rerun of a blocked match, or continuing past a
`failed`/`reverted`/`superseded` one), link it to the matched record via
`rerun_of` — a blocked match with no rerun produces no new record to link.
