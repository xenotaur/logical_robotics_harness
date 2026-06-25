"""Install LRH skills from the package to the global Claude Code skills directory."""

from __future__ import annotations

import importlib.resources
import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

_SKILLS_PACKAGE = "lrh.skills"
_DEFAULT_SKILLS_DIR = Path.home() / ".claude" / "skills"


class SkillStatus(str, Enum):
    INSTALLED = "installed"
    UP_TO_DATE = "up_to_date"
    USER_MODIFIED = "user_modified"
    FORCED = "forced"


@dataclass(frozen=True)
class SkillResult:
    name: str
    status: SkillStatus


@dataclass(frozen=True)
class InstallReport:
    results: list[SkillResult]
    newly_created_skills_dir: bool


def _skill_names() -> list[str]:
    root = importlib.resources.files(_SKILLS_PACKAGE)
    return sorted(
        item.name
        for item in root.iterdir()
        if item.is_dir() and not item.name.startswith("_")
    )


def _collect_pkg_files(node: object, prefix: str = "") -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for item in node.iterdir():  # type: ignore[union-attr]
        rel = f"{prefix}/{item.name}" if prefix else item.name
        if item.is_file():
            result[rel] = item.read_bytes()
        elif item.is_dir():
            result.update(_collect_pkg_files(item, rel))
    return result


def _collect_fs_files(directory: Path) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for path in directory.rglob("*"):
        if path.is_file():
            result[path.relative_to(directory).as_posix()] = path.read_bytes()
    return result


def _skill_differs_from_package(skill_name: str, skills_dir: Path) -> bool:
    src = importlib.resources.files(_SKILLS_PACKAGE).joinpath(skill_name)
    pkg_files = _collect_pkg_files(src)
    fs_files = _collect_fs_files(skills_dir / skill_name)
    return pkg_files != fs_files


def _copy_resource_tree(node: object, dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    for item in node.iterdir():  # type: ignore[union-attr]
        if item.is_file():
            (dest_dir / item.name).write_bytes(item.read_bytes())
        elif item.is_dir():
            _copy_resource_tree(item, dest_dir / item.name)


def _copy_skill(skill_name: str, skills_dir: Path) -> None:
    dest = skills_dir / skill_name
    if dest.exists():
        shutil.rmtree(dest)
    src = importlib.resources.files(_SKILLS_PACKAGE).joinpath(skill_name)
    _copy_resource_tree(src, dest)


def install_skills(
    skills_dir: Path | None = None,
    dry_run: bool = False,
    force: bool = False,
) -> InstallReport:
    """Copy LRH skills from the package to the Claude Code skills directory.

    Returns an InstallReport describing what was done (or would be done in dry-run).
    """
    target = skills_dir if skills_dir is not None else _DEFAULT_SKILLS_DIR
    newly_created = not target.exists()
    results: list[SkillResult] = []

    for name in _skill_names():
        dest = target / name
        if not dest.exists():
            if not dry_run:
                target.mkdir(parents=True, exist_ok=True)
                _copy_skill(name, target)
            status = SkillStatus.INSTALLED
        elif _skill_differs_from_package(name, target):
            if force:
                if not dry_run:
                    _copy_skill(name, target)
                status = SkillStatus.FORCED
            else:
                status = SkillStatus.USER_MODIFIED
        else:
            status = SkillStatus.UP_TO_DATE
        results.append(SkillResult(name=name, status=status))

    return InstallReport(results=results, newly_created_skills_dir=newly_created)


def format_report(report: InstallReport, dry_run: bool = False) -> str:
    lines: list[str] = []
    for result in report.results:
        if result.status == SkillStatus.INSTALLED:
            verb = "would install" if dry_run else "installed"
            lines.append(f"  {verb}: {result.name}")
        elif result.status == SkillStatus.UP_TO_DATE:
            lines.append(f"  up to date: {result.name}")
        elif result.status == SkillStatus.USER_MODIFIED:
            lines.append(
                f"  warning: {result.name} has local modifications"
                " — skipped (use --force to overwrite)"
            )
        elif result.status == SkillStatus.FORCED:
            verb = "would overwrite" if dry_run else "overwritten"
            lines.append(f"  {verb}: {result.name}")
    if report.newly_created_skills_dir and not dry_run:
        lines.append(
            "\nnote: ~/.claude/skills/ was newly created."
            " Restart Claude Code to discover the installed skills."
        )
    return "\n".join(lines)
