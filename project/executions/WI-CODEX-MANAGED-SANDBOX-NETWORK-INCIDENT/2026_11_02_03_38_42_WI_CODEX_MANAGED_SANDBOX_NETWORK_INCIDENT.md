---
execution_id: 2026_11_02_03_38_42_WI_CODEX_MANAGED_SANDBOX_NETWORK_INCIDENT
prompt_id: PROMPT(WI-CODEX-MANAGED-SANDBOX-NETWORK-INCIDENT:WI_CODEX_MANAGED_SANDBOX_NETWORK_INCIDENT)[2026-11-01T09:17:15+00:00]
work_item: WI-CODEX-MANAGED-SANDBOX-NETWORK-INCIDENT
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/860
commit: efd9a334b538666635b860a2d7c74574972f5c72
agent: codex_app
instruction_source: project/work_items/proposed/WI-CODEX-MANAGED-SANDBOX-NETWORK-INCIDENT.md
session_transcript: pending
created_at: 2026-11-02T03:38:42+00:00
---

# Summary

Create a sanitized evidence artifact for the Codex managed-sandbox GitHub
networking incident, preserving the normal-versus-approved execution
comparison and its unresolved follow-up state.

# Result

Created `project/evidence/EV-CODEX-MANAGED-SANDBOX-NETWORK.md`. It records the
normal-sandbox DNS/HTTPS/GraphQL failures, the successful approved-execution
comparison, the distinction from the LRH `cwd` classification defect, the
credential-diagnosis boundary, the safe workaround, and the unresolved
platform/executor alternatives. No tokens, authorization headers, full API
bodies, private transcripts, or private repository contents are included.

The external OpenAI/Codex report reference remains pending because this
environment does not expose an approved support-submission connector. The
artifact explicitly records that state and the required follow-up.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `git diff --check`: passed.
- `scripts/version tools`: Black 26.3.1, Ruff 0.15.12, Python 3.11.8;
  Pyright not installed.
- `scripts/format --check --diff`: 299 files unchanged.
- `scripts/lint`: passed.
- `scripts/test --log` with the repository Anaconda toolchain: 2378 tests
  passed.
- An initial test attempt used system Python 3.9 and failed from environment
  mismatch; a normal-sandbox retry failed loopback-dependent desktop tests;
  approved execution passed the canonical suite.

# Follow-up

Submit the sanitized report through the appropriate OpenAI/Codex support path,
record its non-secret reference and response, then reassess whether normal
execution succeeds without approved network escalation before resolving this
work item.
