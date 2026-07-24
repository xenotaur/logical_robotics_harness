# Reference — Reporting Format

Loaded on demand. How the Serve Interface Steward renders semantic messages for
its human supervisor.

A message carries an `intent` (inform / request / direct / respond /
acknowledge), a `topic` (progress / completion / blocker / decision / scope /
risk / review / handoff / control), an `urgency` (routine / elevated / urgent /
critical), and a structured payload. The same semantic message is rendered
differently per audience via a profile.

Common assistant-to-human combinations:

| Human label | Intent | Topic |
|---|---|---|
| Status update | inform | progress |
| Completion candidate | inform | completion |
| Blocked and need help | request | blocker |
| Decision request | request | decision |
| Risk alert | inform/request | risk |
| Handoff | inform | handoff |

Default renderers for this role: status → `standard_markdown`; alerts →
`compact_chat`; decision requests → `detailed_report`.

A completion message is rendered as a **candidate pending verification**, never
as a resolution. Acknowledgment is rendered distinctly from approval.
