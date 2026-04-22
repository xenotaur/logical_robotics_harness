"""Project-directory loader for a minimal LRH control-plane runtime state."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lrh.control.models import Contributor, Focus, ProjectState, WorkItem
from lrh.control.parser import ParsedMarkdown, parse_markdown_file


def find_project_dir(root: Path) -> Path:
    """Find the project directory from either repo root or project root."""

    resolved = root.resolve()
    if (resolved / "focus").exists() and (resolved / "work_items").exists():
        return resolved

    candidate = resolved / "project"
    if (candidate / "focus").exists() and (candidate / "work_items").exists():
        return candidate

    raise FileNotFoundError(f"could not locate project directory from: {root}")


def load_project(root: Path) -> ProjectState:
    project_dir = find_project_dir(root)
    current_focus = _load_focus(project_dir / "focus" / "current_focus.md")

    work_items = _load_work_items(project_dir / "work_items")
    work_items_by_id = _index_by_id(work_items, artifact_label="work item")

    contributors = _load_contributors(project_dir / "contributors")
    contributors_by_id = _index_by_id(contributors, artifact_label="contributor")

    return ProjectState(
        project_dir=project_dir,
        current_focus=current_focus,
        work_items=work_items,
        work_items_by_id=work_items_by_id,
        contributors=contributors,
        contributors_by_id=contributors_by_id,
    )


def _load_focus(path: Path) -> Focus:
    parsed = parse_markdown_file(path)
    fm = parsed.frontmatter
    return Focus(
        path=path,
        id=_required_str(fm, "id", path),
        title=_required_str(fm, "title", path),
        status=_required_str(fm, "status", path),
        priority=_optional_str(fm, "priority"),
        owner=_optional_str(fm, "owner"),
        related_principles=_list_of_strings(fm, "related_principles"),
        body=parsed.body,
        frontmatter=fm,
    )


def _load_work_items(directory: Path) -> tuple[WorkItem, ...]:
    items: list[WorkItem] = []
    for path in sorted(directory.glob("WI-*.md")):
        parsed = parse_markdown_file(path)
        fm = parsed.frontmatter
        items.append(
            WorkItem(
                path=path,
                id=_required_str(fm, "id", path),
                title=_required_str(fm, "title", path),
                type=_required_str(fm, "type", path),
                status=_required_str(fm, "status", path),
                priority=_optional_str(fm, "priority"),
                owner=_optional_str(fm, "owner"),
                contributors=_list_of_strings(fm, "contributors"),
                assigned_agents=_list_of_strings(fm, "assigned_agents"),
                related_focus=_list_of_strings(fm, "related_focus"),
                related_roadmap=_list_of_strings(fm, "related_roadmap"),
                depends_on=_list_of_strings(fm, "depends_on"),
                blocked_by=_list_of_strings(fm, "blocked_by"),
                expected_actions=_list_of_strings(fm, "expected_actions"),
                forbidden_actions=_list_of_strings(fm, "forbidden_actions"),
                acceptance=_list_of_strings(fm, "acceptance"),
                required_evidence=_list_of_strings(fm, "required_evidence"),
                artifacts_expected=_list_of_strings(fm, "artifacts_expected"),
                body=parsed.body,
                frontmatter=fm,
            )
        )
    return tuple(items)


def _load_contributors(directory: Path) -> tuple[Contributor, ...]:
    contributors: list[Contributor] = []
    for path in sorted(directory.glob("**/*.md")):
        parsed = parse_markdown_file(path)
        fm = parsed.frontmatter
        if "id" not in fm:
            continue
        contributors.append(_contributor_from_parsed(path, parsed))
    return tuple(contributors)


def _contributor_from_parsed(path: Path, parsed: ParsedMarkdown) -> Contributor:
    fm = parsed.frontmatter
    return Contributor(
        path=path,
        id=_required_str(fm, "id", path),
        type=_required_str(fm, "type", path),
        roles=_list_of_strings(fm, "roles"),
        display_name=_required_str(fm, "display_name", path),
        status=_required_str(fm, "status", path),
        email=_optional_str(fm, "email"),
        github=_optional_str(fm, "github"),
        execution_mode=_optional_str(fm, "execution_mode"),
        description=_optional_str(fm, "description"),
        body=parsed.body,
        frontmatter=fm,
    )


def _required_str(frontmatter: dict[str, Any], field: str, path: Path) -> str:
    value = frontmatter.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing or invalid string field '{field}' in {path}")
    return value


def _optional_str(frontmatter: dict[str, Any], field: str) -> str | None:
    value = frontmatter.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"invalid field '{field}': expected string or null")
    return value


def _list_of_strings(frontmatter: dict[str, Any], field: str) -> tuple[str, ...]:
    value = frontmatter.get(field)
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"invalid field '{field}': expected list")
    if any(not isinstance(item, str) for item in value):
        raise ValueError(f"invalid field '{field}': expected list[str]")
    return tuple(value)


def _index_by_id(artifacts: tuple[Any, ...], artifact_label: str) -> dict[str, Any]:
    indexed: dict[str, Any] = {}
    for artifact in artifacts:
        artifact_id = getattr(artifact, "id")
        if artifact_id in indexed:
            raise ValueError(f"duplicate {artifact_label} id: {artifact_id}")
        indexed[artifact_id] = artifact
    return indexed
