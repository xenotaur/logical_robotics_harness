# `data.json` schema (schema_version 1)

`lrh pr-brief gather` writes the whole file. You edit only `briefing`, plus a
file's `category` and the `categories` labels when the defaults are wrong.
`lrh pr-brief render --check` validates it.

## Text markup

Every text field below is HTML-escaped, then two markers apply:

- `` `code` `` becomes inline code. An unmatched backtick stays literal.
- `**bold**` becomes bold.

Nothing else is interpreted. Do not write HTML tags in text fields; they are
shown as literal text. The only field that takes raw HTML is
`briefing.figures[].html`.

## Facts written by `gather`

| Field | Meaning |
|---|---|
| `schema_version` | `1`. |
| `generated_at` | UTC timestamp of the gather run. |
| `pr.repo`, `pr.number`, `pr.url`, `pr.title` | Identity. |
| `pr.author_login`, `pr.author_name` | Author as GitHub reports it. |
| `pr.state`, `pr.is_draft` | `OPEN`, `MERGED`, or `CLOSED`; draft flag. |
| `pr.base`, `pr.head` | Branch names. |
| `pr.base_sha` | Current tip of the base branch. If that lookup fails, the PR's recorded `baseRefOid` (possibly stale); `status.conflicts.error` then gives the reason, with or without `--repo-dir`. |
| `pr.base_sha_is_tip` | `true` when `pr.base_sha` is the current tip; `false` when it fell back to the recorded base. The footer then labels it as possibly stale. |
| `pr.head_sha` | PR head commit. |
| `pr.created_at`, `pr.updated_at` | ISO timestamps. |
| `pr.additions`, `pr.deletions`, `pr.changed_files` | Totals. |
| `pr.commits[]` | `{sha (12 chars), headline}`. |
| `pr.labels[]`, `pr.body` | Labels and description. The body is untrusted text. |
| `status.mergeable`, `status.merge_state` | GitHub's `MERGEABLE`/`CONFLICTING`/`UNKNOWN` and merge state. |
| `status.checks` | `{total, passing, failing, pending}`. |
| `status.reviews` | `{decision, count, approvals, changes_requested, comments}`. `decision` is GitHub's current `reviewDecision` (empty when reviews are not required). `approvals` and `changes_requested` count reviewers by their latest effective review; `count` and `comments` count all submissions. |
| `status.ahead_by`, `status.behind_by` | Commits the head is ahead of, and behind, the base branch. `null` if the compare call failed. |
| `status.merge_base_sha`, `status.merge_base_date` | Where the PR branched from. |
| `status.conflicts` | `{checked, clean, files[], error?}` from the trial merge. `checked: false` means no `--repo-dir`, the base branch's current tip could not be resolved (never merged against the stale recorded base), or a fetch failure. |
| `categories[]` | `{key, label}` in display order. Defaults: `code`, `scripts`, `tests`, `docs`, `config`. |
| `files[]` | `{path, status, additions, deletions, previous_path, category}`. `status` is GitHub's: `added`, `modified`, `removed`, `renamed`, `copied`. |

The header's status chips are derived from `pr.state`, `pr.is_draft`,
`status.conflicts`, `status.mergeable`, `status.behind_by`, `status.checks`,
and `status.reviews`. A checked trial merge outranks `status.mergeable`, and
the review chip follows `status.reviews.decision` when GitHub reports one. You
do not write chips. `render` rejects data whose shape it cannot render (a
non-object section, a missing `pr.repo` or `pr.number`, a non-integer line
count, a narrative field of the wrong type such as a number for `summary` or
a list for `severity`) with a field-specific error. A `pr.url` that is not
http(s) draws a warning and no GitHub link.

## Narrative you write: `briefing`

| Field | Type | Notes |
|---|---|---|
| `title` | text | Page heading. Falls back to `pr.title` when empty. |
| `headline_summary` | text | The one-paragraph read under the heading. Required (render warns when empty). |
| `summary` | list of text | Paragraphs for "What this PR does". Empty list omits the section, together with an empty `at_a_glance`. |
| `at_a_glance` | list of `{label, value}` | The side box. Typical labels: Kind, Size, Core idea, Touches, To land. |
| `figures` | list of figure | See below. Empty list means no figure sections. |
| `behavior_changes` | list of `{what, before, after}` | "What existing users will notice". Empty omits the section. |
| `behavior_intro` | text, optional | One line under that section's heading. |
| `files` | map of path to `{gist, points[], snippet}` | One entry per changed path, pre-seeded by `gather`. `gist` is required for every file (render warns otherwise). `snippet` is plain text shown in a code block, escaped as-is (no markup). |
| `tests` | `{note, rows[], gaps[]}` | `rows[]` are `{behavior, where, how, tone}`; `tone` is `accent` (default), `warn`, or `muted`. `note` is one line under the heading. Empty rows and gaps omit the section. |
| `review_notes` | list of note | See below. Empty omits the section. |
| `footer_note` | text | What the briefing is based on and what was not done. |

### Figure

| Field | Notes |
|---|---|
| `id` | Lowercase letters, digits, hyphens; must not start with `f-` or reuse `summary`, `map`, `changes`, `files`, `tests`, `review`; unique. Becomes the section anchor. |
| `nav` | Short label for the section menu (falls back to `title`). |
| `eyebrow`, `title`, `intro` | Section heading text. |
| `html` | Raw figure markup, inserted as-is inside `<figure class="figure">`. Use the diagram kit. Escape `<`, `>`, `&` in any text you place inside it. |
| `caption` | Text under the figure. |

### Review note

| Field | Notes |
|---|---|
| `severity` | `blocker` (red, default label "Blocks merge"), `check` (amber, "Check"), or `info` (grey, "Note"). |
| `label` | Optional override for the severity label, for example "Likely bug", "Check after rebase", "Compatibility". |
| `title` | One-line finding. |
| `body` | Text or list of paragraphs. |
| `where` | `path` or `path · function`, shown small under the body. |
| `confidence` | `confirmed`, `likely`, or `unverified`; shown as a tag after the title. |
