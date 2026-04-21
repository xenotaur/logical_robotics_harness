"""Initialize LRH workspace/meta-control directory layouts."""

from __future__ import annotations

import dataclasses
import pathlib

GITIGNORE_BEGIN = "# --- lrh meta init managed block ---"
GITIGNORE_END = "# --- end lrh meta init managed block ---"


class MetaInitError(RuntimeError):
    """Raised when workspace initialization cannot proceed safely."""


@dataclasses.dataclass(frozen=True)
class MetaWorkspaceSpec:
    """Minimal typed specification for an initialized LRH workspace."""

    workspace_name: str
    private_dirs: tuple[str, ...] = (
        "logs",
        "chats",
        "cache",
        "state",
        "tmp",
        "secrets",
    )


@dataclasses.dataclass(frozen=True)
class MetaInitResult:
    """Summary of init actions for CLI reporting and tests."""

    created: tuple[pathlib.Path, ...]
    updated: tuple[pathlib.Path, ...]
    unchanged: tuple[pathlib.Path, ...]


def init_workspace(
    root: pathlib.Path,
    *,
    spec: MetaWorkspaceSpec,
    force: bool = False,
) -> MetaInitResult:
    """Initialize an LRH meta workspace at ``root``.

    Args:
      root: Target directory where layout should be created.
      spec: Typed workspace configuration for generated content.
      force: If true, allow replacing incompatible path types and managed file content.

    Returns:
      MetaInitResult containing created/updated/unchanged paths.

    Raises:
      MetaInitError: If incompatible existing paths are detected and ``force``
        is false.
    """
    created: list[pathlib.Path] = []
    updated: list[pathlib.Path] = []
    unchanged: list[pathlib.Path] = []

    for relative_dir in (".lrh", "projects", "private"):
        _ensure_directory(root / relative_dir, force=force, created=created)

    for private_dir in spec.private_dirs:
        _ensure_directory(root / "private" / private_dir, force=force, created=created)

    _write_readme(
        root / "README.md",
        workspace_name=spec.workspace_name,
        created=created,
        unchanged=unchanged,
    )
    _write_gitignore(
        root / ".gitignore", created=created, updated=updated, unchanged=unchanged
    )
    _write_config(
        root / ".lrh" / "config.toml",
        workspace_name=spec.workspace_name,
        force=force,
        created=created,
        updated=updated,
        unchanged=unchanged,
    )

    return MetaInitResult(
        created=tuple(sorted(created, key=str)),
        updated=tuple(sorted(updated, key=str)),
        unchanged=tuple(sorted(unchanged, key=str)),
    )


def _ensure_directory(
    path: pathlib.Path,
    *,
    force: bool,
    created: list[pathlib.Path],
) -> None:
    if path.exists() and not path.is_dir():
        if not force:
            raise MetaInitError(
                f"expected directory at {path}, but found a non-directory path"
            )
        path.unlink()
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        created.append(path)


def _write_readme(
    path: pathlib.Path,
    *,
    workspace_name: str,
    created: list[pathlib.Path],
    unchanged: list[pathlib.Path],
) -> None:
    if path.exists():
        unchanged.append(path)
        return
    content = (
        f"# {workspace_name}\n\n"
        "This repository is an LRH workspace/meta-control dashboard.\n\n"
        "Use `lrh meta init` to ensure required directories and configuration exist.\n"
    )
    path.write_text(content, encoding="utf-8")
    created.append(path)


def _managed_gitignore_block() -> str:
    return "\n".join(
        [
            GITIGNORE_BEGIN,
            "private/logs/",
            "private/chats/",
            "private/cache/",
            "private/state/",
            "private/tmp/",
            "private/secrets/",
            GITIGNORE_END,
            "",
        ]
    )


def _write_gitignore(
    path: pathlib.Path,
    *,
    created: list[pathlib.Path],
    updated: list[pathlib.Path],
    unchanged: list[pathlib.Path],
) -> None:
    managed_block = _managed_gitignore_block()
    if not path.exists():
        path.write_text(managed_block, encoding="utf-8")
        created.append(path)
        return

    existing = path.read_text(encoding="utf-8")
    if GITIGNORE_BEGIN in existing and GITIGNORE_END in existing:
        unchanged.append(path)
        return

    separator = "\n" if existing and not existing.endswith("\n") else ""
    path.write_text(f"{existing}{separator}\n{managed_block}", encoding="utf-8")
    updated.append(path)


def _write_config(
    path: pathlib.Path,
    *,
    workspace_name: str,
    force: bool,
    created: list[pathlib.Path],
    updated: list[pathlib.Path],
    unchanged: list[pathlib.Path],
) -> None:
    content = _config_text(workspace_name)
    if not path.exists():
        path.write_text(content, encoding="utf-8")
        created.append(path)
        return

    existing = path.read_text(encoding="utf-8")
    if existing == content:
        unchanged.append(path)
        return

    if not force:
        raise MetaInitError(
            "found existing .lrh/config.toml with different content; "
            "rerun with --force to replace managed config"
        )

    path.write_text(content, encoding="utf-8")
    updated.append(path)


def _config_text(workspace_name: str) -> str:
    return (
        'schema_version = "0.1"\n\n'
        "[workspace]\n"
        f'name = "{workspace_name}"\n'
        'projects_dir = "projects"\n'
        'private_dir = "private"\n\n'
        "[meta]\n"
        'mode = "workspace"\n'
        'authority = "catalog_only"\n'
    )
