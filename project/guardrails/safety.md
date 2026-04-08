---
id: GUARDRAIL-SAFETY
title: Safety Guardrails
status: active
owner: human_agent
---

# Safety Guardrails

## Initial rules

- Block actions that can irreversibly delete repository history or project control records.
- Require explicit human approval for actions with production-side effects.
- Prefer reversible, auditable actions when multiple options exist.
