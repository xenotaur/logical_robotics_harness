"""Design-proposal lifecycle bucket organization."""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any

from lrh.control import parser

STATUS_BUCKETS = {
    "proposed": "proposed",
    "adopted": "adopted",
    "accepted": "adopted",
    "rejected": "rejected",
    "superseded": "superseded",
}
IGNORED_FILENAMES = {"README.md", "index.md"}


@dataclasses.dataclass(frozen=True)
class DesignProposalPlan:
    """Planned organization action for one design-proposal file."""

    source: Path
    target: Path
    status: str | None
    skipped_reason: str | None = None
    blocking_errors: tuple[str, ...] = ()

    def needs_move(self) -> bool:
        return self.skipped_reason is None and self.source != self.target


@dataclasses.dataclass(frozen=True)
class OrganizationPlan:
    """Design-proposal organization plan for a project tree."""

    project_root: Path
    project_dir: Path
    proposals_dir: Path
    inspected: tuple[DesignProposalPlan, ...]

    def planned_moves(self) -> list[DesignProposalPlan]:
        return [item for item in self.inspected if item.needs_move()]


def plan_organization(project_root: Path) -> OrganizationPlan:
    """Build a deterministic design-proposal organization plan."""

    root = project_root.expanduser().resolve()
    project_dir = _project_dir(root)
    proposals_dir = project_dir / "design" / "proposals"
    if not proposals_dir.exists():
        return OrganizationPlan(root, project_dir, proposals_dir, ())

    planned_targets: set[Path] = set()
    plans: list[DesignProposalPlan] = []
    for path in sorted(proposals_dir.glob("**/*.md")):
        if _is_ignored_file(path):
            continue

        parsed = _parse_design_proposal(path)
        if parsed is None:
            continue

        data, parse_error = parsed
        if parse_error is not None:
            plans.append(
                DesignProposalPlan(
                    source=path,
                    target=path,
                    status=None,
                    skipped_reason=parse_error,
                )
            )
            continue

        assert data is not None
        status = data.get("status")
        metadata_error = _design_proposal_metadata_error(data)
        if metadata_error is not None:
            plans.append(
                DesignProposalPlan(
                    source=path,
                    target=path,
                    status=status if isinstance(status, str) else None,
                    skipped_reason=f"invalid proposal metadata: {metadata_error}",
                )
            )
            continue

        assert isinstance(status, str)
        bucket = STATUS_BUCKETS[status]

        target = proposals_dir / bucket / _proposal_relative_path(path, proposals_dir)
        blocking_errors: list[str] = []
        if target in planned_targets and target != path:
            blocking_errors.append(
                "target collision: another proposal maps to the same target"
            )
        if target.exists() and target != path:
            blocking_errors.append("target collision: target file already exists")
        planned_targets.add(target)
        plans.append(
            DesignProposalPlan(
                source=path,
                target=target,
                status=status,
                blocking_errors=tuple(blocking_errors),
            )
        )

    return OrganizationPlan(root, project_dir, proposals_dir, tuple(plans))


def apply_plan(plan: OrganizationPlan) -> None:
    """Apply safe design-proposal moves from a plan."""

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
        item.source.replace(item.target)


def build_text_report(plan: OrganizationPlan, applied: bool = False) -> str:
    """Format a human-readable, copy/paste-friendly organization report."""

    movable = [item for item in plan.planned_moves() if not item.blocking_errors]
    blocked = [item for item in plan.inspected if item.blocking_errors]
    skipped = [item for item in plan.inspected if item.skipped_reason]

    if not movable and not blocked and not skipped:
        return "Design proposals already organized."

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
            source = _relative_path(plan, item.source)
            target = _relative_path(plan, item.target)
            lines.append(f"  {source}")
            lines.append(f"  -> {target}")
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


def _format_move(plan: OrganizationPlan, item: DesignProposalPlan) -> list[str]:
    source = _relative_path(plan, item.source)
    target = _relative_path(plan, item.target)
    return [f"  {source}", f"  -> {target}"]


def _relative_path(plan: OrganizationPlan, path: Path) -> Path:
    try:
        return path.resolve().relative_to(plan.project_root)
    except ValueError:
        return path


def _proposal_relative_path(path: Path, proposals_dir: Path) -> Path:
    relative = path.relative_to(proposals_dir)
    if relative.parts and relative.parts[0] in STATUS_BUCKETS.values():
        return Path(*relative.parts[1:])
    return relative


def _project_dir(root: Path) -> Path:
    if (root / "design" / "proposals").exists():
        return root
    return root / "project"


def _is_ignored_file(path: Path) -> bool:
    return path.name in IGNORED_FILENAMES


def _parse_design_proposal(
    path: Path,
) -> tuple[dict[str, Any] | None, str | None] | None:
    try:
        parsed = parser.parse_markdown_file(path)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return None, f"invalid proposal metadata: {exc}"

    data = parsed.frontmatter
    if not _is_design_proposal(data):
        return None
    return data, None


def _is_design_proposal(data: dict[str, Any]) -> bool:
    return (
        data.get("type") == "design_proposal" or data.get("kind") == "design_proposal"
    )


def _design_proposal_metadata_error(data: dict[str, Any]) -> str | None:
    artifact_type = data.get("type")
    kind = data.get("kind")
    if artifact_type is not None and artifact_type != "design_proposal":
        return "type must be design_proposal when present"
    if kind is not None and kind != "design_proposal":
        return "kind must be design_proposal when present"
    if artifact_type is not None and kind is not None and artifact_type != kind:
        return "type and kind must agree when both are present"
    if not isinstance(data.get("id"), str):
        return "id is required"

    status = data.get("status")
    if not isinstance(status, str):
        return "status is required"
    if status not in STATUS_BUCKETS:
        return f"unsupported status '{status}'"
    return None
