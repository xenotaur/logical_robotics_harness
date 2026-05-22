---
execution_id: 2026_05_22_19_12_08_DOCS_AUDIT_ARTIFACT_CONVENTION
prompt_id: PROMPT(AD_HOC:DOCS_AUDIT_ARTIFACT_CONVENTION)[2026-05-22T10:10:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-22T19:12:08+00:00
---

# Summary

Document the version-1 LRH docs-audit artifact convention for future two-stage `audit_docs` → `organize_docs` request workflows, without implementing request commands.

# Result

Added a new reference page defining:

- purpose and workflow role of docs audits
- Diátaxis classification expectations
- separation between project-control state and human docs
- recommended audit artifact path
- minimal v1 frontmatter
- required headings for v1 audits
- note that validation tooling may be added later

Also updated `docs/reference/README.md` to link the new reference page.

# Validation

- `scripts/version tools`
- `scripts/lint`
- `scripts/test`

All commands completed successfully in Codex Cloud.

# Follow-up

Future work may add request generators (`lrh request audit_docs`, `lrh request organize_docs`) and optional validation checks for docs-audit frontmatter and required headings.
