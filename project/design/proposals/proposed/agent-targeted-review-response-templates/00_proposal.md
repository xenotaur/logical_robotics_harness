---
id: PROP-AGENT-TARGETED-REVIEW-RESPONSE-TEMPLATES
type: design_proposal
title: Agent-Targeted vs Agent-General review_response/review_protocol Templates
status: proposed
created_on: 2026-07-22
updated_on: 2026-07-22
implementation_status: deferred
implemented_by: []
supersedes: []
superseded_by: null
related_design:
  - project/design/backlog.md
  - src/lrh/assist/templates/request/review_response.md
  - src/lrh/assist/templates/request/review_protocol.md
  - src/lrh/assist/request_cli.py
  - src/lrh/assist/request_service.py
  - src/lrh/assist/request_templates.py
---

## Summary

Captures the design decision space for whether — and how — `lrh request
review-response` should tailor its generated prompt to a known target agent,
versus keeping the current single agent-general template. Records the
analysis, the recommended direction (additive per-agent guidance, validated
by dogfooding), and an explicit deferral pending a concrete revisit trigger.
No implementation is proposed now.

## Background / Motivation

`review_response.md` (162 lines) and `review_protocol.md` (150 lines) were
made agent-neutral about *how* a fix reaches a PR — a three-way outcome
(pushed directly / submitted via platform / local only) — after the old
"`git push` always works" precondition hard-stopped Codex Cloud in a sandbox
with no configured git remote (dogfooded on `xenotaur/LCATS#140`, landed in
PR #405).

Two distinct growth forces on these templates were identified during the
2026-07-22 design review:

- **Force A — generic-correctness growth:** the templates accreting more
  precise language each review round (PR #405's own review added two such
  fixes: a `headRefOid` identity cross-check, and deriving the "Local only"
  remote from the PR's head repository). Applied identically to both copies.
- **Force B — agent-specific-vocabulary growth:** a specific agent's
  publication idiom needing to be spelled out beyond the generic three-way
  vocabulary. **Not yet observed.**

A third consideration surfaced separately: the agent-general publication
taxonomy imposes a **standing cost on every invocation** — though a
narrower one than first estimated. "Local only" is the shared *failure
fallback* ("neither of the above was possible",
`review_response.md:126-143`), reachable by any agent when its normal
publication path fails: Claude.app can land there after a push or
authentication failure, and Codex Cloud when platform-managed publication
is unavailable. So the fallback branch and its ~14-line remote-repair
recipe are *not* dead weight for a known agent. What is necessarily
irrelevant to a known agent is only the **other agent's
successful-publication branch** — roughly one of the three outcomes
(Codex Cloud never uses "Pushed directly"; Claude.app never uses
"Submitted via platform") — a materially smaller standing cost than a
two-thirds-of-the-taxonomy framing would suggest. This correction (raised
in PR #408 review) weakens the motivation for agent targeting and, if
anything, reinforces this proposal's deferral recommendation.

Finally, the two files **substantially duplicate each other** — but not
completely. `review_protocol.md` is mirrored inline into
`review_response.md` via a manual "Sync note" (`review_protocol.md:5-7`),
and the shared protocol core is word-for-word identical (Canonical
validation, Repair sequencing, and Evidence-requirements bodies match
byte-for-byte). Each PR #405 fix was applied by hand to both copies — real
duplicate-edit toil. However, `review_response.md` also carries
**intentional response-context content that `review_protocol.md` does not
contain** (raised in PR #408 review): a precondition written for the
generated-prompt context (with substituted `{{REVIEW_URL}}` rather than
generic `<pr-url>` placeholders), a `## Repository overrides` section
(`review_response.md:42-46`), the trailing untrusted-reviewer-input
security note plus `{{UNRESOLVED_THREADS}}` injection point
(`review_response.md:152-162`), and differently-worded triage and section
headings. Any single-sourcing effort must treat these as deliberate
divergences to preserve, not sync drift to reconcile.

## Prior Art Check

### Duplication search
- In-repo: No existing implementation. `--target-agent`/`REQUEST_TARGET_AGENT`
  plumbing exists (`request_cli.py:189`, `request_service.py:283`) but only
  substitutes a *name string* into `audit_docs`/`organize_docs`
  (`audit_docs.md:4`); it does not select content blocks. The renderer is
  flat `{{VAR}}` substitution with no conditionals
  (`request_service.py:167-174`).
- Sibling repos: None identified.
- External libraries: None identified — a general templating engine (Jinja2,
  etc.) would be far more than this narrow need warrants.
- Recommendation: Proceed (as design capture; no build now).

### Demand search
- Work items: `WI-SYNCED-COPY-DRIFT-CHECK` (PR #407) — being
  **closed/abandoned**; this proposal supersedes it as the path for these
  threads.
- Proposals: None found.
- Backlog: Found — both "Validator drift-check for synced skill references"
  and "Agent-specific publication guidance for
  `review_response`/`review_protocol`" in `project/design/backlog.md`. This
  proposal is their design-capture path; the backlog entries reference it.
- Recommendation: Update the two backlog entries to point here; close PR #407.

## Design Decisions

### Decision: How should the review-response prompt handle agent-specific publication mechanics?

**Options considered:**

1. **General-only (status quo).** One agent-neutral template. Robust across
   unknown environments (RFC 1122 robustness principle — "be liberal in what
   you accept"), but larger, and presents inapplicable options on every run.
2. **Additive per-agent guidance string.** Inject a short, Python-selected
   `{{PUBLICATION_GUIDANCE}}` string naming the concrete mechanism for known
   agents, *alongside* the general taxonomy (which remains as the fallback).
   Achievable today with the existing flat-substitution engine; degrades
   safely if the `--target-agent` guess is wrong. Low cost, reversible.
3. **Subtractive targeted template.** A smaller template that *removes*
   inapplicable branches. Requires new conditional/block-selection machinery
   the flat engine lacks; per the corrected standing-cost analysis above,
   safely removable content is only the other agent's success branch (the
   "Local only" fallback and its remote-repair recipe must stay, since any
   agent can reach them on publication failure) — an even smaller trim than
   first estimated; re-introduces the exact per-agent-assumption brittleness
   that caused the LCATS#140 incident; re-creates per-agent maintenance
   burden that goes stale as platforms change.
4. **De-duplication / single-sourcing (orthogonal enabling seam).** Make
   `review_response.md` include/reference `review_protocol.md` rather than
   inline a second copy — eliminating the hand-sync burden for the shared
   protocol core and shrinking the template. This is more than a
   placeholder reconcile: no include mechanism exists today, the two files
   deliberately use different placeholder styles (`{{REVIEW_URL}}` vs
   `<pr-url>`), and `review_response.md` carries intentional
   response-context content the protocol file lacks (response-context
   precondition, `## Repository overrides`, the untrusted-reviewer-input
   note and `{{UNRESOLVED_THREADS}}` injection point, differently-worded
   triage — see Background). An implementation must first enumerate these
   deliberate divergences and preserve them outside the single-sourced
   core; only the byte-identical shared sections are candidates for
   single-sourcing. If done, the seam it creates is also where per-agent
   guidance would be injected.

**Recommended direction (not a commitment to build now):**

- **Defer building** until a concrete agent-publication issue recurs with
  more data. The value of targeting is presently an *a-priori* argument —
  there is no observed failure caused by the current menu, and the single
  incident on record points *against* baking in per-agent assumptions.
- When triggered, **prefer Option 2 (additive)**, **validated by dogfooding**
  (run targeted vs. general prompt against a real Codex and a real Claude
  session and measure), not asserted.
- **Reject Option 3 (subtractive)** as not-worth-it: high cost, modest size
  win, and it fights the robustness lesson already paid for (YAGNI).
- **Consider Option 4 (de-duplication)** as the enabling seam, decided
  together with the publication-guidance question rather than separately.

**Revisit trigger:** a concrete agent-publication failure or friction that
the general three-way vocabulary demonstrably cannot convey, **OR** a
decision to invest in single-sourcing the shared protocol (which would create
the injection seam anyway).

## Non-Goals

- Does not implement any option now — this proposal is design capture only.
- Does not revive `WI-SYNCED-COPY-DRIFT-CHECK` — drift *detection* was the
  wrong tool (it addresses divergence-once-introduced, not the
  duplication/size actually at issue); that WI is being closed.
- Does not adopt a general templating engine (Jinja2 etc.) — out of
  proportion to the need.
- Does not address Force A (generic-correctness growth) via this mechanism —
  that is ordinary template maintenance, not agent targeting.

## Implementation Plan

Deferred. No work items or workstream are opened by this proposal. When the
revisit trigger fires, the expected shape is a single-workstream effort:
(1) a dogfooding evaluation comparing targeted vs. general prompts on real
Codex and Claude sessions, then, if favorable, (2) an additive
`{{PUBLICATION_GUIDANCE}}` injection wired through the existing
`--target-agent` plumbing, optionally preceded by (3) a
de-duplication/single-sourcing change to `review_response.md`/
`review_protocol.md` that provides the injection seam.

## Cross-References

- Backlog threads: `project/design/backlog.md` — "Validator drift-check for
  synced skill references"; "Agent-specific publication guidance for
  `review_response`/`review_protocol`"
- Superseded WI: `WI-SYNCED-COPY-DRIFT-CHECK` (PR #407, being closed)
- Origin incident: PR #405; `xenotaur/LCATS#140`
- Templates: `src/lrh/assist/templates/request/review_response.md`,
  `review_protocol.md`
- Plumbing: `src/lrh/assist/request_cli.py`, `request_service.py`,
  `request_templates.py`
