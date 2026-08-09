---
execution_id: 2026_08_08_21_03_32_CODEX_APP_SERVER_EXPORT_DOGFOOD
prompt_id: PROMPT(AD_HOC:CODEX_APP_SERVER_EXPORT_DOGFOOD)[2026-08-08T21:03:32+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_08_08_06_28_06_WI_CODEX_CONVERSATION_EXPORT_APP_SERVER
pr:
commit:
created_at: 2026-08-08T21:03:32+00:00
agent: codex_app
instruction_source: user-request:dogfood-codex-app-server-exporter
session_transcript: codex-app:019fc43f-e2d9-7503-88cb-9d9a8136c111
---

# Summary

Dogfood the landed `lrh conversation export-codex-thread` command against this
real Codex session before creating the thin `/lrh-codex-export` skill wrapper.

# Result

The real app-server export path works when Codex can access its own local state.
The export command produced private Markdown plus private raw JSON in
`/private/tmp/lrh-codex-dogfood-019fc43f-e2d9-7503-88cb-9d9a8136c111/`.

The committed record intentionally excludes transcript text and raw JSON. The
private artifact reported:

- `source_adapter: codex_app_server_thread_read`
- `privacy: private`
- `authority: non_authoritative_context`
- `sensitivity: potential`
- `sensitivity_scan.finding_count: 2`
- `sensitivity_scan.categories: credit_card`
- `warnings: 8`
- `turn_count: 145`
- `message_count: 2047`
- `item_type_counts: agentMessage=1903, contextCompaction=14, fileChange=218,
  mcpToolCall=1, reasoning=440, userMessage=144, webSearch=25`
- `source_sha256: a1b68efd0843e778a7dbf88d25b139ab4d66a04a8b127a130f25b225a6374ac8`

# Findings

- The first sandboxed run failed before export because `codex app-server` could
  not initialize SQLite state under `~/.codex`. The skill wrapper should note
  that Codex app-server export requires access to Codex local state and may need
  an unsandboxed/approved run in restricted execution environments.
- The unsandboxed run succeeded and printed metadata only. This validates the
  app-server route for a real, large Codex task.
- `lrh conversation inspect-export --source ... --format json` returned
  `valid: true`, `manifest_valid: true`, source hash `match`, and transcript
  statistics `match`.
- A naive line-based preview command can cross the frontmatter boundary and
  print transcript content. Future dogfood instructions should use
  `inspect-export` or manifest-aware tooling for human/machine checks rather
  than `head`, `sed`, or similar line previews.
- The renderer surfaced one unknown item type, `mcpToolCall`. This is not a
  blocker because unknown item types are metadata-only with warnings, but it is
  useful evidence for later renderer hardening.

# Validation

- `git pull --ff-only origin main` — already up to date.
- `lrh conversation export-codex-thread --thread-id 019fc43f-e2d9-7503-88cb-9d9a8136c111 --out /private/tmp/.../export.md --raw-out /private/tmp/.../raw.json --force --timeout-seconds 20` — succeeded after rerunning with access to Codex local state.
- `lrh conversation inspect-export /private/tmp/.../export.md --source /private/tmp/.../raw.json --format json` — succeeded with `valid: true` and source hash `match`.

# Follow-up

- Create a proposed work item for the thin `/lrh-codex-export` skill wrapper on
  top of the now-dogfooded CLI.
- Consider a later renderer hardening item for first-class `mcpToolCall`
  metadata if future dogfood sessions show it is common enough to warrant a
  named renderer.
