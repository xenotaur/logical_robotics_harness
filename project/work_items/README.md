# Work Items

Work items are organized in status buckets under this directory:

- `project/work_items/proposed/`
- `project/work_items/active/`
- `project/work_items/resolved/`
- `project/work_items/abandoned/`

## Source of truth

The YAML frontmatter is authoritative. Directory placement is a derived, human-facing view and must match `status`.

Required work-item frontmatter fields:

- `id`
- `status` (`proposed` | `active` | `resolved` | `abandoned`)
- `blocked` (boolean)
- `blocked_reason` (must be set when `blocked: true`; otherwise `null`)
- `resolution` (`null` for non-terminal items; required for `resolved` / `abandoned`)

## Creating a new work item

1. Create `project/work_items/proposed/<ID>.md`.
2. Set `id: <ID>`.
3. Set `status: proposed`.
4. Set:
   - `blocked: false`
   - `blocked_reason: null`
   - `resolution: null`
5. Fill the remaining metadata and markdown body.

## Changing status

When status changes:

1. Update the YAML `status`.
2. Move the file into the matching status directory.
3. For terminal statuses (`resolved` / `abandoned`), set a non-null `resolution`.

## Marking blocked work

Blocked state is only valid for active items:

- `status: active`
- `blocked: true`
- non-empty `blocked_reason`

Do not create a separate `blocked/` directory.

## Validation requirement

Run validation after edits:

```bash
lrh validate
```

Or from repository scripts:

```bash
scripts/validate
```
