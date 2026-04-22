"""Minimal runtime models for LRH control-plane loading."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Focus:
    """Current focus artifact loaded from project/focus/current_focus.md."""

    path: Path
    id: str
    title: str
    status: str
    priority: str | None
    owner: str | None
    related_principles: tuple[str, ...] = ()
    body: str = ""
    frontmatter: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkItem:
    """Work-item artifact loaded from project/work_items/*.md."""

    path: Path
    id: str
    title: str
    type: str
    status: str
    priority: str | None
    owner: str | None
    contributors: tuple[str, ...] = ()
    assigned_agents: tuple[str, ...] = ()
    related_focus: tuple[str, ...] = ()
    related_roadmap: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()
    blocked_by: tuple[str, ...] = ()
    expected_actions: tuple[str, ...] = ()
    forbidden_actions: tuple[str, ...] = ()
    acceptance: tuple[str, ...] = ()
    required_evidence: tuple[str, ...] = ()
    artifacts_expected: tuple[str, ...] = ()
    body: str = ""
    frontmatter: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class Contributor:
    """Contributor artifact loaded from project/contributors/**/*.md."""

    path: Path
    id: str
    type: str
    roles: tuple[str, ...]
    display_name: str
    status: str
    email: str | None = None
    github: str | None = None
    execution_mode: str | None = None
    description: str | None = None
    body: str = ""
    frontmatter: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ProjectState:
    """Loaded, indexed control-plane subset for focus/work-items/contributors."""

    project_dir: Path
    current_focus: Focus
    work_items: tuple[WorkItem, ...]
    work_items_by_id: dict[str, WorkItem]
    contributors: tuple[Contributor, ...]
    contributors_by_id: dict[str, Contributor]

    def work_items_for_focus(self, focus_id: str) -> tuple[WorkItem, ...]:
        return tuple(item for item in self.work_items if focus_id in item.related_focus)
