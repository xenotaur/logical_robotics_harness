# Design Backlog

Lightweight list of deferred ideas that are not yet ready for a formal
proposal or work item. Each entry should record what was noted, why it was
deferred, and where it came from so a future reader can act on it without
re-deriving context.

---

## Validator drift-check for synced skill references

**Noted:** 2026-06-30, during `WS-PRIOR-ART-CHECK` design session.

**Idea:** Extend `lrh validate` (or a small standalone script) to diff each
consuming skill's copy of a shared reference doc against the `_shared/`
master and fail on drift — replacing the comment-only sync convention
currently used for `prior-art-check.md` copies.

**Status:** Trigger fired — 2026-07-22 design review of the "Agent-specific
publication guidance" entry below found that `review_response.md` and
`review_protocol.md` (the other manually-synced copy pair in this repo,
kept in sync via a "Sync note" convention rather than a shared `_shared/`
master) had already drifted in section-header wording (`## 1) Triage` vs
`## 1) Triage each reported comment/issue`, and similarly for sections 4
and 5) within the same same-day PR (#405) that added both copies' content.
Harmless so far, but it's a real instance of undetected sync drift, not a
hypothetical — the revisit condition is met. Ready to generalize into a
`lrh validate` rule covering both known copy pairs (`prior-art-check.md`
copies; `review_response.md`/`review_protocol.md`) and graduate to a
`/lrh-work-item`.

**Related:** `project/workstreams/proposed/WS-PRIOR-ART-CHECK.md` Non-Goals;
`src/lrh/assist/templates/request/review_response.md`;
`src/lrh/assist/templates/request/review_protocol.md` (second observed
copy pair, see entry below).

---

## `/lrh-decision` skill for authoring `project/memory/decisions/*.md` files

**Noted:** 2026-07-05, during design and implementation of
`WI-DECISION-RECORD-CONVENTIONS`.

**Idea:** A skill (parallel to `/lrh-work-item` and `/lrh-proposal`) that
interviews the user and writes a new `project/memory/decisions/<slug>.md`
file — following the `Context` / `Options considered` / `Decision` /
`Invariants` / `Consequences` shape and the `DEC-*` id convention — for a
decision that resolves an ambiguity or contradiction in existing docs or
implementation. Distinct from `/lrh-proposal`, which proposes new design
direction under a proposed/adopted lifecycle; `/lrh-decision` would record a
decision that's already effectively made, promoted out of
`project/memory/decision_log.md` because other documents need to cite it
independently and repeatedly.

**Status:** Deferred — only one promoted decision file exists in this repo
(`project/memory/decisions/precedence_semantics.md`). The interview
questions and body-section shape can't be specified with confidence from a
single instance; a synthetic second file would prove nothing. Revisit once a
second `project/memory/decisions/*.md` file is created by hand and the
promotion pattern (see `design.md` §14 "Decision-record tiers") has a real
second data point.

**Related:** `project/work_items/resolved/WI-DECISION-RECORD-CONVENTIONS.md`
Non-Goals; `project/design/design.md` §14 "Decision-record tiers"; `project/memory/decisions/precedence_semantics.md`.

---

## Agent-specific publication guidance for `review_response`/`review_protocol`

**Noted:** 2026-07-21, while dogfooding the `review-response` prompt against
Codex Cloud on an external repo (`xenotaur/LCATS#140`).

**Idea:** `review_response.md`/`review_protocol.md` were made agent-neutral
about *how* fixes reach a PR — a three-way outcome (pushed directly /
submitted via platform / local only) instead of assuming `git push` always
works — because different agent sandboxes publish PR fixes through
different mechanisms (direct git push, a platform "Update PR" action with
no working git push inside the container, etc.) and the prompt can't know
in advance which one a given execution environment provides. That generic
framing is deliberately vague about the concrete idiom for any one agent
(e.g. it can't say "click Update PR" because it doesn't know the agent is
Codex).

A sharper version would let `lrh request review-response` accept a target
agent (the `--target-agent`/`REQUEST_TARGET_AGENT` plumbing already exists
for `audit_docs`/`organize_docs`, see `request_cli.py` and
`request_service.py`, but isn't wired into `review_response`) and inject a
short, Python-selected "publication guidance" string naming the concrete
mechanism for known agents, while leaving the rest of the prompt
(triage/validation/evidence, which is agent-independent) single-sourced —
not a full per-agent template file, which would duplicate the ~90% of the
prompt that has nothing to do with publication and re-create the
maintenance burden the `review_response.md`/`review_protocol.md` manual
sync note already causes with just two copies.

**Status:** Deferred — reviewed again 2026-07-22 after PR #405's own review
round grew the precondition/output sections twice more (tightening
`headRefOid` identity verification; deriving the "Local only" remote from
the PR's head repository, not the base repository). Both changes were
generic-correctness fixes applied identically to both `review_response.md`
and `review_protocol.md` — not an instance of a specific agent's
publication idiom needing to be spelled out. This entry's trigger — "a
specific agent's publication idiom repeatedly needs spelling out beyond
what the generic three-way vocabulary can convey" — has still not fired;
generic-correctness churn on the shared prose does not count toward it and
should not be mistaken for it in a future review. That churn is a
different problem (duplicate-copy sync burden), now tracked separately via
the "Validator drift-check for synced skill references" entry above, which
found real (if so far harmless) drift between these same two files and is
graduating to a work item. Continue to defer this entry until an agent's
own idiom is what's driving a change.

**Related:** `src/lrh/assist/templates/request/review_response.md`;
`src/lrh/assist/templates/request/review_protocol.md`;
`src/lrh/assist/request_cli.py` (`--target-agent`);
`src/lrh/assist/request_service.py` (`REQUEST_TARGET_AGENT`);
"Validator drift-check for synced skill references" entry above.
