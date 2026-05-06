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

## Validation requirement

Before committing work-item edits, run:

```bash
lrh validate
```

CI also runs validation and will fail on policy violations.


## Workstream-control sequencing note

Workstream-control MVP planning is currently active. Until that MVP is implemented,
work items remain the executable planning leaves and should be kept narrowly scoped.

When workstreams are introduced, their frontmatter metadata will be authoritative and
directory buckets will remain human navigation projections, matching this work-item policy.

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
