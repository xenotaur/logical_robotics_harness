"""Deterministic work-item prompt-readiness diagnostics."""

from __future__ import annotations

import dataclasses
import json
import pathlib

from lrh.assist import work_item_prompt_core
from lrh.work_items import validate as work_items_validate

_SCHEMA_VERSION = "1.0"
_ALLOWED_STATUS_FILTERS = ("proposed", "active", "resolved", "abandoned")


@dataclasses.dataclass(frozen=True)
class WorkItemReadinessItem:
    work_item_id: str
    path: str
    status: str
    prompt_ready: bool
    blocking_reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    recommended_next: str | None


@dataclasses.dataclass(frozen=True)
class WorkItemReadinessReport:
    project_root: pathlib.Path
    items: tuple[WorkItemReadinessItem, ...]

    @property
    def summary(self) -> dict[str, int]:
        ready_count = sum(1 for item in self.items if item.prompt_ready)
        return {
            "items_checked": len(self.items),
            "ready": ready_count,
            "not_ready": len(self.items) - ready_count,
        }


def evaluate_readiness(
    *,
    project_root: pathlib.Path,
    work_item_id: str | None = None,
    status: str | None = None,
) -> WorkItemReadinessReport:
    if status is not None and status not in _ALLOWED_STATUS_FILTERS:
        raise ValueError(f"unsupported status filter: {status}")

    work_items_root = project_root / "project" / "work_items"
    if not work_items_root.is_dir():
        return WorkItemReadinessReport(project_root=project_root, items=())

    selected_paths = []
    for path in work_items_validate.discover_work_item_paths(work_items_root):
        parsed = work_item_prompt_core.parse_work_item_markdown(path)
        if work_item_id is not None and parsed.work_item_id != work_item_id:
            continue
        if status is not None and parsed.status != status:
            continue
        selected_paths.append(path)

    items = [_build_item(project_root, path) for path in selected_paths]
    return WorkItemReadinessReport(project_root=project_root, items=tuple(items))


def format_json(report: WorkItemReadinessReport) -> str:
    payload = {
        "schema_version": _SCHEMA_VERSION,
        "summary": report.summary,
        "items": [
            {
                "id": item.work_item_id,
                "path": item.path,
                "status": item.status,
                "prompt_ready": item.prompt_ready,
                "blocking_reasons": list(item.blocking_reasons),
                "warnings": list(item.warnings),
                "recommended_next": item.recommended_next,
            }
            for item in report.items
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def format_markdown(report: WorkItemReadinessReport) -> str:
    lines = [
        "# Work Item Readiness",
        "",
        "## Summary",
        "",
        f"- Items checked: {report.summary['items_checked']}",
        f"- Ready: {report.summary['ready']}",
        f"- Not ready: {report.summary['not_ready']}",
        "",
    ]
    for item in report.items:
        lines.extend(
            [
                f"## {item.work_item_id}",
                f"status: {item.status}",
                f"prompt_ready: {'yes' if item.prompt_ready else 'no'}",
                "blocking:",
            ]
        )
        if item.blocking_reasons:
            lines.extend(f"  - {reason}" for reason in item.blocking_reasons)
        else:
            lines.append("  - none")
        lines.append("warnings:")
        if item.warnings:
            lines.extend(f"  - {warning}" for warning in item.warnings)
        else:
            lines.append("  - none")
        lines.append("recommended_next:")
        if item.recommended_next is None:
            lines.append("  - none")
        else:
            lines.append(f"  {item.recommended_next}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _build_item(
    project_root: pathlib.Path, path: pathlib.Path
) -> WorkItemReadinessItem:
    parsed = work_item_prompt_core.parse_work_item_markdown(path)
    readiness = work_item_prompt_core.evaluate_prompt_readiness(parsed)
    recommended_next = None
    if not readiness.is_ready:
        recommended_next = f"lrh request ready-work-item {parsed.work_item_id}"
    return WorkItemReadinessItem(
        work_item_id=parsed.work_item_id,
        path=path.relative_to(project_root).as_posix(),
        status=parsed.status,
        prompt_ready=readiness.is_ready,
        blocking_reasons=readiness.blocking_reasons,
        warnings=readiness.warnings,
        recommended_next=recommended_next,
    )
