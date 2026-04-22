"""Initialize LRH workspace/meta-control directory layouts."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import pathlib
import re
import shutil
import tomllib
from typing import Literal

GITIGNORE_BEGIN = "# --- lrh meta init managed block ---"
GITIGNORE_END = "# --- end lrh meta init managed block ---"


class MetaInitError(RuntimeError):
    """Raised when workspace initialization cannot proceed safely."""


class MetaRegistryError(RuntimeError):
    """Raised when the workspace project registry cannot be read."""


class MetaWorkspaceResolutionError(RuntimeError):
    """Raised when an active meta workspace cannot be resolved."""


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


@dataclasses.dataclass(frozen=True)
class MetaRegisterSpec:
    """Input parameters for registering one project record."""

    repo_locator: str
    project_dir: str = "project"
    directory_name: str | None = None
    short_name: str | None = None
    display_name: str | None = None


@dataclasses.dataclass(frozen=True)
class MetaRegisterResult:
    """Summary of one successful registration write."""

    directory_name: str
    project_id: str
    setup_state: str
    record_path: pathlib.Path


@dataclasses.dataclass(frozen=True)
class MetaWorkspaceResolveOptions:
    """Optional explicit overrides for workspace resolution."""

    workspace_path: pathlib.Path | None = None
    config_path: pathlib.Path | None = None
    mode: Literal["local", "global"] | None = None


@dataclasses.dataclass(frozen=True)
class MetaWorkspace:
    """Resolved runtime workspace context for meta CLI commands."""

    mode: Literal["local", "global"]
    config_path: pathlib.Path
    projects_dir: pathlib.Path
    state_dir: pathlib.Path
    cache_dir: pathlib.Path
    workspace_root: pathlib.Path | None
    resolution_source: str


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
        'mode = "local"\n\n'
        "[paths]\n"
        'projects_dir = "projects"\n'
        'state_dir = "private/state"\n'
        'cache_dir = "private/cache"\n\n'
        "[meta]\n"
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


def resolve_meta_workspace(
    *,
    cwd: pathlib.Path,
    options: MetaWorkspaceResolveOptions | None = None,
    environ: dict[str, str] | None = None,
) -> MetaWorkspace:
    """Resolve the active workspace context for ``lrh meta`` commands."""
    if options is None:
        options = MetaWorkspaceResolveOptions()
    if environ is None:
        environ = dict(os.environ)

    resolution_error = _workspace_resolution_error(
        cwd=cwd,
        options=options,
        environ=environ,
    )

    if options.config_path is not None:
        return _workspace_from_config_path(
            config_path=options.config_path,
            mode_override=options.mode,
            source="flag(--config)",
            resolution_error=resolution_error,
            environ=environ,
        )

    if options.workspace_path is not None:
        if options.mode == "global":
            raise MetaWorkspaceResolutionError(
                "--workspace cannot be used with --mode global; "
                "use --config for global workspace config selection"
            )
        local_config = options.workspace_path / ".lrh" / "config.toml"
        return _workspace_from_config_path(
            config_path=local_config,
            mode_override="local",
            source="flag(--workspace)",
            resolution_error=resolution_error,
            environ=environ,
        )

    if options.mode == "local":
        local_config = _discover_local_config(cwd)
        if local_config is None:
            raise resolution_error
        return _workspace_from_config_path(
            config_path=local_config,
            mode_override="local",
            source="flag(--mode=local)+local_discovery",
            resolution_error=resolution_error,
            environ=environ,
        )
    if options.mode == "global":
        config_path = _xdg_config_path(environ)
        return _workspace_from_config_path(
            config_path=config_path,
            mode_override="global",
            source="flag(--mode=global)+global_discovery",
            resolution_error=resolution_error,
            environ=environ,
        )

    env_config = environ.get("LRH_CONFIG")
    if env_config:
        return _workspace_from_config_path(
            config_path=pathlib.Path(env_config).expanduser(),
            mode_override=None,
            source="env(LRH_CONFIG)",
            resolution_error=resolution_error,
            environ=environ,
        )

    env_workspace = environ.get("LRH_WORKSPACE")
    if env_workspace:
        local_config = pathlib.Path(env_workspace).expanduser() / ".lrh" / "config.toml"
        return _workspace_from_config_path(
            config_path=local_config,
            mode_override="local",
            source="env(LRH_WORKSPACE)",
            resolution_error=resolution_error,
            environ=environ,
        )

    discovered_config = _discover_local_config(cwd)
    if discovered_config is not None:
        return _workspace_from_config_path(
            config_path=discovered_config,
            mode_override="local",
            source="local_discovery",
            resolution_error=resolution_error,
            environ=environ,
        )

    global_config = _xdg_config_path(environ)
    if global_config.exists():
        return _workspace_from_config_path(
            config_path=global_config,
            mode_override="global",
            source="global_discovery",
            resolution_error=resolution_error,
            environ=environ,
        )

    raise resolution_error


def _workspace_from_config_path(
    *,
    config_path: pathlib.Path,
    mode_override: Literal["local", "global"] | None,
    source: str,
    resolution_error: MetaWorkspaceResolutionError,
    environ: dict[str, str] | None = None,
) -> MetaWorkspace:
    if not config_path.exists() or not config_path.is_file():
        raise resolution_error

    try:
        content = config_path.read_text(encoding="utf-8")
    except OSError as err:
        raise MetaWorkspaceResolutionError(
            f"unable to read workspace config at {config_path}: {err}"
        ) from err

    try:
        parsed = tomllib.loads(content)
    except tomllib.TOMLDecodeError as err:
        raise MetaWorkspaceResolutionError(
            f"invalid workspace config TOML at {config_path}: {err}"
        ) from err

    mode = mode_override or _config_mode(parsed) or _mode_for_config_path(config_path)
    if mode == "local":
        return _build_local_workspace(
            config_path=config_path,
            parsed=parsed,
            source=source,
        )
    return _build_global_workspace(
        config_path=config_path,
        parsed=parsed,
        source=source,
        environ=environ or dict(os.environ),
    )


def _mode_for_config_path(config_path: pathlib.Path) -> Literal["local", "global"]:
    if config_path.parent.name == ".lrh":
        return "local"
    return "global"


def _config_mode(parsed: dict[str, object]) -> Literal["local", "global"] | None:
    workspace_data = parsed.get("workspace")
    if not isinstance(workspace_data, dict):
        return None
    raw_mode = workspace_data.get("mode")
    if raw_mode in ("local", "global"):
        return raw_mode
    return None


def _build_local_workspace(
    *,
    config_path: pathlib.Path,
    parsed: dict[str, object],
    source: str,
) -> MetaWorkspace:
    workspace_root = config_path.parent.parent
    projects_dir = _configured_path(
        parsed=parsed,
        key="projects_dir",
        base_dir=workspace_root,
        default=workspace_root / "projects",
    )
    state_dir = _configured_path(
        parsed=parsed,
        key="state_dir",
        base_dir=workspace_root,
        default=workspace_root / "private" / "state",
    )
    cache_dir = _configured_path(
        parsed=parsed,
        key="cache_dir",
        base_dir=workspace_root,
        default=workspace_root / "private" / "cache",
    )
    return MetaWorkspace(
        mode="local",
        config_path=config_path,
        projects_dir=projects_dir,
        state_dir=state_dir,
        cache_dir=cache_dir,
        workspace_root=workspace_root,
        resolution_source=source,
    )


def _build_global_workspace(
    *,
    config_path: pathlib.Path,
    parsed: dict[str, object],
    source: str,
    environ: dict[str, str],
) -> MetaWorkspace:
    state_root = _xdg_state_path(environ)
    cache_root = _xdg_cache_path(environ)
    projects_dir = _configured_path(
        parsed=parsed,
        key="projects_dir",
        base_dir=config_path.parent,
        default=state_root / "projects",
    )
    state_dir = _configured_path(
        parsed=parsed,
        key="state_dir",
        base_dir=config_path.parent,
        default=state_root,
    )
    cache_dir = _configured_path(
        parsed=parsed,
        key="cache_dir",
        base_dir=config_path.parent,
        default=cache_root,
    )
    return MetaWorkspace(
        mode="global",
        config_path=config_path,
        projects_dir=projects_dir,
        state_dir=state_dir,
        cache_dir=cache_dir,
        workspace_root=None,
        resolution_source=source,
    )


def _configured_path(
    *,
    parsed: dict[str, object],
    key: str,
    base_dir: pathlib.Path,
    default: pathlib.Path,
) -> pathlib.Path:
    paths_data = parsed.get("paths")
    if not isinstance(paths_data, dict):
        return default
    value = paths_data.get(key)
    if not isinstance(value, str) or not value.strip():
        return default
    path_value = pathlib.Path(value).expanduser()
    if path_value.is_absolute():
        return path_value
    return (base_dir / path_value).resolve()


def _discover_local_config(cwd: pathlib.Path) -> pathlib.Path | None:
    current = cwd.resolve()
    for candidate in (current, *current.parents):
        config_path = candidate / ".lrh" / "config.toml"
        if config_path.exists() and config_path.is_file():
            return config_path
    return None


def _xdg_config_path(environ: dict[str, str]) -> pathlib.Path:
    xdg_config_home = environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        return pathlib.Path(xdg_config_home).expanduser() / "lrh" / "config.toml"
    return pathlib.Path("~/.config/lrh/config.toml").expanduser()


def _xdg_state_path(environ: dict[str, str]) -> pathlib.Path:
    xdg_state_home = environ.get("XDG_STATE_HOME")
    if xdg_state_home:
        return pathlib.Path(xdg_state_home).expanduser() / "lrh"
    return pathlib.Path("~/.local/state/lrh").expanduser()


def _xdg_cache_path(environ: dict[str, str]) -> pathlib.Path:
    xdg_cache_home = environ.get("XDG_CACHE_HOME")
    if xdg_cache_home:
        return pathlib.Path(xdg_cache_home).expanduser() / "lrh"
    return pathlib.Path("~/.cache/lrh").expanduser()


def _workspace_resolution_error(
    *,
    cwd: pathlib.Path,
    options: MetaWorkspaceResolveOptions,
    environ: dict[str, str],
) -> MetaWorkspaceResolutionError:
    checked_lines = [
        "- --config / --workspace / --mode",
        f"- LRH_CONFIG={environ.get('LRH_CONFIG', '<unset>')}",
        f"- LRH_WORKSPACE={environ.get('LRH_WORKSPACE', '<unset>')}",
        f"- local .lrh/config.toml discovery from {cwd.resolve()}",
        f"- global XDG config path {_xdg_config_path(environ)}",
        "- built-in defaults (XDG paths) for global mode",
    ]
    detail = "\n".join(checked_lines)
    return MetaWorkspaceResolutionError(
        "No LRH meta workspace could be resolved.\n\n"
        f"Checked:\n{detail}\n\n"
        "To initialize a local workspace in the current directory:\n"
        "  lrh meta init\n\n"
        "To force an explicit workspace config path:\n"
        "  lrh meta list --config /path/to/config.toml"
    )


def register_project(
    root: pathlib.Path,
    *,
    spec: MetaRegisterSpec,
    force: bool = False,
) -> MetaRegisterResult:
    """Register a project in ``root/projects`` by writing ``project.toml``."""
    local_workspace = MetaWorkspace(
        mode="local",
        config_path=root / ".lrh" / "config.toml",
        projects_dir=root / "projects",
        state_dir=root / "private" / "state",
        cache_dir=root / "private" / "cache",
        workspace_root=root,
        resolution_source="legacy(root)",
    )
    return register_project_in_workspace(local_workspace, spec=spec, force=force)


def register_project_in_workspace(
    workspace: MetaWorkspace,
    *,
    spec: MetaRegisterSpec,
    force: bool = False,
) -> MetaRegisterResult:
    """Register a project by writing one ``project.toml`` under projects_dir."""
    projects_dir = _require_projects_dir(workspace.projects_dir)

    repo_locator = _normalized_required_value("repo_locator", spec.repo_locator)
    project_dir = _normalized_required_value("project_dir", spec.project_dir)
    directory_name = _normalized_directory_name(spec.directory_name, repo_locator)
    short_name = _normalized_optional_value(spec.short_name) or directory_name
    display_name = _normalized_optional_value(spec.display_name) or _display_from_name(
        short_name
    )

    records = list_registered_projects_in_workspace(workspace)
    duplicate = _find_duplicate_record(records, repo_locator, project_dir)
    if duplicate is not None and not force:
        raise MetaRegistryError(
            "duplicate registration detected for "
            f"repo_locator={repo_locator!r} project_dir={project_dir!r}; "
            f"existing registry entry={duplicate.registry_name!r}; rerun with --force "
            "to allow a deliberate duplicate record"
        )

    setup_state = _detect_setup_state(repo_locator, project_dir)
    project_id = _stable_project_id(repo_locator, project_dir)
    record_dir = projects_dir / directory_name
    record_path = record_dir / "project.toml"

    if record_dir.exists() and not record_dir.is_dir():
        raise MetaRegistryError(f"expected directory at {record_dir}")
    record_dir.mkdir(parents=True, exist_ok=True)

    if record_path.exists() and not force:
        raise MetaRegistryError(
            f"project record already exists at {record_path}; "
            "choose a different --directory-name or rerun with --force"
        )

    record_path.write_text(
        _project_record_text(
            directory_name=directory_name,
            short_name=short_name,
            display_name=display_name,
            project_id=project_id,
            repo_locator=repo_locator,
            project_dir=project_dir,
            setup_state=setup_state,
        ),
        encoding="utf-8",
    )

    return MetaRegisterResult(
        directory_name=directory_name,
        project_id=project_id,
        setup_state=setup_state,
        record_path=record_path,
    )


def _project_record_text(
    *,
    directory_name: str,
    short_name: str,
    display_name: str,
    project_id: str,
    repo_locator: str,
    project_dir: str,
    setup_state: str,
) -> str:
    return "\n".join(
        [
            'schema_version = "0.1"',
            "",
            "[project]",
            f"short_name = {_toml_basic_string(short_name)}",
            f"display_name = {_toml_basic_string(display_name)}",
            'status = "active"',
            f"setup_state = {_toml_basic_string(setup_state)}",
            "",
            "[identity]",
            f"project_id = {_toml_basic_string(project_id)}",
            "",
            "[locators]",
            f"repo_locator = {_toml_basic_string(repo_locator)}",
            f"project_dir = {_toml_basic_string(project_dir)}",
            "",
            "[registry]",
            f"directory_name = {_toml_basic_string(directory_name)}",
            "",
        ]
    )


def _normalized_required_value(field_name: str, value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise MetaRegistryError(f"{field_name} must not be empty")
    return normalized


def _normalized_optional_value(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized if normalized else None


def _normalized_directory_name(directory_name: str | None, repo_locator: str) -> str:
    requested = _normalized_optional_value(directory_name)
    if requested is None:
        requested = _infer_name_from_locator(repo_locator)

    normalized = requested.lower()
    normalized = re.sub(r"[^a-z0-9._-]+", "-", normalized)
    normalized = normalized.strip(".-_")
    if not normalized:
        raise MetaRegistryError("unable to derive a valid registry directory name")
    return normalized


def _infer_name_from_locator(repo_locator: str) -> str:
    inferred = repo_locator.rstrip("/").split("/")[-1]
    if inferred.endswith(".git"):
        inferred = inferred[:-4]
    if inferred:
        return inferred
    return "project"


def _display_from_name(short_name: str) -> str:
    words = re.split(r"[-_.]+", short_name)
    titled_words = [word.capitalize() for word in words if word]
    if titled_words:
        return " ".join(titled_words)
    return short_name


def _find_duplicate_record(
    records: tuple[MetaProjectRecord, ...],
    repo_locator: str,
    project_dir: str,
) -> MetaProjectRecord | None:
    for record in records:
        if record.repo_locator == repo_locator and record.project_dir == project_dir:
            return record
    return None


def _detect_setup_state(repo_locator: str, project_dir: str) -> str:
    repo_path = pathlib.Path(repo_locator).expanduser()
    if repo_path.is_dir() and (repo_path / project_dir).is_dir():
        return "lrh_project_present"
    return "not_set_up"


def _stable_project_id(repo_locator: str, project_dir: str) -> str:
    source = f"{repo_locator}\n{project_dir}".encode("utf-8")
    digest = hashlib.sha256(source).hexdigest()
    return f"proj-{digest[:16]}"


def list_registered_projects(root: pathlib.Path) -> tuple[MetaProjectRecord, ...]:
    """Load project records from ``root/projects`` in stable directory order."""
    local_workspace = MetaWorkspace(
        mode="local",
        config_path=root / ".lrh" / "config.toml",
        projects_dir=root / "projects",
        state_dir=root / "private" / "state",
        cache_dir=root / "private" / "cache",
        workspace_root=root,
        resolution_source="legacy(root)",
    )
    return list_registered_projects_in_workspace(local_workspace)


def list_registered_projects_in_workspace(
    workspace: MetaWorkspace,
) -> tuple[MetaProjectRecord, ...]:
    """Load project records in stable directory order from workspace projects_dir."""
    projects_dir = _require_projects_dir(workspace.projects_dir)

    try:
        project_entries = sorted(projects_dir.iterdir(), key=lambda entry: entry.name)
    except OSError as err:
        raise MetaRegistryError(
            f"unable to enumerate registry directory {projects_dir}: {err}"
        ) from err

    records: list[MetaProjectRecord] = []
    for record_dir in project_entries:
        if not record_dir.is_dir():
            continue
        records.append(_load_project_record(record_dir))
    return tuple(records)


def _require_projects_dir(projects_dir: pathlib.Path) -> pathlib.Path:
    if not projects_dir.exists():
        raise MetaRegistryError(
            f"missing projects directory at {projects_dir}; run `lrh meta init` first"
        )
    if not projects_dir.is_dir():
        raise MetaRegistryError(f"expected directory at {projects_dir}")
    return projects_dir


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
        repo_locator=_optional_locator_string(locators_data, project_file),
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


def _optional_locator_string(
    table: dict[str, object], project_file: pathlib.Path
) -> str | None:
    repo_locator = _optional_string(table, "repo_locator", project_file)
    if repo_locator is not None:
        return repo_locator
    return _optional_string(table, "repo", project_file)


def _display_value(value: str | None) -> str:
    return "<missing>" if value is None else value
