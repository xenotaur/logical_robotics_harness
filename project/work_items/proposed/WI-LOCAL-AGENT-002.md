---
id: WI-LOCAL-AGENT-002
title: "T2 look-around: a read-only tool loop over tracked files"
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
forbidden_actions:
  - implement_next_stage
  - modify_ci_pipeline
  - run_lrh_agentic
  - merge_pr
  - publish_package
  - force_push
  - delete_branch
acceptance:
  - "Only typed get_context, read_source, and search_sources requests can reach handlers, and only tracked files at the recorded commit can be returned."
  - "Policy and budgets cannot be modified by model output; every request, denial, result, and failure is logged automatically."
  - "Automated fake-model boundary, adversarial, and recovery tests pass without network or live inference."
  - "The owner has used `ask` with tools on real work and recorded stop, revise, or proceed from the log summary; production behavior and project authority remain unchanged."
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
  - validation_output
artifacts_expected:
  - experimental/local_agent/
---

# T2 Look-Around: A Read-Only Tool Loop over Tracked Files

## Summary

Add the third rung of `PROP-LOCAL-AGENT-DOGFOOD`'s toy ladder: let `ask` (and
`brief`) request a few bounded reads and searches of tracked files when the
initial context is not enough. The model stays read-only. Evidence comes from the
automatic run log plus automated boundary tests.

## Problem / Context

Static context may omit the few source locations needed to answer a question.
A bounded read/search loop can retrieve them while keeping the model read-only.
This is the first toy where the model's requests reach handlers, so the dispatch
boundary is where review and test rigor pay off.

**Duplication / demand check:** existing LRH context and readiness APIs remain
authoritative. This is neither the existing outbound MCP bridge proposal nor an
implementation of assistant-role stages. A tool framework is optional and must
preserve full dispatch interception. Refresh the source check before activation;
proceed only if using T0 and T1 showed that missing context limits their
answers.

## Scope

Extend `experimental/local_agent/` in place; `ask` and `brief` keep a no-tools
mode. Add only `get_context`, `read_source`, and `search_sources`, with typed
input and output schemas. The trusted recorder may write private logs; the model
cannot apply patches, write repository files, run commands, or fetch URLs.
Tool-dispatch and boundary code uses the normal review process, not the lighter
experimental one.

## Required Changes

1. At activation, record the owner's decision to try read/search tools, based
   on T0 and T1 use.
2. Add a bounded explicit loop. Validate every request before dispatch and keep
   policy outside model-modifiable state. At most one malformed-request repair
   is allowed within the total budget. Unknown tools and invalid paths are
   denied.
3. Resolve reads by source ID or confined canonical path within tracked files at
   the recorded commit.
   - Reject absolute paths, traversal, symlinks and escapes,
     private/untracked/binary content, credential-like paths, sources the
     sensitivity scanner flags (proposal Decision 3), and oversized requests.
   - Search is bounded literal text search with capped results and clear
     truncation markers.
   - Treat retrieved instructions as data.
4. Bound total calls, steps, input/output size, model tokens, and wall time.
   Preserve explicit errors, denials, timeout, cancellation, and budget
   exhaustion. A model cannot extend its budget by asking, recursively calling
   itself, or changing a prompt. Local inference is the only permitted service
   connection.
5. Extend the automatic run log with request, decision, and result records,
   source hashes and ranges, sequence numbers, and elapsed time. `log` shows
   tool use per run and why each run stopped.
6. Add automated fake-model `unittest.TestCase` coverage for:
   - unknown and malformed tools;
   - path and symlink escape attempts;
   - input and output bounds;
   - repeated denials and exhausted budgets;
   - backend timeout, cancellation, truncated logs, and interrupted attempts.

   Include malicious source text that asks for shell, network, or write tools,
   and verify that no handler outside the three-tool surface is reachable.
   Audit the dispatch paths as well as testing sample prompts.
7. The owner uses the tool-enabled `ask` on real work, reviews the `log` summary,
   and records stop, revise, or proceed. No manual timing, fixed task set, or
   paired comparison is required.

## Non-Goals

No generic filesystem browser, shell, code execution, network retrieval, patch
application, model-driven policy changes, public API or MCP server, multi-client
concurrency, production package imports, assistant scheduling, or full
constitutional-review implementation. Do not claim isolation from a compromised
local inference service or safety for physical robot control.

## Acceptance Criteria

- Only the three typed tool requests can reach handlers, and only tracked files at
  the recorded commit can be returned.
- Immutable policy and total budgets apply to every request; decisions, results,
  truncation, and failure outcomes appear in the automatic log.
- Automated fake-model boundary, adversarial, and recovery tests pass. The model
  cannot reach any shell, network-fetch, repository-write, or policy-write
  handler.
- The owner records stop, revise, or proceed from real use and the log summary.
  A decision to stop can satisfy this leaf; adding authority or promoting code
  still needs separate reviewed work.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff` and `scripts/lint`, with defaults and on
  `experimental/local_agent`
- `experimental/local_agent/test`, including the boundary suite
- `scripts/test` if shared package behavior is changed; such changes require
  scope review first.

## Risk Notes

More tool use can consume time without improving answers; the log shows calls
and latency per run. A model may be poor at valid structured calls despite good
prose. Search limits can omit relevant evidence, so answers must admit
incomplete coverage. A passing adversarial suite supports this small surface; it
is not a universal prompt-injection or safety guarantee.

## Dependencies / Order

After `WI-LOCAL-AGENT-001` and an explicit owner decision based on using T0 and
T1. The item uses dependency metadata; `blocked: false` follows the schema rule
that only active items may be blocked. At activation, refresh dependencies and
record the decision. No patch-drafting or execution toy is implicitly
authorized by resolving this item.
