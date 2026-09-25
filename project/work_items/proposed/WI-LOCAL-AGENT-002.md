---
id: WI-LOCAL-AGENT-002
title: "Add bounded repository investigation and evaluate its benefit"
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
blocked: false
blocked_reason: null
resolution: null
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams:
  - WS-LOCAL-AGENT-DOGFOOD
related_design:
  - project/design/proposals/proposed/local-agent-dogfood/00_proposal.md
  - project/design/execution_framework_mvp.md
depends_on:
  - WI-LOCAL-AGENT-001
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - run_tests
  - write_docs
  - create_report
forbidden_actions:
  - implement_next_stage
  - modify_ci_pipeline
  - run_lrh_agentic
  - merge_pr
  - publish_package
  - force_push
  - delete_branch
acceptance:
  - "Only typed get_context, read_source, and search_sources requests can reach bounded immutable-corpus handlers."
  - "Policy and budgets cannot be modified by model output; every request, denial, result, and failure is recorded."
  - "Opt-in fake-model boundary and recovery tests pass without network or live inference."
  - "A reproducible comparison measures the additional value and cost over stage 0 with held-out tasks."
  - "A human records stop, revise, or promote; production behavior and project authority remain unchanged."
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
  - validation_output
artifacts_expected:
  - experimental/local_agent/
  - "Numbered bounded-investigation experiment with comparative results and a human decision."
---

# Add Bounded Repository Investigation and Evaluate Its Benefit

## Summary

Extend the stage-0 prototype with a short read/search loop over an explicitly
approved immutable source corpus. Measure whether the extra model calls and
tool complexity improve useful answers enough to justify continuing.

## Problem / Context

Static packets may omit the few source locations needed to answer a work-item
question. A bounded investigator can retrieve those locations while preserving
the read-only model authority of the first experiment.

**Duplication / demand check:** use the proposal's Prior Art Check and stage-0
findings. Existing context/readiness APIs remain authoritative. This is neither
the existing outbound MCP bridge proposal nor implementation of assistant-role
stages. A tool framework is optional and must preserve full dispatch interception.
Refresh the source check before activation; proceed only if observed briefing
limitations justify tool access.

## Scope

Extend `experimental/local_agent/` in place and retain the stage-0 mode for paired
comparisons. Add only `get_context`, `read_source`, and `search_sources` with typed
input/output schemas. The trusted recorder may write private artifacts; the model
cannot apply patches, write repository files, run commands, or fetch URLs.

## Required Changes

1. Record the human review of 001 and explicit authorization to test investigation.
   Pin the source corpus, model/backend, task split, budgets, numeric usefulness
   thresholds, and latency ceiling before live evaluation.
2. Add a bounded explicit loop. Validate every request before dispatch and keep
   policy outside model-modifiable state. At most one malformed-request repair
   is allowed within the total budget; unknown tools and invalid paths are denied.
3. Materialize a preapproved tracked-text corpus from a pinned commit. Resolve
   reads by source ID or confined canonical path; reject absolute paths,
   traversal, symlinks/escapes, unselected/private/binary content, and oversized
   requests. Use bounded literal text search with capped results and clear
   truncation markers. Treat retrieved instructions as data.
4. Bound total calls, steps, input/output size, model tokens, and wall time.
   Preserve explicit errors, denials, timeout, cancellation, and budget exhaustion.
   A model cannot extend its budget by asking, recursively calling itself, or
   changing a prompt. Local inference is the only permitted service connection.
5. Extend the existing event format with request/decision/result records, source
   hashes/ranges, sequence numbers, and elapsed time. Inspection/export must show
   what was read and why execution stopped. Reuse the private storage and failure
   recovery contracts from 001; do not introduce canonical run-state writes.
6. Add opt-in fake-model `unittest.TestCase` coverage for unknown/malformed tools,
   path/symlink escape attempts, input/output bounds, repeated denials, exhausted
   budgets, backend timeout, cancellation, truncated logs, and interrupted attempts.
   Include malicious source text requesting shell/network/write tools and verify
   that no handler outside the three-tool surface is reachable. Audit dispatch
   paths as well as testing sample prompts.
7. Run paired/counterbalanced comparisons against deterministic/manual completion
   and stage-0 one-call results with equivalent source availability. Keep held-out
   tasks. Record benefit, extra calls/latency, correction/review effort, resources,
   unsupported assertions, and all failure outcomes. Report whether the predeclared
   advancement criteria passed and obtain a human stop/revise/promote decision.

## Non-Goals

No generic filesystem browser, shell, code execution, network retrieval, patch
application, model-driven policy changes, public API/MCP server, multi-client
concurrency, production package imports, assistant scheduling, or full
constitutional-review implementation. Do not claim isolation from a compromised
local inference service or safety for physical robot control.

## Acceptance Criteria

- Only the three specified typed tool requests can reach handlers, and only
  approved immutable-corpus data can be returned.
- Immutable policy and total budgets apply to every request; decisions, results,
  truncation, and failure outcomes remain visible in inspectable logs/export.
- Deterministic fake-model boundary and recovery checks pass. The model cannot
  use any shell, network-fetch, repository-write, or policy-write handler.
- A reproducible report compares stage 1 against stage 0 and manual/deterministic
  baselines with held-out tasks and predeclared criteria, including failed runs.
- A human records stop/revise/promote. A negative evaluation can satisfy this leaf;
  adding authority or promoting code still needs separate reviewed work.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test` if shared package behavior is changed; such changes require scope review first.
- Run the documented opt-in fake-model boundary suite and record its exact command and results.
- Run the documented local-model comparison commands on the approved hardware/corpus and preserve sanitized per-task results.

## Risk Notes

More tool use can consume time without improving answers. A shared model may be
poor at valid structured calls despite good prose. Corpus approval is still a
privacy boundary. Search limits can omit relevant evidence, so the assistant must
admit incomplete coverage. A passing adversarial suite supports this small surface;
it is not a universal prompt-injection or safety guarantee.

## Dependencies / Order

After `WI-LOCAL-AGENT-001` and explicit human approval based on its findings.
The proposed item uses dependency metadata; `blocked: false` follows the schema
rule that only active items may be blocked. At activation, refresh dependencies
and record the advancement decision. No patch-drafting or execution leaf is
implicitly authorized by resolving this item.
