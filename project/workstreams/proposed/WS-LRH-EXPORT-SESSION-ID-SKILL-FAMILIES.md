---
id: WS-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES
kind: planning_node
title: "Unified /lrh-export and /lrh-session-id skill families"
status: proposed
stage: designed
origin: design_review
summary: "Deliver PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES: rename the transcript-export and session-ID skills to lrh-<verb>-<vendor>, keeping deprecated stubs for the old names; add /lrh-export and /lrh-session-id dispatchers; add an Antigravity session-ID resolver; and document both families."
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_design:
  - project/design/proposals/proposed/lrh-export-session-id-skill-families/00_proposal.md
  - project/design/proposals/adopted/lrh-claude-conversation-exporter/00_proposal.md
  - project/design/proposals/adopted/lrh-codex-app-server-conversation-export/00_proposal.md
  - project/design/proposals/adopted/lrh-antigravity-conversation-exporter/00_proposal.md
work_items:
  - WI-EXPORT-SKILL-FAMILY-RENAME
  - WI-SESSION-ID-CODEX-SKILL-RENAME
  - WI-SKILLS-LRH-CLAUDE-SESSION
  - WI-ANTIGRAVITY-EXPORT-CONFIRM-GATE-ASSESSMENT
  - WI-ANTIGRAVITY-SESSION-ID-INVESTIGATION
  - WI-ANTIGRAVITY-SESSION-ID-RESOLVER
  - WI-LRH-EXPORT-DISPATCHER
  - WI-LRH-SESSION-ID-DISPATCHER
  - WI-EXPORT-SESSION-ID-DOCS
exit_criteria:
  - "Every shipped export and session-ID skill is named lrh-export-<vendor> or lrh-session-id-<vendor>, and each old name (lrh-codex-export, lrh-antigravity-export, lrh-codex-session) is a deprecated stub with disable-model-invocation set to true."
  - "/lrh-export and /lrh-session-id dispatch to the right variant from an explicit argument or the environment, ask when the vendor is ambiguous or unknown, and add no write step or gate of their own."
  - "The Antigravity session-ID investigation has recorded a decision, and lrh-session-id-antigravity has either shipped or been explicitly deferred with the reason recorded."
  - "Every export and session-ID skill and dispatcher is installed in .claude/skills/, .agents/skills/ and .gemini/plugins/lrh/skills/, and CLAUDE.md lists each one."
  - "docs/conversations/ has a how-to for each vendor, a reference page lists both skill families, and the stale backlog entry, proposals README link and inspect-export help text are fixed."
---

# Unified /lrh-export and /lrh-session-id skill families

## Purpose

This workstream delivers `PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES`:

- One `lrh-<verb>-<vendor>` naming scheme for LRH's transcript-export and
  session-ID skills.
- Two dispatchers, `/lrh-export` and `/lrh-session-id`, that pick the right
  per-vendor variant.
- The missing Antigravity session-ID path.
- Documentation for both families.

## Scope

### Included
- Renaming `lrh-codex-export`, `lrh-antigravity-export` and
  `lrh-codex-session` to the new scheme, with deprecated stubs for the old
  names.
- Shipping the Claude session-ID skill as `lrh-session-id-claude`, by
  retargeting the existing `WI-SKILLS-LRH-CLAUDE-SESSION`.
- Bringing `lrh-export-antigravity` up to the other export skills (confirm
  gate, invocation limits), and installing it to the Antigravity target.
- An investigation into Antigravity session identity, then the resolver CLI
  and `lrh-session-id-antigravity` skill.
- The `/lrh-export` and `/lrh-session-id` dispatcher skills.
- How-to and reference docs for both families, and fixes to the stale planning
  and help text.

### Excluded
- Renaming `lrh conversation` CLI subcommands (proposal Decision 4).
- Changes to the export manifest, the archive layout or inspection logic, and
  the archive sorter proposed in PR #542.
- Rewriting `adopted` or `resolved` documents that quote the old names.
- Removing the deprecated stubs. This is a later follow-up; its trigger is an
  open question in the proposal.

## Prior Art Check

### Duplication search
- In-repo: No existing workstream covers skill naming or dispatchers.
  - Related, resolved: `WS-ANTIGRAVITY-CONVERSATION-EXPORT`,
    `WS-LRH-CODEX-CONVERSATION-EXPORTER`, `WS-LRH-CODEX-APP-SERVER-EXPORT`.
    These built the per-vendor exporters this workstream renames.
  - Related, active: `WS-SESSION-ARCHIVE-SYNC`. It covers session storage and
    mirroring, not skill naming. `WI-SKILLS-LRH-CLAUDE-SESSION` currently
    lists it, and will list this workstream too.
- Sibling repos: None identified.
- External libraries: Not applicable.
- Recommendation: Proceed.

### Demand search
- Work items:
  - Found, absorbed: `WI-SKILLS-LRH-CLAUDE-SESSION`,
    `WI-ANTIGRAVITY-EXPORT-CONFIRM-GATE-ASSESSMENT`.
  - Found, related: `WI-EXPORT-SKILLS-LIVE-SESSION-WORDING`. It is not
    absorbed, but must not land while `WI-EXPORT-SKILL-FAMILY-RENAME` is in
    flight.
- Proposals: `PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES`, which this
  workstream delivers.
- Backlog: "Generalize conversation export manifests beyond Codex before
  `/lrh-export`". `WI-EXPORT-SESSION-ID-DOCS` resolves it.
- Recommendation: Link the absorbed work items to this workstream.

## Work Items

Listed in delivery order. Each item's `depends_on:` enforces the order.

1. `WI-EXPORT-SKILL-FAMILY-RENAME`
   - Rename `lrh-codex-export` to `lrh-export-codex` and
     `lrh-antigravity-export` to `lrh-export-antigravity`.
   - Add deprecated stubs for both old names.
   - Install the Antigravity exporter to the Antigravity target.
2. `WI-SESSION-ID-CODEX-SKILL-RENAME`
   - Rename `lrh-codex-session` to `lrh-session-id-codex` and add a
     deprecated stub.
   - Update the skills that reference it.
3. `WI-SKILLS-LRH-CLAUDE-SESSION` (existing, retitled)
   - Add `lrh-session-id-claude` and route Claude session-pointer resolution
     through it.
4. `WI-ANTIGRAVITY-EXPORT-CONFIRM-GATE-ASSESSMENT` (existing)
   - Add a confirm-before-write gate to `lrh-export-antigravity`.
   - Depends on item 1.
5. `WI-ANTIGRAVITY-SESSION-ID-INVESTIGATION`
   - Find a reliable source for the current Antigravity conversation ID and
     define its pointer format.
6. `WI-ANTIGRAVITY-SESSION-ID-RESOLVER`
   - Add the Antigravity resolver CLI and `lrh-session-id-antigravity`.
   - Depends on item 5.
7. `WI-LRH-EXPORT-DISPATCHER`
   - Add the `/lrh-export` dispatcher.
   - Depends on item 1.
8. `WI-LRH-SESSION-ID-DISPATCHER`
   - Add the `/lrh-session-id` dispatcher.
   - Depends on items 2 and 3.
9. `WI-EXPORT-SESSION-ID-DOCS`
   - Per-vendor how-tos, a reference page for both families, and the stale
     docs fixes.
   - Depends on items 7 and 8.

Items 1, 2, 3 and 5 have no dependencies on each other and can run in
parallel. Item 1 and `WI-EXPORT-SKILLS-LIVE-SESSION-WORDING` both edit the
export skill files, so land one before starting the other.

## Exit Criteria

- Every shipped export and session-ID skill follows `lrh-export-<vendor>` or
  `lrh-session-id-<vendor>`, and each old name is a deprecated stub that only
  a typed command can reach.
- Both dispatchers select the right variant from an explicit argument or the
  environment, and ask when the vendor is ambiguous or unknown.
- The Antigravity session-ID investigation has recorded a decision, and the
  Antigravity variant has either shipped or been explicitly deferred with the
  reason recorded.
- Every skill in both families is installed to all three targets and listed
  in `CLAUDE.md`.
- Per-vendor how-tos and a reference page for both families exist, and the
  stale docs and help text are fixed.

## Non-Goals

- Does not rename or add aliases for `lrh conversation` CLI subcommands.
- Does not change the export manifest, archive layout or `inspect-export`
  verification logic.
- Does not add vendors beyond Claude, Codex and Antigravity.
- Does not add installer pruning of removed skills.

## Open Questions

- When are the deprecated stubs removed? This is the proposal's open
  question. Once a trigger is chosen, file the removal work item here or as
  a follow-up.
