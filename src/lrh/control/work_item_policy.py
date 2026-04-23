"""Work-item status bucket policy validation scaffolding.

This module provides a first-pass, typed validation surface for the work-item
bucket model documented in project/design/design.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

WORK_ITEM_BUCKETS = ("proposed", "active", "resolved", "abandoned")
TERMINAL_WORK_ITEM_STATUSES = ("resolved", "abandoned")


@dataclass(frozen=True)
class WorkItemPolicyIssue:
    """A single work-item policy validation finding."""

    severity: str
    code: str
    message: str
    file: str


@dataclass(frozen=True)
class WorkItemPolicyResult:
    """Aggregate policy findings for one or more work items."""

    issues: tuple[WorkItemPolicyIssue, ...]

    @property
    def errors(self) -> tuple[WorkItemPolicyIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "error")

    @property
    def warnings(self) -> tuple[WorkItemPolicyIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "warning")

    @property
    def is_valid(self) -> bool:
        return not self.errors


@dataclass(frozen=True)
class WorkItemPathContext:
    """Derived location metadata for a work-item markdown file."""

    file: Path
    filename_stem: str
    bucket: str | None


def derive_work_item_path_context(
    project_dir: Path, work_item_file: Path
) -> WorkItemPathContext:
    """Build normalized, policy-relevant location context for a work item."""

    work_items_dir = project_dir / "work_items"
    file_path = work_item_file.resolve()
    bucket: str | None = None
    try:
        relative = file_path.relative_to(work_items_dir.resolve())
    except ValueError:
        relative = None

    if relative is not None and len(relative.parts) >= 2:
        candidate = relative.parts[0]
        if candidate in WORK_ITEM_BUCKETS:
            bucket = candidate

    return WorkItemPathContext(
        file=work_item_file,
        filename_stem=work_item_file.stem,
        bucket=bucket,
    )


def validate_work_item_policy(
    project_dir: Path,
    work_item_file: Path,
    metadata: dict[str, Any],
) -> WorkItemPolicyResult:
    """Validate one work-item metadata/path pair against bucket policy rules."""

    issues: list[WorkItemPolicyIssue] = []
    path_context = derive_work_item_path_context(project_dir, work_item_file)

    status = metadata.get("status")
    if status is None:
        issues.append(
            _issue(
                path_context.file,
                "error",
                "WORK_ITEM_STATUS_REQUIRED",
                "work item metadata must include a status",
            )
        )
    elif status not in WORK_ITEM_BUCKETS:
        allowed = ", ".join(WORK_ITEM_BUCKETS)
        issues.append(
            _issue(
                path_context.file,
                "error",
                "WORK_ITEM_STATUS_INVALID",
                f"status must be one of: {allowed}",
            )
        )

    work_item_id = metadata.get("id")
    if isinstance(work_item_id, str):
        if work_item_id != path_context.filename_stem:
            issues.append(
                _issue(
                    path_context.file,
                    "error",
                    "WORK_ITEM_ID_FILENAME_MISMATCH",
                    (
                        f"filename stem '{path_context.filename_stem}' does not "
                        f"match id '{work_item_id}'"
                    ),
                )
            )

    blocked = metadata.get("blocked")
    if blocked is not None and not isinstance(blocked, bool):
        issues.append(
            _issue(
                path_context.file,
                "error",
                "WORK_ITEM_BLOCKED_NOT_BOOLEAN",
                "blocked must be a boolean when provided",
            )
        )

    blocked_reason = metadata.get("blocked_reason")
    if blocked is True:
        if status != "active":
            issues.append(
                _issue(
                    path_context.file,
                    "error",
                    "WORK_ITEM_BLOCKED_STATUS_INVALID",
                    "blocked may only be true when status is 'active'",
                )
            )
        if not isinstance(blocked_reason, str) or not blocked_reason.strip():
            issues.append(
                _issue(
                    path_context.file,
                    "error",
                    "WORK_ITEM_BLOCKED_REASON_REQUIRED",
                    "blocked_reason is required when blocked is true",
                )
            )

    if status in TERMINAL_WORK_ITEM_STATUSES:
        resolution = metadata.get("resolution")
        if not isinstance(resolution, str) or not resolution.strip():
            issues.append(
                _issue(
                    path_context.file,
                    "error",
                    "WORK_ITEM_RESOLUTION_REQUIRED",
                    "terminal statuses require a non-empty resolution",
                )
            )

    if path_context.bucket is None:
        issues.append(
            _issue(
                path_context.file,
                "error",
                "WORK_ITEM_BUCKET_INVALID",
                "work item must be located under a recognized status bucket directory",
            )
        )
    elif (
        isinstance(status, str)
        and status in WORK_ITEM_BUCKETS
        and status != path_context.bucket
    ):
        issues.append(
            _issue(
                path_context.file,
                "error",
                "WORK_ITEM_BUCKET_STATUS_MISMATCH",
                (
                    f"directory bucket '{path_context.bucket}' does not match "
                    f"status '{status}'"
                ),
            )
        )

    return WorkItemPolicyResult(issues=tuple(issues))


def validate_work_item_collection(
    project_dir: Path,
    items: list[tuple[Path, dict[str, Any]]],
) -> WorkItemPolicyResult:
    """Validate multiple work items, including ID uniqueness across the set."""

    issues: list[WorkItemPolicyIssue] = []
    seen_ids: dict[str, Path] = {}

    for work_item_file, metadata in items:
        item_result = validate_work_item_policy(project_dir, work_item_file, metadata)
        issues.extend(item_result.issues)

        work_item_id = metadata.get("id")
        if not isinstance(work_item_id, str):
            continue
        previous = seen_ids.get(work_item_id)
        if previous is not None:
            issues.append(
                _issue(
                    work_item_file,
                    "error",
                    "WORK_ITEM_ID_DUPLICATE",
                    f"duplicate work item id '{work_item_id}' also found at {previous}",
                )
            )
        else:
            seen_ids[work_item_id] = work_item_file

    return WorkItemPolicyResult(issues=tuple(issues))


def _issue(path: Path, severity: str, code: str, message: str) -> WorkItemPolicyIssue:
    return WorkItemPolicyIssue(
        severity=severity, code=code, message=message, file=str(path)
    )
