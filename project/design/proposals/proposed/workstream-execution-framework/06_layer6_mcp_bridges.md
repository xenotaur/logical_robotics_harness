---
id: PROP-WORKSTREAM-LAYER6-MCP-BRIDGES
title: Layer 6 — MCP Bridges
status: proposed
type: design_proposal
created_on: 2026-04-26
updated_on: 2026-04-26
parent: PROP-WORKSTREAM-EXECUTION-FRAMEWORK
---

# Layer 6 — MCP Bridges

## Summary

This sub-proposal specifies the **bridge layer**: how LRH attaches
external tool surfaces — robotics simulators, real robots,
evaluation harnesses, generic Model Context Protocol servers — to
workstream runtime calls in a typed, lifecycle-aware, manual-mode-
parity-preserving way. The bridge layer is the thinnest reasonable
wrapper over the **Model Context Protocol** ([MCP spec][mcp]) plus
LRH-specific lifecycle and evidence concerns. Concretely, Layer 6
defines a `BridgeAdapter` Protocol that yields a `BridgeSession`
context manager, a registry that turns workstream config (`bridges:
[ros, arena_bench]`) into attached MCP servers passed to Layer 4's
`RuntimeRequest.mcp_servers`, and adapter implementations for
generic MCP, ROS (via [robotmcp/ros-mcp-server][ros-mcp]),
Arena-Bench (via [ignc-research/arena-bench][arena-bench]), and a
`FakeAdapter` for tests.

The deliverable boundary is: after Layer 6 ships, a workstream
frontmatter line like `bridges: [arena_bench]` causes the agent
runtime to attach the Arena-Bench MCP server, the agent receives
typed tools (`start_scenario`, `step`, `get_metrics`,
`get_trajectory`), and on workstream stop the bridge teardown is
guaranteed by a context manager — even on crash. Manual-mode parity
is preserved through a `manual_bridge_protocol.md` file per adapter
that prescribes what a human operator does in lieu of the MCP
session (e.g., "open Arena-Bench in a terminal, run the scenario
named in the prompt, paste the metrics JSON into
`project/evidence/staging/`"). This is Layer 6 of the six-layer
stack defined in [00_proposal.md](00_proposal.md). It depends on
Layer 4 ([04_layer4_agent_runtime.md](04_layer4_agent_runtime.md))
for runtime attachment and on Layer 5
([05_layer5_observability_and_evidence.md](05_layer5_observability_and_evidence.md))
for bridge-specific evidence extractors.

## Table of contents

1. [Goals and non-goals](#1-goals-and-non-goals)
2. [Why MCP and not a custom RPC layer](#2-why-mcp-and-not-a-custom-rpc-layer)
3. [Module layout](#3-module-layout)
4. [The BridgeAdapter / BridgeSession Protocols](#4-the-bridgeadapter--bridgesession-protocols)
5. [Bridge configuration in workstream frontmatter](#5-bridge-configuration-in-workstream-frontmatter)
6. [The adapter set](#6-the-adapter-set)
7. [Lifecycle and process-group handling](#7-lifecycle-and-process-group-handling)
8. [Bridge-specific evidence extractors](#8-bridge-specific-evidence-extractors)
9. [Worked example — NARROW DOORWAY scenario](#9-worked-example--narrow-doorway-scenario)
10. [Worked example — PROSOC mapping](#10-worked-example--prosoc-mapping)
11. [Manual-mode parity](#11-manual-mode-parity)
12. [CLI surface](#12-cli-surface)
13. [Tests](#13-tests)
14. [Risks](#14-risks)
15. [References](#15-references)

## 1. Goals and non-goals

### Summary

Layer 6 turns "the agent needs to drive a simulator" into a
declarative, typed, idempotent, observable thing. It does not
attempt to be a robotics framework, an evaluation framework, or an
MCP client implementation — it adapts existing implementations to
LRH conventions.

### Goals

A `BridgeAdapter` Protocol with `name()`, `mcp_server_config()`,
and `open_session()` methods, where `open_session()` returns a
`BridgeSession` context manager. A `BridgeSession` Protocol with
`enter()`, `exit()`, `health_check()`, and `teardown_evidence()`
methods. A registry mapping bridge name → adapter. A loader that
reads workstream frontmatter `bridges:` and produces the list of
attached MCP servers for `RuntimeRequest.mcp_servers`. Built-in
adapters: `mcp_adapter` (generic MCP server passthrough),
`ros_adapter` (wraps `robotmcp/ros-mcp-server`),
`arena_bench_adapter` (wraps Arena-Bench via a custom scenario-
control MCP server we ship in this layer), `fake_adapter` (for
tests, returns canned tool results). Bridge-specific evidence
extractors registered with Layer 5b. Manual-mode parity via per-
adapter `manual_bridge_protocol.md`. Process-group teardown
guaranteed by context manager protocol — no orphan
`gz`/`gazebo`/`roscore`/`rviz2` processes after a workstream
crashes.

### Non-goals

We do not write our own MCP client. Layer 4 already imports
`mcp.client` from the official Python SDK ([modelcontextprotocol/\
python-sdk][mcp-py]); we hand it server configs and let it manage
the session.

We do not write our own ROS bridge. `robotmcp/ros-mcp-server`
exists and works; we wrap its lifecycle.

We do not embed Arena-Bench. It runs in its own conda env / docker
container; we expose its scenario-control surface through an MCP
server that we author (because Arena-Bench upstream does not yet
ship one) and we keep that MCP server in
`src/lrh/bridges/arena_bench_mcp_server/` so it is co-versioned
with the adapter that calls it. The adapter is the LRH-shaped
glue; the upstream evaluator stays upstream.

We do not implement Gazebo, Webots, or any specific simulator
backend. Those are already handled by `robotmcp/ros-mcp-server`'s
configuration matrix or by Arena-Bench's scenario configs.

We do not provide a "let the agent design new scenarios" tool. The
scenario set is a config artifact, not an agent decision; Pass B
flagged free-form scenario synthesis as a guardrails risk.

### Out-of-scope (deferred)

Multi-agent / multi-robot orchestration through one bridge session
(deferred — Arena-Bench supports it, but our v1 adapter exposes
single-robot scenarios because that's what current LRH workstreams
need).

Bridge-level cost accounting (e.g., GPU-seconds in Gazebo). Layer 4
attributes LLM cost; bridge cost is captured as duration and tool
calls, not dollars, in v1.

Live human teleop alongside an agent run (deferred — would require
threading concerns we don't want to take on yet).

## 2. Why MCP and not a custom RPC layer

### Summary

MCP is the right substrate because it already solves the problem
LRH would otherwise re-solve, and because the runtime layer (Layer
4) already speaks it.

### The argument

Per the Model Context Protocol spec ([modelcontextprotocol.io][mcp]),
"MCP follows a client-host-server architecture where each host can
run multiple client instances. This architecture enables users to
integrate AI capabilities across applications while maintaining
clear security boundaries and isolating concerns." That isolation
is exactly what we want between the workstream agent and the
robotics stack: a typed tool surface, declarative server lifecycle,
and a security boundary the user can reason about.

Three concrete reasons we don't roll our own:

The Claude Agent SDK ([anthropics/claude-agent-sdk-python][cas])
already speaks MCP natively — its `mcp_servers` parameter takes
exactly the kind of server-config list our `BridgeAdapter` produces.
A custom RPC layer would mean re-implementing transport, tool-
schema validation, and permission negotiation, all of which MCP
already specifies.

The robotics community is converging on MCP as the integration
surface. `robotmcp/ros-mcp-server` exists today as production-grade
ROS↔MCP middleware ([ros-mcp]). If we shipped a custom RPC layer
we would have to re-do that work.

MCP servers compose. A workstream that needs both ROS and
Arena-Bench attaches both servers — the agent sees a unioned tool
namespace with no conflict resolution needed at our layer (MCP
servers are namespaced by server name).

### What we add on top of MCP

Three things, all about lifecycle and observability rather than
protocol semantics:

**Workstream-aware configuration.** `bridges: [ros, arena_bench]`
in workstream frontmatter is more declarative than the per-call
MCP server configuration the SDK accepts. The `BridgeAdapter`
registry resolves the names.

**Process-group teardown.** MCP servers that own subprocesses
(rosbridge, gzserver, rviz2) need cleanup discipline. We use POSIX
process groups (`os.setsid`, `os.killpg`) so a crashed parent
doesn't orphan children. The MCP spec doesn't address this — it
trusts the host.

**Bridge-specific evidence.** A "ran NARROW DOORWAY scenario,
3 collisions, 0.86 success rate" finding is structurally distinct
from "called `step` 47 times." The bridge knows what its tools
mean; Layer 6 hands an extractor to Layer 5b that turns tool-call
sequences into `scenario_run` evidence records.

## 3. Module layout

```text
src/lrh/bridges/
├── __init__.py
├── adapter.py            # BridgeAdapter / BridgeSession Protocols
├── registry.py           # name → adapter registry; loader from frontmatter
├── config.py             # frozen dataclasses for bridge configs
├── lifecycle.py          # process-group handling, health checks
├── evidence.py           # bridge-specific extractors → Layer 5b
├── manual.py             # manual-mode parity helpers
├── adapters/
│   ├── __init__.py
│   ├── mcp_adapter.py    # generic MCP server passthrough
│   ├── ros_adapter.py    # wraps robotmcp/ros-mcp-server
│   ├── arena_bench_adapter.py
│   ├── fake_adapter.py   # canned responses for tests
│   └── arena_bench_mcp_server/
│       ├── __init__.py
│       ├── server.py     # @tool-decorated start_scenario / step / get_metrics / get_trajectory
│       └── README.md     # what this server exposes and why it lives here
├── prompts/              # per-adapter manual-mode prompts
│   ├── ros_manual.md
│   ├── arena_bench_manual.md
│   └── mcp_generic_manual.md
└── cli.py                # `lrh bridges` subcommands
```

### Style conformance

Module imports, not member imports (per
`STYLE.md` §"Imports"). Built-in generics (`list[str]`,
`dict[str, BridgeConfig]`). Frozen dataclasses for all public
records. Module-mirrored test layout under `tests/bridges/`.
`--dry-run` and `--check` on every CLI subcommand that mutates
state.

### Test layout

```text
tests/bridges/
├── test_adapter.py
├── test_registry.py
├── test_config.py
├── test_lifecycle.py
├── test_evidence.py
├── test_manual.py
├── adapters/
│   ├── test_mcp_adapter.py
│   ├── test_ros_adapter.py     # uses fake rosbridge process
│   ├── test_arena_bench_adapter.py
│   ├── test_fake_adapter.py
│   └── test_arena_bench_mcp_server.py
├── manual_parity_test.py        # one bridge advance, both modes, identical evidence
└── fixtures/
    ├── fake_ros_responses.json
    ├── fake_arena_bench_responses.json
    └── narrow_doorway_scenario.yaml
```

## 4. The BridgeAdapter / BridgeSession Protocols

### Summary

Two Protocols. `BridgeAdapter` is process-free metadata: it knows
the adapter's name, what MCP server config to hand the runtime, and
how to open a session. `BridgeSession` is the live thing: it owns
subprocesses, exposes a health check, and produces teardown
evidence on `__exit__`.

### Protocol definitions

```python
# src/lrh/bridges/adapter.py
from __future__ import annotations

import contextlib
import dataclasses
from typing import Protocol

from lrh.bridges import config as bridge_config_mod
from lrh.bridges import evidence as bridge_evidence_mod


@dataclasses.dataclass(frozen=True)
class McpServerConfig:
    """Shape we hand to RuntimeRequest.mcp_servers (Layer 4)."""

    name: str
    command: list[str]
    env: dict[str, str]
    cwd: str | None = None
    transport: str = "stdio"  # or "sse" or "websocket"


class BridgeSession(Protocol):
    """A live bridge attachment. Context manager.

    Owns subprocesses (rosbridge, gzserver, etc.) when applicable.
    On __exit__, guarantees process-group teardown and produces a
    teardown evidence record.
    """

    def health_check(self) -> bool:
        """Return True iff the bridge is responsive.

        Called by the runtime before each tool call when
        `permission_mode == strict`. Cheap, no side effects.
        """
        ...

    def teardown_evidence(self) -> bridge_evidence_mod.TeardownEvidence:
        """Return the evidence record produced by this session.

        Includes start/end timestamps, exit code(s), tool-call
        count, any subprocess-level errors observed.
        """
        ...

    def __enter__(self) -> "BridgeSession": ...
    def __exit__(self, *args: object) -> None: ...


class BridgeAdapter(Protocol):
    """Process-free metadata about a bridge.

    A BridgeAdapter is registered once at import time. A
    BridgeSession is opened once per workstream advance.
    """

    def name(self) -> str:
        """The name used in workstream frontmatter (e.g. 'ros')."""
        ...

    def supports_manual_mode(self) -> bool:
        """True if this bridge has a manual-mode prompt path.

        ros_adapter: True. fake_adapter: False (no manual analog).
        """
        ...

    def mcp_server_config(
        self, cfg: bridge_config_mod.BridgeConfig
    ) -> McpServerConfig:
        """Compute the MCP server config from BridgeConfig."""
        ...

    def open_session(
        self, cfg: bridge_config_mod.BridgeConfig
    ) -> contextlib.AbstractContextManager[BridgeSession]:
        """Open a session. Caller MUST use this as a context manager.

        Implementations typically return `contextlib.contextmanager`-
        decorated generators or class-based context managers that
        own subprocess lifecycle.
        """
        ...
```

### Why two Protocols and not one

The adapter is reusable across workstreams; the session is single-
use. Treating them as one type would either pin process state to
the registry (leaking subprocess handles across workstreams) or
require every adapter to implement context-manager semantics
itself. The split also matches the existing Layer 4 split between
`RuntimeBackend` (reusable) and the `RuntimeResult` of a single
call (single-use).

### Why context manager and not start/stop methods

Process leaks. A workstream that crashes in the middle of a Gazebo
run has to clean up `gzserver` somehow. If the session is a
context manager, `__exit__` runs even on exception — guaranteed
teardown is structurally enforced. Start/stop methods rely on the
caller remembering to call `stop`, which Pass B identified as a
common failure mode in robotics plumbing.

## 5. Bridge configuration in workstream frontmatter

### Summary

A workstream declares its bridges in frontmatter. The orchestrator
resolves declarations to attached MCP servers at runtime-call time.

### Frontmatter schema additions

```yaml
---
id: WS-LCATS-CORPORA-ANALYSIS
# ... other frontmatter ...

# NEW: bridge attachments
bridges:
  - name: arena_bench
    config:
      scenarios: [NARROW_DOORWAY, OBSTACLE_AVOIDANCE]
      timeout_seconds: 600
      seed: 42
  - name: ros
    config:
      ros_distro: humble
      launch_file: turtlebot3_world.launch.py
      robot_namespace: tb3_0
---
```

### Resolution

```python
# src/lrh/bridges/registry.py
from lrh.bridges import adapter as bridge_adapter_mod
from lrh.bridges import config as bridge_config_mod
from lrh.bridges.adapters import (
    arena_bench_adapter,
    fake_adapter,
    mcp_adapter,
    ros_adapter,
)


_ADAPTERS: dict[str, bridge_adapter_mod.BridgeAdapter] = {
    "ros": ros_adapter.RosAdapter(),
    "arena_bench": arena_bench_adapter.ArenaBenchAdapter(),
    "mcp": mcp_adapter.GenericMcpAdapter(),
    "fake": fake_adapter.FakeAdapter(),
}


def resolve_bridges(
    decls: list[bridge_config_mod.BridgeDecl],
) -> list[bridge_adapter_mod.McpServerConfig]:
    """Turn frontmatter bridge declarations into MCP server configs.

    Raises BridgeNotFoundError if a name isn't registered.
    """
    out: list[bridge_adapter_mod.McpServerConfig] = []
    for decl in decls:
        if decl.name not in _ADAPTERS:
            raise bridge_config_mod.BridgeNotFoundError(decl.name)
        adapter = _ADAPTERS[decl.name]
        cfg = bridge_config_mod.BridgeConfig.from_decl(decl)
        out.append(adapter.mcp_server_config(cfg))
    return out
```

### Validation

Layer 1 (control plane) gains a validator pass that verifies every
`bridges:` entry references a registered adapter. Same severity
model as the rest of Layer 1 — `error` for unknown adapter names,
`warning` for adapter-specific config issues (e.g., scenario name
not in the adapter's known set).

## 6. The adapter set

### Summary

Four adapters ship in v1: `mcp` (generic), `ros`, `arena_bench`,
`fake`. Each gets its own subsection.

### 6.1 `mcp_adapter` — Generic MCP server passthrough

The simplest adapter. The user supplies a full MCP server config in
the workstream frontmatter; `mcp_adapter` returns it unchanged.
This is the escape hatch — for any MCP server we don't have a
purpose-built adapter for.

```yaml
bridges:
  - name: mcp
    config:
      server:
        name: filesystem
        command: [npx, -y, "@modelcontextprotocol/server-filesystem", /workspace]
        env: {}
```

The session has no subprocesses LRH owns (the MCP client manages
the server lifecycle), so `BridgeSession.__exit__` is a no-op. The
teardown evidence records start/end timestamps and the count of
tool calls observed by Layer 5a.

### 6.2 `ros_adapter` — Wraps `robotmcp/ros-mcp-server`

Per the upstream README ([ros-mcp]):

> "ros-mcp-server is a Model Context Protocol server that exposes
> ROS 2 topics, services, and actions to MCP-compatible clients."

We don't reimplement that. The adapter:

Reads `ros_distro`, `launch_file`, and `robot_namespace` from
`BridgeConfig`. Resolves them to env vars (`ROS_DISTRO`,
`ROS_DOMAIN_ID`) and command-line flags. Constructs the
`McpServerConfig` that boots `ros-mcp-server` as a subprocess via
its documented entry point. Opens a session that:

  - Starts the launch file in a new process group (`os.setsid`);
  - Waits for `health_check()` to return True (rosbridge replies
    to a `__health__` topic) with a timeout;
  - Yields control to the runtime;
  - On `__exit__`, sends `SIGTERM` to the process group, waits
    `--bridge-grace-seconds` (default 5), then `SIGKILL`s the
    group;
  - Captures stdout/stderr to `project/runs/RUN-{ulid}/bridges/\
ros/`.

### 6.3 `arena_bench_adapter` — Wraps Arena-Bench

Per the upstream README ([arena-bench]):

> "Arena-bench is a benchmarking tool for navigation algorithms in
> Arena 4.0, allowing users to compare different motion planners
> across multiple scenarios using diverse evaluation metrics."

Arena-Bench upstream does not yet ship an MCP server. We author
one: `src/lrh/bridges/adapters/arena_bench_mcp_server/server.py`,
co-versioned with the adapter so we can change them in lockstep.

The MCP server we ship exposes four `@tool`-decorated methods —
the surface area an agent needs to drive a benchmark, no more:

```python
# src/lrh/bridges/adapters/arena_bench_mcp_server/server.py
"""LRH-authored MCP server that wraps Arena-Bench scenario control.

Why this lives here: Arena-Bench upstream does not yet ship an MCP
server. Co-versioning the server with the adapter that calls it
means we can change both in lockstep without coordinating with
upstream releases.
"""

from __future__ import annotations

import dataclasses
import json
import pathlib

from mcp import server as mcp_server_mod
from mcp.server import stdio as mcp_stdio_mod

# Imports of the Arena-Bench Python API would go here. They are
# guarded so this module can be imported in environments without
# Arena-Bench installed (test environments use the FakeAdapter).
try:
    from arena_bench import scenario as arena_scenario_mod
    from arena_bench import metrics as arena_metrics_mod
except ImportError:  # pragma: no cover
    arena_scenario_mod = None
    arena_metrics_mod = None


_app = mcp_server_mod.Server("arena-bench-lrh")


@_app.tool()
def start_scenario(name: str, seed: int = 0) -> dict[str, object]:
    """Start a named Arena-Bench scenario.

    Returns {scenario_id, scenario_name, seed, started_at}.
    """
    if arena_scenario_mod is None:
        raise RuntimeError("arena_bench is not installed")
    handle = arena_scenario_mod.start(name=name, seed=seed)
    return dataclasses.asdict(handle)


@_app.tool()
def step(scenario_id: str, action: dict[str, float]) -> dict[str, object]:
    """Apply one action to the running scenario.

    Returns {observation, reward, terminated, truncated, info}.
    """
    if arena_scenario_mod is None:
        raise RuntimeError("arena_bench is not installed")
    res = arena_scenario_mod.step(scenario_id=scenario_id, action=action)
    return dataclasses.asdict(res)


@_app.tool()
def get_metrics(scenario_id: str) -> dict[str, object]:
    """Return the metrics dict computed so far.

    Includes: success_rate, collision_count, time_to_goal,
    path_efficiency, jerk_integral, ...
    """
    if arena_metrics_mod is None:
        raise RuntimeError("arena_bench is not installed")
    return arena_metrics_mod.compute(scenario_id=scenario_id)


@_app.tool()
def get_trajectory(scenario_id: str) -> dict[str, object]:
    """Return the trajectory as a list of {t, x, y, theta} points."""
    if arena_scenario_mod is None:
        raise RuntimeError("arena_bench is not installed")
    return {"points": arena_scenario_mod.trajectory(scenario_id=scenario_id)}


def main() -> None:
    """Entry point for the MCP server subprocess."""
    mcp_stdio_mod.run(_app)


if __name__ == "__main__":
    main()
```

The adapter then constructs the server config:

```python
# src/lrh/bridges/adapters/arena_bench_adapter.py (excerpt)
from lrh.bridges import adapter as bridge_adapter_mod


class ArenaBenchAdapter:
    def name(self) -> str:
        return "arena_bench"

    def supports_manual_mode(self) -> bool:
        return True

    def mcp_server_config(self, cfg):
        return bridge_adapter_mod.McpServerConfig(
            name="arena-bench-lrh",
            command=[
                "python", "-m",
                "lrh.bridges.adapters.arena_bench_mcp_server.server",
            ],
            env={
                "ARENA_BENCH_SCENARIOS": ",".join(cfg.scenarios),
                "ARENA_BENCH_SEED": str(cfg.seed),
                "ARENA_BENCH_TIMEOUT_S": str(cfg.timeout_seconds),
            },
            transport="stdio",
        )

    def open_session(self, cfg):
        # See lifecycle.py for the contextmanager implementation.
        ...
```

### 6.4 `fake_adapter` — Canned responses for tests

Mirror of `FakeBackend` from Layer 4. Reads a JSON fixture from a
configured path; returns canned tool results. Used by every test
that exercises the bridges layer without touching ROS / Arena-
Bench. No subprocesses; no manual mode (it has no real-world
analog).

```yaml
bridges:
  - name: fake
    config:
      fixture: tests/bridges/fixtures/fake_arena_bench_responses.json
```

## 7. Lifecycle and process-group handling

### Summary

The single largest source of pain in robotics plumbing is orphaned
subprocesses after a crash. This section is the one technical
prescription we're making strongly.

### Process group discipline

Every subprocess an adapter starts goes in a fresh process group:

```python
# src/lrh/bridges/lifecycle.py (excerpt)
import os
import signal
import subprocess
import time


def spawn_in_process_group(cmd: list[str], env: dict[str, str], cwd: str | None) -> subprocess.Popen:
    """Spawn a subprocess in a new POSIX process group.

    The new group ID equals the child PID. The parent can later
    `os.killpg(child.pid, SIGTERM)` to take down the child and any
    grandchildren (rviz2, gzserver, ...) atomically.
    """
    return subprocess.Popen(
        cmd,
        env=env,
        cwd=cwd,
        start_new_session=True,  # equivalent to preexec_fn=os.setsid
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def teardown_process_group(proc: subprocess.Popen, grace_seconds: float = 5.0) -> int:
    """Send SIGTERM to the process group, wait grace, then SIGKILL.

    Returns the eventual exit code (or -SIGKILL if killed).
    """
    if proc.poll() is not None:
        return proc.returncode

    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return proc.returncode if proc.returncode is not None else 0

    deadline = time.monotonic() + grace_seconds
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return proc.returncode
        time.sleep(0.1)

    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    proc.wait(timeout=2.0)
    return proc.returncode if proc.returncode is not None else -signal.SIGKILL
```

### Why this matters specifically for ROS

A `ros2 launch` command typically forks `gzserver`, `gzclient`,
`rviz2`, the robot driver node, and a half-dozen lifecycle nodes.
A naive `proc.terminate()` only signals the launcher itself; the
children stay alive and hold ports / shared memory. We've all
debugged the "address already in use" rerun. Process groups solve
this; this layer enforces the discipline so individual adapters
don't have to remember.

### Health checks

Each adapter implements `BridgeSession.health_check()` cheaply.
Recommended patterns:

ROS adapter: subscribe to `/rosout`, return True if a message
arrives within 250 ms. Arena-Bench adapter: call `get_metrics`
with a known-bad scenario_id and verify the error shape. Generic
MCP adapter: call MCP's `tools/list` ([mcp-tools-list]) and verify
the response is well-formed. Fake adapter: always True.

### Health-check usage by mode

In `permission_mode == strict` (Layer 4), the runtime calls
`health_check()` before each tool call; a False result aborts the
call with `Outcome.TOOL_DENIED`. In `accept_edits` and `ask`, the
runtime trusts the bridge unless tool-call timeouts pile up.

## 8. Bridge-specific evidence extractors

### Summary

The orchestrator already extracts generic evidence from traces
(per Layer 5b). Bridges register additional extractors that
understand bridge-specific tool semantics.

### Extractor registration

```python
# src/lrh/bridges/evidence.py
from lrh.evidence import extractors as evidence_extractors_mod


def register_bridge_extractors() -> None:
    """Called once at LRH startup; registers all bridge-specific extractors."""
    evidence_extractors_mod.register(ArenaBenchScenarioRunExtractor())
    evidence_extractors_mod.register(RosLaunchTeardownExtractor())
    evidence_extractors_mod.register(McpToolErrorExtractor())
```

### Example: ArenaBenchScenarioRunExtractor

Reads spans where `mcp.server.name == "arena-bench-lrh"` and a
`get_metrics` call appears at the end. Synthesizes a
`scenario_run` evidence record per scenario:

```yaml
---
id: EV-WS-LCATS-CORPORA-ANALYSIS-NARROW-DOORWAY-001
workstream: WS-LCATS-CORPORA-ANALYSIS
kind: scenario_run
provenance: agent_trace
extractor: ArenaBenchScenarioRunExtractor
extracted_at: 2026-04-26T18:42:11Z
data:
  scenario_name: NARROW_DOORWAY
  seed: 42
  success: true
  collision_count: 0
  time_to_goal_seconds: 14.3
  path_efficiency: 0.91
  jerk_integral: 1.42
  tool_call_count: 47
  trajectory_ref: project/runs/RUN-01HZ.../trajectories/NARROW_DOORWAY-42.json
---

# Scenario run: NARROW_DOORWAY (seed=42)

The agent drove the navigation stack through the NARROW DOORWAY
scenario in 14.3 seconds with no collisions. Path efficiency 0.91,
jerk integral 1.42 (lower is smoother). Trajectory captured at the
ref above for offline review.
```

The extractor's full source:

```python
# src/lrh/bridges/evidence.py (excerpt)
import dataclasses
import datetime
import pathlib

from lrh.evidence import models as evidence_models_mod
from lrh.evidence import extractors as evidence_extractors_mod
from lrh.observability import models as obs_models_mod


class ArenaBenchScenarioRunExtractor:
    def applies_to(self, span: obs_models_mod.Span) -> bool:
        return (
            span.attributes.get("mcp.server.name") == "arena-bench-lrh"
            and span.attributes.get("mcp.tool.name") == "get_metrics"
        )

    def extract(
        self,
        run_dir: pathlib.Path,
        span: obs_models_mod.Span,
        ctx: evidence_extractors_mod.ExtractContext,
    ) -> list[evidence_models_mod.EvidenceRecord]:
        metrics = span.events[-1].attributes.get("mcp.tool.result", {})
        scenario = ctx.find_earlier_span(
            run_dir,
            mcp_tool_name="start_scenario",
            within=span,
        )
        return [
            evidence_models_mod.EvidenceRecord(
                kind="scenario_run",
                provenance=evidence_models_mod.Provenance.AGENT_TRACE,
                extractor=type(self).__name__,
                extracted_at=datetime.datetime.now(tz=datetime.UTC),
                data={
                    "scenario_name": scenario.attributes["mcp.tool.args"]["name"],
                    "seed": scenario.attributes["mcp.tool.args"]["seed"],
                    "success": metrics["success"],
                    "collision_count": metrics["collision_count"],
                    "time_to_goal_seconds": metrics["time_to_goal_seconds"],
                    "path_efficiency": metrics["path_efficiency"],
                    "jerk_integral": metrics["jerk_integral"],
                    "tool_call_count": ctx.tool_call_count_in(run_dir),
                    "trajectory_ref": str(
                        run_dir / "trajectories" /
                        f"{scenario.attributes['mcp.tool.args']['name']}-"
                        f"{scenario.attributes['mcp.tool.args']['seed']}.json"
                    ),
                },
            )
        ]
```

### Per-extractor schema

Each bridge-specific extractor registers a JSON Schema for its
evidence kind in `project/evidence/schemas/`, per Layer 5b §5. This
is the per-evidence-kind schema registry pattern; bridges just hook
into it.

## 9. Worked example — NARROW DOORWAY scenario

### Summary

A workstream needs to evaluate two motion planners (TEB and DWA) on
the NARROW DOORWAY scenario from Arena-Bench. The agent runs each
planner three times with different seeds, produces metrics, and
writes a comparison evidence record. End-to-end Layer 6 walkthrough.

### Workstream frontmatter

```yaml
---
id: WS-NAV-PLANNER-COMPARISON-DOORWAY
title: Compare TEB vs DWA on NARROW DOORWAY
status: planned
mode: hybrid
bridges:
  - name: arena_bench
    config:
      scenarios: [NARROW_DOORWAY]
      timeout_seconds: 600
      seed: 42
  - name: ros
    config:
      ros_distro: humble
      launch_file: turtlebot3_world.launch.py
      robot_namespace: tb3_0
prompts:
  - id: P-001
    template: prompt
    role: orchestrator
budget:
  per_call_max_usd: 0.50
  per_workstream_max_usd: 5.00
expected_evidence_at_close:
  - kind: scenario_run
    count: 6           # 2 planners × 3 seeds
  - kind: planner_comparison
    count: 1
---
```

### Prompt (excerpt)

> "You are evaluating two motion planners on the NARROW DOORWAY
> scenario in Arena-Bench. For each of `[teb_local_planner,
> dwa_local_planner]`, call `start_scenario(name='NARROW_DOORWAY',
> seed=S)` for `S in [42, 43, 44]`. Drive the robot through using
> `step()` calls. Call `get_metrics()` at the end of each run.
> Stop on success or after 600 simulated seconds. Do not call
> `start_scenario` more than 6 times total."

### Runtime trace (abbreviated)

The agent attaches both bridges. The MCP server namespace shows
`arena-bench-lrh.start_scenario`, `ros.publish`, etc. Agent calls
proceed:

```text
[span] mcp.tool.call name=ros.set_parameter args={planner: teb_local_planner}
[span] mcp.tool.call name=arena-bench-lrh.start_scenario args={name: NARROW_DOORWAY, seed: 42}
  └─ result: {scenario_id: "abc-1", started_at: "2026-04-26T18:40:11Z"}
[span] mcp.tool.call name=arena-bench-lrh.step args={...}    × 47 times
[span] mcp.tool.call name=arena-bench-lrh.get_metrics args={scenario_id: "abc-1"}
  └─ result: {success: true, collision_count: 0, time_to_goal: 14.3, ...}
... (5 more iterations: TEB seed=43, TEB seed=44, DWA seed=42, ...)
[span] runtime.advance.complete outcome=success cost=$1.84 turns=18
```

### Evidence after extraction

After Layer 5b runs:

`EV-WS-NAV-PLANNER-COMPARISON-DOORWAY-NARROW-DOORWAY-001`
through `-006` (six `scenario_run` records, one per
planner×seed). One synthesized `planner_comparison` record (the
agent writes this directly via the extractor's
`agent_writes` pattern from Layer 5b §4 — see the markdown body
below).

```yaml
---
id: EV-WS-NAV-PLANNER-COMPARISON-DOORWAY-COMPARISON-001
kind: planner_comparison
provenance: agent_trace
data:
  planners: [teb_local_planner, dwa_local_planner]
  scenario: NARROW_DOORWAY
  seeds: [42, 43, 44]
  metrics_summary:
    teb_local_planner:
      success_rate: 1.0
      mean_time_to_goal: 14.5
      mean_path_efficiency: 0.91
      mean_jerk_integral: 1.40
    dwa_local_planner:
      success_rate: 0.67
      mean_time_to_goal: 16.8
      mean_path_efficiency: 0.84
      mean_jerk_integral: 2.31
  recommendation: teb_local_planner
  confidence: high
---
```

### Closure check

Layer 3's `can_close()` validator reads
`expected_evidence_at_close: [scenario_run × 6, planner_comparison
× 1]` and confirms 6 + 1 records exist with matching kinds. Pass.
The workstream transitions `executing → reviewing → closed` after
the human reviewer signs off (the workstream is `mode: hybrid`).

### Trace and evidence in observability widget

The post-run summary link in the workstream's `runs/` ref points to
`project/runs/RUN-{ulid}/`, which contains spans, transcripts, and
trajectories. The reviewer can replay the agent's trajectory frame-
by-frame via the static trajectory JSON without re-running the
simulator.

## 10. Worked example — PROSOC mapping

### Summary

PROSOC is a constitution-based reasoning project the user has
worked on. Mapping its components to the six-layer stack
demonstrates that Layer 6 isn't simulator-specific.

### PROSOC ↔ LRH mapping

| PROSOC component | LRH layer | Concrete artifact |
|------------------|-----------|-------------------|
| Constitution / principles | Layer 1 | `project/workstreams/active/WS-PROSOC-EVAL/principles/` (Markdown files; precedence-ordered) |
| Agent reasoning loop | Layer 4 | `RuntimeBackend` (Claude SDK) with `prompts: [P-reason, P-reflect]` |
| Constitution evaluation | Layer 5b | `EvidenceExtractor` that reads `prompts/P-evaluate` spans and produces `principle_violation` records |
| External knowledge / tools | Layer 6 | `mcp_adapter` with the constitution-corpus MCP server attached |

### Workstream excerpt

```yaml
---
id: WS-PROSOC-CONSTITUTION-AUDIT
title: Audit constitution for principle conflicts
status: planned
mode: hybrid
bridges:
  - name: mcp
    config:
      server:
        name: prosoc-corpus
        command: [python, -m, prosoc.mcp_server]
        env: {PROSOC_CORPUS_DIR: project/workstreams/active/WS-PROSOC-EVAL/principles}
prompts:
  - id: P-001
    template: prompt
    role: auditor
expected_evidence_at_close:
  - kind: principle_violation
    count: ">=0"
  - kind: audit_summary
    count: 1
---
```

### Why this matters

PROSOC has nothing to do with robotics simulation. Layer 6's
adapter set is open: any MCP server is a bridge. The robotics
adapters (`ros`, `arena_bench`) are the heavy artillery; the
generic `mcp_adapter` is the everyday tool. The same lifecycle
discipline applies — process groups, health checks, teardown
evidence — even when the "subprocess" is a pure-Python MCP server
the user wrote in their own repo.

## 11. Manual-mode parity

### Summary

The manual-mode-parity invariant from the umbrella proposal
applies here too: every bridge has a manual analog. For some
bridges that's exotic (you can't manually drive Arena-Bench at
agent speed, but you can run the scenario, paste the metrics, and
sign off); for `fake_adapter` it's nonsense (no real-world analog,
so `supports_manual_mode()` returns False).

### The manual prompt pattern

Per adapter, a `prompts/{adapter}_manual.md` file. Format:

```markdown
# Manual-mode protocol for {ADAPTER}

If `mode: manual` is set on the workstream and this bridge is
declared, the orchestrator emits this prompt to the human operator
in lieu of opening an MCP session.

## What the agent would have done

(Bridge-specific description, e.g., "started a NARROW_DOORWAY
scenario, called step() N times, captured metrics.")

## What you should do instead

1. ...
2. ...
3. Paste the resulting JSON into project/evidence/staging/{ev_id}.yml
4. Run `lrh evidence promote {ev_id}` to commit.

## Schema for the manual evidence record

(Reference to the per-evidence-kind schema in
project/evidence/schemas/.)
```

### Arena-Bench manual prompt (excerpt)

```markdown
## What you should do instead

1. In a separate terminal, activate the Arena-Bench conda env:
   `conda activate arena4`
2. Run the scenario:
   `python -m arena_bench.scenarios.run NARROW_DOORWAY --seed 42 \
     --metrics-out /tmp/metrics-narrow-42.json --trajectory-out \
     /tmp/traj-narrow-42.json`
3. Open `/tmp/metrics-narrow-42.json` and copy the contents.
4. `lrh evidence stub --workstream WS-NAV-PLANNER-COMPARISON-DOORWAY \
     --kind scenario_run --extractor manual`
5. Paste the metrics into the `data:` block of the staged record.
6. `lrh evidence promote {ev_id}` to commit.
```

This is structurally identical to the agent path: same evidence
kind, same schema, same closure-check semantics. The only
difference is who fills in the `data:` block.

## 12. CLI surface

### Summary

`lrh bridges` for inspection and one-off attachment / teardown.
Mutating subcommands ship `--dry-run`.

### Subcommands

```text
lrh bridges list                       # registered adapters
lrh bridges show <name>                # adapter metadata, MCP config preview
lrh bridges open <ws> [--dry-run]      # open a session for a workstream (debugging)
lrh bridges teardown <run-id>          # force teardown of a possibly-orphaned run
lrh bridges health <ws>                # call health_check() on all attached bridges
lrh bridges manual-prompt <ws> <name>  # render the per-adapter manual prompt
```

### Example session

```text
$ lrh bridges list
NAME         SUPPORTS_MANUAL  MCP_TRANSPORT
ros          yes              stdio
arena_bench  yes              stdio
mcp          conditional      stdio | sse | websocket
fake         no               stdio (in-process)

$ lrh bridges show arena_bench
adapter: ArenaBenchAdapter
mcp server: arena-bench-lrh
tools: start_scenario, step, get_metrics, get_trajectory
co-located mcp server: src/lrh/bridges/adapters/arena_bench_mcp_server/
manual prompt: src/lrh/bridges/prompts/arena_bench_manual.md
```

## 13. Tests

### Summary

Module-mirrored test layout (per `STYLE.md`), one
`manual_parity_test.py` that exercises a full workstream advance
through both bridge modes and asserts evidence equality, fixture-
backed adapters for everything that would otherwise need ROS or
Arena-Bench installed.

### Test outline

`tests/bridges/test_adapter.py` — Protocol shape conformance,
`McpServerConfig` immutability.

`tests/bridges/test_registry.py` — Lookup, missing-name error,
duplicate registration error.

`tests/bridges/test_lifecycle.py` — Process-group spawn / teardown
on a sentinel script that forks twice; assert the grandchild is
killed.

`tests/bridges/test_evidence.py` — `ArenaBenchScenarioRunExtractor`
on a fixture span; `RosLaunchTeardownExtractor` on a fixture span.

`tests/bridges/adapters/test_arena_bench_mcp_server.py` — boots
the server with `arena_bench` mocked at the module level; calls
each `@tool` and asserts response shape.

`tests/bridges/manual_parity_test.py` — runs `WS-FIXTURE-DOORWAY`
in `mode: agent` (with `fake_adapter`) and `mode: manual` (with
hand-pasted evidence); asserts the resulting evidence records are
byte-equal except for `extractor:` and `extracted_at:`.

### CI consideration

The Arena-Bench and ROS test suites are gated behind opt-in pytest
markers (`@pytest.mark.requires_ros`,
`@pytest.mark.requires_arena_bench`). The default CI run uses the
`fake_adapter` and the in-process Arena-Bench MCP server with
`arena_bench` module mocked. Robotics-environment CI is a separate
job that runs only on PRs touching
`src/lrh/bridges/adapters/ros_adapter.py` or the Arena-Bench server.

## 14. Risks

### Summary

Five categories: schema/upstream drift, process-group portability,
permission boundary leakage, evidence non-determinism, scope creep.

### Risk: upstream MCP server drift

`robotmcp/ros-mcp-server` is third-party. A breaking change to
its tool surface breaks our adapter. Mitigation: pin to a tagged
release in `pyproject.toml`; track upstream via a `lrh.bridges`
ADR. The `arena_bench_mcp_server` we ship ourselves; co-versioning
removes that risk for Arena-Bench.

### Risk: process-group teardown on non-POSIX

`os.setsid` and `os.killpg` are POSIX. Windows support requires
`CREATE_NEW_PROCESS_GROUP` and `CTRL_BREAK_EVENT`; our v1 is
POSIX-only and we declare it explicitly in the README. Most ROS
work happens on Linux anyway, but we shouldn't pretend we support
Windows.

### Risk: permission boundary leakage

An MCP server can in principle expose tools that violate the
workstream's `permission_mode`. Layer 4 enforces `permission_mode`
at the runtime, but a malicious adapter could expose a "shell"
tool that bypasses the policy. Mitigation: bridge configs in
frontmatter list expected tools (an `expected_tools:` field, future
work); the runtime warns if the adapter exposes tools not on the
list. v1 keeps this advisory only.

### Risk: evidence non-determinism

`ArenaBenchScenarioRunExtractor` reads `time_to_goal_seconds` —
which depends on simulator wall-clock variation. Mitigation: seed
fixtures, declare nondeterministic fields in the schema as
`tolerance: { abs: 0.5 }`; the closure-check tooling can compare
within tolerance. Pass B flagged this for the analysis-corpus case
(model-stability tolerance); the same machinery applies.

### Risk: scope creep into being a robotics framework

The line is firm: Layer 6 adapts existing tools. It does not
implement scenarios, controllers, planners, or simulators. Anyone
adding code that does should write a separate proposal — that is
a different project.

## 15. References

[modelcontextprotocol.io][mcp] — protocol spec. Quote in §2:
"MCP follows a client-host-server architecture where each host can
run multiple client instances. This architecture enables users to
integrate AI capabilities across applications while maintaining
clear security boundaries and isolating concerns."

[modelcontextprotocol/python-sdk][mcp-py] — the Python MCP SDK
that Layer 4 imports. We hand it server configs; it does the rest.

[Tools list — MCP spec][mcp-tools-list] — `tools/list` request used
by the generic MCP adapter's health check.

[robotmcp/ros-mcp-server][ros-mcp] — third-party ROS↔MCP server
that `ros_adapter` wraps. Quote in §6.2: "ros-mcp-server is a
Model Context Protocol server that exposes ROS 2 topics, services,
and actions to MCP-compatible clients."

[ignc-research/arena-bench][arena-bench] — third-party benchmark
suite that `arena_bench_adapter` wraps. Quote in §6.3: "Arena-bench
is a benchmarking tool for navigation algorithms in Arena 4.0,
allowing users to compare different motion planners across multiple
scenarios using diverse evaluation metrics."

[Arena-Rosnav][arena-rosnav] — the simulator stack underneath
Arena-Bench.

[anthropics/claude-agent-sdk-python][cas] — the runtime that
consumes our `McpServerConfig` outputs.

`04_layer4_agent_runtime.md` (sibling proposal) — Layer 4. Defines
`RuntimeRequest.mcp_servers`, which Layer 6 populates.

`05_layer5_observability_and_evidence.md` (sibling proposal) —
Layer 5. Defines `EvidenceExtractor` and the per-evidence-kind
schema registry that bridge extractors register against.

`AGENTS.md` §"Architectural boundary" — "the architectural
boundary is enforced by code review." Layer 6 stays inside the
boundary by adapting rather than implementing simulator stacks.

`STYLE.md` §"Imports", §"Determinism" — both enforced in this
layer's tests.

[mcp]: https://modelcontextprotocol.io/
[mcp-py]: https://github.com/modelcontextprotocol/python-sdk
[mcp-tools-list]: https://modelcontextprotocol.io/specification/server/tools/
[ros-mcp]: https://github.com/robotmcp/ros-mcp-server
[arena-bench]: https://github.com/ignc-research/arena-bench
[arena-rosnav]: https://github.com/Arena-Rosnav/arena-rosnav
[cas]: https://github.com/anthropics/claude-agent-sdk-python
