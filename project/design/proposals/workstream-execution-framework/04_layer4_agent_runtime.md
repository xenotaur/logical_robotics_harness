---
id: PROP-WORKSTREAM-LAYER4-RUNTIME
title: Layer 4 — Agent Runtime
status: proposed
type: design_proposal
created_on: 2026-04-26
updated_on: 2026-04-26
parent: PROP-WORKSTREAM-EXECUTION-FRAMEWORK
---

# Layer 4 — Agent Runtime

## Summary

This sub-proposal specifies the **agent runtime** layer: the narrow
`RuntimeBackend` Protocol that Layer 3's orchestrator calls to
actually run a prompt, plus three concrete implementations
(`claude_backend` wrapping the Claude Agent SDK, `manual_backend` for
human-as-runtime, and `fake_backend` for tests). The Protocol's job
is to make manual mode and agent mode genuinely interchangeable from
the orchestrator's perspective — same input shape (`RuntimeRequest`),
same output shape (`RuntimeResult`), same set of `Outcome` values,
same hook contract. That interchangeability is what makes manual-mode
parity an enforceable invariant rather than a pious wish.

The deliverable boundary for Layer 4 is: after this layer ships,
Layer 3 can call `runtime.execute(request)` and get back a typed
`RuntimeResult` regardless of whether the work was done by an agent
or a human, including a transcript on disk, a cost figure, an outcome
enum, and a list of tool calls. Hooks, permission modes, and budget
enforcement are wired through the Protocol. The Claude backend uses
`anthropics/claude-agent-sdk-python` ([cas][cas]), preserving its
hooks, permission modes, structured outputs, and W3C trace context
propagation rather than reinventing any of it.

## Table of contents

1. [Goals and non-goals](#1-goals-and-non-goals)
2. [Why a Protocol with three backends](#2-why-a-protocol-with-three-backends)
3. [Module layout](#3-module-layout)
4. [The RuntimeBackend Protocol](#4-the-runtimebackend-protocol)
5. [RuntimeRequest and RuntimeResult dataclasses](#5-runtimerequest-and-runtimeresult-dataclasses)
6. [The Outcome enum](#6-the-outcome-enum)
7. [Hooks](#7-hooks)
8. [Permission modes](#8-permission-modes)
9. [Budget enforcement](#9-budget-enforcement)
10. [The three backends](#10-the-three-backends)
11. [Async/sync boundary](#11-asyncsync-boundary)
12. [Worked examples](#12-worked-examples)
13. [Tests](#13-tests)
14. [Risks](#14-risks)
15. [References](#15-references)

## 1. Goals and non-goals

### Summary

Layer 4 is a thin adapter layer. The Claude Agent SDK ([cas][cas])
already does the hard work of running an agent loop — tool
allowlisting, hooks, permission gating, structured outputs, trace
context. Layer 4's job is to wrap the SDK in a Protocol that the
orchestrator can call, plus implement two non-SDK backends so the
orchestrator never has to know which one it's calling.

### Goals

A frozen `RuntimeBackend` Protocol whose semantics are stable across
Claude SDK upgrades. Frozen `RuntimeRequest` and `RuntimeResult`
dataclasses. A single `Outcome` enum with values rich enough that the
orchestrator can branch on outcomes without inspecting strings. Hook
wiring (PreToolUse, PostToolUse, PostToolUseFailure, Stop) plumbed
through to the Claude backend. Per-call and per-workstream budget
caps. A symmetric `ManualBackend` that returns the same shapes as
the agent backend so the orchestrator can't tell. A `FakeBackend`
suitable for tests.

### Non-goals

We do not reimplement agent loops, tool dispatch, or LLM API calls —
the Claude Agent SDK handles those. We do not add a custom
permission system on top of the SDK's; we map our three modes
(`ask`, `accept_edits`, `strict`) onto the SDK's permission modes
and let the SDK enforce. We do not design for non-Claude backends
(future work). We do not orchestrate multiple prompts in parallel —
the runtime is per-call.

## 2. Why a Protocol with three backends

### Summary

The Protocol is what makes Invariant A (manual-mode parity) testable.
This section names the alternatives we considered and why the chosen
shape lands here.

### Alternative A: agent-only

Have the orchestrator call the SDK directly. This is fastest to
build but breaks parity: there's no way to drive a manual stage
through the same code path. We'd end up with two orchestrator paths,
one for agents and one for humans, with no structural guarantee
they stay in sync.

### Alternative B: stringly-typed runtime

Define a runtime by its inputs and outputs as JSON, with no Python
Protocol. This works in principle but loses the type safety LRH
wants (per AGENTS.md "Source vs runtime model"). It also makes the
orchestrator's pattern-matching on `Outcome` fragile.

### Alternative C: full driver model

Define a runtime as a class with a dozen methods covering every
phase of a prompt's life. Over-engineered: most backends would have
empty implementations.

### Chosen: thin Protocol with `execute()`

A `RuntimeBackend` Protocol with a single primary method,
`execute(request: RuntimeRequest) -> RuntimeResult`, plus a small
set of capability-discovery methods (`name()`, `supports_hooks()`,
`supports_mcp_servers()`). The Protocol is small enough that
implementing a new backend is a couple-hundred-line job and large
enough to carry all the information the orchestrator needs.

## 3. Module layout

### Summary

All Layer 4 code lives under `src/lrh/runtime/`.

### Modules

```text
src/lrh/runtime/
  __init__.py
  api.py              # RuntimeBackend Protocol; type re-exports
  models.py           # RuntimeRequest, RuntimeResult, Outcome,
                      # ToolCall, RuntimeContext
  hooks.py            # HookRegistry; PreToolUse/PostToolUse/Stop
                      # default implementations
  permissions.py      # permission-mode mapping
  budget.py           # per-call + per-workstream cumulative tracking
  transcript.py       # transcript file format and writer
  claude_backend.py   # ClaudeBackend(RuntimeBackend) wrapping the SDK
  manual_backend.py   # ManualBackend(RuntimeBackend) for human-as-runtime
  fake_backend.py     # FakeBackend(RuntimeBackend) for tests
```

Tests:

```text
tests/runtime_tests/
  __init__.py
  api_test.py
  models_test.py
  hooks_test.py
  permissions_test.py
  budget_test.py
  transcript_test.py
  claude_backend_test.py        # uses recorded fixtures, no real API
  manual_backend_test.py
  fake_backend_test.py
  protocol_parity_test.py       # all three backends honor the contract
```

## 4. The RuntimeBackend Protocol

### Summary

The Protocol is small and stable. New backends implement these
methods and nothing else.

### The Protocol

```python
# src/lrh/runtime/api.py
from typing import Protocol

from lrh.runtime import models


class RuntimeBackend(Protocol):
    """A runtime that can execute a prompt and return a typed result.

    Implementations must be drop-in interchangeable from the
    orchestrator's perspective. The shape of RuntimeResult, the
    Outcome enum, and the hook contract are stable across backends.
    """

    def name(self) -> str:
        """Stable identifier, e.g. 'claude_agent_sdk', 'manual', 'fake'."""

    def supports_hooks(self) -> bool:
        """Whether this backend honors the PreToolUse/PostToolUse/Stop
        hook contract."""

    def supports_mcp_servers(self) -> bool:
        """Whether this backend can attach MCP servers per request."""

    def execute(
        self,
        request: models.RuntimeRequest,
    ) -> models.RuntimeResult:
        """Execute one prompt and return a typed result.

        The call is synchronous from the caller's perspective.
        Async-only backends (the Claude SDK) wrap their async
        implementation in `asyncio.run()`.

        Implementations must:
          1. Honor request.allowed_tools.
          2. Apply request.permission_mode.
          3. Track cost against request.max_budget_usd; if exceeded
             mid-run, abort and return Outcome.BUDGET_EXHAUSTED.
          4. Honor request.timeout_seconds; if exceeded, return
             Outcome.TIMEOUT.
          5. Record a transcript at request.transcript_path.
          6. Return a RuntimeResult populated with whatever happened,
             even on failure.
        """
```

## 5. RuntimeRequest and RuntimeResult dataclasses

### Summary

Frozen dataclasses everywhere. Inputs are immutable; outputs are a
faithful record of what happened.

### `RuntimeRequest`

```python
# src/lrh/runtime/models.py
from dataclasses import dataclass, field
from pathlib import Path
import enum


@dataclass(frozen=True)
class RuntimeRequest:
    prompt_id: str                       # PROMPT-XXX-... id
    workstream_id: str                   # WS-... id
    prompt: str                          # the actual prompt text
    cwd: Path                            # working directory for tools
    allowed_tools: tuple[str, ...]       # ("Read", "Write", ...)
    permission_mode: PermissionMode
    mcp_servers: tuple[str, ...] = ()    # registered MCP server names
    max_turns: int = 10
    max_budget_usd: float = 2.00
    timeout_seconds: int = 600
    transcript_path: Path = ...          # where to write transcript
    structured_output_schema: dict | None = None
    trace_parent: str | None = None      # W3C traceparent for context propagation
    invoker: str = "anthony"             # contributor id
    extras: dict = field(default_factory=dict)  # backend-specific extras
```

### `RuntimeResult`

```python
@dataclass(frozen=True)
class ToolCall:
    name: str                            # "Read", "Write", "mcp__ros__publish"
    args: dict
    started_at: str                      # ISO-8601
    finished_at: str
    succeeded: bool
    error: str | None = None
    result_size_bytes: int | None = None


@dataclass(frozen=True)
class RuntimeResult:
    completed: bool
    outcome: Outcome
    backend_name: str
    workstream_id: str
    prompt_id: str
    tool_calls: tuple[ToolCall, ...]
    cost_usd: float
    input_tokens: int
    output_tokens: int
    turns_used: int
    duration_seconds: float
    transcript_path: Path
    structured_output: dict | None = None  # populated on schema-coerced runs
    final_message: str = ""
    trace_id: str | None = None            # OTel trace id if observer was active
    failure_detail: str | None = None      # populated when outcome != SUCCESS
```

The frozen choice is for safety: results are passed across module
boundaries (orchestrator, observer, evidence extractors) and we don't
want any of them mutating the record after the fact.

## 6. The Outcome enum

### Summary

Outcomes are richer than success/failure so the orchestrator can
branch on them without parsing failure strings.

### The enum

```python
class Outcome(enum.Enum):
    SUCCESS            = "success"
    BUDGET_EXHAUSTED   = "budget_exhausted"
    TURNS_EXHAUSTED    = "turns_exhausted"
    TIMEOUT            = "timeout"
    TOOL_DENIED        = "tool_denied"     # PreToolUse hook said no
    ERROR              = "error"           # backend-side exception
    ABORTED            = "aborted"         # caller cancelled (Ctrl-C)
    PENDING_HUMAN      = "pending_human"   # ManualBackend signal
```

### Outcome → orchestrator behavior

```text
Outcome             AdvanceResult outcome
---------------------------------------------
SUCCESS             ADVANCED  (or NOOP_IDEMPOTENT if already done)
BUDGET_EXHAUSTED    FAILED    (failure_reason: budget_exhausted ($X used))
TURNS_EXHAUSTED     FAILED    (failure_reason: turns_exhausted (N turns))
TIMEOUT             FAILED    (failure_reason: timeout (Ns))
TOOL_DENIED         FAILED    (failure_reason: tool_denied (Tool, reason))
ERROR               FAILED    (failure_reason: error: <detail>)
ABORTED             FAILED    (failure_reason: aborted)
PENDING_HUMAN       MANUAL_PROMPT_READY  (orchestrator stamps the prompt
                                          file and returns; no transition)
```

The orchestrator's branch table is small and total — every outcome
maps to exactly one advance-result outcome. This is the property
that makes Layer 3's tests tractable.

## 7. Hooks

### Summary

Hooks are how Layer 5b (evidence) gets fed without coupling Layer 4
to evidence semantics. The Claude SDK's hook system already supports
PreToolUse, PostToolUse, and Stop ([cas][cas]); we wire ours through.

### Hook surface

```python
# src/lrh/runtime/hooks.py
from typing import Protocol
from lrh.runtime import models


class PreToolUseHook(Protocol):
    """Called before a tool runs. Returning False blocks the tool
    (resulting in Outcome.TOOL_DENIED if the agent doesn't recover)."""

    def __call__(
        self,
        ctx: models.RuntimeContext,
        tool_name: str,
        tool_args: dict,
    ) -> bool:
        ...


class PostToolUseHook(Protocol):
    """Called after a successful tool run. Side-effects only."""

    def __call__(
        self,
        ctx: models.RuntimeContext,
        tool_name: str,
        tool_args: dict,
        tool_result: object,
    ) -> None:
        ...


class PostToolUseFailureHook(Protocol):
    """Called after a failed tool run."""

    def __call__(
        self,
        ctx: models.RuntimeContext,
        tool_name: str,
        tool_args: dict,
        error: Exception,
    ) -> None:
        ...


class StopHook(Protocol):
    """Called when the agent reaches a stop condition (success, budget
    exhausted, turns exhausted, etc.). Side-effects only."""

    def __call__(
        self,
        ctx: models.RuntimeContext,
        result: models.RuntimeResult,
    ) -> None:
        ...
```

### Default hook wiring

Layer 4 ships these default hooks, which are what most callers want:

`AllowlistPreToolUseHook` — enforces `request.allowed_tools` strictly,
returning False (blocking) when a tool not in the allowlist is
attempted. Defense-in-depth; the SDK already filters but this catches
backends that don't.

`InjectionScanPreToolUseHook` — runs a heuristic scan on tool inputs
for obvious prompt-injection patterns (e.g. "ignore previous
instructions" inside file contents read in by Read). Logs a warning
and continues; doesn't block. Future work could promote it to a
block.

`TranscriptPostToolUseHook` — appends a structured record of the tool
call to the transcript file. The transcript format is JSONL.

`EvidenceExtractionStopHook` — calls into Layer 5b's extractor
registry on stop, producing evidence records from the trace.

### Custom hooks

Callers pass a `HookRegistry` in `RuntimeRequest.extras["hooks"]`
or via a Layer-4-level configuration. Most callers won't customize.

## 8. Permission modes

### Summary

Three modes mapped onto the Claude SDK's permission system. Other
backends honor the same modes.

### The modes

```python
class PermissionMode(enum.Enum):
    ASK           = "ask"            # prompt user for every write/dangerous op
    ACCEPT_EDITS  = "accept_edits"   # allow writes within cwd silently
    STRICT        = "strict"         # only Read tools; writes denied
```

### Mode-to-SDK mapping

The Claude Agent SDK exposes a `permission_mode` parameter; we map
ours to its values per [the SDK's documentation][cas]. `ASK` maps
to the SDK's interactive permission flow; `ACCEPT_EDITS` maps to the
SDK's edit-acceptance mode; `STRICT` maps to a tool-allowlist that
contains only `Read`-class tools.

### Mode selection

Per-prompt mode is set in `prompts/PROMPT-XXX.md` frontmatter
(`permission_mode: strict`) and threaded through to the runtime
request. Mode defaults are mode-driven: agent-mode workstreams
default to `ACCEPT_EDITS` for executing-stage prompts; manual-mode
workstreams use `STRICT` (the manual backend ignores writes and
relies on the human to write artifacts).

### Strict-mode wins

If a workstream has `forbidden_actions: [production_write]` in its
prompt frontmatter, that translates to additional tool denials at the
hook level on top of the permission mode. Strict overrides
ACCEPT_EDITS — denials always win.

## 9. Budget enforcement

### Summary

Two budgets — per-call and per-workstream cumulative — enforced
during execution and recorded after.

### Per-call budget

`RuntimeRequest.max_budget_usd` is the cap for this single
`execute()` call. The Claude backend tracks cost incrementally
(input+output tokens at provider-published rates) and aborts when
the running total would exceed the cap. The result is
`Outcome.BUDGET_EXHAUSTED`. Cost figures come from `gen_ai.usage.*`
attributes per [OpenTelemetry GenAI semconv][otel-genai].

### Per-workstream cumulative budget

Cumulative budget is enforced by the orchestrator (Layer 3) before
calling `execute()`. Layer 4 reports `cost_usd` in the result; Layer
3 sums against the workstream's `budget.per_workstream_usd` and
refuses to start a new prompt that would push the cumulative over.
A workstream that would exceed cumulative budget gets `FAILED` with
`failure_reason: workstream_budget_exhausted` *before* the runtime
is even called.

### Per-prompt rate limits (future)

Future work: per-prompt rate limits (X calls per Y minutes) for cases
where a workstream might re-run a prompt repeatedly. Out of scope
for v1.

## 10. The three backends

### Summary

`ClaudeBackend` wraps the Claude Agent SDK; `ManualBackend` is a
human-as-runtime; `FakeBackend` is for tests. Each implements the
Protocol fully.

### `ClaudeBackend`

```python
# src/lrh/runtime/claude_backend.py
import asyncio

from claude_agent_sdk import ClaudeSDKClient, query
from lrh.runtime import api, models, hooks


class ClaudeBackend:
    """Runtime backend wrapping the Claude Agent SDK."""

    def name(self) -> str:
        return "claude_agent_sdk"

    def supports_hooks(self) -> bool:
        return True

    def supports_mcp_servers(self) -> bool:
        return True

    def execute(
        self,
        request: models.RuntimeRequest,
    ) -> models.RuntimeResult:
        return asyncio.run(self._execute_async(request))

    async def _execute_async(
        self,
        request: models.RuntimeRequest,
    ) -> models.RuntimeResult:
        # 1. Build SDK client with permission_mode, allowed_tools,
        #    mcp_servers, hooks wired.
        # 2. Iterate query() responses, accumulating cost and tool calls.
        # 3. On each tool use, fire PreToolUse hook (deny -> abort).
        # 4. On each tool result, fire PostToolUse hook.
        # 5. On stop, fire Stop hook.
        # 6. Compute Outcome from final state (SUCCESS, BUDGET_EXHAUSTED,
        #    TURNS_EXHAUSTED, TIMEOUT, ERROR).
        # 7. Return RuntimeResult.
        ...
```

The implementation depends on `claude_agent_sdk` (the SDK package).
Hook wiring follows the SDK's hook contract; permission mode maps to
the SDK's; `mcp_servers` are passed through to the SDK; W3C trace
context is propagated when the observer is active. Per the SDK's
documentation, all of this is supported in current versions
([cas][cas]).

### `ManualBackend`

```python
# src/lrh/runtime/manual_backend.py
class ManualBackend:
    """Runtime backend that signals the orchestrator to ask a human."""

    def name(self) -> str:
        return "manual"

    def supports_hooks(self) -> bool:
        return False  # manual mode bypasses tool hooks

    def supports_mcp_servers(self) -> bool:
        return False

    def execute(
        self,
        request: models.RuntimeRequest,
    ) -> models.RuntimeResult:
        # Stamp out a manual prompt file from the prompt template,
        # write it to disk, and return Outcome.PENDING_HUMAN. The
        # orchestrator handles the rest of the two-step flow.
        ...
```

The `ManualBackend` doesn't actually run tools or call models; it
signals the orchestrator to do the two-step manual-advance dance from
Layer 3. The result it returns has `cost_usd: 0.00`, `tool_calls:
()`, and `outcome: PENDING_HUMAN`. The orchestrator's mapping table
in §6 turns that into `MANUAL_PROMPT_READY`.

### `FakeBackend`

```python
# src/lrh/runtime/fake_backend.py
class FakeBackend:
    """Deterministic backend for tests. Returns canned responses."""

    def __init__(self, canned: dict[str, models.RuntimeResult]) -> None:
        self._canned = canned

    def name(self) -> str:
        return "fake"

    def supports_hooks(self) -> bool:
        return True

    def supports_mcp_servers(self) -> bool:
        return True

    def execute(
        self,
        request: models.RuntimeRequest,
    ) -> models.RuntimeResult:
        if request.prompt_id not in self._canned:
            raise KeyError(f"no canned result for {request.prompt_id}")
        return self._canned[request.prompt_id]
```

The fake backend is what every Layer 3 and Layer 5b test uses.
Determinism (per STYLE.md §"Determinism") demands it.

## 11. Async/sync boundary

### Summary

The Claude Agent SDK is async. The orchestrator is sync. The runtime
is the boundary.

### Why sync orchestrator

The orchestrator is invoked from `lrh workstream advance`, which is a
synchronous CLI command. Pushing async into the orchestrator would
make the CLI more complex and the test surface harder. Async is an
implementation detail of the Claude backend.

### How we bridge

Each Claude backend `execute()` call wraps its async implementation
in `asyncio.run()`. There's a per-`execute()` event loop. Hooks are
fired from within the loop; transcripts are written from within the
loop; the loop completes when the SDK's iterator is exhausted or a
budget/timeout is hit.

### Trade-offs

`asyncio.run()` per call has overhead (event loop creation/teardown).
For most workstream prompts (a few seconds to a few minutes of
agent time), this overhead is negligible. For high-frequency runs
(thousands of small prompts), we'd revisit and use a long-lived
event loop. Out of scope for v1.

## 12. Worked examples

### Summary

Three short examples covering the most common flows.

### Example A — Successful agent run

```python
from lrh.runtime import api, claude_backend, models

backend = claude_backend.ClaudeBackend()
request = models.RuntimeRequest(
    prompt_id="WS-LCATS-CORPORA-ANALYSIS:P-001",
    workstream_id="WS-LCATS-CORPORA-ANALYSIS",
    prompt="Read corpus/poe/tell-tale-heart.txt and write a "
           "corpus_issue_report evidence record for it...",
    cwd=pathlib.Path("/repo"),
    allowed_tools=("Read", "Write"),
    permission_mode=models.PermissionMode.ACCEPT_EDITS,
    max_budget_usd=2.00,
    transcript_path=pathlib.Path("project/runs/RUN-01J.../transcript.jsonl"),
)
result = backend.execute(request)
assert result.outcome == models.Outcome.SUCCESS
assert result.cost_usd <= 2.00
assert any(tc.name == "Write" for tc in result.tool_calls)
```

### Example B — Budget exhausted

Same setup, but the prompt is more expensive than the cap allows.

```python
result = backend.execute(request)
assert result.outcome == models.Outcome.BUDGET_EXHAUSTED
assert result.cost_usd >= 1.95   # tracked up to abort
assert result.failure_detail.startswith("budget_exhausted at $")
```

The orchestrator turns this into `AdvanceResult(FAILED,
failure_reason="budget_exhausted")` and appends a transition entry
with `from == to`.

### Example C — Manual mode is symmetric

```python
from lrh.runtime import manual_backend, models

backend = manual_backend.ManualBackend()
result = backend.execute(request)  # same RuntimeRequest shape
assert result.outcome == models.Outcome.PENDING_HUMAN
assert result.cost_usd == 0.00
assert result.tool_calls == ()
# orchestrator turns this into AdvanceResult(MANUAL_PROMPT_READY, ...)
```

The point: from the orchestrator's perspective, the two backends
return the same shape. The only branch is on `Outcome`. This is the
parity invariant in code form.

## 13. Tests

### Summary

Tests are layered: unit tests per module, a Protocol-parity test
across all three backends, and a smoke test against recorded
fixtures.

### Test plan

`api_test.py` — Protocol shape (uses `typing.runtime_checkable` to
verify implementations satisfy the Protocol).

`models_test.py` — dataclass invariants (frozen, JSON-serializable,
defaults).

`hooks_test.py` — hook firing order; PreToolUse denial leads to
`TOOL_DENIED`; PostToolUseFailure does not abort.

`permissions_test.py` — mode mapping; STRICT denies writes; per-prompt
`forbidden_actions` denials always win.

`budget_test.py` — per-call budget tracking and abort; per-workstream
budget pre-check.

`transcript_test.py` — JSONL transcript format; one record per tool
call plus a final stop record.

`claude_backend_test.py` — uses recorded SDK responses (saved JSONL
fixtures) to drive a deterministic test of the Claude backend
without making real API calls. Per STYLE.md §"Testing Principles,"
prefer real fixtures over heavy mocking.

`manual_backend_test.py` — verifies `Outcome.PENDING_HUMAN`, prompt
file stamping, zero cost.

`fake_backend_test.py` — verifies canned-response replay.

`protocol_parity_test.py` (load-bearing) — parametrized tests that
run the same `RuntimeRequest` through all three backends and assert
the result shapes match (modulo the expected differences:
`backend_name`, `outcome`, `cost_usd`, `tool_calls`).

### Recorded SDK fixtures

The Claude backend test uses recorded `claude_agent_sdk` responses
under `tests/runtime_tests/fixtures/sdk_recordings/`. We add a
maintainer-only `scripts/aiprog/record_sdk_fixture.py` (per AGENTS.md,
maintainer scripts live there) that runs a real SDK call and saves
the response JSONL for later test playback. CI never makes real API
calls.

## 14. Risks

### Summary

Layer 4's risks are operational and mostly about coupling.

### Risk: Claude SDK API churn

The Claude Agent SDK is actively maintained ([cas][cas]). Future
versions may rename methods, change hook signatures, or add new
permission modes. Mitigation: pin a Claude SDK version in
`pyproject.toml`; bump deliberately; the `RuntimeBackend` Protocol
absorbs churn — the orchestrator never sees SDK types directly.

### Risk: hook semantics drift

If the SDK changes how hooks fire (e.g., async vs. sync, new
parameters), our wired-through hooks could silently stop working.
Mitigation: `claude_backend_test.py` covers each hook with a fixture
that asserts the hook actually fires.

### Risk: budget accounting drift

Token-cost calculation depends on per-model rates that change. If
Anthropic publishes new rates or a new model, our cost figures could
go stale. Mitigation: cost rates live in a single
`src/lrh/runtime/cost_rates.py` table with version comments; CI
warns when a rate is older than 90 days.

### Risk: PreToolUse blocking is one-shot

If the agent's plan depends on a tool that gets blocked, the agent
may not recover gracefully. Mitigation: PreToolUse denials always
fire `PostToolUseFailure` with a clear error; agents see this in
their tool-result history and can adjust. We document the pattern.

### Risk: ManualBackend looks like an agent did it

A casual reader of evidence records might not notice that
`source: human` versus `source: agent_trace`. Mitigation: Layer 5b's
evidence schema requires `source` and the validator enforces it; the
manual backend's transcripts are clearly labeled.

## 15. References

[anthropics/claude-agent-sdk-python][cas] — the SDK we wrap. Important
for understanding hook semantics, permission modes, structured
outputs, and trace-context propagation. Per the SDK README:
"Distributed tracing with W3C trace context (TRACEPARENT/TRACESTATE)
support is available when an OpenTelemetry span is active" — that's
the hook into Layer 5a.

[modelcontextprotocol.io][mcp] — MCP spec. The Claude backend's
`mcp_servers` parameter is forwarded to the SDK's MCP-server
attachment mechanism. Layer 6 (bridges) provides the actual MCP
servers; Layer 4 just plumbs the configuration.

[OpenTelemetry GenAI semconv][otel-genai] — span attributes the
Claude backend emits via the observer. Specifically `gen_ai.usage.*`
attributes drive our `cost_usd` calculation; `gen_ai.request.model`
and `gen_ai.provider.name` populate `RuntimeResult.backend_name`-
adjacent metadata.

`PROMPTS.md` — existing prompt-record schema; the runtime extends
the per-prompt frontmatter with `permission_mode`, `allowed_tools`,
`max_budget_usd`, etc., which Layer 3 plumbs through to the runtime
request.

`AGENTS.md` §"Architectural boundary" — maintainer-only AI helpers
live in `scripts/aiprog/`; `record_sdk_fixture.py` lives there.

`STYLE.md` §"Testing Principles" — prefer real fixtures over heavy
mocking; this informs the recorded-SDK-fixture test approach.

[cas]: https://github.com/anthropics/claude-agent-sdk-python
[mcp]: https://modelcontextprotocol.io/
[otel-genai]: https://opentelemetry.io/docs/specs/semconv/gen-ai/
