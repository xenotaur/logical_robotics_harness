---
id: WI-LOCAL-AGENT-001
title: "Build and evaluate a local work-item briefing prototype"
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
depends_on: []
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
  - "An opt-in local CLI briefs one selected work item from an approved immutable context packet with no agent tools."
  - "Private versioned logs and sanitized exports preserve provenance, diagnostics, and failure outcomes."
  - "Deterministic fake-model tests cover data boundaries, recording, and interruption without model or network access."
  - "A reproducible pilot compares deterministic/manual and single-call local baselines with predeclared criteria."
  - "A human records a stop, revise, or proceed decision; production behavior is unchanged."
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
  - validation_output
artifacts_expected:
  - experimental/local_agent/
  - experiments/README.md
  - "Numbered local-agent briefing experiment with sanitized findings and provenance."
---

# Build and Evaluate a Local Work-Item Briefing Prototype

## Summary

Deliver stage 0 of `PROP-LOCAL-AGENT-DOGFOOD`: a small opt-in Python CLI that
explains one chosen LRH work item using a local model and a static context packet.
Use it on real work, export its record, and measure whether it reduces effort.
There is no agent tool loop in this leaf.

## Problem / Context

A full agent runtime is unjustified until a local model demonstrably helps with
a narrow daily task. Briefing should summarize intent, constraints, dependencies,
evidence gaps, relevant sources, and questions for the human. It must distinguish
source facts from suggestions and avoid presenting unready work as ready.

**Duplication / demand check:** the parent proposal records source-grounded prior
art at commit `8603b6514329ea242294da420aa448d2fc959fd1`. Reuse
`src/lrh/assist/snapshot_cli.py:53-68` and the diagnostics from
`src/lrh/assist/run_packet.py:25-68`; do not implement another control-plane
loader or assessment skill. The new demand is a measured local-language briefing
plus portable run evidence, not another readiness authority. Refresh this check
and the applicable runtime/assistant gates before activation.

## Scope

One evolving prototype under `experimental/local_agent/`, with a documented
Python entry point, a deterministic fake model, and one optional local-model
adapter. Mac is the initial live-test platform. Interfaces and paths should be
portable Python; do not claim Linux/Windows support without testing.

The implementation agent may edit the scoped prototype/evidence files. The
prototype model itself receives no execution, filesystem, or network tools and
cannot modify repository files or project state. These are different authorities.

## Required Changes

1. Before coding, record approval of the experimental lane, the target Mac/RAM,
   locally installed model/quantization, safe task corpus, private storage path,
   retention policy, and numerical usefulness/latency criteria. Do not download a
   model or use a cloud-backed service implicitly.
2. Implement explicit project/work-item selection, context generation using
   existing LRH semantics, preserved readiness diagnostics, and source references
   with commit, content hashes, and line ranges. Materialize an approved immutable
   text packet; reject untracked/private/binary sources and over-budget input.
   Readiness errors must remain visible even when a briefing can still be made.
3. Implement small typed model/context/recorder seams and a one-call runner.
   Pin/record prompt, model, backend, and policy versions. Enforce input/output,
   token, and wall-time bounds; distinguish missing prerequisites, cancellation,
   timeout, malformed output, and completion. Do not hide stopped attempts.
4. Add a private single-writer JSONL/artifact store with versioned manifests,
   source provenance, actual outputs, checkpoints, and outcome. Handle a truncated
   final event without treating the attempt as successful. Provide readable
   inspection and explicit sanitized export; raw content stays out of Git.
   Logs are experimental evidence, not canonical run or work-item state.
5. Document a durable `experiments/` convention and use the next available numbered
   directory. Record task definitions or reproducible references, source/code
   commits, setup, exact invocation commands, scoring rubric, sanitized per-task
   results, failures, limitations, and human decision. Keep private artifacts in
   the durable user-data store, not disposable temporary directories.
6. Add opt-in `unittest.TestCase` tests under the prototype tree, with a documented
   test runner. Use a fake backend for context bounds, preserved diagnostics,
   provenance/export, timeout/error handling, and interrupted recording. Do not
   add live model/network calls to normal CI or normal package test discovery.
7. Run a small pilot (approximately 12 tasks across LRH/LCATS, some held out) against
   deterministic/manual and one-call local baselines. Report citation support,
   unsupported claims, correction/review time, human effort, latency/resources,
   and all failures. Record a human stop/revise/proceed decision using the
   predeclared rubric. A negative result is a valid deliverable.

## Non-Goals

No read/search loop, patch drafting/application, shell tools, cloud fallback,
project-status writes, production imports/dependencies, MCP server, desktop UI,
assistant-stage activation, public service, fine-tuning, or model benchmarking
unrelated to the selected workflow. Do not modify the default serve surface.

## Acceptance Criteria

- An opt-in local CLI briefs one selected work item from an approved immutable
  context packet; it has no agent tools and reports unresolved facts honestly.
- Private versioned logs and sanitized export retain source references, readiness
  diagnostics, model/prompt configuration, outcomes, and interruptions.
- Fake-model tests demonstrate the recording and data boundaries without a live
  inference service or network access.
- A reproducible live pilot compares the required baselines using criteria chosen
  beforehand. The report includes poor results and does not equate generated
  completion with task acceptance.
- A human records stop/revise/proceed. No runtime authority, project state, default
  package test discovery, or production API changes as part of this leaf.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test` if shared package behavior is changed; such changes require scope review first.
- Run the prototype's documented opt-in fake-model test command and record it in the experiment report.
- Run the documented live-model pilot commands on the selected Mac only after the corpus and budgets are approved.

The implementation must document how its opt-in checks use repository-pinned
tool versions without adding `experimental/` to default test discovery. No model
performance requirement is asserted to have passed by merely adding tests.

## Risk Notes

A model can invent a readiness fact or cite a real file that does not support its
claim. Score support, not just citation existence. Selected tracked text can
contain secrets; inspect the manifest and exports. Local daemon configuration can
enable cloud routing; verify local-only inference. Tiny tasks and practice effects
can exaggerate time savings; preserve held-out tasks and compare total effort.

## Dependencies / Order

Proposed, not active. Requires approval of the design's isolated experimental
lane and the pre-run choices above. No hard dependency on an unfinished production
runtime is implied because this leaf adds no execution authority. Any contrary
canonical sequencing decision must be reconciled before activation.

`WI-LOCAL-AGENT-002` depends on this leaf and a separate human advancement decision;
resolving this leaf does not start it automatically.
