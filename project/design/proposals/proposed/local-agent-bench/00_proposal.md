---
id: "PROP-LOCAL-AGENT-BENCH"
type: "design_proposal"
title: "Local-agent bench: T1 toys with a browser UI and follow-up chat"
status: "proposed"
created_on: "2026-10-12"
updated_on: "2026-10-12"
implementation_status: "not_started"
implemented_by: []
supersedes: []
superseded_by: null
related_design:
  - "project/design/proposals/proposed/local-agent-dogfood/00_proposal.md"
  - "project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md"
  - "docs/reference/desktop-server-protocol.md"
---

# Local-agent bench: T1 toys with a browser UI and follow-up chat

## Summary

Give the owner a small local web UI, the **local-agent bench**, to run the T1
`brief` toy on a work item and ask follow-up questions about the same sources.
It runs as a separate, experimental loopback server with its own authentication,
not as routes in `lrh serve`, and keeps T1's authority unchanged: no tools, no
repository writes, local inference only. LRH Console work-item pages link to it.
This proposal is design only. Implementation waits for the owner's next
proceed/revise/stop decision on `WI-LOCAL-AGENT-001`, because the bench builds
on the toys that item is evaluating.

## Background / Motivation

The owner wants LRH Console to become a project browser that can (a) show the
planning tree, (b) run the local-model toys on a work item, and (c) support
follow-up chat, on a local model first and a pluggable backend later. Part (a)
fits the console's read-only charter and is captured as
`WI-LRH-CONSOLE-WORK-ITEM-BROWSER`. Parts (b) and (c) need a surface that can
start model calls, which the console deliberately cannot:

- `lrh serve` is read-only. Mutating methods return 405
  (`src/lrh/serve.py:4030-4043`), and `_safe_capabilities` reports
  `agent_dispatch: False` and `external_network_calls: False`
  (`serve.py:2845-2861`).
- It has no HTTP authentication and does not check the Host header
  (`docs/reference/desktop-server-protocol.md:334-345`), and standalone it uses a
  fixed port, 8765 (`serve.py:38`).
- The console proposal requires "a separate authorization/CSRF design" for any
  mutation interface (`lrh-console-local-dogfood/00_proposal.md:222-223`) and
  forbids secret tokens in URLs (`:218`).
- `experimental/` code must not be imported into `src/lrh/`
  (`experimental/README.md:11`).

On the toy side, the local-agent proposal names a T6 "Local workbench", says "a
local web workbench can precede a Mac app wrapper", and requires fresh design
review for later toys (`local-agent-dogfood/00_proposal.md:119,127-129`). The
bench is narrower than T6: T1's read-only authority with a UI and multi-turn
follow-ups, not T6's session, permission, and approval management.

Follow-up chat is cheap enough to be worth having. The toys' prompts put the
sources before the question (`ask_v2`, `brief_v2`), so later turns reuse
Ollama's prefix cache. A 2026-10-11 timing check measured about 130 s for a cold
call against 1-3 s for follow-ups (a 17.7k-token prompt, with the model kept
loaded).

## Prior Art Check

### Duplication search
- In-repo: No bench, chat, or authenticated local UI exists. Related: serve's
  `/workbench` (prompt/packet/report previews, no model calls), and the
  `experimental/local_agent/` CLI (`ask`, `brief`, single-prompt, with
  `run_ask` at `ask.py:368` and `run_brief` at `brief.py:174`).
- Sibling repos: None identified.
- External libraries: Open WebUI provides chat over Ollama, but it would bypass
  the T1 adapter's local-only checks (pinned model digest, loopback endpoint, no
  proxies or cloud models), LRH's tracked-file source packing and exclusions,
  and the private run records. Jupyter Server is prior art for the auth model,
  not a component.
- Recommendation: Proceed with a small purpose-built server that reuses the
  toys' modules.

### Demand search
- Work items: `WI-LRH-CONSOLE-WORK-ITEM-BROWSER` (proposed) provides the page the
  bench is linked from. `WI-LRH-CONSOLE-DEEPLINK-HANDOFF` (proposed) is a
  complementary handoff to vendor agent apps, not a substitute.
- Proposals: `PROP-LOCAL-AGENT-DOGFOOD` T6 "Local workbench" (a broader rung;
  this proposal covers a narrower T1-authority slice of it).
- Backlog: No matching entries.
- Recommendation: No action; cross-reference both.

## Design Decisions

### 1. A separate experimental server, not routes in `lrh serve` or Tauri IPC

| Option | Verdict |
|---|---|
| Action routes in `lrh serve` | Rejected. Without authentication or a Host check, any web page could use CSRF or DNS rebinding to make it send repository content to a model. It also breaks the console's read-only charter and the no-import rule. |
| Actions over Tauri IPC to the supervisor's stdio pipe | Rejected for now. The channel can't be forged, but it works only in the app, its control messages are capped at 64 KiB and don't stream, each action needs Rust plumbing, and it loosens the pinned main-window `permissions: []` boundary (`apps/desktop/src-tauri/tests/capability_boundaries_test.rs`). |
| Separate loopback server | **Chosen.** All existing console boundaries stay as they are. It follows the local-agent proposal's "local web workbench" path, and its authority stays in experimental code. |

The bench lives in a new sibling directory, `experimental/local_bench/`. It
imports `experimental/local_agent/` modules and never edits them. It is named
"bench" because serve already owns `/workbench`.

### 2. Local-only authentication: Host allowlist, a secret pasted once, a same-site cookie

- **Bind and Host:** bind `127.0.0.1` on an ephemeral port by default. Reject
  any request whose `Host` header is not `127.0.0.1:<port>` or
  `localhost:<port>` with 403. This defends against DNS rebinding; the 2018
  Transmission RPC flaw (CVE-2018-5702) is the canonical loopback example.
- **Secret delivery:** generate a per-launch random secret and print it only on
  the bench's terminal. The browser pastes it once into a form, and the bench
  answers by setting an `HttpOnly; SameSite=Strict; Path=/` session cookie. The
  secret never appears in a URL, server log, or record. That honors the console
  rule and rules out Jupyter's `?token=` links.
- **Request checks:** every POST requires the cookie, `Sec-Fetch-Site:
  same-origin` (W3C Fetch Metadata), and an `Origin` that matches the bench
  origin. These are the layered defenses recommended in OWASP's CSRF Prevention
  Cheat Sheet. GET routes have no side effects.
- **Page policy:** strict CSP (`default-src 'self'`, no inline script),
  `X-Frame-Options: DENY`, no CORS headers.

### 3. T1 authority, unchanged

Each model call keeps the toys' boundaries: tracked files read at a pinned
commit, the toys' exclusions and sensitivity handling, the toys' egress checks
(loopback endpoint, no proxies or redirects, pinned local model digest, refusal
of remote or cloud-tagged models), no tools, no repository or project writes, and
`think: false`. The bench adds UI and turn management, not capabilities.

### 4. Sessions with sources frozen at a commit; follow-ups append

- `POST /wi/<ID>/brief` starts a session. It builds the source block once from
  the commit at session start, runs `brief`, and returns a session id.
- `POST /s/<sid>/ask` appends a turn. The prompt is the same system text and
  source block, then the prior turns, then the new question. That keeps the
  prefix byte-stable for the cache and needs no change to `ModelAdapter`, whose
  `ModelRequest` takes one prompt string (`model.py:40-50`).
- If the checkout moves, the page says the sources are stale and offers "Start a
  new session". It never refreshes sources silently inside a session.
- Per-session token budgets come from the toys' `settings.Budgets`. When the
  next turn would exceed the context budget, the bench says so and stops; it
  does not truncate silently.

### 5. Separate records so the WI-LOCAL-AGENT-001 evidence stays clean

Bench sessions are written to their own private store
(`~/.local/share/lrh/local-bench/` by default, outside Git), with the same
record shape, recovery, and pruning, but never into the T0/T1 store whose logs
inform the `WI-LOCAL-AGENT-001` decision. Records mark each turn's role and
prompt version (for example `bench_chat_v1`).

### 6. Console integration adds no authority

When a bench URL is configured, work-item pages from
`WI-LRH-CONSOLE-WORK-ITEM-BROWSER` show an "Open in local-agent bench" link to
`/wi/<ID>`, which carries no secret. In LRH Console the main window hands this
cross-origin link to Chrome (`apps/desktop/src-tauri/src/shell.rs:895-925`), so
the bench runs in a browser tab. `_safe_capabilities` and the desktop capability
files do not change.

## Non-Goals

- Do not modify `experimental/local_agent/`, `WI-LOCAL-AGENT-001`,
  `WS-LOCAL-AGENT-DOGFOOD`, or `PROP-LOCAL-AGENT-DOGFOOD`.
- Do not add tools, file reads beyond the toys' source packing, patches,
  repository writes, or command execution (T2+ authority).
- Do not add cloud or vendor backends. A backend registry and cloud adapters need
  their own design with a stricter egress policy: no medium-sensitivity
  findings, explicit opt-in per provider, and key handling. Vendor agent apps are
  agents, not completion endpoints; `WI-LRH-CONSOLE-DEEPLINK-HANDOFF` covers
  handing off to them.
- Do not have the desktop app supervise, embed, or authenticate the bench.
- Do not add routes, capabilities, or imports of `experimental/` to `lrh serve`
  or `src/lrh/`.
- Do not provide remote, multi-user, or public access.

## Implementation Plan

Design only until the gate below is met. After that, roughly one or two PRs, so
a single work item under `WS-LOCAL-AGENT-DOGFOOD` or a new small workstream,
chosen at that point.

| Step | Deliverable | Gate |
|---|---|---|
| 0 | This proposal reviewed. | Owner review of this PR. |
| 1 | `WI-LRH-CONSOLE-WORK-ITEM-BROWSER` landed (the link anchor). | Its own acceptance criteria. |
| 2 | Bench work item: server, auth, `brief` + follow-up sessions, separate store, tests (Host/Origin/Fetch-Metadata/cookie rejection, no-secret-in-URL or logs, egress checks still run every call, stale-source detection). | The owner's next proceed decision on `WI-LOCAL-AGENT-001`, and an explicit owner go-ahead for the bench. |
| 3 | Console link (config-gated) from the work-item browser. | Step 2 used on real work items. |
| Later | Backend registry and cloud adapters; desktop supervision. | Separate proposals. |

## Open Questions

- Should the bench also run T0 `ask` on free questions, or only `brief`-rooted
  sessions on a work item?
- How should the console learn the bench URL: a serve flag, Meta settings, or a
  fixed documented default port?
- Does a follow-up turn get rated with the same one-key rating as toy runs, and
  should bench ratings feed any later toy decision?
- Context budget: cap total turns, or summarize earlier turns? The current answer
  is to stop and start a new session; revisit with usage evidence.

## Cross-References

- `project/design/proposals/proposed/local-agent-dogfood/00_proposal.md` (toy ladder, T6, Decision 3 egress)
- `project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md` (read-only charter, CSRF requirement, no secrets in URLs)
- `project/work_items/proposed/WI-LRH-CONSOLE-WORK-ITEM-BROWSER.md`
- `project/work_items/proposed/WI-LRH-CONSOLE-DEEPLINK-HANDOFF.md`
- `docs/reference/desktop-server-protocol.md` (no HTTP auth, no Host check)
- `experimental/local_agent/README.md` (Boundaries)
- External: OWASP CSRF Prevention Cheat Sheet; W3C Fetch Metadata Request Headers; CVE-2018-5702 (Transmission DNS rebinding); Jupyter Server security documentation.
