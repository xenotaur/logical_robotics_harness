---
resolution: "Superseded by PROP-LRH-FRONTMATTER-PARSER (WS-LRH-FRONTMATTER-PARSER), which subsumes and substantially extends this work item's scope: parser consolidation across both control/parser.py and control/validator.py (this WI covered only validator.py), plus a content-safety migration tool, lint guard, and authoring guidance the original WI did not anticipate."
blocked_reason: null
blocked: false
id: WI-VALIDATOR-YAML-PARSER
title: Replace bootstrap YAML parser with production-grade parser
type: investigation
status: abandoned
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-CONTROL-PLANE-SEMANTICS
depends_on: []
blocked_by: []
---

## Superseded

Superseded by [`PROP-LRH-FRONTMATTER-PARSER`](../../design/proposals/proposed/lrh-frontmatter-parser/00_proposal.md)
and its governing workstream [`WS-LRH-FRONTMATTER-PARSER`](../../workstreams/proposed/WS-LRH-FRONTMATTER-PARSER.md).
That proposal was produced by a fuller investigation that found this WI's
premise correct but its scope too narrow: the actually-reported parser bug
lives in `control/parser.py`, not `validator.py` alone, and a naive swap
to a production-grade parser would silently mishandle real existing
content in ways this WI did not anticipate. See the proposal's Design
Decisions for the resolution.

## Summary

The current validator uses a custom `_parse_simple_yaml` implementation. This was intentionally created to avoid introducing dependencies during bootstrap, but it is not robust enough for long-term use.

This work item evaluates and replaces the parser with a production-grade YAML/frontmatter solution.

## Goals

- Ensure correct parsing of valid YAML frontmatter
- Support common YAML features (quoting, lists, multiline, etc.)
- Reduce risk of silent misinterpretation of metadata

## Proposed Actions

- Evaluate options:
  - PyYAML
  - ruamel.yaml
  - frontmatter-specific libraries
- Select minimal-dependency, stable solution
- Replace `_parse_simple_yaml` with selected parser
- Update validator tests if necessary

## Acceptance Criteria

- All existing validator tests pass
- Additional tests added for:
  - multiline values
  - quoted strings
  - inline comments
- Validator correctly parses realistic YAML frontmatter

## Notes

This is a follow-up to the initial bootstrap validator implementation.
