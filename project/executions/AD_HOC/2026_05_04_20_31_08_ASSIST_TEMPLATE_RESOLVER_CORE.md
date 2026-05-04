---
execution_id: 2026_05_04_20_31_08_ASSIST_TEMPLATE_RESOLVER_CORE
prompt_id: PROMPT(AD_HOC:ASSIST_TEMPLATE_RESOLVER_CORE)[2026-05-04T15:00:00-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: 
commit: 
created_at: 2026-05-04T20:31:08+00:00
---

# Summary

Added the core assist-template resolver for LRH with exact-name filesystem overrides and package-resource fallback.

# Result

Implemented `TemplateResolver` and `TemplateResolution` under `src/lrh/assist/`, added a package marker for `lrh.assist.templates`, wired request-template fallback loading through the resolver, documented override precedence in the assist README, and added unittest coverage for precedence, overrides, missing templates, and unsafe logical names.

# Validation

- `rg -n "PROMPT\\(AD_HOC:ASSIST_TEMPLATE_RESOLVER_CORE\\)\\[2026-05-04T15:00:00-04:00\\]|ASSIST_TEMPLATE_RESOLVER_CORE" project/executions || true` found no prior execution records for this exact prompt ID before implementation.
- `scripts/version tools` passed; Black and Ruff versions matched repository expectations.
- `python -m unittest tests.assist_tests.template_resolver_test tests.assist_tests.request_templates_test` passed.
- `scripts/test` passed.
- `scripts/lint` initially failed because the new resolver test needed Black wrapping; after running `scripts/format tests/assist_tests/template_resolver_test.py`, `scripts/lint` passed.
- `scripts/format --check` passed.
- `scripts/lint && scripts/format --check && python -m unittest tests.assist_tests.template_resolver_test tests.assist_tests.request_templates_test tests.assist_tests.request_service_test` passed after the small request-service integration.
- `scripts/test` passed after adding the HOME-default user-global config coverage.

# Follow-up

None.
