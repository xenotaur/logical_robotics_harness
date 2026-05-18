---
execution_id: 2026_05_18_04_51_12_LRH_CONVERSATION_SENSITIVITY_SCANNER
prompt_id: PROMPT(AD_HOC:LRH_CONVERSATION_SENSITIVITY_SCANNER)[2026-05-16T00:46:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-05-18T04:51:12+00:00
---

# Summary

Implemented a narrow, deterministic local sensitivity scanner for LRH conversation transcripts.

# Result

- Added `lrh.conversations.sensitivity` with typed immutable scan result objects.
- Implemented local heuristic rules for email addresses, US SSN-like values, Luhn-valid credit-card-like numbers, PEM private key blocks, keyword secret assignments, known token prefixes, URLs containing credentials, IPv4 addresses, and US-like phone numbers.
- Kept findings to redacted previews only; the scanner does not redact source text or certify publish safety.
- Added focused `unittest` coverage for detections, Luhn filtering, preview redaction, no-finding behavior, and deterministic category ordering.
- Added a short `src/lrh/conversations/README.md` note describing scanner limitations.
- Review follow-up broadened `sk-` token matching for separator-bearing token shapes and kept this record `in_progress` while PR metadata is unavailable.

# Validation

- `scripts/version tools` passed with expected Ruff 0.15.12 and Black 26.3.1 versions.
- `python -m unittest tests.conversations_tests.sensitivity_test` passed.
- `scripts/format --check` initially reported formatting changes needed for the new files.
- `scripts/format` reformatted the new scanner and test files.
- `scripts/lint` passed.
- `scripts/test` passed: 542 tests.
- `scripts/format --check` passed after formatting.
- `lrh validate` passed with 0 errors and 0 warnings.
- Review follow-up validation reran `scripts/version tools`, `scripts/format --check --diff`, `scripts/format`, `scripts/format --check --diff`, `scripts/lint`, `scripts/test`, and `lrh validate`.

# Follow-up

- Optional enhanced scanners can be added later behind explicit local integration boundaries.
- Redaction, transcript storage, PDF conversion, OCR, public export enforcement, LLM calls, and external scanner integrations remain out of scope for this prompt.
