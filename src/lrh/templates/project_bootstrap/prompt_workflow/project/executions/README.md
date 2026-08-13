# Execution Records (starter stub)

Execution records live under `project/executions/<WORK_ITEM_OR_AD_HOC>/`.

For the canonical execution-record schema and allowed status values, see
`project/executions/README.md`.

Use concise records with front matter fields:

- execution_id
- prompt_id
- work_item
- status
- created_at
- rerun_of
- pr
- commit

Exact matches against the front-matter `prompt_id` field are authoritative
for rerun and idempotence decisions for a prompt ID.
Use `lrh prompt check-execution --prompt-id ...` when the ID is available,
`lrh match executions <prompt-file>` when a prompt file should supply the ID,
and `lrh search executions <query>` only for exploratory local substring search.

**Exception — pre-mint duplicate detection by slug:** before a prompt ID
exists to check, a filename search against the relevant execution bucket
for the exact trailing slug segment (not a bare substring) is
authoritative for that narrower question. See `PROMPTS.md` in this
repository for the full rule and status handling.
