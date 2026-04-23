---
resolution: null
blocked_reason: null
blocked: false
id: WI-VALIDATOR-YAML-PARSER
title: Replace bootstrap YAML parser with production-grade parser
type: investigation
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-CONTROL-PLANE-SEMANTICS
depends_on: []
blocked_by: []
---

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
