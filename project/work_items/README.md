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
