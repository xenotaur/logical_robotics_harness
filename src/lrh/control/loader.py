"""Project-directory loader for a minimal LRH control-plane runtime state."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lrh.control.models import (
    Contributor,
    DesignProposal,
    Focus,
    ProjectState,
    WorkItem,
    Workstream,
)
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

    workstreams = load_workstreams(project_dir)
    workstreams_by_id = _index_by_id(workstreams, artifact_label="workstream")

    design_proposals = load_design_proposals(project_dir)
    design_proposals_by_id = _index_by_id(
        design_proposals, artifact_label="design proposal"
    )

    contributors = _load_contributors(project_dir / "contributors")
    contributors_by_id = _index_by_id(contributors, artifact_label="contributor")

    return ProjectState(
        project_dir=project_dir,
        current_focus=current_focus,
        work_items=work_items,
        work_items_by_id=work_items_by_id,
        workstreams=workstreams,
        workstreams_by_id=workstreams_by_id,
        design_proposals=design_proposals,
        design_proposals_by_id=design_proposals_by_id,
        contributors=contributors,
        contributors_by_id=contributors_by_id,
    )


def load_workstreams(root: Path) -> tuple[Workstream, ...]:
    """Load single-file workstreams from a project or repository root."""

    project_dir = find_project_dir(root)
    return _load_workstreams(project_dir / "workstreams")


def load_design_proposals(root: Path) -> tuple[DesignProposal, ...]:
    """Load design proposals from a project or repository root."""

    project_dir = find_project_dir(root)
    return _load_design_proposals(project_dir / "design" / "proposals")


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
    for path in sorted(directory.glob("**/WI-*.md")):
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
                parent_id=_optional_str(fm, "parent_id"),
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


def _load_workstreams(directory: Path) -> tuple[Workstream, ...]:
    if not directory.exists():
        return ()

    workstreams: list[Workstream] = []
    for path in _iter_workstream_files(directory):
        parsed = parse_markdown_file(path)
        workstreams.append(_workstream_from_parsed(path, directory, parsed))
    return tuple(workstreams)


def _iter_workstream_files(directory: Path) -> tuple[Path, ...]:
    bucket_names = ("proposed", "active", "resolved", "abandoned")
    paths: list[Path] = []
    for bucket_name in bucket_names:
        bucket_dir = directory / bucket_name
        if not bucket_dir.exists():
            continue
        for path in sorted(bucket_dir.glob("WS-*.md")):
            if _is_ignored_workstream_file(path):
                continue
            paths.append(path)
    return tuple(paths)


def _is_ignored_workstream_file(path: Path) -> bool:
    ignored_stems = {"placeholder", ".placeholder", "gitkeep", ".gitkeep"}
    return path.name == "README.md" or path.stem.lower() in ignored_stems


def _workstream_from_parsed(
    path: Path,
    workstreams_dir: Path,
    parsed: ParsedMarkdown,
) -> Workstream:
    fm = parsed.frontmatter
    return Workstream(
        path=path,
        id=_required_str(fm, "id", path),
        kind=_required_str(fm, "kind", path),
        title=_required_str(fm, "title", path),
        status=_required_str(fm, "status", path),
        stage=_required_str(fm, "stage", path),
        bucket=_workstream_bucket(path, workstreams_dir),
        origin=_optional_str(fm, "origin"),
        parent_id=_optional_str(fm, "parent_id"),
        children=_list_of_strings(fm, "children"),
        summary=_optional_str(fm, "summary"),
        rationale=_optional_str(fm, "rationale"),
        related_focus=_list_of_strings(fm, "related_focus"),
        related_roadmap=_list_of_strings(fm, "related_roadmap"),
        work_items=_list_of_strings(fm, "work_items"),
        execution_records=_list_of_strings(fm, "execution_records"),
        evidence=_list_of_strings(fm, "evidence"),
        exit_criteria=_list_of_strings(fm, "exit_criteria"),
        closeout=_optional_str(fm, "closeout"),
        body=parsed.body,
        frontmatter=fm,
    )


def _workstream_bucket(path: Path, workstreams_dir: Path) -> str | None:
    try:
        relative_parts = path.relative_to(workstreams_dir).parts
    except ValueError:
        return None
    if not relative_parts:
        return None
    return relative_parts[0]


def _load_design_proposals(directory: Path) -> tuple[DesignProposal, ...]:
    if not directory.exists():
        return ()

    proposals: list[DesignProposal] = []
    for path in sorted(directory.glob("**/*.md")):
        if _is_ignored_design_proposal_file(path):
            continue
        parsed = parse_markdown_file(path)
        fm = parsed.frontmatter
        if not _is_design_proposal_frontmatter(fm):
            continue
        proposals.append(
            DesignProposal(
                path=path,
                id=_required_str(fm, "id", path),
                title=_optional_str(fm, "title") or _optional_str(fm, "summary"),
                status=_required_str(fm, "status", path),
                implementation_status=_optional_str(fm, "implementation_status"),
                implemented_by=_list_of_strings(fm, "implemented_by"),
                evidence=_list_of_strings(fm, "evidence"),
                supersedes=_list_of_strings(fm, "supersedes"),
                superseded_by=_optional_str(fm, "superseded_by"),
                body=parsed.body,
                frontmatter=fm,
            )
        )
    return tuple(proposals)


def _is_ignored_design_proposal_file(path: Path) -> bool:
    return path.name in {"README.md", "index.md"}


def _is_design_proposal_frontmatter(frontmatter: dict[str, Any]) -> bool:
    return (
        frontmatter.get("type") == "design_proposal"
        or frontmatter.get("kind") == "design_proposal"
    )


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
