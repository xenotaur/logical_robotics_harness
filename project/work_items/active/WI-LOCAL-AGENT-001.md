---
id: WI-LOCAL-AGENT-001
title: "T0 ask and T1 brief: usable local-model toys with automatic logging"
type: deliverable
status: active
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
forbidden_actions:
  - implement_next_stage
  - modify_ci_pipeline
  - run_lrh_agentic
  - merge_pr
  - publish_package
  - force_push
  - delete_branch
acceptance:
  - "`ask` answers a free-form question about the current checkout from tracked files, streaming readable Markdown with source references, with no agent tools."
  - "`brief` produces a work-item briefing that carries LRH readiness diagnostics and flags claims that contradict them."
  - "Every run is logged automatically and privately, including failures, with a one-key rating and a `log` summary; no manual bookkeeping is required."
  - "Sources matching the listed credential-like patterns, or with a high-severity sensitivity-scanner finding, are never sent to the model or logged, while medium-only sources are still sent with category-only warnings, shown by boundary tests on both sides (a best-effort guard, per proposal Decision 3); `export` and `report` withhold text on any finding; logs can be deleted and pruned."
  - "Fake-model tests cover the commands, logging, and local-only checks without model or network access."
  - "The owner has used both toys on real work and recorded a stop, revise, or proceed decision; production behavior is unchanged."
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
  - validation_output
artifacts_expected:
  - experimental/local_agent/
---

# T0 Ask and T1 Brief: Usable Local-Model Toys with Automatic Logging

## Summary

Deliver the first two rungs of `PROP-LOCAL-AGENT-DOGFOOD`'s toy ladder as
commands the owner can use on real work right away:

- **T0 ask:** ask a free-form question about the current checkout and get a
  streamed Markdown answer with source references.
- **T1 brief:** get a structured briefing of one work item, carrying LRH's
  readiness diagnostics.

Every run is logged automatically. There is no agent tool loop in this leaf.

## Problem / Context

The starting point is the CODE Magazine agent: about 50 lines making one local
Gemma call over a workspace. An earlier version of this item required a
pre-registered, twelve-task pilot with manual timed baselines before any
decision. The first smoke run showed the prototype did not yet produce usable
output (all 2,048 output tokens went somewhere other than the answer, most likely
hidden model reasoning), and the owner judged that evaluation machinery
disproportionate for read-only toys. This item now aims at something usable
first, with evidence collected automatically.

Much of the plumbing already exists in `experimental/local_agent/` from PRs #735
and #745: pinned tracked-file sources, LRH readiness and context reuse, the
local-only Ollama adapter, the private recorder with recovery, and export. Reuse
it rather than rebuilding.

**Duplication / demand check:** reuse existing LRH readiness and context seams:

- `evaluate_readiness` (`src/lrh/work_items/readiness.py:47`);
- `render_run_packet_from_work_item` (`src/lrh/assist/run_packet.py:25-68`);
- `render_ready_work_item_request` (`src/lrh/assist/ready_work_item.py:73-90,137`).

Do not implement another control-plane loader or assessment skill.

## Scope

One evolving CLI under `experimental/local_agent/`, outside the package and
default test discovery, with a fake backend for tests and the local Ollama
adapter for real use. Mac is the initial platform. The implementation agent may
edit the prototype files; the model itself receives no execution, filesystem, or
network tools and cannot modify repository files or project state.

## Required Changes

1. **Make it produce output.** Turn model thinking off in requests (or record
   thinking separately), stream the answer to the terminal as it arrives, and
   set output budgets so a normal answer fits.
2. **T0 `ask "<question>"`.** Context comes from tracked files at `HEAD`, read
   from Git objects:
   - with `--wi <WI-ID>`, the work item and its related sources;
   - with `--files <paths>`, those tracked files;
   - otherwise, the repository README plus a tracked-file listing.

   Print a short source summary before calling the model. Answers are Markdown
   and cite sources as `S<n>` or `S<n>:L<a>-L<b>`. Exclude:
   - private paths, untracked files, and binary files;
   - credential-like paths, per the proposal's Decision 3 list;
   - any source with a high-severity finding from the sensitivity scanner
     (`lrh.conversations.sensitivity`), which is dropped and listed as
     excluded in the source summary. Medium-severity findings (email, IP
     address, phone) are listed as warnings instead, per Decision 3.

   Enforce input, output, and wall-time budgets.
3. **T1 `brief <WI-ID>`.** A briefing preset built on T0 that includes LRH
   readiness diagnostics. Automatically flag a briefing whose readiness claims
   contradict the diagnostics.
4. **Automatic logging and rating.**
   - Record every run privately (`~/.local/share/lrh/local-agent/`): question
     or work item, sources, model and prompt versions, timings, tokens,
     outcome, citation checks, and flags. Failed and cancelled runs are
     recorded too.
   - After each answer, prompt for a one-key rating (good / ok / bad, or skip)
     and an optional note, and store them with the run.
5. **Retention and deletion.** Document the store path
   (`~/.local/share/lrh/local-agent/`, or `LRH_LOCAL_AGENT_STORE`) and the
   retention (until the workstream closes, plus 90 days). Provide
   `delete <run-id>` and `prune --before <date>`.
6. **`log` summary.** Show recent runs and computed statistics: counts, outcome
   mix, latency and token distributions, ratings, citation-resolution rate, and
   flagged runs. An optional `report` writes a sanitized summary suitable for
   committing to `experiments/`. Like `export`, it withholds any question,
   rating note, or generated text in which the sensitivity scanner reports any
   finding, medium-severity (email, IP address, phone) included.
7. **Tests and docs.** Opt-in fake-backend `unittest.TestCase` tests for the new
   commands, logging, rating capture, flags, and deletion. Boundary tests must
   cover both sides of the severity boundary:
   - credential-like paths and sources with high-severity scanner findings are
     never sent or logged;
   - medium-only sources are still sent, and their warnings name categories but
     never the matched values;
   - `export` and `report` withhold text with any finding, including a
     medium-only finding in a question, rating note, or answer. Update `experimental/local_agent/README.md` to describe the
   toys; the pilot runbook material is retired. Do not add live model or
   network calls to normal CI.
8. **Use it and decide.** The owner uses `ask` and `brief` on real LRH or LCATS
   work, reviews the `log` summary, and records stop, revise, or proceed in this
   item's resolution. No numeric thresholds, manual timing, or hand-written
   baselines are required.

## Non-Goals

No read/search tool loop, patch drafting or application, shell tools, cloud
fallback, project-status writes, production imports or dependencies, MCP server,
desktop UI, assistant-stage activation, public service, fine-tuning, or formal
comparative study. Do not modify the default serve surface.

## Acceptance Criteria

- `ask` answers free-form questions from tracked files with streamed Markdown and
  source references; it has no agent tools.
- `brief` carries LRH readiness diagnostics and flags contradicting claims.
- Every run is logged automatically and privately, including failures, with a
  one-key rating and a `log` summary; no manual bookkeeping is required.
- Sources matching the listed credential-like patterns, or with a high-severity
  sensitivity-scanner finding, are never sent to the model or logged.
  Medium-only sources are still sent, with warnings that name categories but
  never values. `export` and `report` withhold text with any finding. Boundary
  tests show both sides. This is a best-effort guard (proposal Decision 3), not
  a guarantee against every secret. Logs can be deleted and pruned.
- Fake-model tests cover the commands, logging, and local-only checks without a
  live inference service or network access.
- The owner has used both toys on real work and recorded stop, revise, or
  proceed. No runtime authority, project state, default package test discovery,
  or production API changes as part of this leaf.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff` and `scripts/lint`, with defaults and on
  `experimental/local_agent`
- `experimental/local_agent/test`
- `scripts/test` if shared package behavior is changed; such changes require
  scope review first.

## Risk Notes

A model can invent a readiness fact or cite a real file that does not support its
claim; the automatic flags and citation checks catch some of this, and the rating
note records the rest. Tracked text can contain secrets; the source summary is
shown on every run. Local daemon configuration can enable cloud routing; the
adapter's local-only checks run before every prompt.

## Dependencies / Order

Active since 2026-09-25; re-scoped on 2026-09-29 by the owner's toy-ladder
approval (the parent proposal's "Toy Ladder Approval" section). PRs #735 and #745
delivered reusable plumbing and are partial progress. Code PRs for this item use
the proposal's Experimental PR Process. This item resolves when the owner
records a decision after using the toys.

`WI-LOCAL-AGENT-002` (T2) depends on this leaf and a separate owner decision;
resolving this leaf does not start it automatically.
