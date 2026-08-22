---
execution_id: 2026_08_22_16_55_43_WI_PII_SCAN_RULE_TAXONOMY
prompt_id: PROMPT(WI-PII-SCAN-RULE-TAXONOMY:WI_PII_SCAN_RULE_TAXONOMY)[2026-08-22T05:26:58+00:00]
work_item: WI-PII-SCAN-RULE-TAXONOMY
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/604
commit: 1703c872
created_at: 2026-08-22T16:55:43+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-PII-SCAN-RULE-TAXONOMY.md
session_transcript: claude-app:cf93c405-ed0f-409d-946f-7451a1cb2f7c
---

# Summary

Implemented `WI-PII-SCAN-RULE-TAXONOMY` via `/lrh-execute`'s inlined
`/lrh-implement`: extracted `lrh.conversations.sensitivity`'s rule
taxonomy into a new shared module, per `PROP-LRH-PII-SCAN` Decision 5.

# Result

Created `src/lrh/shared/sensitivity_rules.py` containing the `_Rule`
dataclass, `SEVERITY_*`/`CONFIDENCE_*` constants, the full regex rule
table (`_BASIC_RULES` and the individually-applied patterns), and the
`_digits_only`/`_passes_luhn_check`/`_is_valid_ipv4_address` validators —
moved verbatim from `sensitivity.py`. Refactored `sensitivity.py` to
import `sensitivity_rules` (module import, not member import, per
`STYLE.md` Rule 3) and reference every extracted name through it; no
detection-behavior change. Added `tests/shared_tests/sensitivity_rules_test.py`
(10 new tests) covering the extracted module directly.

Discovered and worked around a shared-environment issue: multiple stale
`__editable__.lrh-*.pth` entries in the shared conda environment (from
other, unrelated worktrees, including one from a different Codex session)
were shadowing this worktree's own editable install, and `black`/`ruff`
versions had drifted from `constraints-dev.txt`'s pins. Fixed the tool
versions locally (`pip install black==26.3.1 ruff==0.15.12`); worked
around the `.pth` shadowing with an explicit `PYTHONPATH` prefix rather
than touching the other worktrees' `.pth` entries, since they may belong
to other active sessions. Documented in the PR body as an environment
note, not a code issue.

# Validation

- `PYTHONPATH=<worktree>/src python -m unittest discover -s tests -p
  '*_test.py'` — 1276 tests, OK.
- `tests.shared_tests.sensitivity_rules_test` (10 tests, new) and
  `tests.conversations_tests.sensitivity_test` (13 tests, pre-existing,
  unmodified) both pass — confirms behavior preservation.
- `scripts/format --check --diff` / `scripts/lint` — clean after fixing
  the local tool-version drift.
- `lrh validate` — 0 errors, 0 warnings.
- Independent cold-context self-review (`/lrh-self-review` diff-mode) —
  clean, no findings. Independently re-verified (mandatory top-finding
  check): grepped the full repo for any other file referencing the
  extracted symbols — none found outside the three touched paths.

# Follow-up

- Run `/lrh-review-response`/`/lrh-confirm-fixes` on PR #604, then merge
  and `/lrh-closeout` to resolve `WI-PII-SCAN-RULE-TAXONOMY`.
- `WI-PII-SCAN-LAYER1-ENUMERATOR` (no dependencies) can proceed in
  parallel; `WI-PII-SCAN-LAYER2-CONTENT` depends on this item merging
  first.
