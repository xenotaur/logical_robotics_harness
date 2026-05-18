---
id: PROP-LRH-CONVERSATIONS-STORAGE-INTEROP
type: design_proposal
title: LRH Conversations, Storage, and External Agent Interop
status: proposed
created_on: 2026-05-16
updated_on: 2026-05-16
implementation_status: not_started
related_design:
  - project/design/architecture.md
  - project/design/design.md
  - project/design/meta_control_plane_mvp_spec.md
  - project/design/execution_framework_mvp.md
  - project/design/proposals/proposed/workstream-execution-framework/00_proposal.md
  - project/design/proposals/proposed/constitutional-sandbox-envelope/00_proposal.md
  - project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md
  - PROMPTS.md
  - project/executions/README.md
supersedes: []
superseded_by: null
---

# LRH Conversations, Storage, and External Agent Interop Design Proposal

## Summary

This proposal defines **LRH Conversations, Storage, and External Agent
Interop** as a unified architecture for making AI-assisted development
conversations and tool work auditable, private-by-default, scoped,
promotable, and interoperable.

LRH should become a control-plane hub and protocol layer around many tools,
not a replacement for every chat or agent tool. External tools such as
ChatGPT, Codex, Claude Code, GitHub Copilot, Aider, Kiro-like systems, GitHub
integrations, and future agents should be able to exchange context,
proposals, progress, and evidence with LRH without turning raw conversation
history into authoritative project state.

This is a design-only proposal. It records storage semantics, conversation
semantics, protocol boundaries, safety rules, and implementation phasing. It
does not implement storage code, a chat UI, an MCP server, a GitHub App, model
provider integration, HTTP behavior, or run execution behavior. The companion
[`01_chatgpt_pdf_import.md`](01_chatgpt_pdf_import.md) design note records an
early manual capture path for converting ChatGPT browser Save as PDF exports
into private-by-default, non-authoritative Markdown transcripts.

## Motivation

AI-assisted development work often happens in opaque external chats and agent
tools. Useful reasoning, decisions, prompt attempts, failures, handoffs,
review notes, and context packets can remain trapped in vendor silos or local
sessions that are hard to audit later.

LRH's value is explicit, evidence-backed, human-auditable, and
machine-interpretable workflow state. LRH already treats project documents,
work items, evidence, status, and executions as control-plane artifacts rather
than optimistic summaries. Conversations should fit that philosophy: they can
be rich context and useful provenance, but they are not automatically truth.

The goal is to preserve user control over data and process while allowing
users to keep using best-of-breed tools. LRH should support future tools
without requiring users to abandon current tools, copy every chat transcript
into a public repository, or accept a single vendor as the source of project
memory.

## Target use cases

### `@lrh record this` / `@lrh promote this` from an external chat

- **Enables:** A user in an external chat can ask LRH to record the
  conversation or promote selected material into a design proposal draft, work
  item draft, prompt package, evidence candidate, or run proposal.
- **Why it fits LRH:** LRH can preserve provenance while keeping the promoted
  artifact reviewable, scoped, and subject to validation before it becomes
  authoritative.
- **Major risks:** Accidental publication, over-promoting unreviewed model
  output, secret leakage, and authority confusion where a chat transcript is
  mistaken for a decision.
- **Minimum technical requirements:** Private conversation import, object
  metadata with privacy and authority classes, redaction, draft generation,
  promotion records, and validation of promoted artifacts.
- **Existing alternatives and why LRH is still useful:** Users can manually
  copy text into Markdown or rely on vendor chat history, but LRH adds stable
  project-relative provenance, explicit promotion, validation, and evidence
  linkage.

### Contextual chat from the LRH meta/project dashboard

- **Enables:** A user can select a project in a future `Needs Attention` lane,
  chat about what to do next, draft a work item, request a design proposal, or
  propose a run from the same operational context.
- **Why it fits LRH:** The dashboard already aims to expose project state,
  attention needs, evidence, and status. A contextual chat panel can use that
  state without becoming the authority over it.
- **Major risks:** UI affordances could imply that chat output is approved;
  stale context could cause bad recommendations; local APIs could expose
  private data if bound too broadly.
- **Minimum technical requirements:** Context-packet generation, scoped
  conversation creation, non-agentic `ask` semantics, private storage, and
  promotion actions separated from chat turns.
- **Existing alternatives and why LRH is still useful:** General chat tools can
  discuss pasted context, but LRH can assemble current control-plane context,
  retain private provenance, and require explicit promotion into repository
  artifacts.

### External tool integration API

- **Enables:** A GitHub integration, OpenAI or Anthropic tool, Aider session,
  Kiro-like workflow, or future agent can ask LRH for context, propose work,
  report progress, and attach evidence.
- **Why it fits LRH:** LRH can be the stable protocol layer that maps many
  vendor-specific tools into one evidence-backed control plane.
- **Major risks:** Prompt injection, unsafe tool execution, forged evidence,
  inconsistent vendor metadata, and accidental broad repository authority.
- **Minimum technical requirements:** Stable conceptual APIs, signed or
  authenticated adapter calls where appropriate, untrusted input labeling,
  backend capability checks, evidence-candidate records, and run proposal
  review.
- **Existing alternatives and why LRH is still useful:** Individual vendors can
  provide their own task tracking or memories, but LRH provides a user-owned
  format and a cross-tool audit trail.

### Durable private conversation ledger

- **Enables:** Raw conversations can be stored privately, searched, exported,
  summarized, and curated into repository artifacts without making the raw chat
  the default public record.
- **Why it fits LRH:** LRH needs durable provenance for reasoning and handoffs,
  but its authoritative source remains curated control artifacts and evidence.
- **Major risks:** Conversation data can grow large, include secrets, carry
  retention obligations, or create false expectations about backend privacy.
- **Minimum technical requirements:** Privacy, durability, retention, and
  authority metadata; local durable storage; indexing; redaction events;
  backup; export policy; and verification.
- **Existing alternatives and why LRH is still useful:** Vendor histories,
  local files, and notebooks can store transcripts, but LRH adds policy-aware
  storage, promotion semantics, and cross-project scoping.

### Private multi-repo control plane

- **Enables:** One private LRH control repo can coordinate public code repos,
  private asset repos, and private publishing/release repos while preserving
  selective visibility for conversations, evidence, and plans.
- **Why it fits LRH:** LRH is intended to be reusable across independent
  project repositories, so its control plane should support a project that is
  larger than any single Git repository.
- **Major risks:** Cross-repo privacy mistakes, leaking private release data
  into public repos, and confusing which repository owns which artifact.
- **Minimum technical requirements:** Explicit scopes, LRH URI namespaces,
  export policies, repository references, shared-private storage, and
  validation that path policy and metadata policy agree.
- **Existing alternatives and why LRH is still useful:** Monorepos, issue
  trackers, and private wikis can coordinate multiple repos, but LRH adds
  machine-interpretable workflow artifacts and evidence/status rules.

### Chat-to-run cockpit

- **Enables:** A conversation can produce a prompt draft, run proposal,
  approval decision, execution events, evidence attachments, and derived status
  interpretation.
- **Why it fits LRH:** LRH's execution model should keep the chain from intent
  to evidence visible, reviewable, and bounded.
- **Major risks:** Chat could be mistaken for approval, an external agent could
  overstep scope, evidence could be weak or forged, and status could be updated
  without validation.
- **Minimum technical requirements:** Run proposal objects, approval records,
  event logs, evidence candidates, status interpretation rules, and guardrail
  checks before execution.
- **Existing alternatives and why LRH is still useful:** Agent tools can run
  tasks directly, but LRH can require proposal, approval, evidence, and status
  interpretation instead of treating agent success messages as completion.

## Non-goals

- Do not build a full LRH-native chatbot as the first implementation.
- Do not train or require an LRH-specific LLM.
- Do not store raw conversations in public repos by default.
- Do not use Git as the live database for raw chat or event streams by default.
- Do not allow chats or external agents to directly mark work complete or
  mutate authoritative status.
- Do not build deep MCP, GitHub App, or vendor-specific integrations before the
  storage and conversation semantics are defined.
- Do not implement this proposal in this PR.

## Core decisions

1. **LRH Conversations are non-authoritative until promoted.**
   - Consequence: conversation content can inform later artifacts, but only an
     explicit promotion creates drafts, proposals, evidence candidates, or
     authoritative control artifacts.
2. **Raw conversations are private by default.**
   - Consequence: imports and live chat records must begin in private storage
     unless the user explicitly chooses a broader export policy.
3. **Storage has explicit privacy, durability, retention, and authority
   policies.**
   - Consequence: every stored object must declare how visible, durable,
     retained, and authoritative it is, and verification must catch
     path/metadata/backend mismatches.
4. **Git stores curated control artifacts, not raw chat by default.**
   - Consequence: Git remains strong for reviewable Markdown, evidence records,
     execution records, and accepted status, while raw chat ledgers use more
     suitable private backends unless explicitly exported.
5. **External tools integrate through stable protocol surfaces.**
   - Consequence: CLI, file exchange, MCP, GitHub, OpenAPI, and UI adapters sit
     above conceptual APIs rather than defining the foundation themselves.
6. **Chat-to-run requires explicit proposal, approval, evidence, and status
   interpretation.**
   - Consequence: a conversation may suggest action, but execution and status
     changes require reviewable run proposals, logged events, accepted evidence,
     and validation-aware interpretation.

## High-level architecture

```text
LRH authoritative control artifacts
  design / work_items / evidence / status / executions

LRH Conversation Model
  conversations / turns / events / summaries / proposals

LRH Storage API
  privacy / durability / retention / versioning / authority

Storage backends
  in-memory / filesystem / SQLite / Git exports / private control repo / future service

External adapters
  CLI / file exchange / MCP / GitHub / GPT Actions/OpenAPI / lrh serve UI
```

Adapters sit above stable conceptual APIs. The first durable design work should
therefore define storage and conversation semantics before relying on MCP,
GitHub, provider-specific APIs, or UI behavior.

## LRH Storage Model

### LRH URI/address namespace

LRH objects should have stable addresses that communicate policy without making
path naming the only source of truth. Example URIs:

- `lrh://transient/private/conversations/local/CHAT-123`
- `lrh://versioned/private/conversations/WS-STEAM-RELEASE/CHAT-456`
- `lrh://versioned/public/evidence/WI-123/EV-789`
- `lrh://sealed/shared_private/runs/RUN-456`

The URI policy and object metadata policy must agree. Moving an object must not
silently change privacy, durability, retention, or authority. Promotion and
export must be explicit operations.

### Privacy classes

- `private`: visible only to the local user or configured private workspace.
- `shared_private`: visible to an explicitly defined private group or private
  control repo.
- `public`: safe for public repository or public artifact export.
- `secret`: contains sensitive material requiring stronger handling than normal
  private data.

### Durability classes

- `transient`: may be discarded at process end.
- `session`: lasts for the active interactive session.
- `durable`: persists locally or in a configured backend.
- `versioned`: preserves historical versions or append-only events.
- `sealed`: immutable after sealing except for later references.

### Retention classes

- `ttl=<duration>`: expire after a duration.
- `keep`: retain until explicit user action or policy change.
- `archive_after=<duration>`: move to archive storage after a duration.
- `delete_after=<duration>`: delete or expire after a duration when backend
  capabilities permit.
- `manual`: no automatic retention action; user review required.

### Authority classes

- `non_authoritative_context`: useful context only.
- `draft`: user- or tool-generated draft that has not been proposed.
- `proposal`: reviewable proposal for later acceptance.
- `approved_run`: approved execution intent, not proof of completion.
- `evidence_candidate`: possible evidence awaiting review or validation.
- `accepted_evidence`: evidence accepted under project policy.
- `authoritative_control_artifact`: canonical project control state.

### Object metadata

Every stored object should carry metadata including:

- ID;
- kind;
- URI;
- privacy;
- durability;
- retention;
- authority;
- timestamps;
- scope;
- backend;
- export policy; and
- provenance.

Metadata is not decorative. It is the basis for verification, safe export,
retention, redaction, promotion, and later status interpretation.

## Storage API operations

The first implementation should model these as conceptual operations before
choosing final Python APIs:

- `put_object`: store an object with required metadata and backend checks.
- `get_object`: retrieve an object subject to privacy and backend policy.
- `list_objects`: list objects by scope, kind, policy, and authority.
- `append_event`: append an event to a versioned stream where supported.
- `promote`: explicitly change authority and/or exportability through a
  reviewable action.
- `export`: write a curated representation to a target backend or repository.
- `import_object`: import external content with provenance and untrusted-input
  labeling.
- `redact`: record redaction and produce redacted views or replacements.
- `seal`: make an object immutable except for later references.
- `delete_or_expire`: apply retention policy where backend capabilities allow.
- `verify`: check path, URI, metadata, and backend consistency.
- `backup`: create or verify a backup according to backend capability.

Expected semantics:

- `promote` changes authority and/or exportability only through explicit,
  reviewable action.
- `redact` should be modeled as a redaction event unless secure deletion is
  explicitly supported and policy permits it.
- `seal` makes an object immutable except for later references.
- `verify` checks path/metadata/backend consistency and should fail safe when
  backend capability claims do not match observed behavior.

## Backend capability model

Storage backends must advertise capabilities rather than relying on informal
assumptions. Capabilities include:

- transactions;
- versioning;
- private storage;
- public export;
- retention enforcement;
- encryption support;
- concurrent writers;
- search; and
- backup.

Likely backend roles:

- **In-memory:** tests, examples, and ephemeral sessions.
- **Filesystem:** simple import/export, debugging, and human inspection.
- **SQLite:** local private durable ledger for conversations, turns, events,
  attachments, references, indexes, and exports.
- **Git:** curated control artifacts, accepted evidence records, prompt
  packages, design proposals, work items, and execution records.
- **Private control repo:** shared-private multi-repo control plane where a
  private repository coordinates public and private project repositories.
- **Future service:** team/server workflows, stronger search, shared access,
  and centralized backup.

Git is not the default raw chat database. Git can export curated artifacts and
selected summaries, but raw chat/event streams should begin in private storage
that is designed for append-heavy, searchable, policy-aware data.

## LRH Conversation Model

Core objects:

- `Conversation`: scoped thread or imported transcript container.
- `ConversationTurn`: user, assistant, system, tool, or adapter turn.
- `ConversationEvent`: append-only event describing what happened.
- `Attachment`: file, image, log, patch, report, or external object reference.
- `ContextPacket`: bounded LRH context assembled for a model or tool.
- `ModelRequest`: provider-neutral model request metadata.
- `ModelResponse`: provider-neutral response metadata and content references.
- `ToolInvocation`: external or local tool call record.
- `PromptDraft`: draft prompt package produced by a conversation.
- `RunProposal`: proposed bounded run derived from conversation context.
- `PromotionRecord`: provenance-preserving record of promotion or rejection.
- `EvidenceCandidate`: possible evidence derived from or attached to a
  conversation.
- `ConversationSummary`: curated summary with source links.
- `ExternalReference`: reference to vendor chat, PR, issue, model run, or tool
  session.

The structure should combine an event stream and an artifact graph:

- the event stream records what happened; and
- the artifact graph records what the conversation produced, linked to, or
  promoted.

Example events:

- `conversation.created`
- `turn.added`
- `attachment.added`
- `summary.created`
- `prompt_draft.created`
- `run_proposal.created`
- `run.linked`
- `evidence_candidate.created`
- `promotion.accepted`
- `conversation.sealed`

## Conversation scopes

Possible scopes:

- `global`
- `workspace`
- `project`
- `repository`
- `workstream`
- `work_item`
- `run`
- `evidence`
- `release/product`

A multi-repo Replication Vector style project could use one private LRH control
repo to coordinate:

- a public graphics library repo;
- a public or private game engine repo;
- a private assets and levels repo;
- a private Steam publishing repo; and
- one private LRH control repo containing shared-private plans, conversations,
  evidence, and release coordination state.

This requires conversations and storage objects to carry explicit scope and
export policy so a private release conversation cannot be silently promoted
into a public code repository.

## Conversation API operations

Conceptual operations:

- `create_conversation`
- `append_turn`
- `attach`
- `build_context_packet`
- `ask`
- `summarize`
- `create_prompt_draft`
- `create_design_proposal_draft`
- `create_work_item_draft`
- `create_run_proposal`
- `promote`
- `import_external`
- `export`
- `seal`
- `redact`

`ask` is non-agentic by default. It should not execute tools, mutate project
state, mark work complete, or attach accepted evidence unless a later explicit
run/action design authorizes that behavior through proposal, approval,
capability checks, and evidence rules.

## Promotion model

Promotion path:

```text
conversation
  -> summary
  -> draft
  -> proposal
  -> approved artifact
  -> evidence/status
```

Examples:

- conversation -> design proposal draft ->
  `project/design/proposals/proposed/...`
- conversation -> work item draft -> `project/work_items/proposed/...`
- conversation -> prompt draft -> prompt package
- conversation -> run proposal -> execution/run record
- conversation -> evidence candidate -> `project/evidence/...`

Promotion rules:

- promotion is explicit;
- promotion preserves provenance;
- promotion may require redaction;
- promotion may target private state, a private control repo, or a public repo;
- promotion should run validation where applicable; and
- promotion does not allow chat to bypass LRH authority and evidence rules.

A rejected promotion should remain auditable when policy permits: the rejection
is itself useful provenance and can explain why a conversation was not promoted.

## External adapter surfaces

These surfaces are intended adapters over stable conceptual APIs, not the
foundation itself.

### CLI adapter

Possible future commands:

- `lrh conversation create`
- `lrh conversation import`
- `lrh conversation summarize`
- `lrh conversation promote`
- `lrh context get --format json`
- `lrh run propose --from-conversation ...`

### File exchange adapter

Some tools cannot call a local server. LRH should support inbox/outbox JSON
files with atomic write requirements, schema validation, provenance metadata,
and explicit import/promotion steps.

### MCP adapter

Future MCP resources could include projects, snapshots, conversations, work
items, runs, and evidence. Future MCP tools could include context get,
conversation import/promote, run propose, and evidence attach. MCP should come
after storage and conversation semantics are stable.

### GitHub adapter

Future GitHub integration could support slash commands or PR comments, evidence
links, run progress, and proposal references. GitHub comments should not become
authoritative status without LRH validation and evidence interpretation.

### GPT Actions/OpenAPI or similar adapter

External chat tools may call a local or private LRH endpoint to record,
promote, or request context. Such endpoints should not be internet-exposed by
default and should require explicit user configuration and authentication.

### `lrh serve` UI adapter

A future `lrh serve` dashboard may include a chat panel, context preview,
promotion actions, and run proposal review. UI actions should remain safe by
default and should present authority, privacy, and evidence state clearly.

## Security and privacy model

### Threats

- **Prompt injection:** imported or generated text may attempt to override LRH
  policies, leak secrets, or instruct adapters to execute unsafe actions.
- **Accidental publication:** private conversations, assets, credentials, or
  release plans may be exported to public repos.
- **Authority confusion:** users or tools may mistake chat output, summaries,
  or agent progress messages for accepted project status.
- **Evidence forgery:** external tools may attach logs, screenshots, or claims
  that do not prove the asserted result.
- **Secret leakage:** transcripts may include API keys, local paths,
  credentials, private customer data, or unreleased product details.
- **Vendor lock-in:** valuable context may remain in vendor histories or
  provider-specific schemas.
- **Backend false guarantees:** a backend may claim privacy, retention,
  encryption, transactions, or deletion guarantees it cannot actually provide.
- **Unsafe tool execution:** chat affordances may blur into agentic execution
  before guardrails exist.

### Controls

- Private by default.
- Explicit promotion and export.
- Untrusted input labeling.
- No direct execution from chat.
- Run proposal and guardrail review before execution.
- Backend capability checks.
- Redaction workflow.
- Provenance and source links.
- Validation before status interpretation.
- Local APIs are not exposed publicly by default.

## Implementation phases

- **Phase 0: design only.** Record this proposal and keep it free of runtime
  behavior changes.
- **Phase 1: minimal storage prototype.** Define policy dataclasses or typed
  models, an in-memory backend for tests, a filesystem backend for debugging
  and import/export, and metadata validation.
- **Phase 2: local durable ledger.** Add a SQLite backend, schema versioning,
  and tables for conversations, turns, events, attachments, references,
  indexes, and exports.
- **Phase 3: conversation import/export.** Add `lrh conversation
  import/list/show/export` without requiring a model provider.
- **Phase 4: promotion.** Promote conversations into design proposal drafts,
  work item drafts, prompt drafts, and evidence candidates.
- **Phase 5: context-aware ask.** Add provider-neutral, non-agentic model
  adapter behavior with no tool execution.
- **Phase 6: external protocol.** Add CLI JSON and file exchange first; add
  MCP later after semantics are stable.
- **Phase 7: chat-to-run.** Support run proposals from conversations,
  approval, event logs, external tool reporting, and evidence attachment.
- **Phase 8: UI.** Integrate with `lrh serve` once the storage,
  conversation, promotion, and run proposal semantics are validated.

## Low-level choices still open

Open questions include:

- exact storage paths;
- SQLite database location;
- encryption-at-rest posture;
- schema migration approach;
- retention enforcement;
- redaction semantics;
- single-writer versus multi-writer assumptions;
- attachment hashing;
- provider metadata schema;
- CLI naming: `chat` versus `conversation`;
- MCP URI design;
- GitHub slash command vocabulary;
- local API authentication; and
- whether external tools can request context without user confirmation.

## Pros, cons, and tradeoffs

### Pros

- Preserves user control over data.
- Keeps LRH future-tool friendly.
- Avoids vendor lock-in.
- Aligns with LRH's evidence/status philosophy.
- Supports multi-repo control planes.
- Enables gradual adoption from manual import to richer adapters.

### Cons

- The architecture is abstract upfront.
- Storage security is hard.
- Conversation data can grow large.
- External protocols evolve quickly.
- There is a risk of over-engineering before the control-plane slice is stable.

### Mitigations

- Design first and implement in small phases.
- Start with minimal storage and validation models.
- Keep raw conversations private by default.
- Require explicit promotion.
- Avoid deep integrations until storage and conversation semantics are stable.

## Relationship to existing LRH docs

This proposal extends, but does not replace, existing LRH control-plane design
work:

- `project/design/design.md` and `project/design/architecture.md` define the
  reusable harness and its repository-centered control-plane boundary.
- `project/design/meta_control_plane_mvp_spec.md` describes meta/workspace
  concepts that future conversation scopes can use.
- `project/design/execution_framework_mvp.md` and the proposed workstream
  execution framework provide context for later run proposal and execution
  event integration.
- `project/design/proposals/proposed/constitutional-sandbox-envelope/00_proposal.md`
  defines safety boundaries that chat-to-run must respect.
- `project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md`
  is relevant to future `lrh serve` dashboard chat and promotion surfaces.
- `PROMPTS.md` and `project/executions/README.md` define current prompt and
  execution record traceability that conversation promotion should eventually
  complement.

If adopted later, this proposal should inform follow-on changes to canonical
architecture, storage, conversation, execution, and adapter documentation. Those
canonical updates should land with the implementation slices that make each
part concrete.
