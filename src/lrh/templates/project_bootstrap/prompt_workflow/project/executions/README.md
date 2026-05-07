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

`lrh search executions <query>` can help discover related records by local
substring search, but exact prompt-ID checks remain authoritative for rerun and
idempotence decisions.
