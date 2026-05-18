# LRH UX Support

This package contains typed semantic contracts for future `lrh serve` and meta-dashboard views. It is intentionally a support layer, not a frontend implementation.

The initial dashboard support is grounded in the proposed LRH Console visual language at `project/design/proposals/proposed/lrh-console-visual-language/`, especially the Alternative D enhanced swimlane console concept. It provides:

- an operational dashboard status vocabulary distinct from work-item lifecycle status;
- deterministic status badges and lane ordering;
- typed meta-dashboard, lane, project, validation, and evidence view models;
- conservative status derivation helpers that return `unknown` when available data is insufficient.

Future `lrh serve` work can adopt these view models when rendering meta/project dashboards without introducing a frontend framework, mutating UI actions, or hard-coded LRH-repository fixture data.
