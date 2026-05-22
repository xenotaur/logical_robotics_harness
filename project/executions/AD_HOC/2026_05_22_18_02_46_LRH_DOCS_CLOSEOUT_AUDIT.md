---
execution_id: 2026_05_22_18_02_46_LRH_DOCS_CLOSEOUT_AUDIT
prompt_id: PROMPT(AD_HOC:LRH_DOCS_CLOSEOUT_AUDIT)[2026-05-18T17:30:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-22T18:02:46+00:00
---

# Summary

Closed out the broad LRH docs reorg with a focused dogfood pass on docs navigation, CLI accuracy, stale-link hygiene, and control-plane status alignment.

# Result

- Confirmed soft idempotence with exact prompt-id lookup; no prior execution record existed for this prompt ID.
- Ran CLI help audits against both `python -m lrh.cli.main ... --help` and installed `lrh ... --help` for the requested command set.
- Updated docs navigation indexes so current CLI reference listings include `lrh serve` and clearly point prompt-workflow readers to existing docs.
- Added a status closeout note that marks the broad human-facing docs reorg as closed as of 2026-05-22.
- Captured remaining docs gaps as two specific follow-up proposed work items instead of keeping an indefinite “docs reorg” stream:
  - `WI-DOCS-CLI-OPTION-TABLES`
  - `WI-DOCS-SCHEMA-REFERENCE-SEED`

# Validation

- `lrh prompt check-execution --prompt-id 'PROMPT(AD_HOC:LRH_DOCS_CLOSEOUT_AUDIT)[2026-05-18T17:30:00-04:00]' --project-root .`
- `find docs -name README.md -print`
- `rg -n "docs/release.md|release.md|docs/project-setup|project-setup" README.md docs project || true`
- `rg -n "TODO|TBD|planned|future" docs || true`
- `python -m lrh.cli.main --help`
- `python -m lrh.cli.main validate --help`
- `python -m lrh.cli.main snapshot --help`
- `python -m lrh.cli.main survey --help`
- `python -m lrh.cli.main request --help`
- `python -m lrh.cli.main meta --help`
- `python -m lrh.cli.main serve --help`
- `lrh validate --help`
- `lrh snapshot --help`
- `lrh survey --help`
- `lrh request --help`
- `lrh meta --help`
- `lrh serve --help`
- `lrh validate`
- `scripts/version tools`
- `scripts/lint`
- `scripts/test`

# Follow-up

- Implement `WI-DOCS-CLI-OPTION-TABLES` to add concise, maintainable command option tables for high-traffic CLI docs.
- Implement `WI-DOCS-SCHEMA-REFERENCE-SEED` to populate `docs/reference/schemas/` with concrete implemented schema contracts.
