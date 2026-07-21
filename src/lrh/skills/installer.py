"""Install LRH skills from the package to the global Claude Code skills directory."""

from __future__ import annotations

import difflib
import importlib.resources
import importlib.resources.abc
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
    skills_dir: Path


def _skill_names() -> list[str]:
    root = importlib.resources.files(_SKILLS_PACKAGE)
    return sorted(
        item.name
        for item in root.iterdir()
        if item.is_dir() and not item.name.startswith("_")
    )


def _collect_pkg_files(
    node: importlib.resources.abc.Traversable, prefix: str = ""
) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for item in node.iterdir():
        rel = f"{prefix}/{item.name}" if prefix else item.name
        if item.is_file():
            result[rel] = item.read_bytes()
        elif item.is_dir():
            result.update(_collect_pkg_files(item, rel))
    return result


def _collect_fs_files(directory: Path) -> dict[str, bytes]:
    if directory.is_symlink():
        # Refuse to traverse a symlinked skill root: rglob() would follow it
        # to an arbitrary target outside the skills directory and read its
        # files. Reporting no files here makes the skill compare unequal to
        # the package (see _skill_differs_from_package), which is the safe
        # outcome — never dereference, never silently treat as up to date.
        return {}
    result: dict[str, bytes] = {}
    for path in directory.rglob("*"):
        if path.is_symlink():
            continue
        if path.is_file():
            result[path.relative_to(directory).as_posix()] = path.read_bytes()
    return result


def _collect_fs_symlinks(directory: Path) -> set[str]:
    """Return relative paths of symlinked entries under `directory`.

    Symlinks are never dereferenced here — a skill file replaced by a
    symlink could point outside the installed skill directory, and reading
    through it would expose the target's contents. If `directory` itself is
    a symlink, it is not traversed (see `_collect_fs_files`) and this
    returns an empty set — the root-symlink case is signaled separately.
    """
    if directory.is_symlink():
        return set()
    return {
        path.relative_to(directory).as_posix()
        for path in directory.rglob("*")
        if path.is_symlink()
    }


def _skill_differs_from_package(skill_name: str, skills_dir: Path) -> bool:
    src = importlib.resources.files(_SKILLS_PACKAGE).joinpath(skill_name)
    pkg_files = _collect_pkg_files(src)
    skill_dir = skills_dir / skill_name
    fs_files = _collect_fs_files(skill_dir)
    if pkg_files != fs_files:
        return True
    # A nested symlink (e.g. an added file replaced by one) can leave the
    # byte dicts equal, since symlinks are excluded from both — but its
    # presence is itself a local modification that must not be masked as
    # up to date.
    return bool(_collect_fs_symlinks(skill_dir))


def diff_skill(skill_name: str, skills_dir: Path) -> str:
    """Return a unified-diff report of how an installed skill differs from the package.

    Symlinked entries under the installed skill directory are reported but
    never dereferenced — their target contents are never read or diffed.
    """
    skill_dir = skills_dir / skill_name
    if skill_dir.is_symlink():
        return (
            f"{skill_name}: installed skill directory is a symlink — skipped"
            " (refusing to read through it)\n"
        )

    src = importlib.resources.files(_SKILLS_PACKAGE).joinpath(skill_name)
    pkg_files = _collect_pkg_files(src)
    fs_files = _collect_fs_files(skill_dir)
    fs_symlinks = _collect_fs_symlinks(skill_dir)

    segments: list[str] = []
    for rel_path in sorted(set(pkg_files) | set(fs_files) | fs_symlinks):
        if rel_path in fs_symlinks:
            segments.append(f"{rel_path}: symlink — skipped\n")
            continue
        in_pkg = rel_path in pkg_files
        in_fs = rel_path in fs_files
        if in_pkg and not in_fs:
            segments.append(
                f"{rel_path}: removed (present in package, missing on disk)\n"
            )
            continue
        if in_fs and not in_pkg:
            segments.append(f"{rel_path}: added (present on disk, not in package)\n")
            continue
        pkg_bytes = pkg_files[rel_path]
        fs_bytes = fs_files[rel_path]
        if pkg_bytes == fs_bytes:
            continue
        try:
            pkg_lines = pkg_bytes.decode("utf-8").splitlines(keepends=True)
            fs_lines = fs_bytes.decode("utf-8").splitlines(keepends=True)
        except UnicodeDecodeError:
            segments.append(f"{rel_path}: binary files differ\n")
            continue
        diff_lines = difflib.unified_diff(
            pkg_lines,
            fs_lines,
            fromfile=f"package/{rel_path}",
            tofile=f"installed/{rel_path}",
        )
        segments.append("".join(diff_lines))

    return "".join(segments)


def _copy_resource_tree(
    node: importlib.resources.abc.Traversable, dest_dir: Path
) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    for item in node.iterdir():
        if item.is_file():
            (dest_dir / item.name).write_bytes(item.read_bytes())
        elif item.is_dir():
            _copy_resource_tree(item, dest_dir / item.name)


def _copy_skill(skill_name: str, skills_dir: Path) -> None:
    dest = skills_dir / skill_name
    if dest.is_symlink() or (dest.exists() and not dest.is_dir()):
        dest.unlink()
    elif dest.is_dir():
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

    return InstallReport(
        results=results, newly_created_skills_dir=newly_created, skills_dir=target
    )


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
            f"\nnote: {report.skills_dir} was newly created."
            " Restart Claude Code to discover the installed skills."
        )
    return "\n".join(lines)
