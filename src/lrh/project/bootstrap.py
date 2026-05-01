"""Project bootstrap template install helpers."""

from __future__ import annotations

from dataclasses import dataclass
import importlib.resources
from pathlib import Path


_TEMPLATE_ROOT = "lrh"
_TEMPLATE_BASE = Path("templates") / "project_bootstrap"

_PROFILE_GROUPS = {
    "minimal": ["common"],
    "prompt-workflow": ["prompt_workflow"],
    "full": ["common", "prompt_workflow", "full"],
}


@dataclass(frozen=True)
class BootstrapPlan:
    to_create: list[Path]
    to_skip: list[Path]
    to_overwrite: list[Path]
    to_update: list[Path]


@dataclass(frozen=True)
class BootstrapResult:
    created: list[Path]
    skipped: list[Path]
    overwritten: list[Path]
    updated: list[Path]


def _iter_group_templates(group: str):
    root = importlib.resources.files(_TEMPLATE_ROOT).joinpath(
        str(_TEMPLATE_BASE / group)
    )

    def _walk(node, relative_parts: tuple[str, ...] = ()):
        for item in node.iterdir():
            item_relative_parts = (*relative_parts, item.name)
            if item.is_dir():
                yield from _walk(item, item_relative_parts)
            elif item.is_file():
                yield item, Path(*item_relative_parts)

    yield from _walk(root)


def _read_existing_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def build_plan(project_root: Path, profile: str, force: bool = False) -> BootstrapPlan:
    if profile not in _PROFILE_GROUPS:
        raise ValueError(f"unsupported profile: {profile}")

    create: list[Path] = []
    skip: list[Path] = []
    overwrite: list[Path] = []
    update: list[Path] = []

    for group in _PROFILE_GROUPS[profile]:
        for template_file, relative_path in _iter_group_templates(group):
            target = project_root / relative_path
            template_text = template_file.read_text(encoding="utf-8")
            if target.exists():
                if _read_existing_file(target) != template_text:
                    if force:
                        overwrite.append(target)
                    else:
                        update.append(target)
                else:
                    skip.append(target)
            else:
                create.append(target)

    return BootstrapPlan(
        to_create=create,
        to_skip=skip,
        to_overwrite=overwrite,
        to_update=update,
    )


def apply_plan(project_root: Path, profile: str, force: bool = False) -> BootstrapResult:
    plan = build_plan(project_root=project_root, profile=profile, force=force)

    created: list[Path] = []
    overwritten: list[Path] = []

    for group in _PROFILE_GROUPS[profile]:
        for template_file, relative_path in _iter_group_templates(group):
            target = project_root / relative_path
            if target.exists() and not force:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(template_file.read_text(encoding="utf-8"), encoding="utf-8")
            if target in plan.to_overwrite:
                overwritten.append(target)
            elif target in plan.to_create:
                created.append(target)

    return BootstrapResult(
        created=created,
        skipped=plan.to_skip,
        overwritten=overwritten,
        updated=plan.to_update,
    )


def format_plan(plan: BootstrapPlan, project_root: Path) -> str:
    lines: list[str] = []
    for path in sorted(plan.to_create):
        lines.append(f"CREATE {path.relative_to(project_root)}")
    for path in sorted(plan.to_skip):
        lines.append(f"SKIP {path.relative_to(project_root)}")
    for path in sorted(plan.to_update):
        lines.append(f"UPDATE {path.relative_to(project_root)}")
    for path in sorted(plan.to_overwrite):
        lines.append(f"OVERWRITE {path.relative_to(project_root)}")
    return "\n".join(lines)
