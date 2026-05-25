---
title: Docs request workflow dogfood audit on nested LCATS-style layout
date: 2026-05-24
scope: lrh request audit_docs + organize_docs prompt generation
type: dogfood_audit
status: pass_with_followups
prompt_id: PROMPT(AD_HOC:DOGFOOD_DOCS_REQUESTS_ON_LCATS)[2026-05-22T10:14:00-04:00]
---

# Summary

Dogfooded `lrh request audit_docs` and `lrh request organize_docs` against a synthetic nested layout that mirrors LCATS path shape:

```text
/tmp/lcats_fixture/
  corpora/
  lcats/
    lcats/
    docs/
    project/
```

Both request templates rendered successfully with nested roots and produced bounded prompts appropriate for a later real LCATS run.

# Commands run

1. Exact prompt-id execution check:
   - `lrh prompt check-execution --prompt-id "PROMPT(AD_HOC:DOGFOOD_DOCS_REQUESTS_ON_LCATS)[2026-05-22T10:14:00-04:00]" --project-root .`
   - Result: `No execution records found for prompt_id.`

2. Nested fixture setup + initial organize command attempt:
   - `lrh request organize_docs ... --audit ...`
   - Result: CLI parse error: `ambiguous option: --audit could match --audit-file, --audit-output`.

3. Nested fixture setup + successful generation:
   - `lrh request audit_docs --repo-root /tmp/lcats_fixture --project-root /tmp/lcats_fixture/lcats --docs-root /tmp/lcats_fixture/lcats/docs --control-root /tmp/lcats_fixture/lcats/project --package-root /tmp/lcats_fixture/lcats/lcats --out /tmp/lcats_fixture/audit-docs.prompt.md`
   - `lrh request organize_docs --repo-root /tmp/lcats_fixture --project-root /tmp/lcats_fixture/lcats --docs-root /tmp/lcats_fixture/lcats/docs --control-root /tmp/lcats_fixture/lcats/project --audit-file /tmp/lcats_fixture/lcats/project/audits/2026-05-24-docs-audit.md --out /tmp/lcats_fixture/organize-docs.prompt.md`
   - Result: both prompts written (`47` and `49` lines respectively).

# Required checks and outcomes

1. `audit_docs` renders prompt for nested roots: **pass**.
2. Audit prompt avoids standard-layout assumptions (`repo_root/docs`, `repo_root/project`, `src/<package>`): **pass**.
3. Audit prompt instructs downstream agent to write a structured docs-audit artifact: **pass**.
4. `organize_docs` renders prompt that consumes audit path (`--audit-file`): **pass**.
5. Organization prompt is phase-bounded and audit-constrained: **pass**.
6. Human docs match implemented behavior: **pass with caveat**.
   - Current docs already describe the implemented `--audit-file` option.
   - User shorthand `--audit` is not accepted by parser and raises an ambiguity error.
7. Suitability for later real LCATS run: **pass**.

# Discrepancies observed

- `--audit` is ambiguous at CLI parse time because both `--audit-file` and `--audit-output` exist.
- This is currently documented in CLI reference as expected behavior (`--audit-file` is the implemented option).

# Focused follow-up recommendations

1. Add support for an explicit `--audit` alias to `--audit-file` to match user shorthand and reduce parse-time ambiguity.
2. Add a regression test that asserts nested-root `organize_docs` invocation with `--audit-file` works and that `--audit` ambiguity is either intentionally preserved or intentionally resolved.
3. Consider harmonizing option names so `organize_docs` input and `audit_docs` output are less confusable (`--audit-file` vs `--audit-output`).

# Evidence artifacts

- Generated prompt: `/tmp/lcats_fixture/audit-docs.prompt.md`
- Generated prompt: `/tmp/lcats_fixture/organize-docs.prompt.md`
- Referenced audit placeholder: `/tmp/lcats_fixture/lcats/project/audits/2026-05-24-docs-audit.md`
