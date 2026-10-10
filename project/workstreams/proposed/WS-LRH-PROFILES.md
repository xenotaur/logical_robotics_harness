---
id: "WS-LRH-PROFILES"
kind: "planning_node"
title: "LRH Profiles"
status: "proposed"
stage: "designed"
origin: "design_review"
parent_id: null
children: []
summary: "Implement named, isolated LRH profiles (Meta config/state/cache and LRH Console config) shared by the lrh CLI and LRH Console, per PROP-LRH-PROFILES."
related_focus: []
related_roadmap: []
related_design:
- "project/design/proposals/proposed/lrh-profiles/00_proposal.md"
- "project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md"
- "docs/how-to/lrh-console-local-dogfood.md"
work_items: []
execution_records: []
evidence: []
exit_criteria:
- "PROP-LRH-PROFILES is reviewed and merged (as proposed), with its remaining open questions (profiles root, spike results) resolved or recorded as evidence."
- "save_settings no longer writes the shared config.json while an LRH_CONSOLE_* override is active, with a regression test."
- "A profile resolver is used by resolve_meta_workspace, meta init, serve, and the assist template resolver, and the default profile resolves to today's paths unchanged."
- "LRH Console runs two profiles side by side with isolated app config and Meta, with webview-store isolation and the second-profile launch verified on macOS, or the limit recorded as evidence."
- "Docs explain profiles and disambiguate them from bootstrap, chain-defaults, and assistant profiles."
---

# LRH Profiles

## Purpose

Coordinate delivery of PROP-LRH-PROFILES: Chrome-style named profiles that give
a user several isolated LRH setups, and give developers a fresh profile with a
new Meta directory for testing a new installation. It spans the `lrh` CLI
resolver and the LRH Console app, so the work needs sequencing across both.

## Scope

- Fix the Console Save hazard in env-override mode, independently and first.
- A shared `lrh.meta.profiles` resolver, wired into Meta resolution, `meta init`,
  `serve`, and assist templates; `default` stays today's layout. Non-default
  profiles are self-contained, relocatable directories, global mode only.
- Console per-profile app config, child environment, window title, webview
  store, and second-profile launch.
- User documentation and naming disambiguation.

## Prior Art Check

### Duplication search
- In-repo: No existing implementation found. Related: PROP-LRH-PROFILES,
  WS-LRH-CONSOLE-LOCAL-DOGFOOD (owns the Console settings work this builds on).
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed

### Demand search
- Work items: None found.
- Proposals: PROP-LRH-PROFILES is the governing proposal (PR #814, not yet merged).
- Backlog: No matching entries.
- Recommendation: No action

## Work Items

No work items exist yet; they will be created now that the proposal's main
design questions are settled (see PROP-LRH-PROFILES, "Decisions Recorded"). The
stage moves from `designed` to `planned` once they exist. Planned, in proposed
order:

1. Fix `save_settings` in env-override mode (standalone; ships first).
2. `lrh.meta.profiles` resolver plus tests.
3. Wire the resolver into Meta resolution, `meta init`, `serve`, assist templates,
   help text, and release-smoke sanitising.
4. Console: a short macOS spike (webview-store isolation, `open -n`), then
   per-profile app config dir, child `LRH_PROFILE` and `LRH_CONFIG`,
   window title, webview `data_store_identifier`, second-profile launch.
5. Docs: how-to and naming disambiguation.

## Exit Criteria

- PROP-LRH-PROFILES is reviewed and merged (as proposed), with its remaining
  open questions (profiles root, spike results) resolved or recorded as evidence.
- `save_settings` no longer writes the shared `config.json` during an
  `LRH_CONSOLE_*` override, with a regression test.
- The resolver is used by `resolve_meta_workspace`, `meta init`, `serve`, and the
  assist template resolver; `default` resolves to today's paths unchanged.
- Two Console profiles run side by side with isolated app config and Meta;
  webview-store isolation and `open -n` launch are verified on macOS, or the
  limit is recorded as evidence.
- Docs explain profiles and disambiguate the other "profile" meanings.

## Non-Goals

- Does not change bootstrap, chain-defaults, or assistant "profile" behavior.
- Does not add a persisted active profile, in-app profile picker, or
  `lrh profile list/create/use` in v1.
- Does not migrate existing configuration, add `--from`/save/load commands, or
  support `hybrid`/`local` profile modes in v1 (the latter is a backlog item).
- Does not move work out of WS-LRH-CONSOLE-LOCAL-DOGFOOD; the two are related, not nested.
