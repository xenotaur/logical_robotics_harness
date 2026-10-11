---
id: PROP-LOCAL-AGENT-DOGFOOD
type: design_proposal
title: "Local Agent Dogfood and a Durable Session Boundary"
status: proposed
created_on: "2026-09-24"
updated_on: "2026-10-11"
implementation_status: not_started
implemented_by: []
supersedes: []
superseded_by: null
related_design:
  - project/design/execution_framework_mvp.md
  - project/design/proposals/proposed/workstream-execution-framework/04_layer4_agent_runtime.md
  - project/design/proposals/proposed/workstream-execution-framework/06_layer6_mcp_bridges.md
  - project/design/proposals/proposed/constitutional-sandbox-envelope/00_proposal.md
  - project/design/proposals/adopted/lrh-assistants/00_proposal.md
---

# Local Agent Dogfood and a Durable Session Boundary

## Summary

Build a local-first agent as a **ladder of small, usable toys**. Each toy is
something the owner can run on real LRH or LCATS work within days, not a
formal study. The starting point is the CODE Magazine agent: about 50 lines of
Python making one Gemma 4 12B call over a workspace. The first toy, **T0 ask**,
is that idea grounded in LRH: answer a question about the current checkout,
with source references. Each later toy adds one capability. Evidence scales with
authority: read-only toys are judged by the owner from automatic run logs, and
heavy evaluation and safety gates begin at the first toy that can change files
or run commands.

The long-term abstraction is an LRH-owned, durable session with a model-independent
semantic API. The native local runner and third-party agents use that same
authority boundary. MCP is the first agent-facing binding; vendor conversation
formats remain adapters. A separate reviewer contributes semantic judgment, while
deterministic policy and a constrained executor enforce permissions.

This is a **draft planning package for joint iteration**, not an adopted API or
authorization to run an agent. Two implementation leaves are filed, coordinated
by `WS-LOCAL-AGENT-DOGFOOD` under `WS-EXECUTION-FRAMEWORK`: `WI-LOCAL-AGENT-001`
(T0 ask and T1 brief, active) and `WI-LOCAL-AGENT-002` (T2 look-around,
proposed). See [Toy Ladder Approval](#toy-ladder-approval). No production runtime
code, dependencies, assistant scheduling, or serving mutations are introduced.

## Background / Motivation

Proprietary agent interfaces and export behavior change independently of LRH.
Cost and capacity limits also force work across several vendor sessions. LRH
should retain project context, policy, evidence, and continuity while allowing
the user to choose a local model or a third-party coding agent.

The Gemma coding-agent article is a starting point, not evidence that a
particular model or framework satisfies LRH's needs. The first question is
simple: is a local assistant useful enough on real LRH and LCATS work that the
owner keeps reaching for it? Usable toys answer that faster than a formal study,
and their automatic logs show where they fail.

The ladder also limits speculative infrastructure: exportable logs do not
require a public protocol, and a useful answer does not require autonomous
execution, a desktop application, or fine-tuning.

**Revision note (2026-09-29).** An earlier draft of this proposal made stage 0 a
pre-registered, counterbalanced pilot with manual timed baselines. The first
smoke run showed the prototype did not yet produce usable output, and the owner
judged the evaluation machinery disproportionate for read-only prototypes. This
revision replaces it with the toy ladder. The earlier text remains in Git
history, and `experiments/01_local_agent_briefing/` is marked superseded.

## Prior Art Check

Repository findings below are anchored to main commit
`8603b6514329ea242294da420aa448d2fc959fd1`. Paths and line numbers refer to that
snapshot. Recheck these contracts when activating a leaf.

| Existing source | Finding and consequence |
| --- | --- |
| `project/design/execution_framework_mvp.md:3-29,53-85` | Canonical architecture prioritizes manual contracts and safe-default surfaces. This proposal requests a separately approved experimental lane; it does not silently revise that priority. |
| `project/design/proposals/proposed/workstream-execution-framework/04_layer4_agent_runtime.md:15-34,77-85` | Existing proposed `RuntimeBackend` wraps Claude/manual/fake backends and explicitly excludes custom loops, a new permission system, and non-Claude backends. A local runner is a proposed extension; production adoption requires reconciling those non-goals. |
| `project/design/proposals/proposed/workstream-execution-framework/06_layer6_mcp_bridges.md:15-28` | Existing bridges expose external tools to LRH. The proposed agent-facing MCP adapter exposes LRH sessions to external agents: a complementary direction, with a separate trust boundary. |
| `project/design/proposals/proposed/constitutional-sandbox-envelope/00_proposal.md:127-184` | Layered constitutional review, capability policy, and sandboxing are already proposed. Extend that design before adding execution, rather than introducing a competing safety subsystem. |
| `src/lrh/assist/snapshot_cli.py:53-68`; `src/lrh/assist/run_packet.py:25-68` | Work-item snapshots and non-mutating, readiness-checked run packets already exist. Reuse their semantics and preserve their diagnostics; never manufacture readiness to get a packet. |
| `src/lrh/prompt_workflow_sessions.py:1-12,35-55` | Session identity and archive reconciliation exist. Host/child transcript identity is not an action-execution session contract. Link these identities later without replacing their meaning. |
| `project/workstreams/active/WS-LRH-ASSISTANTS.md:41-49,84-101` | Assistant roles have a staged plan and explicit archive/execution-tree gates. This experiment is a runner feasibility lane, not delivery of those assistant stages or permission to bypass their gates. |
| `experimental/README.md:3-17` | Temporary code belongs outside the package and default tests; private captures stay out of Git; promotion requires separate reviewed work. Follow this policy. |
| `project/design/backlog.md:1614-1659` | A separate `/lrh-assess` skill was judged unwarranted. Measure against deterministic readiness/context before inventing another assessment workflow. |

Also inspected the proposed parent workstream, the resolved
`WS-SESSION-ARCHIVE-SYNC`, and `WI-AGENT-BRANCH-CONTAINMENT`. Archive work has
advanced since some assistant blocker prose was written; this PR neither fixes
that prose nor unblocks assistant/runtime work. Branch containment remains a
separate dependency before mutation-capable work.

LCATS provides a useful organizational precedent:
[durable experiments](https://github.com/xenotaur/LCATS/tree/main/experiments)
and [temporary package experiments](https://github.com/xenotaur/LCATS/tree/main/lcats/experimental).
LRH now has both conventions: temporary code in `experimental/` and durable,
numbered reports in `experiments/` (`experiments/README.md`). It does not import
LCATS's package placement into LRH's production package.

**Duplication decision:** keep this as a child of the existing execution
workstream. Its distinct deliverable is a ladder of small, usable local-model
toys with automatic logging, not another production orchestrator, assistant role
model, session archive, or guardrail design.

## Design Decisions

### 1. A ladder of toys; evidence scales with authority

| Toy | What the owner can do | Added authority | Gate to the next toy |
| --- | --- | --- | --- |
| T0 — Ask | Ask a free-form question about the current checkout (optionally scoped to a work item or files) and get a streamed Markdown answer with source references. | One local inference over tracked text; no agent tools. | Owner has used it on real questions; the automatic log shows it completing reliably. |
| T1 — Brief | Get a structured briefing of one work item, including LRH readiness diagnostics. | Same as T0. | As T0, plus the automatic check that its readiness claims match the LRH diagnostics. |
| T2 — Look around | Ask questions that need a few additional reads; the model can request bounded read/search of tracked files. | Read-only tools over tracked files. | **Automated** dispatch-boundary and adversarial tests pass, plus the owner's judgment from the log. |
| T3 — Suggest a patch | Receive a proposed diff and validation plan; the owner applies and tests it by hand, outside the tool, if wanted. | Writes only to the private artifact store; no repository apply or command execution. | The log records automatically whether each patch would apply cleanly (a non-mutating check by trusted tool code, not a model action), plus the owner's rating and notes on how it went when applied by hand. |
| T4 — Execute under guardrails | Apply a reviewed patch and run bounded validation in an isolated workspace. | Explicit capabilities, independent action review, human escalation, sandboxed execution. | Durable action ledger, crash/retry reconciliation, containment and revocation demonstrated. |
| T5 — Resume and hand off | Resume work or attach a different agent through the same LRH session. | Authenticated session access and serialized action ownership; MCP adapter. | Two independent clients pass semantic conformance and interruption tests. |
| T6 — Local workbench | Inspect sessions, evidence, permissions, approvals, and model choices in a local UI. | Explicit user actions through the same API. | Preserve the read-only default and test the complete user workflow. |

T0–T3 are read-only with respect to the repository and project state, so their
gates rest on automatic logs and owner judgment. From T4, a toy can change files
or run commands, and the heavy design applies unchanged: Decision 6's action
contract, a transactional action ledger, and demonstrated containment. These are
capability gates, not calendar promises. Stopping is a valid outcome at any rung.

Only T0–T2 are currently decomposed into work items. Later toys require fresh
design review and executable leaves. A local web workbench can precede a Mac app
wrapper; private remote access follows local validation. Public service,
multi-user tenancy, quotas, abuse handling, and operational support require a
separate design. Linux/Windows portability is an interface requirement, not a
claim that Mac testing validates those platforms.

### 2. One evolving prototype with small typed boundaries

Use `experimental/local_agent/` for one evolving Python prototype, with an
explicit CLI and opt-in tests outside normal package discovery. Do not maintain
separate copied prototypes; earlier toys stay available as subcommands.

Initial boundaries are small internal Protocols/dataclasses:

- **Context provider:** adapts existing LRH snapshots/readiness/packets for one
  explicitly selected project and work item. An unready item can be explained,
  with its diagnostics intact; it cannot be presented as execution-ready.
- **Model adapter:** local inference with a pinned model/quantization and
  recorded runtime version. Ollama is the initial candidate, not a required
  production dependency. Gemma is a candidate to measure, not the API's identity.
- **Runner:** one call for T0 and T1; a bounded explicit loop from T2. It never
  owns credentials or gets direct filesystem, shell, or network execution tools.
- **Dispatcher/policy:** validates typed requests and immutable budgets before
  any tool handler. Model output cannot rewrite policy or widen the source set.
- **Recorder:** trusted persistence of inputs, outputs, outcomes, and provenance
  to a private directory, separate from model-accessible repository sources.
- **Evaluator:** records a one-key owner rating and an optional note per run;
  generation completion never constitutes human acceptance or project status
  evidence.

| Option | Advantage | Limitation / decision |
| --- | --- | --- |
| Small explicit loop | Easy to audit the complete first-stage dispatch surface; few dependencies. | LRH owns retry and event plumbing. Recommended for the read-only toys. |
| Framework such as smolagents behind Runner | Existing agent-loop facilities may reduce later maintenance. | Adopt only if all tool paths are interceptable and logs/budgets remain LRH-controlled. An unrestricted code-executing agent is unsuitable for T2. |
| Vendor agent SDK adapter | Strong coding behavior with less runner implementation. | Retains vendor cost and lifecycle dependencies. Useful as another client/backend, not the only session authority. |
| Full session server first | Early external-agent interoperability. | Expensive before workflow value is established. Defer stable API commitments while preserving typed seams. |

No option has a universal performance advantage without measurement. A runner
that can bypass the dispatcher is disqualified from a claimed managed mode;
it can still be an explicitly advisory external client.

### 3. Keep the data boundary simple for read-only toys

Read-only toys (T0–T3) read only files tracked at the current checkout's `HEAD`,
from Git objects rather than the working tree, so uncommitted edits never mix in.
A `--commit` option pins another revision. Before calling the model, the tool
prints a short summary of the sources it will send (paths, line ranges, sizes);
no hash approval step is required.

Excluded by default:

- private transcripts and session, execution, and memory records;
- untracked content and binary files;
- **credential-like paths:** `.env*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`,
  `id_rsa*`, `id_ed25519*`, and names containing `credential` or `secret`,
  plus `.netrc`, `.npmrc`, and `.pypirc`;
- **any source with a high-severity finding from LRH's sensitivity scanner**
  (`lrh.conversations.sensitivity`): secrets, tokens, private keys, credentials
  in URLs, and payment-card or government-ID numbers. Every source is scanned
  before sending, and such a source is dropped and listed as excluded in the
  source summary, unless the owner overrides it for that file (below).

Medium-severity findings (email addresses, IP addresses, phone numbers) do not
exclude a source; the source summary lists them as warnings, by category and
never by value, so the owner sees them before the model is called. Excluding on
them dropped common documentation such as the repository README, which
mentions `127.0.0.1`. Such text does reach the model, which is acceptable only
because the adapter's local-only checks keep it on this machine. Anything
leaving the private store stays stricter: exports and, if implemented, the
`report` summary withhold text on any finding.

**Explicit owner override for scanner findings.** The scanner's rules were
written for transcripts and configuration text, and they misfire on code: a
Python parameter named `token` annotated with a `Callable` type reads as a
secret assignment, which excluded `experimental/local_agent/recorder.py`. The
owner may send such a file anyway, with
`--allow-flagged <path>=<category>[,<category>...]` on a `--files` question:

- **scope:** only files named in the same command's `--files`, matched after
  the same path normalization; never `--wi`, `brief`, or overview questions,
  and never model-initiated T2 reads or searches;
- **what it lifts:** only the exclusion for a high-severity scanner finding,
  and only for the categories the owner names. If the file has any other
  high-severity category, or none, the run is refused. The owner therefore
  names categories already reported for that file, and a changed file cannot
  slip a new kind of finding through;
- **what it never lifts:** private paths, untracked or binary files, and
  credential-like file and directory names (so `src/lrh/secrets/` stays
  excluded by path, whatever the scanner says);
- **refusals:** an override for a file that was not requested, is excluded by
  path, or lacks a high-severity finding is refused with its reason, not
  silently ignored;
- **per-finding confirmation:** a category cannot tell a false positive from
  a real secret of the same category (that `token` annotation and a real
  password assignment are both `secret`). So an override run always stops at
  a confirmation that lists every finding it would let through, by rule and
  line, never by value (`ALLOWED DESPITE <category>: <rule> at L<n>`, shown
  in the terminal only and never stored). `L<n>` is the line where the match
  starts, `L<a>-L<b>` when it spans lines, and `L?` when the scanner reports
  no line. A newly added secret therefore shows up as a new line before the
  owner decides. The confirmation comes before the model adapter is built or
  any model call is made; only a typed `yes` sends, anything else (including
  a bare Enter) declines, and a decline is logged as `cancelled` with nothing
  sent. `--allow-flagged` is refused with `--yes` and without an interactive
  terminal;
- **the final context scan:** the prototype also scans the whole assembled
  context before sending. That scan skips only the allowed file's numbered
  body lines, which were already scanned once, on raw text, for the
  confirmation. It still scans everything else, including that file's own
  header with its path, the other requested files, and the excluded-sources
  block, and refuses the request on any high-severity finding there.
  Positions are never compared across the two scans, because the rendered
  context adds headers and line prefixes;
- **visibility:** the run record notes the override and the confirmed
  findings as structured fields (path, category, rule ID, start and end
  line), never by value and never as `category: rule` text, which the
  secret rule itself would match at export;
- **what is stored:** the allowed file's text reaches the model and may
  appear in the private store (for example, echoed in an answer); exports
  are unchanged and withhold any text with a finding.

Recorded 2026-10-08 by the owner: this trades a little of the guard for
usability, by the owner's explicit, per-run decision, while inference stays
local. Fixing the scanner's false positives on code is a separate work item
(`WI-SENSITIVITY-ASSIGNMENT-RULE-CODE-FP`).

This is a best-effort guard, not a guarantee; the source summary is shown on
every run, and budgets cap what is sent. The same exclusions apply to T2 tool
reads and searches.

From T2, tools may read or search only those tracked files, through typed
`get_context`, `read_source`, and `search_sources` requests with validated
schemas. Paths resolve inside the tracked set; absolute paths, traversal,
symlink escapes, and unknown source IDs are rejected. Search is bounded literal
text search, not shell interpolation or an unrestricted regular expression
engine. Calls, steps, input/output bytes, model tokens, and wall time are
capped. Truncation and missing files are reported explicitly. Source content is
data, even when it contains instructions to an agent.

**Local-only inference.** Use an explicitly configured local inference service
and a locally installed model. A loopback endpoint alone does not prove local
inference, because the service could forward a remote model's requests. The
adapter therefore requires a loopback endpoint with proxies and redirects
disabled, requests only a pinned locally installed model digest, refuses any
model the service reports as remote or cloud-tagged before sending a prompt, and
records these checks on every run. No cloud fallback, automatic model download,
automatic installation, or external network tool is allowed. The inference
service remains a trusted component; this is not OS isolation against a
compromised daemon. Disabling the service's cloud features is optional defense
in depth.

### 4. Log every run automatically; keep it private and non-canonical

Every run of every toy writes a private record: question or work item, sources
sent (paths, commit, hashes, line ranges), model and backend versions, prompt
version, budgets, timings, token counts, outcome, automatic checks (such as
citation resolution), and the owner's rating and note if given. Failed,
cancelled, and timed-out runs are recorded like any other, so they cannot
silently disappear from what the owner reviews. Outcomes distinguish
`completed`, `missing_prerequisite`, `budget_exhausted`, `invalid_model_output`,
`backend_error`, `timeout`, and `cancelled`. `completed` means inference ended,
not that the answer is correct.

For T0–T3, a single-process JSONL and artifact store is sufficient, as already
built in `experimental/local_agent/` (single writer, atomic manifests, recovery
of an interrupted tail). Do not promise that replaying inference reproduces an
answer. A resumed run is a new attempt linked to the previous one, and it never
silently executes a partial tool request. A transactional action ledger is
required from T4, before any side-effect dispatch.

Store records in a private user-data directory with restrictive permissions
(`~/.local/share/lrh/local-agent/` by default, overridable with
`LRH_LOCAL_AGENT_STORE`), outside any Git worktree. Keep records until
`WS-LOCAL-AGENT-DOGFOOD` closes, plus 90 days. The tool provides `delete
<run-id>` and `prune --before <date>` commands, and deleting the store
directory removes everything.
Raw prompts, context, and model outputs are not committed to Git; a sanitized
summary may be committed to `experiments/` when the owner wants a durable
record. These are **experimental attempt logs**, not canonical `project/runs` or
work-item state; promoting them requires an explicit reviewed mapping. The
recorder's trusted writes do not give the model repository write permission.

### 5. Grow a native semantic Session API; bind it to MCP first

Do not freeze endpoint names in the prototypes. Preserve the conceptual
separation among an authenticated actor, durable LRH session, run/attempt,
vendor conversation, and transport connection. The session survives connections
and model changes; a vendor transcript is an attachment, not authoritative state.

A later versioned API should cover capabilities, session creation/attachment,
context inspection, proposed actions, action decisions, execution status,
event cursors, artifacts, cancellation, and evidence submission. The local CLI,
UI, native runner, and MCP server call the same service layer. A separate REST
server is optional, not a prerequisite for a native API.

The public contract must specify typed schemas, errors, authorization scopes,
session/action state machines, idempotency keys, optimistic revisions,
capability negotiation, event ordering/retention, and compatibility policy.
Provide conformance tests and a second independently written client before
claiming anyone can implement it. MCP handles connection/tool exposure; it does
not itself define LRH durability, execution authority, or workflow semantics.

| Connection mode | LRH guarantee |
| --- | --- |
| Advisory external agent | LRH protects its own tools; it cannot govern actions the agent performs elsewhere. |
| Managed native agent | All model-requested actions pass through LRH policy and executor boundaries. |
| Brokered external agent | Equivalent mediation only if its workspace/tools/credentials prevent bypass and that containment is tested. |

Skills/plugins teach an agent how to attach and use the tools. They improve
usability; they are not an enforcement mechanism. The external agent may retain
its own reasoning/session language, but must use LRH references, decisions, and
capabilities for actions inside an LRH-managed runtime.

### 6. Put constitutional judgment inside an enforceable safety design

The read-only toys (T0–T3) confine reads to tracked files and enforce each read
deterministically. They do not claim to implement the full second-agent review
design. Before T4, reconcile and adopt the existing constitutional sandbox
envelope with an explicit action contract:

1. An agent proposes a normalized action with resources and expected effects.
2. Hard policy validates scope/budgets; a separate reviewer assesses intent,
   instruction conflicts, disclosure, and semantic risk from bounded context.
3. Required human decisions are collected. A reviewer may deny/escalate and may
   not grant authority forbidden by policy; reviewer failure denies or pauses.
4. The executor validates a short-lived decision bound to the exact action digest,
   actor, workspace revision, policy version, and capability before dispatch.
5. Persist the decision before dispatch and record results and verification after.

Every externally effectful operation must use this path, including writes,
commands, network access, publication, and robot actions. Define read/disclosure
classes explicitly; a read that exposes private data outside its authorized
boundary is not exempt simply because it does not modify a file. The trusted
recorder is a narrow platform capability, not a generic write tool.

The reviewer has no execution capability and cannot modify its own constitution.
Different context and, where feasible, a different model reduce shared failure
modes but do not prove independence or safety. Log decisions and concise reasons,
not hidden chain-of-thought. Human escalation and sandbox enforcement remain
necessary; a second model does not guarantee alignment.

Before effects, specify stale-grant rejection, revocation, cancellation races,
crash recovery, and reconciliation of unknown outcomes. Idempotency is not an
exactly-once guarantee for arbitrary external effects. Physical robotics needs
additional hardware/interlock and domain-specific safety work; this coding prototype
does not authorize robot control.

### 7. Evaluate by using it; automate the evidence

Evaluation for T0–T3 is built into the tool, not run as a separate study:

- **Automatic logging** of every run (Decision 4).
- **A one-key rating** after each answer (good / ok / bad) with an optional note.
  Skipping the rating is allowed and recorded.
- **`log` summaries** computed from the records: run counts, outcome mix,
  latency and token distributions, rating distribution, citation-resolution
  rate, and flagged runs. An optional `report` command writes a sanitized
  summary for committing to `experiments/`.
- **Automatic flags** where cheap: for example, a T1 briefing whose readiness
  statement contradicts the LRH diagnostics, or a citation to a source that was
  not sent.

At each toy boundary the owner decides stop, revise, or proceed, informed by the
log summary and experience. No numeric thresholds are required in advance, and
no manual timing or hand-written baselines are collected. Stop signals: the
toy fabricates readiness or status, any sign of off-machine routing, or the
owner stops finding it worth using. A disappointing toy may still be worth a
revision; an impressive one may still be unacceptable. The decision is the
owner's.

Structured, comparative evaluation (fixed task sets, baselines, adversarial
suites) is used where it protects something: automated boundary tests from T2,
and the full safety evidence from T4.

## Non-Goals

- A production agent runtime, public protocol, stable SDK, or immediate MCP server.
- Automatic work-item transitions, evidence acceptance, merge, release, or publish.
- Changing the default `lrh serve` permission surface or enabling assistant stages.
- Shell execution, patch application, arbitrary tools, or network access in the
  read-only toys (T0–T3).
- Autonomous multi-agent scheduling or physical robot control.
- A model leaderboard, commercial service, or guaranteed local-model equivalence
  to Claude, Codex, or Antigravity.
- Fine-tuning before a usable baseline and a curated, permissioned evaluation set.

## Implementation Plan

1. **T0 ask and T1 brief** (`WI-LOCAL-AGENT-001`): `ask` and `brief` commands
   with streamed Markdown output, model thinking off, the automatic log, a
   one-key rating, and `log` summaries. Reuse the existing modules under
   `experimental/local_agent/` (sources, context, model adapter, recorder).
2. The owner uses T0 and T1 on real work and decides stop, revise, or proceed.
3. **T2 look-around** (`WI-LOCAL-AGENT-002`), only after an explicit decision
   that read/search access is worth trying.
4. T3 and later toys require separately scoped work items; T4 and later also
   require the safety design in Decision 6.

Temporary code lives in `experimental/local_agent/` as one evolving CLI. Durable
write-ups, when wanted, go in numbered `experiments/` directories. Full raw logs
stay in the private store. Avoid adding `prototypes/` or `examples/` as
competing homes for the same code.

Later: native Session API and MCP conformance; local web UI and optional desktop
packaging; private remote access; separately designed multi-user service. Build
an opt-in dataset from reviewed runs with provenance, permissions, redaction,
quality labels, and train/evaluation separation. Fine-tune only if measured error
patterns warrant it, and compare against prompt/context/model changes first.
Pin and version model artifacts and retain rollback. MIT licensing for harness
code does not relicense model weights, datasets, or third-party dependencies;
check their terms before distribution.

## Toy Ladder Approval

Recorded 2026-09-29 by the owner. It replaces the earlier stage-0 lane approval
(2026-09-25). The proposal as a whole remains `proposed`.

**Approved:**

- The isolated experimental lane for read-only toys T0 and T1 under
  `experimental/local_agent/`, outside the package and default test discovery,
  with no project-state writes.
- `WI-LOCAL-AGENT-001` (active) re-scoped to T0 ask and T1 brief.
- Evaluation by automatic logging and owner judgment (Decision 7).
- The [Experimental PR Process](#experimental-pr-process), in effect for this
  workstream's PRs. Like the rest of this approval, it is an owner decision
  scoped to `WS-LOCAL-AGENT-DOGFOOD` while the proposal as a whole remains
  `proposed`; it does not apply elsewhere unless adopted.

**Not approved:** T2 (`WI-LOCAL-AGENT-002` stays proposed), later toys, the
native Session API and MCP binding (Decision 5), the constitutional execution
contract (Decision 6), and any production runtime or backend adoption. Each
needs its own decision.

## Experimental PR Process

PRs whose changes are confined to `experimental/` (transient code) and
`project/executions/` (bookkeeping) use a lighter review process. Everything
else, including `experiments/` (archival), planning artifacts, `src/lrh/`, CI,
and skills, uses the normal process.

- **Kept:** automated validation before push; one diff-mode self-review; the
  hosted bots' first-push review and one round of fixes; one confirm-fixes
  pass and one substitute review of the final head; the owner's single
  merge-and-closeout decision; execution records.
- **Severity-gated halts:** only correctness, safety, data-integrity, or
  medium-and-higher findings stop the chain and start another fix round.
- **Deferred findings:** lower findings are not fixed in a new round. Each is
  recorded in the PR's closeout note, named explicitly at the merge gate (a
  deferred review thread gets a reply and uses `/lrh-land`'s named "defer"
  path), and offered at the next toy's plan gate. Open follow-ups are reviewed
  when the workstream closes.
- **Exception:** from T2, tool-dispatch and boundary code uses the full process.
- Promoting code from `experimental/` into `src/lrh/` requires separate reviewed
  work under the normal process.

The process is applied per run through each chain's stated stop-work condition;
the repository's stored default is unchanged unless the owner changes it with
`/lrh-config-gates`.

## Open Questions for Joint Review

- Which question types does T0 serve best (explaining code, finding where
  something lives, summarizing a design), and should T1 briefings stay a separate
  command or become a preset of `ask`?
- What context should T0 send by default when no work item or files are given:
  a directory listing plus README, or a user-chosen file set?
- Which existing run/session types should be reused when promoting the prototype,
  and which policy changes must accompany the non-Claude runtime extension?

## References

- [CODE Magazine: Local Vibe Coding with Gemma 4 12B](https://www.codemag.com/Article/2610021/Local-Vibe-Coding-with-Gemma-4-12B)
  — motivating example, not a dependency or validated LRH result.
- [Ollama tool calling](https://docs.ollama.com/capabilities/tool-calling)
  — candidate model integration surface.
- [smolagents documentation](https://huggingface.co/docs/smolagents/index)
  — alternative runner implementation to evaluate only if needed.
- [MCP architecture](https://modelcontextprotocol.io/docs/2026-07-28/learn/architecture)
  — transport/client/server context for a later agent-facing binding.
- [Robot Constitutions](https://arxiv.org/abs/2503.08663)
  — motivation for separate semantic review; reported experimental alignment is
  not a guarantee for LRH coding or robotics actions.
- [CODE Magazine: Fine-Tuning Large Language Models, Part 1](https://www.codemag.com/Article/2610031/Fine-Tuning-Large-Language-Models-Part-1)
  — deferred learning pathway after useful, permissioned run data exists.
