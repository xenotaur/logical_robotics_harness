# LRH UX Support

This package contains typed semantic contracts for future `lrh serve` and meta-dashboard views. It is intentionally a support layer, not a frontend implementation.

The initial dashboard support is grounded in the proposed LRH Console visual language at `project/design/proposals/proposed/lrh-console-visual-language/`, especially the Alternative D enhanced swimlane console concept. It provides:

- an operational dashboard status vocabulary distinct from work-item lifecycle status;
- deterministic status badges and lane ordering;
- typed meta-dashboard, lane, project, validation, evidence, capability-gap, and operational-card view models;
- meta-project operational cards that carry actionable validation diagnostics and next-action guidance when validation status is `error`;
- conservative status derivation helpers that return `unknown` when available data is insufficient.

The `/meta` route in `lrh serve` now consumes these view models for its safe-default, read-only registered-project swimlane dashboard without introducing a frontend framework, mutating UI actions, or hard-coded LRH-repository fixture data.
For source-state resolution, `lrh serve` consumes shared resolved local meta state and does not fetch or inspect remote repository URLs in this MVP.
