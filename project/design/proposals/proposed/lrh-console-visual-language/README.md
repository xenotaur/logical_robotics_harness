# LRH Console visual language proposal set

This proposal set records the proposed visual language for LRH Console and `lrh serve`. It started
from Alternative D, the Enhanced Swimlane Console. Revision 2 (2026-10-07) extends it to the app
frame, the banded statusboard, and the L1 dependency map, and records the owner's design-language
decisions.

## Status

`proposed` / `not_started`

This is a documentation-only design proposal. It does not implement UI, CSS, server routes,
templates, frontend dependencies, or mutating dashboard behavior.

## Documents

1. [`00_proposal.md`](00_proposal.md)
   — umbrella proposal covering scope, motivation, visual direction, conceptual model, information
   architecture, UI patterns, semantic status vocabulary, theme tokens, accessibility, safe-default
   constraints, UX review criteria, the first implemented `lrh serve` review checklist,
   implementation guidance, open questions, mockup assets, and the Revision 2 decisions.

## Reading order

1. `README.md` (this file)
2. `00_proposal.md`
3. `assets/README.md`

## Canonical-document touchpoints

If adopted later, this proposal would likely inform future updates to:

- `project/design/design.md`
- `project/design/architecture.md`
- `project/design/meta_control_plane_mvp_spec.md`
- future `lrh serve` dashboard implementation documentation
