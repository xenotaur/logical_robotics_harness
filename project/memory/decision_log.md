# Decision Log

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

- Runtime assist templates should move out of `scripts/aiprog/templates/` into package-owned paths (targeting `src/lrh/assist/templates/`).
- Template loading for `lrh request` must use package-resource semantics rather than source-tree-relative paths.
- Packaging/build/install smoke checks for installed `lrh request` and `lrh snapshot` behavior are required before collaborator-facing publication.
- `scripts/aiprog/sourcetree_surveyor.py` migration into `src/lrh/assist/` should be a mechanical migration item.
- Expansion of `sourcetree_surveyor` into broader source-tree audit capability is a separate follow-on item.

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
