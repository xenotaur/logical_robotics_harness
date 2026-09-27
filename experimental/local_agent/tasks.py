"""Resolve pre-registered pilot tasks from ``tasks.yaml`` into packet arguments."""

from __future__ import annotations

import dataclasses
import pathlib

import yaml

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_TASKS_FILE = (
    _REPO_ROOT / "experiments" / "01_local_agent_briefing" / "tasks.yaml"
)


class TaskError(ValueError):
    """Raised for a missing or malformed task definition."""


@dataclasses.dataclass(frozen=True)
class Task:
    task_id: str
    split: str
    repo_label: str
    project_dir: str
    commit: str
    work_item: str
    task_type: str


def load_tasks(path: pathlib.Path = DEFAULT_TASKS_FILE) -> dict[str, Task]:
    """Load and validate every task in a pre-registered tasks file."""
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise TaskError(f"cannot read tasks file {path}: {error}") from error
    if not isinstance(document, dict):
        raise TaskError(f"{path} is not a mapping")
    repos = document.get("repos") or {}
    loaded: dict[str, Task] = {}
    for entry in document.get("tasks") or []:
        missing = [key for key in ("id", "split", "work_item") if key not in entry]
        if missing:
            raise TaskError(f"task entry {entry} is missing {missing}")
        repo_label = entry.get("repo")
        if repo_label not in repos:
            raise TaskError(f"task {entry.get('id')} names unknown repo {repo_label}")
        commit = str(entry.get("commit", ""))
        if len(commit) != 40:
            raise TaskError(f"task {entry.get('id')} must pin a full 40-char commit")
        task = Task(
            task_id=str(entry["id"]),
            split=str(entry["split"]),
            repo_label=str(repo_label),
            project_dir=str(repos[repo_label].get("project_dir", ".")),
            commit=commit,
            work_item=str(entry["work_item"]),
            task_type=str(entry.get("task_type", "")),
        )
        if task.task_id in loaded:
            raise TaskError(f"duplicate task id {task.task_id}")
        loaded[task.task_id] = task
    return loaded


def resolve_task(task_id: str, path: pathlib.Path = DEFAULT_TASKS_FILE) -> Task:
    tasks = load_tasks(path)
    if task_id not in tasks:
        raise TaskError(f"unknown task {task_id}; known: {', '.join(sorted(tasks))}")
    return tasks[task_id]
