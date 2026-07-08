---
id: PROP-LRH-OPEN-WORK
type: design_proposal
title: Holistic Open-Work Survey — /lrh-open-work Skill, Companion Request Template, and Deterministic Git/Audit CLI Modules
status: proposed
created_on: 2026-07-07
updated_on: 2026-07-07
implementation_status: not_started
implemented_by: []
supersedes: []
superseded_by: null
related_design:
  - project/work_items/proposed/WI-SKILLS-LRH-WORK-AUDIT.md
  - project/work_items/proposed/WI-TEMPLATE-AUDIT-WORK-ITEMS.md
  - src/lrh/assist/templates/request/assessment.md
  - src/lrh/assist/templates/request/work_items_from_audit.md
  - src/lrh/work_items/audit.py
  - src/lrh/integrations/github/gh_client.py
  - .claude/skills/lrh-doc-audit/SKILL.md
  - .claude/skills/lrh-closeout/SKILL.md
---

## Summary

This proposal defines `/lrh-open-work`, a Claude Code skill (with a companion
`lrh request open-work` template) that surveys every place open work can
silently drift in an LRH-governed repo — git branch/PR state, work-item
hygiene, focus/status/roadmap/design-doc staleness, and untracked audit
follow-ups — and reports it as one cross-checked "open threads" artifact.
Rather than reimplementing detection logic that already exists, it composes
`lrh work-items audit` and `lrh request assess-repository`, and adds exactly
two new deterministic CLI modules (`lrh git audit`, `lrh audits
list-followups`) for the genuinely uncovered ground.

## Background / Motivation

A single taurworks investigation session (2026-07-06/07) found simultaneously:
four status/design docs framed around a design phase that had shipped five
PRs earlier and never got a follow-up pass; two active work items missing
required frontmatter, failing `lrh validate` with 20+ errors that predated
the session; an orphaned branch with two unmerged commits and no PR; and a
safety audit with 7 follow-up recommendations, none tracked as work items.
None of this was individually hard to find, but required manual
cross-referencing of `git log`/`gh pr list`/`gh branch` against every
`project/` bucket by hand — exactly the class of repeatable, mechanical
survey a skill should own.

An initial `/lrh-design` pass proposed six read-only collectors (git state,
WI schema hygiene, focus/status/roadmap staleness, design-doc staleness,
audit follow-ups, `lrh validate`). Before drafting this proposal, the
required prior-art check (below) found that three of those six collectors,
plus one of the planned cleanup actions, already exist as built CLI/template
infrastructure — so this proposal's actual job is narrower than originally
scoped: compose what exists, build only what's missing, and resolve overlap
with an already-proposed, closely related work item pair.

## Prior Art Check

### Duplication search

- In-repo: **Related** — `lrh work-items audit` (`src/lrh/work_items/audit.py`)
  already performs deterministic WI lifecycle/schema-hygiene auditing; `lrh
  request assess-repository --scope project`
  (`src/lrh/assist/templates/request/assessment.md`) already performs
  declared-vs-actual drift assessment across focus/roadmap/design/status;
  `lrh request work-items-from-audit` already converts audit findings into
  proposed WIs. These three cover half of the originally-scoped collectors
  and one cleanup action.
- Sibling repos: None identified.
- External libraries: None identified — this is control-plane-specific.
- Recommendation: Proceed, but restructure to **compose** the above rather
  than reimplement; scope the new work to the two genuinely uncovered
  collectors (git/PR branch hygiene; audit-followup coverage checking).

### Demand search

- Work items: **Found** — `WI-SKILLS-LRH-WORK-AUDIT`
  (project/work_items/proposed/WI-SKILLS-LRH-WORK-AUDIT.md, "Implement
  lrh-work-audit Claude Code skill") and `WI-TEMPLATE-AUDIT-WORK-ITEMS`
  (project/work_items/proposed/WI-TEMPLATE-AUDIT-WORK-ITEMS.md, "Implement
  lrh request audit-work-items template") — a proposed skill+template pair
  covering WI-hygiene batching, priority scoring, and orphaned-execution-
  record→merged-PR forensics.
- Proposals: None found governing either WI (`related_design: []` on both).
- Backlog: No matching entries in `project/design/backlog.md`.
- Recommendation: **Offer to supersede** both WIs — see Decision 3 below for
  the reasoning and scope reconciliation.

## Design Decisions

### Decision 1: Compose existing infrastructure rather than reimplement

Options considered: (a) build all six original collectors from scratch
inside the new skill; (b) shell out to existing deterministic/template
surfaces where they already cover a collector.

**Chosen: (b).** The WI-hygiene collector becomes a passthrough to `lrh
work-items audit --format json`; the focus/status/roadmap/design-doc
staleness collector becomes a passthrough to `lrh request assess-repository
--scope project`. This avoids two parallel implementations of the same
drift logic and keeps `/lrh-open-work` as an orchestrator, not a competitor.

### Decision 2: Two new deterministic CLI modules for the genuinely uncovered ground

Options considered: (a) embed git/PR and audit-followup detection as inline
Bash steps in the skill (like `/lrh-closeout`'s ad hoc `gh pr view` calls
today); (b) build them as new, independently unit-tested CLI modules
following the `lrh work-items audit` shape (dataclass report, `--format
json/md`, fixture-repo tests).

**Chosen: (b).**

- `lrh git audit` — new top-level CLI group, parallel to
  `work-items`/`design` in `src/lrh/cli/main.py`. Local-git half
  (uncommitted changes, unpushed commits, no-upstream branches) is testable
  against a fixture git repo with zero network dependency. PR-classification
  half (`gh pr list --state all` → tracked/merged-stale/orphaned) reuses the
  existing, already-mocked `gh_client.run_gh_json` wrapper
  (`src/lrh/integrations/github/gh_client.py`) — no new test infrastructure
  needed.
- `lrh audits list-followups` — new small CLI group. Deterministic half:
  discover `project/audits/*.md`, extract candidate follow-up bullets from
  headings matched by a loose keyword heuristic (sampled headings vary:
  "Recommended next steps", "Recommended Follow-Up" — no fixed convention
  exists, so exact-heading matching is not viable; use fuzzy keyword match
  on heading text). The semantic "is this already a WI" matching stays
  agent-side in the skill/template, consuming the structured extraction —
  same two-layer split already established by `lrh work-items audit` →
  `lrh request work-item-semantic-audit`.

Rejected (a) because it produces logic that's only exercised by manual
skill runs, never unit-tested, and not reusable by other skills (e.g.
`/lrh-closeout` still hand-rolls single-PR `gh pr view` lookups today).

### Decision 3: Resolve overlap with WI-SKILLS-LRH-WORK-AUDIT / WI-TEMPLATE-AUDIT-WORK-ITEMS

Options considered: (a) full absorption — treat both WIs as fully subsumed;
(b) full separation — keep both WIs standing, unrelated to this proposal;
(c) partial merge — fold in the mechanism that overlaps, defer the part
that doesn't.

**Chosen: (c).** The proposed skill's "orphaned execution-record → merged-PR
forensics" is mechanically identical to the new `lrh git audit`
branch-classification logic — both reconcile git/PR reality against a
different declared-state source (execution records vs. branches). Building
that gh-querying logic twice would be direct duplication. The remaining
unique scope of WI-SKILLS-LRH-WORK-AUDIT — priority/importance/feasibility/
risk scoring of WIs — is a distinct decision-support capability (ranking
"what to work on next"), not hygiene-surfacing, and is too thin on its own
to justify a second skill and a second companion template pair.
**Recommendation: mark both WIs superseded by `PROP-LRH-OPEN-WORK` once this
proposal is adopted; defer priority scoring as explicitly out of scope
(Non-Goals) with a note that it may become a future optional mode of
`/lrh-open-work` or a narrower follow-on.** This proposal does not itself
edit those WI files — that is a follow-up action for the user to confirm
separately, since `/lrh-proposal` does not mutate other artifacts.

### Decision 4: Report artifact — persisted, gated, dated

Options considered: (a) ephemeral chat-only report; (b) persisted dated
snapshot.

**Chosen: (b).** Persist to `project/status/open-work-YYYY-MM-DD.md`,
written only after an explicit confirm gate (same pattern as
`/lrh-doc-audit` Step 7/8). Recurring surveys benefit from being diffable
over time, consistent with the `project/audits/*` precedent. `lrh validate`
schema support for this new artifact type is explicitly deferred
(Non-Goals) — `project/status/current_status.md` isn't schema-validated
today either, so this isn't a regression.

### Decision 5: Skill and template as parallel deliverables

Per the `audit_docs.md` ↔ `/lrh-doc-audit` precedent (and the WI pair being
superseded, which already established this shape): a Claude-native skill
and an agent-neutral `lrh request open-work` template are two
content-aligned but independently-authored surfaces for the same workflow,
not one wrapping the other. Both are first-cut scope, not phased.

### Decision 6: Cleanup pass — individually-gated menu, git/PR state is report-only

The optional cleanup pass (WI-frontmatter backfill, doc-staleness edits) is
a menu of discrete, individually-confirmable actions — never a blanket
"clean up everything" toggle — and delegates to `/lrh-work-item` for
drafting follow-up WIs rather than reimplementing WI authoring.
Doc-staleness findings are classified `likely-stale` / `unconfirmed` by
heuristic but never auto-edited without per-finding human confirmation,
since each is a distinct factual claim about a different file. Git
branch/PR findings get no cleanup action of any kind (report-only) —
branch/PR state is shared and harder to reverse than a local `project/`
file edit.

### Decision 7: Boundary with /lrh-closeout stays advisory-only

`/lrh-closeout` is reactive/single-target; `/lrh-open-work` is
proactive/repo-wide. The open-work report may *recommend* running
`/lrh-closeout` for WIs/WSs it finds ready-but-unclosed, but never invokes
it automatically.

## Non-Goals

- Does not implement WI priority/importance/feasibility/risk scoring —
  deferred; may become a future optional mode.
- Does not mutate git branches or PRs (no deletion, no closing, no
  force-push) — strictly report-only for git/PR findings.
- Does not auto-edit doc-staleness findings without individual human
  confirmation per finding.
- Does not invoke `/lrh-closeout` automatically — recommends only, in the
  report.
- Does not add `lrh validate` schema support for the new
  `project/status/open-work-*.md` artifact type in this proposal —
  fast-follow scope.
- Does not replace `lrh work-items audit`, `lrh request assess-repository`,
  or `lrh request work-items-from-audit` — composes them.
- Does not itself mark WI-SKILLS-LRH-WORK-AUDIT / WI-TEMPLATE-AUDIT-WORK-ITEMS
  as superseded — that is a follow-up action for the user.

## Implementation Plan

Medium/large scope (four deliverables with a dependency chain) — recommend
a governing workstream to sequence:

1. **`lrh git audit` CLI module + unit tests** — no dependencies; can start
   immediately.
2. **`lrh audits list-followups` CLI module + unit tests** — no
   dependencies; can proceed in parallel with (1).
3. **`/lrh-open-work` skill** — depends on (1) and (2) existing (shells out
   to both), plus composes `lrh work-items audit` and `lrh request
   assess-repository` (already built).
4. **Companion `lrh request open-work` template** — depends on (3),
   mirroring how WI-TEMPLATE-AUDIT-WORK-ITEMS depended on
   WI-SKILLS-LRH-WORK-AUDIT for its cross-reference target.

## Open Questions

- Exact CLI subcommand names (`lrh git audit` vs. `lrh git status`; `lrh
  audits list-followups` vs. `lrh audits audit`) — finalize at
  WI-drafting time.
- Staleness-phrase list and confidence thresholds for the doc-staleness
  collector — start narrow (reusing `assess-repository`'s existing drift
  lens), tune after real runs.
- Follow-up-heading detection heuristic robustness — sampled audits use
  inconsistent headings ("Recommended next steps," "Recommended
  Follow-Up"); the fuzzy-match approach may need widening once tried
  against more audits.

## Cross-References

- Superseded (pending user confirmation):
  `project/work_items/proposed/WI-SKILLS-LRH-WORK-AUDIT.md`,
  `project/work_items/proposed/WI-TEMPLATE-AUDIT-WORK-ITEMS.md`
- Composed, not duplicated:
  `src/lrh/assist/templates/request/assessment.md`,
  `src/lrh/assist/templates/request/work_items_from_audit.md`,
  `src/lrh/work_items/audit.py`
- Pattern precedent: `.claude/skills/lrh-doc-audit/SKILL.md`,
  `.claude/skills/lrh-closeout/SKILL.md`
- Reused wrapper: `src/lrh/integrations/github/gh_client.py`
