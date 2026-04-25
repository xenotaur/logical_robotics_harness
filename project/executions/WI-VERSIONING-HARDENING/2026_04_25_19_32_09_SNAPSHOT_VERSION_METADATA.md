---
execution_id: 2026_04_25_19_32_09_SNAPSHOT_VERSION_METADATA
prompt_id: PROMPT(WI-VERSIONING-HARDENING:SNAPSHOT_VERSION_METADATA)[2026-04-25T02:30:00-04:00]
work_item: WI-VERSIONING-HARDENING
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-04-25T19:32:09+00:00
---

# Summary

Embed additive LRH harness version metadata in snapshot context packet output by
resolving the installed package version via `importlib.metadata`, update
snapshot tests, and document the metadata block in assist snapshot docs.

# Result

Implemented additive snapshot metadata output under each packet Scope section:

```text
harness:
  name: lrh
  version: <resolved installed version or unknown>
```

Version resolution now uses `importlib.metadata.version("logical-robotics-harness")`
with an `"unknown"` fallback when metadata is unavailable. Added unit coverage
for metadata resolution and project context rendering. Updated assist README
snapshot usage docs to describe the new metadata block.

# Validation

- `python -m unittest tests.assist_tests.snapshot_cli_test`
- `python -m unittest tests.cli_tests.snapshot_test`
- `ruff check src/lrh/assist/snapshot_cli.py tests/assist_tests/snapshot_cli_test.py`
- `black --check src/lrh/assist/snapshot_cli.py tests/assist_tests/snapshot_cli_test.py`

# Follow-up

After PR creation and merge, update `status` to `landed` and fill `pr`/`commit`
frontmatter fields.
