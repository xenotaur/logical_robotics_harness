---
id: PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES
type: design_proposal
title: "Unified /lrh-export and /lrh-session-id skill families"
status: proposed
created_on: 2026-09-24
updated_on: 2026-09-24
implementation_status: not_started
implemented_by: []
supersedes: []
superseded_by: null
related_design:
  - project/design/proposals/adopted/lrh-claude-conversation-exporter/00_proposal.md
  - project/design/proposals/adopted/lrh-codex-app-server-conversation-export/00_proposal.md
  - project/design/proposals/adopted/lrh-antigravity-conversation-exporter/00_proposal.md
  - project/design/proposals/adopted/lrh-session-archive-sync/00_proposal.md
  - project/design/backlog.md
  - project/work_items/proposed/WI-SKILLS-LRH-CLAUDE-SESSION.md
---

# Unified /lrh-export and /lrh-session-id skill families

## Summary

Give LRH's transcript-export and session-identity skills one naming scheme,
`lrh-<verb>-<vendor>`, with two verb families: `export` and `session-id`.
Each family gets a dispatcher skill (`/lrh-export`, `/lrh-session-id`) that
works out which vendor the current session belongs to and hands off to the
matching variant (`-claude`, `-codex`, `-antigravity`). The already-shipped
skills are renamed, and each old name is kept as a deprecated stub for a
transition period. Antigravity gets a session-ID resolver once an
investigation finds a reliable ID source. Both families get how-to and
reference docs.

## Background / Motivation

LRH now exports transcripts from three agent environments, but the skill layer
grew one vendor at a time and the names drifted:

| Family | Claude | Codex | Antigravity |
|---|---|---|---|
| Export skill | `lrh-export-claude` | `lrh-codex-export` | `lrh-antigravity-export` |
| Session-ID skill | none (`WI-SKILLS-LRH-CLAUDE-SESSION` proposes `lrh-claude-session`) | `lrh-codex-session` | none |
| Session-ID CLI | `current-claude-session-id` | `current-codex-thread-id` | none |

The Claude exporter deliberately took the `lrh-export-` prefix
(`PROP-LRH-CLAUDE-CONVERSATION-EXPORTER` Decision 9), and deferred renaming
its siblings to the design work for the `/lrh-export` dispatcher. The design
backlog entry "Generalize conversation export manifests beyond Codex before
`/lrh-export`" says the same thing. That design work has not happened yet,
and there is now a second family with the same problem: session-ID skills
that write the `session_transcript:` pointer into execution records.

The backlog entry's original blocker is gone. The manifest's
`SUPPORTED_SOURCE_TOOLS` in `src/lrh/conversations/export_manifest.py` now
accepts `codex`, `antigravity`, and `claude_code`, and the Claude and
Antigravity adapters write their own `KIND_*` values. Delaying further has a
cost: `WI-SKILLS-LRH-CLAUDE-SESSION` (merged in PR #716) would add a fourth
inconsistent name, `lrh-claude-session`. Deciding the scheme now lets that
item ship under the final name.

Other gaps this work should close:

- **Antigravity export skill is behind the others.** `lrh-antigravity-export`
  has no confirm-before-write gate and no limit on model invocation. Both are
  already tracked in `WI-ANTIGRAVITY-EXPORT-CONFIRM-GATE-ASSESSMENT`.
- **Missing from its own target.** `lrh-antigravity-export` is the only
  canonical skill absent from the Antigravity install target at
  `.gemini/plugins/lrh/skills/`.
- **Docs gap.** `docs/conversations/` has a how-to only for Codex. No doc
  lists the export or session-ID skills.

## Prior Art Check

### Duplication search
- In-repo: No unified dispatcher or family-wide naming exists.
  - Related: the per-vendor skills under `src/lrh/skills/` (listed above).
  - Related: open PR #542, which adds
    `project/design/proposals/proposed/lrh-target-aware-export-archive/00_proposal.md`.
    It is a Codex-authored draft, idle since 2026-08-11. Its Decision 1
    chooses the same dispatcher shape for `/lrh-export`, but most of it is
    about a date-first private archive layout and an archive sorter CLI. It
    does not cover skill naming, the session-ID family, or deprecation.
- Sibling repos: None identified.
- External libraries: Not applicable. This is a skill-layer naming and
  orchestration decision.
- Recommendation: Proceed. For `/lrh-export`, this proposal takes over only
  the choice of dispatcher shape from PR #542. PR #542's archive-layout and
  sorter decisions stay independent and are out of scope here.

### Demand search
- Work items:
  - Found: `WI-SKILLS-LRH-CLAUDE-SESSION`, "Add a metadata-only
    /lrh-claude-session skill...". Absorbed: retitled to `lrh-session-id-claude`.
  - Found: `WI-ANTIGRAVITY-EXPORT-CONFIRM-GATE-ASSESSMENT`. Absorbed into the
    workstream and sequenced after the rename.
  - Found: `WI-EXPORT-SKILLS-LIVE-SESSION-WORDING`. Related: it edits the same
    skill files, so it must not land at the same time as the rename.
- Proposals:
  - Found: `PROP-LRH-CLAUDE-CONVERSATION-EXPORTER` Decision 9. This proposal
    carries out the rename that decision deferred.
  - Found: `PROP-LRH-CODEX-APP-SERVER-CONVERSATION-EXPORT` Implementation Plan
    item 3, the dispatcher follow-on it deferred.
- Backlog: Found: "Generalize conversation export manifests beyond Codex
  before `/lrh-export`". The manifest half is already satisfied; this
  proposal satisfies the naming and dispatcher half.
- Recommendation: When the docs work item lands, mark that backlog entry
  resolved and link it to this proposal.

## Design Decisions

### Decision 1: Naming scheme — `lrh-<verb>-<vendor>`

Options considered:
- **`lrh-<vendor>-<verb>`**, matching `lrh-codex-export`,
  `lrh-antigravity-export` and `lrh-codex-session`. Consistent with two
  shipped names, but a vendor-first name cannot share a prefix with a
  dispatcher.
- **`lrh-<verb>-<vendor>`**, matching `lrh-export-claude`. Every variant
  shares its dispatcher's prefix, so `/lrh-export` and `/lrh-session-id`
  autocomplete to their own variants. It also matches the CLI's verb-first
  subcommands (`export-codex-thread`, `export-claude-session`,
  `current-claude-session-id`).

**Chosen: `lrh-<verb>-<vendor>`.**

- **Verbs:** `export` and `session-id`. `session-id` is used instead of
  `session` so the name says the skill reports an identifier and never
  touches transcript content.
- **Vendor tokens:** `claude`, `codex`, `antigravity`.

The resulting skill set:

| Dispatcher | Variants |
|---|---|
| `/lrh-export` | `/lrh-export-claude`, `/lrh-export-codex`, `/lrh-export-antigravity` |
| `/lrh-session-id` | `/lrh-session-id-claude`, `/lrh-session-id-codex`, `/lrh-session-id-antigravity` |

New vendors join by adding a `-<vendor>` variant to each family.

### Decision 2: Dispatchers delegate; variants own the behaviour

Options considered:
- **Full dispatcher.** Merge every vendor's steps into one skill.
- **Thin alias.** Make `/lrh-export` call a single vendor.
- **Delegating dispatcher.** Resolve the vendor, then carry out the variant's
  own steps inline. This is how `/lrh-execute` runs `/lrh-implement`.

**Chosen: delegating dispatcher.** Each variant keeps its own resolution
order, confirm-before-write gate, archive defaults and metadata-only
reporting. The dispatcher adds no write step and no gate of its own. The
`/lrh-export` dispatcher uses the same invocation rule as its variants: it
runs only on an explicit user request and is never started proactively,
because every variant writes a permanent archive copy. `/lrh-session-id` is
metadata-only, so like `lrh-codex-session` it may be called from
`/lrh-closeout`, `/lrh-land` and `/lrh-implement`.

The dispatcher picks the vendor in this order:
1. **Explicit argument.** `/lrh-export codex ...` or `/lrh-session-id claude`.
   Any remaining arguments pass through to the variant unchanged.
2. **Environment variable.**
   - `CLAUDE_CODE_SESSION_ID` means Claude.
   - `CODEX_THREAD_ID` means Codex.
   - An Antigravity signal only if Decision 5's investigation finds one.
3. **Ask.** If no variable is set, or more than one is, ask the user. Never
   guess: a wrong guess writes an archive copy of the wrong session.

### Decision 3: Rename shipped skills and keep deprecated stubs

Options considered:
- **Hard rename.** The installer (`src/lrh/skills/installer.py`) never deletes
  a skill folder whose canonical source has been removed. Downstream installs
  would keep a stale full copy of the old skill indefinitely.
- **Permanent aliases.** Most compatible, but the skill list stays twice as
  long.
- **Deprecated stubs for a transition period.**

**Chosen: deprecated stubs.** Renames:

| Old name | New name |
|---|---|
| `lrh-codex-export` | `lrh-export-codex` |
| `lrh-antigravity-export` | `lrh-export-antigravity` |
| `lrh-codex-session` | `lrh-session-id-codex` |

Each old name stays as a stub `SKILL.md`. The stub:
- says it is deprecated and names its replacement;
- tells the agent to run the replacement with the same arguments;
- sets `disable-model-invocation: true`, so only a typed command reaches it
  and the model always picks the new name.

That protection is enforced differently on each install target:

| Target | How `disable-model-invocation: true` is enforced |
|---|---|
| Claude (`.claude/skills/`) | Honored as written. |
| Codex (`.agents/skills/`) | `CodexSkillRenderer` strips the key and writes `policy.allow_implicit_invocation: false` into `agents/openai.yaml`. Equivalent protection. |
| Antigravity (`.gemini/plugins/lrh/skills/`) | `AntigravitySkillRenderer` strips the key and writes nothing in its place. **No equivalent protection.** |

For Antigravity:
- **Mitigation.** The stub's `description` must itself say not to select it
  (for example, "Deprecated alias; do not select. Use /lrh-export-<vendor>."),
  so model-driven selection prefers the replacement.
- **Check first.** The rename work items must check whether Antigravity
  supports any invocation-control field. If it does, map
  `disable-model-invocation` onto it in the renderer.
- **Residual risk is low.** A stub selected by mistake only hands off to its
  replacement, so the behavior is the same either way.

A reinstall overwrites any stale full copy downstream with the stub. Removing
the stubs is a later follow-up (see Open Questions).

Following this project's lifecycle convention, `adopted` and `resolved`
documents that quote the old names are not rewritten. Only current documents
change: skills, `CLAUDE.md`, `docs/`, and proposed work items.

### Decision 4: CLI subcommands stay as they are

Options considered:
- Normalize CLI names too, for example by adding
  `current-<vendor>-session-id` aliases.
- Leave the CLI alone.

**Chosen: leave the CLI alone.** The CLI is already verb-first. Its names use
each vendor's own terms (Codex "thread", Claude "session", Antigravity
"conversation"), and those terms match the ID each tool actually exposes.
Unifying the skill layer is what users see and is enough.

The one new CLI subcommand, the Antigravity resolver (Decision 5), follows
the same convention: it uses Antigravity's own term, "conversation", and
reports the current ID.

### Decision 5: Investigate Antigravity session identity before building it

Antigravity has no known variable exposing the current conversation ID. It
also has no `session_transcript:` pointer format. The formats that exist are
`codex-app:<task-or-thread-id>` and `claude-app:<host-uuid-stem>`.
`export-antigravity-session` already finds transcripts by `--conversation-id`
or `--latest` under `~/.gemini/antigravity/brain/<id>/`, but `--latest` only
guesses which session is current.

**Chosen: investigate first.** An investigation work item will:
- find a reliable source for the current conversation ID, or confirm there
  isn't one;
- define the pointer format (`antigravity-app:<conversation-id>` is the
  candidate);
- decide what the resolver does when the current session cannot be
  determined.

The resolver CLI and the `lrh-session-id-antigravity` skill depend on that
item. Until they ship, `/lrh-session-id` reports Antigravity as unsupported
and records `pending`, the same way `lrh-codex-session` handles an unresolved
pointer.

### Decision 6: Every variant installs to every target

Each variant and dispatcher is rendered to all three install targets:
`.claude/skills/`, `.agents/skills/` and `.gemini/plugins/lrh/skills/`. The
rename work item closes the gap where the Antigravity target lacks its own
exporter. A variant that cannot work in a given host (for example, exporting
Codex from inside Claude Code) still installs there. It works when given an
explicit ID or path, and otherwise reports that it cannot resolve a current
session.

## Non-Goals

- Does not rename or add aliases for any `lrh conversation` CLI subcommand
  (Decision 4). The only new CLI subcommand is the Antigravity resolver.
- Does not change the export manifest, the archive layout, or
  `inspect-export`'s verification logic. The one change to `inspect-export`
  is its `--help` text, which still says "Codex".
- Does not adopt, supersede or implement PR #542's private-archive layout or
  archive sorter. This proposal takes only the dispatcher shape.
- Does not rewrite `adopted` or `resolved` documents that quote the old skill
  names.
- Does not add a vendor beyond Claude, Codex and Antigravity. Jules ingestion
  stays with `WI-SESSION-SYNC-JULES-INGESTION`.
- Does not add installer pruning of removed skills. The deprecated stubs work
  around this instead.
- Does not change how `/lrh-closeout`, `/lrh-land` or `/lrh-implement` use
  session pointers, except to call the renamed skills. Their routing through
  the session-ID skills is already scoped in `WI-SKILLS-LRH-CLAUDE-SESSION`.

## Implementation Plan

Delivered under `WS-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES`, in roughly this
order:

1. **`WI-EXPORT-SKILL-FAMILY-RENAME`**
   - Rename `lrh-codex-export` to `lrh-export-codex` and
     `lrh-antigravity-export` to `lrh-export-antigravity`.
   - Add deprecated stubs for both old names.
   - Install the Antigravity exporter to `.gemini/plugins/lrh/skills/`.
   - Update `CLAUDE.md` and current docs.
2. **`WI-SESSION-ID-CODEX-SKILL-RENAME`**
   - Rename `lrh-codex-session` to `lrh-session-id-codex` and add a
     deprecated stub.
   - Update the skills that reference it.
3. **`WI-SKILLS-LRH-CLAUDE-SESSION`** (existing, retitled)
   - Ship the Claude session-ID skill as `lrh-session-id-claude` instead of
     `lrh-claude-session`.
   - Scope is otherwise unchanged.
4. **`WI-ANTIGRAVITY-EXPORT-CONFIRM-GATE-ASSESSMENT`** (existing)
   - Now depends on item 1 and edits `lrh-export-antigravity`.
5. **`WI-ANTIGRAVITY-SESSION-ID-INVESTIGATION`**
   - Investigation per Decision 5.
6. **`WI-ANTIGRAVITY-SESSION-ID-RESOLVER`**
   - Depends on item 5.
   - Add the Antigravity resolver CLI and `lrh-session-id-antigravity`.
7. **`WI-LRH-EXPORT-DISPATCHER`**
   - Depends on items 1 and 4 (whether the Antigravity variant has a confirm gate).
   - Add the `/lrh-export` dispatcher.
8. **`WI-LRH-SESSION-ID-DISPATCHER`**
   - Depends on items 2 and 3.
   - Add the `/lrh-session-id` dispatcher. Antigravity reports unsupported
     until item 6 ships.
9. **`WI-EXPORT-SESSION-ID-DOCS`**
   - Depends on items 4, 6, 7 and 8.
   - A how-to per vendor under `docs/conversations/`.
   - A reference page listing both skill families.
   - Fix the stale backlog entry, the `proposals/README.md` bucket link, and
     `inspect-export`'s help text.

`WI-EXPORT-SKILLS-LIVE-SESSION-WORDING` edits the same skill files as item 1.
Land it strictly before or strictly after item 1, never while item 1 is in
flight.

## Cross-References

- Deferred rename: `PROP-LRH-CLAUDE-CONVERSATION-EXPORTER` Decision 9.
- Deferred dispatcher: `PROP-LRH-CODEX-APP-SERVER-CONVERSATION-EXPORT`
  Implementation Plan item 3.
- Backlog: `project/design/backlog.md`, "Generalize conversation export
  manifests beyond Codex before `/lrh-export`".
- Overlapping draft: PR #542,
  `proposed/lrh-target-aware-export-archive/00_proposal.md`.
- Session pointer formats: `PROMPTS.md`, `project/executions/README.md`,
  `src/lrh/skills/lrh-closeout/references/closeout-workflow.md`.
- Session-storage audit:
  `project/audits/2026-09-22-session-sync-export-ecosystem-audit.md`.

## Open Questions

- **When are the stubs removed?** LRH has no release cadence. Candidate
  triggers: a fixed date, or once known downstream projects (for example
  LCATS) have reinstalled. File the removal work item when the trigger is
  chosen.
- **Should PR #542 be closed?** Once this proposal is adopted, decide
  whether PR #542 is narrowed to archive layout only, or closed.
- **What if a session matches two vendors?** For example, Claude Code running
  inside a Codex-hosted terminal. Decision 2 says ask the user; confirm
  during dispatcher dogfooding that this case actually occurs.
