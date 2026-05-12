"""Workstream lifecycle bucket organization."""

from __future__ import annotations

import dataclasses
from pathlib import Path

from lrh.control import loader

STATUS_BUCKETS = {
    "proposed": "proposed",
    "active": "active",
    "resolved": "resolved",
    "abandoned": "abandoned",
}


@dataclasses.dataclass(frozen=True)
class WorkstreamPlan:
    """Planned organization action for one workstream file."""

    source: Path
    target: Path
    workstream_id: str | None
    status: str | None
    skipped_reason: str | None = None
    blocking_errors: tuple[str, ...] = ()

    def needs_move(self) -> bool:
        return self.skipped_reason is None and self.source != self.target


@dataclasses.dataclass(frozen=True)
class OrganizationPlan:
    """Workstream organization plan for a project tree."""

    project_root: Path
    project_dir: Path
    workstreams_dir: Path
    inspected: tuple[WorkstreamPlan, ...]

    def planned_moves(self) -> list[WorkstreamPlan]:
        return [item for item in self.inspected if item.needs_move()]


def plan_organization(project_root: Path) -> OrganizationPlan:
    """Build a deterministic workstream organization plan."""

    root = project_root.expanduser().resolve()
    project_dir = _project_dir(root)
    workstreams_dir = project_dir / "workstreams"
    if not workstreams_dir.exists():
        return OrganizationPlan(root, project_dir, workstreams_dir, ())

    workstreams, warnings = loader.load_workstreams_from_project_dir_permissive(
        project_dir
    )
    plans: list[WorkstreamPlan] = []
    for warning in warnings:
        path = _path_from_warning(workstreams_dir, warning)
        plans.append(
            WorkstreamPlan(
                source=path,
                target=path,
                workstream_id=None,
                status=None,
                skipped_reason=f"invalid workstream metadata: {warning}",
            )
        )

    planned_targets: set[Path] = set()
    for workstream in workstreams:
        status = workstream.status
        if status not in STATUS_BUCKETS:
            plans.append(
                WorkstreamPlan(
                    source=workstream.path,
                    target=workstream.path,
                    workstream_id=workstream.id,
                    status=status,
                    skipped_reason=(
                        "invalid workstream metadata: " f"unsupported status '{status}'"
                    ),
                )
            )
            continue

        target = workstreams_dir / STATUS_BUCKETS[status] / workstream.path.name
        blocking_errors: list[str] = []
        if target in planned_targets and target != workstream.path:
            blocking_errors.append(
                "target collision: another workstream maps to the same target"
            )
        if target.exists() and target != workstream.path:
            blocking_errors.append("target collision: target file already exists")
        planned_targets.add(target)
        plans.append(
            WorkstreamPlan(
                source=workstream.path,
                target=target,
                workstream_id=workstream.id,
                status=status,
                blocking_errors=tuple(blocking_errors),
            )
        )

    plans.sort(key=lambda item: _sort_key(root, item))
    return OrganizationPlan(root, project_dir, workstreams_dir, tuple(plans))


def apply_plan(plan: OrganizationPlan) -> None:
    """Apply safe workstream moves from a plan."""

    blocked = [
        item for item in plan.inspected if item.needs_move() and item.blocking_errors
    ]
    if blocked:
        item = blocked[0]
        raise ValueError(
            f"refusing to move {item.source}: {'; '.join(item.blocking_errors)}"
        )

    for item in plan.inspected:
        if item.skipped_reason or not item.needs_move():
            continue
        item.target.parent.mkdir(parents=True, exist_ok=True)
        if item.target.exists():
            raise ValueError(f"refusing to overwrite existing target {item.target}")
        item.source.replace(item.target)


def build_text_report(plan: OrganizationPlan, applied: bool = False) -> str:
    """Format a human-readable workstream organization report."""

    movable = [item for item in plan.planned_moves() if not item.blocking_errors]
    blocked = [item for item in plan.inspected if item.blocking_errors]
    skipped = [item for item in plan.inspected if item.skipped_reason]

    if not movable and not blocked and not skipped:
        return "Workstreams already organized."

    lines: list[str] = []
    if movable:
        lines.append("Moved:" if applied else "Would move:")
        for item in movable:
            lines.extend(_format_move(plan, item))
    if blocked:
        if lines:
            lines.append("")
        lines.append("Blocked:")
        for item in blocked:
            lines.extend(_format_move(plan, item))
            lines.append(f"  reason: {'; '.join(item.blocking_errors)}")
    if skipped:
        if lines:
            lines.append("")
        lines.append("Skipped:")
        for item in skipped:
            source = _relative_path(plan, item.source)
            lines.append(f"  {source}")
            lines.append(f"  reason: {item.skipped_reason}")
    return "\n".join(lines)


def _format_move(plan: OrganizationPlan, item: WorkstreamPlan) -> list[str]:
    source = _relative_path(plan, item.source)
    target = _relative_path(plan, item.target)
    return [f"  {source}", f"  -> {target}"]


def _relative_path(plan: OrganizationPlan, path: Path) -> Path:
    try:
        return path.resolve().relative_to(plan.project_root)
    except ValueError:
        return path


def _project_dir(root: Path) -> Path:
    if (root / "workstreams").exists():
        return root
    return root / "project"


def _path_from_warning(workstreams_dir: Path, warning: str) -> Path:
    prefix = "Skipped "
    marker = ": "
    if warning.startswith(prefix) and marker in warning:
        relative = warning[len(prefix) : warning.index(marker)]
        return workstreams_dir / relative
    return workstreams_dir


def _sort_key(project_root: Path, item: WorkstreamPlan) -> str:
    try:
        return item.source.resolve().relative_to(project_root).as_posix()
    except ValueError:
        return item.source.as_posix()
