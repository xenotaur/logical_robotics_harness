# Decision Log

## 2026-07-24: Decision: Deliberate Chain Initiation (and the Assist vs. Agentic Boundary, Clarified)

### Summary

A human may authorize an entire lifecycle chain in one deliberate act, rather
than re-authorizing each link. Individual links remain independently available;
an automatic chain over them may run only when a human has explicitly initiated
it and has provided or signed off on both a completion condition and a
stop-work condition. This does not weaken the rule that no chain starts itself,
and it does not move any skill into the agentic package: an agent running skills
or templates is assist, not agentic.

### Context

- The post-PR lifecycle chain is documented as suggestion-only in
  `src/lrh/skills/_shared/lifecycle-chain.md` ("Each link is a suggestion to the
  user, never an automatic invocation … no skill should call another as a side
  effect of finishing"). All nine skills carry `disable-model-invocation: true`.
- `PROP-LRH-EXECUTION-SESSIONS` lists as a non-goal: "Do not automate the
  three-phase workflow. Claude.app sessions are human-driven; the skill guides
  but does not automate."
- Both statements were written before the shift to Claude Code Auto mode. In
  practice the dominant friction is now the opposite of the one they guard
  against: a human mechanically re-typing the same `/lrh-implement` →
  `/lrh-review-response` → `/lrh-confirm-fixes` → merge → `/lrh-closeout`
  sequence, and re-confirming a cold subagent for `/lrh-confirm-fixes` that was
  meant to be the default. This adds no decision value and buries key findings
  in boilerplate, which hides bugs rather than catching them.
- `PROP-SAFE-DEFAULT-AGENTIC-EXTRA-PACKAGING` (adopted) already establishes the
  packaging boundary and, as principle #1, "explicit capability state over
  implicit behavior" — but scoped to install time. It also states the boundary
  "does not imply that LRH artifacts could never be used in any agentic workflow
  outside this package boundary."
- Some collaborators cannot run agentic software at all — including Claude
  itself, per their IT policy — so the assist/agentic boundary must be crisp and
  must not depend on whether Claude is in the loop.
- The Taurworks concept of "deliberate user permission" — an authorization a
  machine cannot self-grant and that is recorded rather than stored in
  machine-flippable config — is the model applied here to chain initiation.

### Decision

1. **Deliberate chain initiation.** Each lifecycle link (`/lrh-implement`,
   `/lrh-review-response`, `/lrh-confirm-fixes`, `/lrh-closeout`, and peers)
   remains independently invocable by a human at any time. An automatic chain
   that follows those links may run, but only when a human has explicitly
   initiated it and has provided or signed off on two conditions:
   - a **completion condition** — what "done" means for this run; and
   - a **stop-work condition** — what forces a halt-and-report.
   Absent an explicit initiation carrying both conditions, no chain self-starts.
   This extends the adopted "explicit capability state over implicit behavior"
   principle from install time (is agentic capability installed?) to run time
   (has this chain been authorized to run?).

2. **`disable-model-invocation` is preserved and orthogonal.** The flag prevents
   the *model* from auto-firing a skill as an implicit side effect; it does not
   prevent a *human* from deliberately initiating a chain. The invariant that
   survives is "no chain starts itself." What changes is that one deliberate
   human act may authorize a whole chain instead of requiring per-link
   re-authorization.

3. **The execution-sessions non-automation was build-order, not a permanent
   non-goal.** `PROP-LRH-EXECUTION-SESSIONS`'s "do not automate the three-phase
   workflow" recorded a sequencing choice — build the human-walkable links
   first — not a standing prohibition. With deliberate chain initiation defined,
   human-initiated automation of those links is permitted.

4. **The assist/agentic boundary is "does LRH itself run the loop," not "is the
   workflow agentic."** An agent (Claude or any other) running skills or
   `lrh request` templates is **assist**; skills and templates ship at parity in
   base `lrh`. Only code in which **LRH itself** programmatically drives an
   execution loop (e.g. the Claude or OpenAI SDK driving a worktree) is
   **agentic** and belongs in `lrh[agentic]`. A deliberately-initiated skill
   chain is assist — it does not require or imply `lrh[agentic]`.

### Rationale

- The original caution targeted runaway *implicit* automation. That target is
  preserved (principle 2). The friction actually being felt — mechanical
  re-authorization that hides findings — is a different problem the original
  wording did not distinguish.
- Grounding the change as an extension of an already-adopted principle
  (explicit capability state) keeps it continuous with existing governance
  rather than a repudiation of it.
- Separating "who runs the loop" from "is Claude involved" gives collaborators
  under agentic-software restrictions a boundary they can rely on: base `lrh`
  (skills + templates) stays assist regardless of which agent drives it.

### Alternatives considered

1. Leave the suggestion-only invariant and the non-goal unchanged.
   Pros: maximum caution; no cascade.
   Cons: entrenches the re-typing friction and the finding-burying it causes;
   leaves standing guidance that current practice already contradicts.
2. Drop the invariant entirely and allow model-initiated chaining.
   Pros: maximum autonomy.
   Cons: removes the human control point the project depends on and the
   compliance boundary; re-conflates assist and agentic.
3. Fold this into `WS-EXECUTION-FRAMEWORK`.
   Pros: single planning frame with the bounded stabilization loop.
   Cons: that workstream is about LRH running the loop (`lrh[agentic]`); folding
   re-conflates the two axes this decision exists to separate. Cross-link
   instead.

### Consequences

- Guidance cascade (in this PR): revise
  `src/lrh/skills/_shared/lifecycle-chain.md` to the deliberate-initiation
  formulation and note the orthogonality of `disable-model-invocation`;
  reclassify the `PROP-LRH-EXECUTION-SESSIONS` non-goal as build-order; add a
  refinement note to `PROP-SAFE-DEFAULT-AGENTIC-EXTRA-PACKAGING` sharpening the
  "does LRH run the loop" axis and skill/template parity.
- Evidence: the Taurcode `:execute` / `:land` prompts are the human-initiated,
  single-cycle expression of this policy (the "Cessna"). Each run emits one
  `CHAIN-NOTE` line into its execution record; these aggregate into an `EV-*`
  record feeding `WI-BOUNDED-STABILIZATION-LOOP-DESIGN`, the multi-cycle
  bounded-stabilization loop (the "747") in `WS-EXECUTION-FRAMEWORK`.
- Downstream (not in this PR): `/lrh-execute` and `/lrh-land` skills may be
  promoted as the reference implementation of deliberate chain initiation —
  after this decision and the guidance cascade land, and after initial
  `CHAIN-NOTE` evidence.

### Revisit conditions

Revisit when:

- `CHAIN-NOTE` evidence shows single-cycle chains frequently need mid-run human
  intervention, or shows the merge gate is never load-bearing (either would
  change where the gates belong);
- `WI-BOUNDED-STABILIZATION-LOOP-DESIGN` is designed (it inherits this policy);
  or
- a compliance collaborator raises the assist/agentic boundary wording.

### Status

Accepted (guidance cascade pending)

## 2026-07-23: Decision: Session Transcripts Are Never Committed to the Repository

### Summary

Session transcripts (Claude Code `/export` output, `~/.claude/projects/`
JSONL files, and equivalent artifacts from other agent backends) are never
committed to this repository. The repository stores only the pointer
`session_transcript: claude-app:<host-uuid-stem>` in execution records.

### Context

- Execution records carry a `session_transcript` field (defined by
  `PROP-LRH-EXECUTION-SESSIONS`) that references the agent session which
  produced the work.
- Raw session transcripts contain environment dumps, absolute local paths,
  and potentially accidental PII; they are also large (multi-MB) and purely
  historical.
- The sensitivity scanner contract in `src/lrh/conversations/README.md`
  already establishes that transcript-derived content is private by default
  and that public export requires human review.
- This practice predates the LRH control plane — it was already the norm in
  the ChatGPT/Codex era — but had never been recorded as a standing
  decision.
- Desktop-app Claude Code sessions have two identifiers (a `local_`-prefixed
  host session id and a child SDK session id that names the JSONL file);
  documenting the pointer convention forced the question of what, if
  anything, of the session itself belongs in the repo.

### Decision

- Never commit session transcripts, in any form, to this repository.
- The repository stores only the pointer `session_transcript:
  claude-app:<host-uuid-stem>` (host UUID stem, `local_` prefix stripped) in
  execution records.
- Users archive `/export` output and/or JSONL files to local disk. A
  private, enhanced-security store for such archives is permitted; a plain
  hosted repository of raw transcripts is not — cf. the sensitivity scanner
  contract in `src/lrh/conversations/README.md`.

### Rationale

- Transcripts leak local workspace layout (absolute paths), environment
  details, and possibly PII to everyone who clones the repository; a pointer
  leaks nothing.
- Multi-MB historical blobs bloat the repository without serving the control
  plane's purpose — traceability needs the link, not the content.
- Keeping archives local (or in a private, enhanced-security store) preserves
  the ability to consult a transcript when provenance questions arise.

### Alternatives considered

1. Commit sanitized/redacted transcripts alongside execution records.
   Pros: self-contained provenance in one repository.
   Cons: sanitization is error-prone (the sensitivity scanner is explicitly
   a safety rail, not a certifier); size and churn costs remain; a single
   miss leaks permanently via git history.
2. Host raw transcripts in a separate plain hosted repository.
   Pros: keeps this repository lean while retaining shared access.
   Cons: merely relocates the leak; a plain hosted repo offers no stronger
   guarantees than committing here, so it is equally disallowed.

## 2026-07-09: Decision: PyPI Release Environment Protection Rules

### Summary

Resolve the open design question from `PROP-TAG-PUSH-PYPI-PUBLISHING` §12
("whether to use GitHub environments/protection rules") by requiring manual
approval before any real PyPI publish, while leaving TestPyPI unprotected.

### Context

- `release.yml` triggers on any `push: tags: v*.*.*` with no gate between a
  successful build/smoke job and the real PyPI publish step.
- `testpypi-rehearsal.yml` is `workflow_dispatch`-only and can only be
  dispatched against a tag ref that already contains the workflow file in its
  tree. No existing tag (`v0.2.0`-`v0.2.4`) postdates the file's addition
  (2026-05-06), so rehearsal against those tags is currently impossible.
- Because `release.yml` and `testpypi-rehearsal.yml` both key off the same
  `vMAJOR.MINOR.PATCH` tag shape, pushing a tag for rehearsal purposes also
  arms a real production publish attempt, with no manual checkpoint, unless a
  GitHub environment protection rule intervenes.
- `docs/how-to/run-a-release.md` already listed "confirm GitHub environment
  protection and approval rules for `pypi` match maintainer intent" as a
  release checklist item, but the intent itself was never decided or
  implemented.

### Decision

- Add a required-reviewer protection rule to the `pypi` GitHub environment,
  reviewer: `xenotaur` (Anthony Francis). This pauses `release.yml`'s
  `publish-pypi` job for manual approval after `build-check-smoke` succeeds,
  creating a window to dispatch `testpypi-rehearsal.yml` against the same tag
  and verify a TestPyPI install before approving the real publish.
- Leave the `testpypi` environment without protection rules for now; TestPyPI
  publishes are disposable and low-stakes, and the rehearsal path should not
  itself require an approval gate.
- Configured via `gh api -X PUT repos/xenotaur/logical_robotics_harness/environments/pypi`
  on 2026-07-09.

### Rationale

- This is the only mechanism available today that lets a maintainer rehearse
  via TestPyPI before a real PyPI publish, given both workflows share the
  same tag-trigger shape and `release.yml` otherwise has no delay or gate.
- Solo-maintainer project: a self-approvable required reviewer is sufficient;
  `prevent_self_review` was left at GitHub's default (`false`) since there is
  no second maintainer to require.
- Protecting `testpypi` as well would add friction without a corresponding
  safety benefit, since TestPyPI failures are cheap to recover from (publish
  a new rehearsal version; no user-facing consequence).

### Alternatives considered

1. Leave `pypi` unprotected and rely on maintainer discipline to check
   TestPyPI before tagging.
   Pros: no GitHub configuration needed.
   Cons: no actual gate; a tag push races straight to a real, non-revocable
   publish; contradicts the phased rehearsal-then-publish intent in
   `PROP-TAG-PUSH-PYPI-PUBLISHING` §15.
2. Protect `testpypi` too.
   Pros: symmetric governance.
   Cons: unnecessary friction for a disposable, low-stakes target; nothing
   currently depends on TestPyPI stability.

### Status

Accepted

## 2026-04-23: Decision: Survey JSON Schema Deferral (YAGNI / Evolutionary Design)

### Summary

Do not expand or formalize the `lrh survey` JSON schema further until a concrete downstream consumer exists.

### Context

- `lrh survey` now produces structured output.
- A design question arose about broadening schema structure and downstream usage conventions.
- No concrete downstream consumer currently requires expanded schema fields or stricter schema formalization.
- The system already supports transient use of survey output inside prompts/workflows without persistent derived artifacts.

### Decision

- Keep current survey output minimal.
- Do **not** expand survey JSON schema until a real downstream consumer exists.
- Treat current survey output as a sufficient foundation for near-term workflows.
- Prefer transient transformations over persistent derived artifacts.

### Rationale

- YAGNI: avoid building unused structure.
- Avoid premature schema design and avoid schema-churn technical debt.
- Preserve flexibility while downstream workflows are still forming.
- Keep the system simple and composable.
- Defer complexity until requirements are concrete.

### Alternatives considered

1. Expand JSON schema now
   Pros: early standardization
   Cons: likely over-engineering and schema churn before clear requirements.

2. Generate and store `project/context/generated/repository.md`
   Pros: human-readable and reusable artifact
   Cons: duplication, staleness risk, and unnecessary persistence for current needs.

3. Keep survey minimal and evolve later (**chosen**)
   Pros: flexible, low-maintenance, aligned with evolutionary design
   Cons: requires a future design step when the first concrete consumer appears.

### Consequences

- Survey remains a lightweight fact producer.
- Downstream workflows must explicitly define required survey fields.
- A future PR will define schema expansion when the first real consumer appears.

### Revisit conditions

Revisit this decision when:

- a workflow requires stable structured survey input;
- audit or work-item generation requires specific survey fields; or
- multiple consumers begin duplicating survey interpretation logic.

### Status

Accepted

## 2026-04-22: Decision: Precedence canonicalization workstream closure validation

### Summary

Validated that precedence canonicalization is complete and can be closed without additional corrective work items.

### Decisions

- Canonical precedence source remains `project/memory/decisions/precedence_semantics.md`.
- `src/lrh/control_plane/precedence.py` continues to implement narrowing-only runtime behavior with subtractive guardrail handling and non-authoritative memory.
- `tests/control_plane/test_precedence.py` covers narrowing-only behavior, guardrail-before-runtime exclusions, and memory non-authoritativeness.
- Precedence-canonicalization workstream tracking may be treated as closed; no unresolved correctness findings were identified during closure review.

### Rationale

- Documentation, implementation, and tests are synchronized on the accepted "refine/narrow, not override" model.
- No competing full semantic specification was found; design/context references point back to the canonical decision.

### Implications

- No new precedence correctness work item is required from this closure pass.
- Any future precedence semantic change still requires synchronized updates across canonical decision, implementation, and tests.

### Status

Accepted

## 2026-04-22: Decision: Explicit Meta workspace-context resolution with XDG global defaults

### Summary

Adopt an explicit, precedence-based workspace-context resolution model for `lrh meta`, with XDG-style global defaults, explicit local workspace support, TTY-aware prompt policy, and user-visible resolution behavior.

### Decisions

- `lrh meta` commands operate against a resolved workspace context rather than implicit cwd-only assumptions.
- Workspace/context precedence is: explicit CLI flags (for example `--workspace`, `--config`, `--mode`) → `LRH_CONFIG` → `LRH_WORKSPACE` → local auto-discovery → global auto-discovery → built-in defaults.
- Global/user-level workspace defaults should follow XDG-style config/state/cache separation.
- Local workspace mode remains explicit via a root containing `.lrh/config.toml` plus sibling `projects/` and `private/` directories.
- Initialization prompts must be interactive-only (TTY-aware) and bypassable with `--yes` for automation.
- Meta command behavior should make active workspace/config resolution inspectable rather than hidden.

### Rationale

- Predictable precedence reduces ambiguity and improves debuggability.
- Clear user-level versus project-local config boundaries reduce surprising behavior.
- XDG-style separation is a stable convention for global data hygiene.
- Automation safety requires non-interactive command paths without prompt dependencies.

### Implications

- Design/spec/roadmap/work items should stay aligned on this workspace-resolution contract before additional Meta CLI expansion.
- Implementation should centralize workspace-resolution logic so `meta init`, `meta register`, and `meta list` share consistent behavior.

### Status

Accepted

## 2026-04-22: Decision: Assist migration sequencing for packaged runtime behavior

### Summary

Prioritize package-owned template migration and installed-package hardening before additional assist capability work.

### Decisions

- Runtime assist templates are package-owned under `src/lrh/assist/templates/`.
- Template loading for `lrh request` uses package-resource semantics rather than source-tree-relative paths.
- Packaging/build/install smoke checks for installed `lrh request` and `lrh snapshot` behavior remain required for ongoing hardening.
- `lrh survey` is canonical and delegated to package code in `src/lrh/assist/sourcetree_surveyor.py`.
- Expansion of `sourcetree_surveyor` into broader source-tree audit capability remains a separate follow-on item.

### Rationale

- Templates used at runtime should ship with the package.
- Installed behavior must be first-class to avoid environment-specific breakage.
- Separating migration mechanics from feature growth keeps PRs smaller and easier to review safely.

### Implications

- Roadmap ordering should emphasize template packaging and installability hardening first.
- Work tracking should explicitly separate sourcetree migration from sourcetree expansion.

### Status

Accepted


## 2026-04-21: Decision: Meta CLI MVP as First Meta-Control Execution Slice

### Summary

Adopted the Meta CLI MVP (`lrh meta init`, `lrh meta register`, `lrh meta list`) as the first executable slice of the workspace/meta-control layer.

### Decisions

- The workspace registry uses a stable `project_id` as persistent identity.
- Repository locators (`repo`, `project_dir`) are mutable to support path and structure changes.
- Human-facing labels (`display_name`, `short_name`) are mutable metadata.
- The registry supports repositories with and without LRH `project/` directories.
- Setup state is explicit (`not_set_up`, `lrh_project_present`).

### Rationale

- Creates a minimal, testable implementation path for Phase 2 without introducing orchestration complexity.
- Preserves LRH's repository-authority model while enabling cross-repository cataloging.
- Provides an auditable registry model before adding deeper meta-control commands.

### Implications

- Phase 2 planning and implementation should prioritize `init` / `register` / `list` plus repository-backed validation.
- Follow-on commands (`deregister`, `inspect`) remain deferred until this slice is stable.

### Status

Accepted


## 2026-04-11: Decision: Contributor and Assignment Validation Model

### Summary

Defined the formal validation model for contributor records, work-item ownership, and agent assignment.

### Decisions

- LRH validates contributor alignment in four passes:
  1. parsing
  2. per-file schema validation
  3. cross-reference validation
  4. semantic policy validation

- Contributor records under `contributors/` must define:
  - `id`
  - `type`
  - `roles`
  - `display_name`
  - `status`

- `owner` must reference a human contributor.
- `contributors` may reference both human and agent contributors.
- `assigned_agents` must reference agent contributors only.

- Agent contributors may define an `execution_mode`, including:
  - `human_orchestrated`
  - `autonomous`
  - `disabled`

- Human-orchestrated agents may exist in the system without being actively assigned to work items.

### Rationale

- Turns contributor and ownership semantics into enforceable validation behavior
- Preserves auditability by requiring human accountability for work-item ownership
- Separates participation from execution responsibility
- Supports a bootstrap phase where AI assistance exists before autonomous agent orchestration

### Implications

- LRH can automatically evaluate the alignment of `contributors/` and `work_items/`
- Validation tooling can distinguish hard failures from warnings
- Future UI, CI, and orchestration layers can rely on stable contributor/assignment semantics
- Bootstrap-style agents can be modeled cleanly without being treated as autonomous workers

### Status

Accepted (Bootstrap Phase)

## 2026-04-11: Decision: Contributor and Ownership Semantics

### Summary

Defined clear semantics for contributor representation and work-item ownership.

### Decisions

- `owner` refers to the **accountable human** responsible for a work item.
- `contributors` includes all humans and agents materially contributing.
- `assigned_agents` lists agents currently authorized or expected to execute work autonomously.

- Contributors are defined as separate artifacts under `contributors/`.
- Contributors have:
  - stable project-local `id`
  - `type` (`human` or `agent`)
  - one or more `roles` (e.g., `admin`, `editor`, `reviewer`, `viewer`)

- Agents are modeled as contributors and may have execution modes such as:
  - human-orchestrated (e.g., bootstrap phase)
  - autonomous (future)

### Rationale

- Separates accountability (owner) from participation (contributors) and execution (assigned_agents)
- Improves auditability and clarity of responsibility
- Aligns with repository-based workflows and future multi-agent coordination
- Avoids ambiguity introduced by using `owner: agent`

### Implications

- All work items should use human identifiers for `owner`
- Contributor identities must be defined in `contributors/`
- Future tooling (validation, UI, agents) can rely on these semantics
- Enables gradual evolution toward autonomous agent assignment without breaking model

### Status

Accepted (Bootstrap Phase)

## 2026-04-03: Decision: Top-Level Schema Definition
Adopted the top-level schema:

Principles → Project Goal → Roadmap → Current Focus → Work Items → Actions → Evidence → Status (+ Guardrails)

Reason:
This separates intent, execution, and truth more clearly than a milestone/sprint/task-only model.

## 2026-04-03: Decision: Defining Top-Level Control as project/s
Renamed `control/` to `project/`.

Reason:
This is friendlier for humans and fits better in client repositories.
