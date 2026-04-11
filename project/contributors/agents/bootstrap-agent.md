---
id: bootstrap-agent
type: agent
roles:
  - editor
status: inactive
execution_mode: human_orchestrated
description: >
  AI-assisted programming conducted through a human operator rather than
  autonomously by the LRH harness.
tools:
  - codex-cloud
  - github-actions
  - request-generation
---
# Bootstrap Agent

The bootstrap agent represents AI-assisted programming orchestrated by a human
user without autonomous scheduling or delegation by LRH itself.

It may be assisted by LRH tools such as request generation, repository
inspection, or prompt scaffolding, but it does not currently operate as an
independent LRH-managed execution agent.

## Notes

- Human-triggered
- No persistent autonomous run loop
- Useful during LRH bootstrap before formal agent orchestration exists