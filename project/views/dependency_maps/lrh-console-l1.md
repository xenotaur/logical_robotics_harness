---
id: "lrh-console-l1"
title: "LRH Console local dogfood"
lanes:
- workstream: "WS-LRH-CONSOLE-LOCAL-DOGFOOD"
  title: "LRH Console local dogfood"
phases:
- id: "l0"
  title: "L0 desktop shell"
  work_items:
  - "WI-LRH-CONSOLE-DESKTOP-PROTOCOL"
  - "WI-LRH-CONSOLE-DESKTOP-L0"
  - "WI-LRH-CONSOLE-DESKTOP-SUPERVISOR"
  - "WI-LRH-CONSOLE-DESKTOP-SHELL"
  - "WI-LRH-CONSOLE-DESKTOP-SETTINGS"
  - "WI-LRH-CONSOLE-DESKTOP-DOGFOOD"
  - "WI-SERVE-QUIET-CLIENT-DISCONNECT"
  - "WI-LRH-CONSOLE-DESKTOP-SHELL-POLISH"
  - "WI-LRH-CONSOLE-DESKTOP-SETTINGS-POLISH"
- id: "foundation"
  title: "L1 foundation"
  work_items:
  - "WI-LRH-CONSOLE-TOKENS"
  - "WI-LRH-CONSOLE-THEME"
  - "WI-LRH-CONSOLE-FRAME"
- id: "map"
  title: "L1 dependency map"
  work_items:
  - "WI-LRH-CONSOLE-MAP-SNAPSHOT"
  - "WI-LRH-CONSOLE-MAP-STATIC"
  - "WI-LRH-CONSOLE-INTERACTIVE"
  - "WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT"
  - "WI-LRH-CONSOLE-STATUS-SHAPES"
- id: "statusboard"
  title: "L1 statusboard"
  work_items:
  - "WI-LRH-CONSOLE-STATUSBOARD"
- id: "evaluation"
  title: "L1 evaluation"
  work_items:
  - "WI-LRH-CONSOLE-L1-DOGFOOD"
---

# LRH Console local dogfood

This dependency-map view shows the work items of `WS-LRH-CONSOLE-LOCAL-DOGFOOD`. It
has one lane, the workstream itself, and phase rows that follow the L0 and L1 plans.
Phases are organizational rows, not gates. Dependencies come only from each work
item's own `depends_on` and `blocked_by` fields.
