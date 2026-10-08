---
id: "WI-LRH-CONSOLE-TOKENS"
title: "Add the shared LRH Console token file, style specimen, and contrast test"
type: "deliverable"
status: "resolved"
blocked: false
blocked_reason: null
resolution: 'Implemented and merged in PR #785 (commit e25bfe31). One --lrh- token file (src/lrh/ux/static/lrh-tokens.css) holds every color, space, radius, font-role, shadow, and motion token for light and dark; Serve inlines it and the desktop app bundles an identical copy, with a sync test. A read-only /style specimen follows the system theme while every existing Serve page stays light until WI-LRH-CONSOLE-THEME. Contrast tests cover every declared text, line, focus, status, and band pair in both themes; they moved the light edge color to #78849f (3.19:1 on the sunken surface). The Settings highlight and scroll honor reduced motion. color.plane tokens are deferred until a view needs them.'
owner: "anthony"
contributors:
- "anthony"
assigned_agents: []
parent_id: "WS-LRH-CONSOLE-LOCAL-DOGFOOD"
related_focus: []
related_roadmap: []
related_workstreams:
- "WS-LRH-CONSOLE-LOCAL-DOGFOOD"
related_design:
- "project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md"
- "project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md"
depends_on: []
blocked_by: []
expected_actions:
- "create_file"
- "edit_file"
- "run_tests"
- "create_pr"
forbidden_actions:
- "force_push"
- "delete_branch"
- "merge_pr"
- "publish_package"
- "deploy_remote_service"
acceptance:
- "One token file holds every color, space, radius, font-role, and motion token for both themes, using the `--lrh-` prefix."
- "Serve and the desktop app render from it, and a test fails if the desktop copy diverges from the source."
- "A contrast test checks every declared text pair at 4.5:1 or more and every line, icon, and focus pair at 3:1 or more, in both themes, and passes."
- "A read-only style specimen page renders every status and band token in the current theme."
- "Existing Serve and desktop pages look unchanged apart from token-driven colors, and the Settings flash honors reduced motion."
required_evidence:
- "test_output"
- "lrh_validate"
artifacts_expected:
- "src/lrh/ux/static/lrh-tokens.css"
- "src/lrh/serve.py"
- "apps/desktop/ui/lrh-tokens.css"
- "apps/desktop/ui/style.css"
- "tests/ (token sync and contrast tests)"
---

# LRH Console shared tokens

## Summary

Create the one shared CSS custom-properties file that every LRH Console surface reads, with light and dark values, a style specimen page, and an automated contrast test. This is the foundation the visual-language Revision 2 decisions build on (Q1, Q10, Q12).

## Problem / Context

Serve and the desktop app style themselves separately today. Serve inlines a small token block, `--lrh-color-*` with light values and an unused `[data-theme="dark"]` override, in `_base_styles` (`src/lrh/serve.py:2162`). The desktop app's bundled pages use hard-coded colors in `apps/desktop/ui/style.css`. The visual-language proposal (Revision 2, Tokens and Color vision) calls for one file, shared by both, with an Okabe–Ito-derived, colorblind-safe palette and contrast of at least 4.5:1 for text and 3:1 for lines, icons, and focus. The draft values are the `:root` block of `project/design/proposals/proposed/lrh-console-visual-language/assets/lrh-console-frame-mock.html`, whose contrast was computed in PR #781.

### Duplication search

In-repo: `_base_styles` in `src/lrh/serve.py` is the only token scaffold, and nothing generates or tests tokens. Recommendation: proceed, extending its `--lrh-` names.

## Scope

- One token file with light values on bare `:root`, dark values under `prefers-color-scheme: dark` guarded by `:root:not([data-theme='light'])`, and again under `:root[data-theme='dark']`.
- Serve inlines the file into its pages; the desktop app bundles an identical copy.
- A read-only style specimen route in Serve.
- An automated WCAG contrast test over declared token pairs in both themes.
- Migrating existing Serve and desktop styles to the tokens without changing behavior.

## Required Changes

1. Add the token file, for example `src/lrh/ux/static/lrh-tokens.css`, using the `--lrh-` prefix and the proposal's categories (`color.surface`, `color.text`, `color.border`, `color.focus`, `color.status`, `color.plane`, `color.action`, `space`, `radius`, `font`, `shadow`, `motion`). Seed the values from the mock's `:root` block.
2. Have Serve inline the file's contents into its existing `<style>` block. That keeps the current content security policy (`style-src 'unsafe-inline'`, `src/lrh/serve.py:3034-3036`) unchanged. This replaces Q10's 'Serve serves the file', because the policy has no `style-src 'self'`. Keep existing `--lrh-color-*` names working as aliases while classes migrate.
3. Copy the file into `apps/desktop/ui/` and link it from the bundled pages, replacing hard-coded colors in `apps/desktop/ui/style.css`. Add a test that fails if the two copies differ.
4. Add a read-only specimen route, for example `/style`. It shows surfaces, text, status pills for every structural state, bands, card states, focus rings, and line styles in the active theme.
5. Add a Python contrast test. It parses the token file and checks every declared pair in both themes: text against its background at 4.5:1 or more, and lines, icons, and focus against their surfaces at 3:1 or more, including the sunken surface.
6. Make the Settings `.flash` highlight honor `prefers-reduced-motion` (`apps/desktop/ui/style.css`).

## Non-Goals

- No theme switching or `--theme` flag (`WI-LRH-CONSOLE-THEME`).
- No app frame, fonts, or icons (`WI-LRH-CONSOLE-FRAME`).
- No new pages beyond the specimen.

## Acceptance Criteria

- One token file holds every color, space, radius, font-role, and motion token for both themes, using the `--lrh-` prefix.
- Serve and the desktop app render from it, and a test fails if the desktop copy diverges from the source.
- A contrast test checks every declared text pair at 4.5:1 or more and every line, icon, and focus pair at 3:1 or more, in both themes, and passes.
- A read-only style specimen page renders every status and band token in the current theme.
- Existing Serve and desktop pages look unchanged apart from token-driven colors, and the Settings flash honors reduced motion.

## Validation

- `scripts/format --check --diff --desktop`
- `scripts/lint --desktop`
- `scripts/test --desktop`
- `lrh validate`
- Open the specimen page with the macOS appearance set to light and to dark.

## Dependencies / Order

- No dependencies. It can run in parallel with `WI-LRH-CONSOLE-MAP-SNAPSHOT`.
- `WI-LRH-CONSOLE-THEME`, `WI-LRH-CONSOLE-FRAME`, and everything visual depend on it.

## Risk Notes

- Renaming tokens can silently break existing classes. Keep aliases and compare the rendered pages before and after.
- The PR #781 review measured light lines against the sunken surface at only 3.01–3.10:1. The contrast test must include that surface, so later edits cannot regress it.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md` (Revision 2 decisions)
- `project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md`
