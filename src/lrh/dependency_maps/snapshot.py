"""Build and serialize the versioned ``DependencyMapSnapshot``.

The snapshot is a read-only projection of a project's work items through a
view declaration. Every derived field says where it came from, nothing is
inferred silently, and no absolute local path is exported.

Structural state follows the Revision 2 precedence: Done, then Blocked (the
item's own ``blocked`` flag, or a ``blocked_by`` target that is not done), then
In progress, Waiting (a ``depends_on`` prerequisite is not done), and
Unblocked. An abandoned item is never Done or Unblocked, and an abandoned or
missing prerequisite never counts as done. Lifecycle, prompt-readiness, and
authorization are separate layers; authorization is never derived.
"""

from __future__ import annotations

import dataclasses
import datetime
import hashlib
import json
import pathlib
import subprocess
from typing import Any

from lrh.control import loader
from lrh.control.models import WorkItem
from lrh.dependency_maps import view as view_module
from lrh.work_items import readiness

SCHEMA_VERSION = 1
UNPLACED = "unplaced"
EDGE_KINDS = ("depends_on", "blocked_by")
STATES = ("done", "blocked", "in_progress", "waiting", "unblocked", "abandoned")
_FINGERPRINT_GLOBS = (
    "project/work_items/**/*.md",
    "project/workstreams/**/*.md",
    "project/views/dependency_maps/*.md",
)


class SnapshotError(RuntimeError):
    """The project's control files could not be loaded at all."""


@dataclasses.dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: str
    message: str
    subjects: tuple[str, ...] = ()


@dataclasses.dataclass(frozen=True)
class StateReason:
    """Why a node has its structural state."""

    kind: str
    target: str | None = None
    target_lifecycle: str | None = None
    detail: str | None = None


@dataclasses.dataclass(frozen=True)
class Node:
    id: str
    title: str
    lifecycle: str
    source: str
    offscreen: bool
    lane: str | None
    lane_source: str
    lane_reason: str | None
    phase: str | None
    phase_source: str
    state: str
    state_reasons: tuple[StateReason, ...]
    prompt_ready: bool | None
    prompt_ready_source: str
    authorization: str
    offscreen_predecessors: int


@dataclasses.dataclass(frozen=True)
class Edge:
    """``item`` declares ``kind`` on ``target``; ``resolved`` is False if missing."""

    kind: str
    item: str
    target: str
    resolved: bool
    source: str


@dataclasses.dataclass(frozen=True)
class Row:
    """A lane or a phase, in view order; ``unplaced`` marks the catch-all row."""

    id: str
    title: str
    unplaced: bool = False


@dataclasses.dataclass(frozen=True)
class ProjectIdentity:
    name: str
    checkout_id: str
    head: str | None


@dataclasses.dataclass(frozen=True)
class DependencyMapSnapshot:
    schema_version: int
    view_id: str
    view_title: str
    view_source: str
    project: ProjectIdentity
    source_fingerprint: str
    generated_at: str
    lanes: tuple[Row, ...]
    phases: tuple[Row, ...]
    nodes: tuple[Node, ...]
    edges: tuple[Edge, ...]
    diagnostics: tuple[Diagnostic, ...]

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DependencyMapSnapshot:
        if data.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(
                f"unsupported schema_version {data.get('schema_version')!r}"
            )
        return cls(
            schema_version=data["schema_version"],
            view_id=data["view_id"],
            view_title=data["view_title"],
            view_source=data["view_source"],
            project=ProjectIdentity(**data["project"]),
            source_fingerprint=data["source_fingerprint"],
            generated_at=data["generated_at"],
            lanes=tuple(Row(**row) for row in data["lanes"]),
            phases=tuple(Row(**row) for row in data["phases"]),
            nodes=tuple(
                Node(
                    **{
                        **node,
                        "state_reasons": tuple(
                            StateReason(**reason) for reason in node["state_reasons"]
                        ),
                    }
                )
                for node in data["nodes"]
            ),
            edges=tuple(Edge(**edge) for edge in data["edges"]),
            diagnostics=tuple(
                Diagnostic(**{**item, "subjects": tuple(item["subjects"])})
                for item in data["diagnostics"]
            ),
        )


def source_fingerprint(repo_root: pathlib.Path) -> str:
    """Hash the control files' relative paths and contents, so uncommitted
    edits change it too (a Git HEAD alone would not)."""

    digest = hashlib.sha256()
    paths = sorted(
        {path for pattern in _FINGERPRINT_GLOBS for path in repo_root.glob(pattern)}
    )
    for path in paths:
        if not path.is_file():
            continue
        digest.update(path.relative_to(repo_root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def freshness_diagnostics(
    snapshot: DependencyMapSnapshot, repo_root: pathlib.Path
) -> tuple[Diagnostic, ...]:
    """Return a ``stale_snapshot`` diagnostic if the sources changed since."""

    current = source_fingerprint(repo_root)
    if current == snapshot.source_fingerprint:
        return ()
    return (
        Diagnostic(
            code="stale_snapshot",
            severity="warning",
            message=(
                f"the control files changed after this snapshot was generated "
                f"at {snapshot.generated_at}; refresh before relying on it"
            ),
        ),
    )


def build_snapshot(
    repo_root: pathlib.Path,
    view_id: str,
    *,
    now: datetime.datetime | None = None,
) -> DependencyMapSnapshot:
    """Project ``repo_root``'s work items through the named view.

    Raises FileNotFoundError for an unknown view, ViewDeclarationError for a
    malformed one, and SnapshotError if the control files cannot be loaded.
    """

    repo_root = repo_root.resolve()
    declaration = view_module.load_view(repo_root, view_id)
    try:
        state = loader.load_project(repo_root)
    except (OSError, ValueError) as err:
        raise SnapshotError(f"could not load project control files: {err}") from err

    items = state.work_items_by_id
    workstreams = state.workstreams_by_id
    diagnostics: list[Diagnostic] = [
        Diagnostic(code="unknown_view_reference", severity="error", message=problem)
        for problem in view_module.reference_problems(
            declaration, set(items), set(workstreams)
        )
    ]

    lane_ids = [lane.workstream for lane in declaration.lanes]
    members: dict[str, list[str]] = {}
    for lane_id in lane_ids:
        workstream = workstreams.get(lane_id)
        listed = set(workstream.work_items) if workstream else set()
        for item in items.values():
            if item.id in listed or item.parent_id == lane_id:
                members.setdefault(item.id, []).append(lane_id)

    phase_of: dict[str, list[str]] = {}
    for phase in declaration.phases:
        for item_id in phase.work_items:
            if item_id in items:
                phase_of.setdefault(item_id, []).append(phase.id)

    in_view = sorted(set(members) | set(phase_of))
    overrides = {
        override.work_item: override
        for override in declaration.lane_overrides
        if override.work_item in items and override.lane in lane_ids
    }

    prompt_ready, readiness_problem = _prompt_readiness(repo_root)
    if readiness_problem:
        diagnostics.append(
            Diagnostic(
                code="partial_source",
                severity="warning",
                message=f"prompt readiness is unavailable: {readiness_problem}",
            )
        )

    edges: list[Edge] = []
    offscreen: set[str] = set()
    for item_id in in_view:
        item = items[item_id]
        for kind in EDGE_KINDS:
            for target in getattr(item, kind):
                resolved = target in items
                edges.append(
                    Edge(
                        kind=kind,
                        item=item_id,
                        target=target,
                        resolved=resolved,
                        source=_relative(item, repo_root),
                    )
                )
                if not resolved:
                    diagnostics.append(
                        Diagnostic(
                            code="missing_reference",
                            severity="error",
                            message=f"{item_id} {kind} {target}, which does not exist",
                            subjects=(item_id, target),
                        )
                    )
                elif target not in phase_of and target not in members:
                    offscreen.add(target)

    nodes: list[Node] = []
    for item_id in in_view:
        item = items[item_id]
        lane, lane_source, lane_reason = _place_lane(
            item_id, members.get(item_id, []), overrides.get(item_id), diagnostics
        )
        phase, phase_source = _place_phase(
            item_id, phase_of.get(item_id, []), diagnostics
        )
        nodes.append(
            _node(
                item,
                items,
                repo_root,
                prompt_ready,
                offscreen=False,
                lane=lane,
                lane_source=lane_source,
                lane_reason=lane_reason,
                phase=phase,
                phase_source=phase_source,
                offscreen_count=sum(
                    1
                    for edge in edges
                    if edge.item == item_id and edge.target in offscreen
                ),
            )
        )
    for item_id in sorted(offscreen):
        nodes.append(
            _node(
                items[item_id],
                items,
                repo_root,
                prompt_ready,
                offscreen=True,
                lane=None,
                lane_source="offscreen",
                lane_reason="referenced by an item in this view",
                phase=None,
                phase_source="offscreen",
                offscreen_count=0,
            )
        )

    diagnostics.extend(_cycle_diagnostics(items, in_view))

    lanes = [
        Row(
            id=lane.workstream,
            title=lane.title
            or (
                workstreams[lane.workstream].title
                if lane.workstream in workstreams
                else lane.workstream
            ),
        )
        for lane in declaration.lanes
    ]
    if any(node.lane is None and not node.offscreen for node in nodes):
        lanes.append(Row(id=UNPLACED, title="Unplaced", unplaced=True))
    phases = [Row(id=phase.id, title=phase.title) for phase in declaration.phases]
    phases.append(Row(id=UNPLACED, title="Unplaced", unplaced=True))

    generated = (now or datetime.datetime.now(datetime.UTC)).astimezone(datetime.UTC)
    return DependencyMapSnapshot(
        schema_version=SCHEMA_VERSION,
        view_id=declaration.id,
        view_title=declaration.title,
        view_source=declaration.source,
        project=_identity(repo_root),
        source_fingerprint=source_fingerprint(repo_root),
        generated_at=generated.isoformat(timespec="seconds"),
        lanes=tuple(lanes),
        phases=tuple(phases),
        nodes=tuple(nodes),
        edges=tuple(edges),
        diagnostics=tuple(diagnostics),
    )


def structural_state(
    item: WorkItem, items: dict[str, WorkItem]
) -> tuple[str, tuple[StateReason, ...]]:
    """Return an item's structural state and the reasons for it."""

    if item.status == "resolved":
        return "done", (StateReason(kind="lifecycle", detail="resolved"),)
    if item.status == "abandoned":
        return "abandoned", (StateReason(kind="lifecycle", detail="abandoned"),)
    blockers: list[StateReason] = []
    if item.blocked:
        blockers.append(StateReason(kind="blocked_flag", detail=item.blocked_reason))
    blockers.extend(_unmet(item.blocked_by, "blocked_by", items))
    if blockers:
        return "blocked", tuple(blockers)
    if item.status == "active":
        return "in_progress", (StateReason(kind="lifecycle", detail="active"),)
    waiting = _unmet(item.depends_on, "depends_on", items)
    if waiting:
        return "waiting", tuple(waiting)
    return "unblocked", tuple(
        StateReason(kind="depends_on", target=target, target_lifecycle="resolved")
        for target in item.depends_on
    )


def _unmet(
    targets: tuple[str, ...], kind: str, items: dict[str, WorkItem]
) -> list[StateReason]:
    reasons = []
    for target in targets:
        found = items.get(target)
        lifecycle = found.status if found else "missing"
        if lifecycle != "resolved":
            reasons.append(
                StateReason(kind=kind, target=target, target_lifecycle=lifecycle)
            )
    return reasons


def _node(
    item: WorkItem,
    items: dict[str, WorkItem],
    repo_root: pathlib.Path,
    prompt_ready: dict[str, bool] | None,
    *,
    offscreen: bool,
    lane: str | None,
    lane_source: str,
    lane_reason: str | None,
    phase: str | None,
    phase_source: str,
    offscreen_count: int,
) -> Node:
    state, reasons = structural_state(item, items)
    return Node(
        id=item.id,
        title=item.title,
        lifecycle=item.status,
        source=_relative(item, repo_root),
        offscreen=offscreen,
        lane=lane,
        lane_source=lane_source,
        lane_reason=lane_reason,
        phase=phase,
        phase_source=phase_source,
        state=state,
        state_reasons=reasons,
        prompt_ready=None if prompt_ready is None else prompt_ready.get(item.id),
        prompt_ready_source="lrh work-items readiness",
        authorization="not_derived",
        offscreen_predecessors=offscreen_count,
    )


def _place_lane(
    item_id: str,
    lanes: list[str],
    override: view_module.LaneOverride | None,
    diagnostics: list[Diagnostic],
) -> tuple[str | None, str, str | None]:
    if override is not None:
        return override.lane, "override", override.reason
    if len(lanes) == 1:
        return lanes[0], "workstream", None
    if lanes:
        diagnostics.append(
            Diagnostic(
                code="ambiguous_lane",
                severity="warning",
                message=(
                    f"{item_id} belongs to {', '.join(lanes)}; add a lane_override "
                    "with a reason to choose one"
                ),
                subjects=(item_id, *lanes),
            )
        )
        return None, "ambiguous", None
    diagnostics.append(
        Diagnostic(
            code="unplaced_lane",
            severity="warning",
            message=f"{item_id} is in no lane of this view",
            subjects=(item_id,),
        )
    )
    return None, "none", None


def _place_phase(
    item_id: str, phases: list[str], diagnostics: list[Diagnostic]
) -> tuple[str, str]:
    if len(phases) == 1:
        return phases[0], "declared"
    if phases:
        diagnostics.append(
            Diagnostic(
                code="ambiguous_phase",
                severity="warning",
                message=f"{item_id} is listed in phases {', '.join(phases)}",
                subjects=(item_id, *phases),
            )
        )
        return UNPLACED, "ambiguous"
    diagnostics.append(
        Diagnostic(
            code="unplaced_phase",
            severity="info",
            message=f"{item_id} is in no phase and shows in the Unplaced row",
            subjects=(item_id,),
        )
    )
    return UNPLACED, "none"


def _cycle_diagnostics(
    items: dict[str, WorkItem], in_view: list[str]
) -> list[Diagnostic]:
    """Report cycles separately per edge kind; the kinds mean different things."""

    diagnostics = []
    for kind in EDGE_KINDS:
        graph = {
            item_id: [target for target in getattr(item, kind) if target in items]
            for item_id, item in items.items()
        }
        view_ids = set(in_view)
        for component in _strongly_connected(graph):
            cyclic = len(component) > 1 or component[0] in graph[component[0]]
            if cyclic and view_ids.intersection(component):
                members = tuple(sorted(component))
                diagnostics.append(
                    Diagnostic(
                        code="cycle",
                        severity="error",
                        message=f"{kind} cycle: {' -> '.join(members)}",
                        subjects=members,
                    )
                )
    return diagnostics


def _strongly_connected(graph: dict[str, list[str]]) -> list[list[str]]:
    """Tarjan's algorithm, iterative so deep chains cannot hit the recursion limit."""

    index: dict[str, int] = {}
    low: dict[str, int] = {}
    on_stack: set[str] = set()
    stack: list[str] = []
    components: list[list[str]] = []
    counter = 0
    for root in sorted(graph):
        if root in index:
            continue
        work = [(root, 0)]
        while work:
            node, child = work.pop()
            if child == 0:
                index[node] = low[node] = counter
                counter += 1
                stack.append(node)
                on_stack.add(node)
            targets = graph[node]
            if child < len(targets):
                work.append((node, child + 1))
                target = targets[child]
                if target not in index:
                    work.append((target, 0))
                elif target in on_stack:
                    low[node] = min(low[node], index[target])
                continue
            if low[node] == index[node]:
                component = []
                while True:
                    member = stack.pop()
                    on_stack.discard(member)
                    component.append(member)
                    if member == node:
                        break
                components.append(component)
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[node])
    return components


def _prompt_readiness(
    repo_root: pathlib.Path,
) -> tuple[dict[str, bool] | None, str | None]:
    try:
        report = readiness.evaluate_readiness(project_root=repo_root)
    except (readiness.WorkItemReadinessError, OSError, ValueError) as err:
        return None, str(err)
    return {item.work_item_id: item.prompt_ready for item in report.items}, None


def _relative(item: WorkItem, repo_root: pathlib.Path) -> str:
    try:
        return item.path.resolve().relative_to(repo_root).as_posix()
    except ValueError:
        return item.path.name


def _identity(repo_root: pathlib.Path) -> ProjectIdentity:
    checkout = hashlib.sha256(str(repo_root).encode("utf-8")).hexdigest()[:16]
    head: str | None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        head = (result.stdout.strip() or None) if result.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        head = None
    return ProjectIdentity(
        name=repo_root.name, checkout_id=f"local:{checkout}", head=head
    )
