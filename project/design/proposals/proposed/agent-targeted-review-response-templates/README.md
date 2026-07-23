# Agent-targeted review-response templates proposal set

This proposal set captures the design decision space for whether — and
how — `lrh request review-response` should tailor its generated prompt to
a known target agent, versus keeping the current single agent-general
template, together with the related duplication/growth concerns of
`review_response.md`/`review_protocol.md`.

## Status

`proposed` / `deferred`

This is a design-capture-only proposal. It records the analysis, the
recommended direction (additive per-agent guidance, validated by
dogfooding), and an explicit deferral pending a concrete revisit trigger.
It does not implement any option, open work items, or modify the
templates.

## Documents

1. [`00_proposal.md`](00_proposal.md)
   — umbrella proposal covering background and motivation (the LCATS#140
   origin incident, the two growth forces, the standing-cost and
   duplication concerns), prior art check, the four options considered,
   the recommended direction and revisit trigger, non-goals, and the
   deferred implementation plan.

## Reading order

1. `README.md` (this file)
2. `00_proposal.md`

## Canonical-document touchpoints

If adopted and implemented later, this proposal would likely inform
future updates to:

- `src/lrh/assist/templates/request/review_response.md`
- `src/lrh/assist/templates/request/review_protocol.md`
- `src/lrh/assist/request_cli.py` / `request_service.py` /
  `request_templates.py`
- `project/design/backlog.md` (the two originating entries reference this
  proposal as their resolution path)
