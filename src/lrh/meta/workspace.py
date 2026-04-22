"""Initialize LRH workspace/meta-control directory layouts."""

from __future__ import annotations

import dataclasses
import json
import pathlib
import shutil
import tomllib

GITIGNORE_BEGIN = "# --- lrh meta init managed block ---"
GITIGNORE_END = "# --- end lrh meta init managed block ---"


class MetaInitError(RuntimeError):
    """Raised when workspace initialization cannot proceed safely."""


class MetaRegistryError(RuntimeError):
    """Raised when the workspace project registry cannot be read."""


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


@dataclasses.dataclass(frozen=True)
class MetaProjectRecord:
    """Typed representation of one registered project record."""

    registry_name: str
    short_name: str | None
    display_name: str | None
    project_id: str | None
    repo_locator: str | None
    project_dir: str | None
    setup_state: str | None


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

    if not path.is_file():
        if not force:
            raise MetaInitError(
                f"expected file at {path}, but found a non-file path; "
                "rerun with --force to replace it"
            )
        _remove_existing_path(path)
        path.write_text(content, encoding="utf-8")
        updated.append(path)
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
    encoded_workspace_name = _toml_basic_string(workspace_name)
    return (
        'schema_version = "0.1"\n\n'
        "[workspace]\n"
        f"name = {encoded_workspace_name}\n"
        'projects_dir = "projects"\n'
        'private_dir = "private"\n\n'
        "[meta]\n"
        'mode = "workspace"\n'
        'authority = "catalog_only"\n'
    )


def _toml_basic_string(value: str) -> str:
    """Encode a Python string as a valid TOML basic string literal."""
    return json.dumps(value)


def _remove_existing_path(path: pathlib.Path) -> None:
    """Remove an existing filesystem path for force-replacement flows."""
    if path.is_dir():
        shutil.rmtree(path)
        return
    path.unlink()


def list_registered_projects(root: pathlib.Path) -> tuple[MetaProjectRecord, ...]:
    """Load project records from ``root/projects`` in stable directory order."""
    projects_dir = root / "projects"
    if not projects_dir.exists():
        raise MetaRegistryError(
            f"missing projects directory at {projects_dir}; run `lrh meta init` first"
        )
    if not projects_dir.is_dir():
        raise MetaRegistryError(f"expected directory at {projects_dir}")

    records: list[MetaProjectRecord] = []
    for record_dir in sorted(projects_dir.iterdir(), key=lambda entry: entry.name):
        if not record_dir.is_dir():
            continue
        records.append(_load_project_record(record_dir))
    return tuple(records)


def format_project_records(records: tuple[MetaProjectRecord, ...]) -> str:
    """Render records as plain, inspectable text for ``lrh meta list``."""
    if not records:
        return "No registered projects found under projects/."

    lines: list[str] = []
    for index, record in enumerate(records, start=1):
        if index > 1:
            lines.append("")
        lines.extend(
            [
                f"[{index}] {record.registry_name}",
                f"  registry_name: {record.registry_name}",
                f"  short_name: {_display_value(record.short_name)}",
                f"  display_name: {_display_value(record.display_name)}",
                f"  project_id: {_display_value(record.project_id)}",
                f"  repo_locator: {_display_value(record.repo_locator)}",
                f"  project_dir: {_display_value(record.project_dir)}",
                f"  setup_state: {_display_value(record.setup_state)}",
            ]
        )
    return "\n".join(lines)


def _load_project_record(record_dir: pathlib.Path) -> MetaProjectRecord:
    project_file = record_dir / "project.toml"
    if not project_file.exists():
        raise MetaRegistryError(
            f"missing project record file: {project_file} "
            f"(expected each registry directory to contain project.toml)"
        )
    if not project_file.is_file():
        raise MetaRegistryError(f"expected file at {project_file}")

    try:
        content = project_file.read_text(encoding="utf-8")
    except UnicodeDecodeError as err:
        raise MetaRegistryError(
            f"project record file is not valid UTF-8: {project_file}"
        ) from err
    except OSError as err:
        raise MetaRegistryError(
            f"unable to read project record file {project_file}: {err}"
        ) from err

    try:
        parsed = tomllib.loads(content)
    except tomllib.TOMLDecodeError as err:
        raise MetaRegistryError(f"invalid TOML in {project_file}: {err}") from err

    project_data = _required_table(parsed, project_file, "project")
    identity_data = _required_table(parsed, project_file, "identity")
    locators_data = _required_table(parsed, project_file, "locators")

    return MetaProjectRecord(
        registry_name=record_dir.name,
        short_name=_optional_string(project_data, "short_name", project_file),
        display_name=_optional_string(project_data, "display_name", project_file),
        project_id=_optional_string(identity_data, "project_id", project_file),
        repo_locator=_optional_string(locators_data, "repo_locator", project_file),
        project_dir=_optional_string(locators_data, "project_dir", project_file),
        setup_state=_optional_string(project_data, "setup_state", project_file),
    )


def _required_table(
    parsed: dict[str, object], project_file: pathlib.Path, key: str
) -> dict[str, object]:
    value = parsed.get(key)
    if value is None:
        raise MetaRegistryError(f"missing [{key}] table in {project_file}")
    if not isinstance(value, dict):
        raise MetaRegistryError(
            f"expected [{key}] table to be a mapping in {project_file}"
        )
    return value


def _optional_string(
    table: dict[str, object], key: str, project_file: pathlib.Path
) -> str | None:
    value = table.get(key)
    if value is None:
        return None
    if isinstance(value, str):
        return value
    raise MetaRegistryError(f"expected string for {key!r} in {project_file}")


def _display_value(value: str | None) -> str:
    return "<missing>" if value is None else value
