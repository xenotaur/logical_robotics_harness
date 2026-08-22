# Project Setup Playbooks

Project setup playbooks capture reusable, human-facing setup and validation guidance that can be applied across LRH and downstream repositories without forcing every project into one template.

## Playbooks

- [CI setup and debugging](ci.md) — assess, repair, and harden continuous integration across heterogeneous repositories using canonical commands, reproducible tool versions, workflow guardrails, and evidence-backed debugging.
- [Claude Code permission allowlist](claude-code-permissions.md) — what the project-level `.claude/settings.json` pre-approves, what it deliberately still gates, and how to extend it.
- [PII and sensitive-content philosophy](pii.md) — decide whether and how to check a repository for PII or misplaced sensitive documents, why detection stays audit-only and opt-in, and how remediation differs from credential handling.
