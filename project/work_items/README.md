# Work Items

Work items are organized by status bucket under this directory:

- `proposed/`
- `active/`
- `resolved/`
- `abandoned/`

## Source of truth

The YAML frontmatter `status` field is authoritative.
Directory location is a derived, human-facing view and must match `status`.

## Required metadata

Each work item must include at least:

- `id`
- `status` (`proposed`, `active`, `resolved`, `abandoned`)
- `blocked` (`true` or `false`)
- `blocked_reason` (`null` unless blocked)
- `resolution` (`null` unless status is terminal)

Filename stem must match `id` (for example, `WI-0001.md` → `id: WI-0001`).

## Creating a work item

1. Create a new Markdown file with YAML frontmatter.
2. Set `status` to the intended lifecycle state.
3. Place the file in the matching bucket directory.
4. Set `blocked: false`, `blocked_reason: null`, and `resolution: null` for non-terminal items.
5. Run `lrh validate` and resolve any issues.

## Changing status

1. Update YAML `status`.
2. Move the file to the matching directory bucket.
3. If moving to `resolved` or `abandoned`, set a non-null `resolution`.
4. If moving out of terminal states, set `resolution: null`.
5. Run `lrh validate`.

## Marking blocked

Blocking is only valid for active work items:

- `status` must be `active`
- `blocked` must be `true`
- `blocked_reason` must be non-empty

When unblocked, set:

- `blocked: false`
- `blocked_reason: null`


## Maintenance commands

### `lrh work-items organize`

`lrh work-items organize` is a conservative organization helper. It inspects work-item files, reports frontmatter or bucket changes that would make files match the status-bucket layout, and can apply those mechanical moves only when invoked with `--apply`. Use `--check` in validation contexts to fail when organization changes are still needed. It does not make semantic lifecycle decisions.

### `lrh work-items validate`

`lrh work-items validate` is deterministic and CI-friendly. It validates work-item hygiene such as required frontmatter identity/status, filename and bucket consistency, duplicate IDs, valid status values, terminal resolution metadata, structured dependency references, selected metadata references, and dependency cycles. It should not decide whether implementation work is complete.

### `lrh work-items audit`

`lrh work-items audit --format md` and `lrh work-items audit --format json` emit a non-mutating lifecycle report. The audit combines validation diagnostics with deterministic traceability signals, such as missing linkage metadata, terminal items lacking resolution evidence, execution records attached to non-terminal items.

The audit distinguishes facts from recommendations. Use the semantic work-item audit assist template (`work_item_semantic_audit`) to compare acceptance criteria against concrete repository evidence before moving files or changing terminal metadata. Ambiguous proposed items should remain proposed until follow-up evidence or human design review resolves the uncertainty.

## Validation requirement

Before committing work-item edits, run:

```bash
lrh validate
```

CI also runs validation and will fail on policy violations.


## Workstream-control sequencing note

Workstream-control MVP planning is currently active. Until that MVP is implemented,
work items remain the executable planning leaves and should be kept narrowly scoped.

The initial `project/workstreams/` directory and `project/workstreams/README.md` now document
the human-facing workstream home. Workstream frontmatter metadata is authoritative and directory
buckets remain human navigation projections, matching this work-item policy.

## Prompt-driven work integration

For meaningful prompt-driven implementation tied to a work item:

1. Use a prompt ID that references the work item per `PROMPTS.md`.
2. Add an execution record under `project/executions/<WORK_ITEM_ID>/` (or `AD_HOC/` when no work item applies).
3. Before rerunning the same prompt ID, follow soft idempotence checks in `PROMPTS.md` and `project/executions/README.md`.

## Planning-tree and workstream sequencing

Planning-tree semantics are core, safe-default LRH control-plane concepts. Workstreams should be
modeled as planning nodes, and work items should remain the independently executable leaves unless a
future design explicitly expands that contract.

Near-term planning-tree work items should stay atomic and should document or implement one concern at
a time:

- planning-node schema (`parent_id`, `children`, identity, and relationship semantics)
- execution-ready work item concept for human-assisted execution
- planning-tree validation rules for references, cycles, and consistency
- workstream schema and workstream-to-work-item relationship conventions
- snapshot visibility for workstreams
- human-assisted run-packet or execution-prompt generation

Agentic execution is not part of the default work-item contract. Work involving `lrh agentic run`,
`lrh-agentic run`, agent adapters, PR stabilization loops, or sandbox-envelope behavior must be marked
deferred / future / requires `lrh[agentic]` until the optional agentic capability boundary exists.

Command naming convention for new work items: use `lrh agentic run` or `lrh-agentic run` for future
autonomous execution. Treat older `lrh run` references as legacy deferred execution-framework shorthand
until a future command-design work item decides whether `lrh run` is omitted, reserved for non-agentic
preparation, or exposed only as an installed-agentic alias.

## Bounded execution-framework planning

The first execution-framework implementation package should be contract-first and dry-run-first:

1. `proposed/WI-EXECUTION-READINESS-SCHEMA.md`
2. `proposed/WI-RUN-PACKET-DRY-RUN.md`
3. `proposed/WI-RUN-REPORT-MVP.md`

Execution readiness is opt-in work-item frontmatter. Ordinary work items require no readiness
metadata. A selected executable leaf declares `execution_ready: true` plus required fields for
autonomy, operation risk, allowed paths, validation commands, and required evidence. Advisory fields
such as forbidden paths, expected artifacts, policy gates, agent constraints, and review/CI limits
are preserved for dry-run packet/report generation. Human approval, merge, and closeout gates default
to safe `true` runtime values when omitted; readiness metadata never authorizes branch mutation,
backend dispatch, PR creation, merge, release, publish, or autonomous runtime execution by itself.

Before generating that prompt package, verify prerequisite control-plane alignment: shared core state
APIs, planning relationship/index validation, and snapshot-visible planning summaries. If a
prerequisite is missing, complete it in a separate prompt rather than broadening the first
execution-contract package.

Follow-on planning items cover safe-default `lrh serve`, branch containment, read-only PR/CI
observation, and bounded stabilization-loop design. Do not plan branch mutation, agent backends,
autonomous stabilization, or merge/publish automation before shared planning interpretation,
readiness, packet, and report contracts exist.

## CI capability scaffolding seeds

`project/workstreams/proposed/WS-CI-CAPABILITY-SCAFFOLDING.md` proposes concise staged
work-item seeds. `WI-CI-PLAYBOOK` is now the active first implementation leaf for the human CI setup
and debugging playbook. The remaining seeds, `WI-CI-REQUEST-TEMPLATES`,
`WI-CI-SKILL-PROTOTYPE`, and `WI-CI-TEMPLATE-FRAGMENTS-ASSESSMENT`, should be created only when
the corresponding phase is ready to execute.
