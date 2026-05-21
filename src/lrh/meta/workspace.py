"""Initialize LRH workspace/meta-control directory layouts."""

from __future__ import annotations

import dataclasses
import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import tomllib
import urllib.parse
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
class MetaProjectLoadResult:
    """Tolerant project-record load result for read-only meta dashboards."""

    registry_name: str
    record: MetaProjectRecord | None
    error: str | None = None


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
    project_dir: str | None = None
    directory_name: str | None = None
    short_name: str | None = None
    display_name: str | None = None


@dataclasses.dataclass(frozen=True)
class LocatorAnalysis:
    """Deterministic locator parse details used for metadata inference."""

    kind: Literal["github_url", "url", "local_path", "unknown"]
    host: str | None = None
    repo_owner: str | None = None
    repo_slug: str | None = None
    repo_ref: str | None = None
    repo_subpath: str | None = None
    local_basename: str | None = None
    path_tail: str | None = None
    project_dir_hint: str | None = None


@dataclasses.dataclass(frozen=True)
class InferredProjectMetadata:
    """Resolved metadata defaults for project registration."""

    repo_locator: str
    directory_name: str
    short_name: str
    display_name: str
    project_dir: str


@dataclasses.dataclass(frozen=True)
class MetaRegisterResult:
    """Summary of one successful registration write."""

    directory_name: str
    project_id: str
    setup_state: str
    record_path: pathlib.Path


@dataclasses.dataclass(frozen=True)
class MetaRefreshResult:
    """Summary of one observation refresh write."""

    selector: str
    record_path: pathlib.Path
    setup_state: str
    checks: dict[str, dict[str, str]]


@dataclasses.dataclass(frozen=True)
class MetaSetResult:
    """Summary of one successful meta set/unset write."""

    selector: str
    record_path: pathlib.Path
    project_id: str
    updated_record: bool = False
    binding_paths: tuple[pathlib.Path, ...] = ()


@dataclasses.dataclass(frozen=True)
class MetaWorkspaceResolveOptions:
    """Optional explicit overrides for workspace resolution."""

    workspace_path: pathlib.Path | None = None
    config_path: pathlib.Path | None = None
    mode: Literal["hybrid", "local", "global"] | None = None


@dataclasses.dataclass(frozen=True)
class MetaWorkspace:
    """Resolved runtime workspace context for meta CLI commands."""

    mode: Literal["hybrid", "local", "global"]
    config_path: pathlib.Path
    projects_dir: pathlib.Path
    state_dir: pathlib.Path
    cache_dir: pathlib.Path
    catalog_root: pathlib.Path
    workspace_root: pathlib.Path | None
    config_dir: pathlib.Path
    resolution_source: str


@dataclasses.dataclass(frozen=True)
class MetaConfigKey:
    """Canonical metadata for supported ``lrh meta config`` keys."""

    canonical: str
    cli_name: str


_META_CONFIG_TRUST_KEY = MetaConfigKey(
    canonical="trusted_persistent_local_state",
    cli_name="trusted-persistent-local-state",
)


def _meta_config_key_map() -> dict[str, str]:
    return {
        _META_CONFIG_TRUST_KEY.canonical: _META_CONFIG_TRUST_KEY.canonical,
        _META_CONFIG_TRUST_KEY.cli_name: _META_CONFIG_TRUST_KEY.canonical,
    }


def normalize_meta_config_key(raw_key: str) -> str:
    key = raw_key.strip()
    if not key:
        raise MetaRegistryError("config key must not be empty")
    canonical = _meta_config_key_map().get(key)
    if canonical is None:
        raise MetaRegistryError(
            f"unknown config key {raw_key!r}; supported keys: "
            f"{_META_CONFIG_TRUST_KEY.cli_name}"
        )
    return canonical


def parse_meta_config_bool(raw_value: str) -> bool:
    value = raw_value.strip().lower()
    if value in {"true", "yes", "1"}:
        return True
    if value in {"false", "no", "0"}:
        return False
    raise MetaRegistryError(
        "invalid boolean value "
        f"{raw_value!r}; expected one of: true, false, yes, no, 1, 0"
    )


def _workspace_config_text(workspace: MetaWorkspace) -> str:
    try:
        return workspace.config_path.read_text(encoding="utf-8")
    except OSError as err:
        raise MetaRegistryError(
            f"unable to read workspace config at {workspace.config_path}: {err}"
        ) from err


def read_meta_config(workspace: MetaWorkspace) -> dict[str, bool]:
    parsed = tomllib.loads(_workspace_config_text(workspace))
    raw_meta = parsed.get("meta")
    if not isinstance(raw_meta, dict):
        raw_meta = {}
    trusted = raw_meta.get(_META_CONFIG_TRUST_KEY.canonical, False)
    if not isinstance(trusted, bool):
        raise MetaRegistryError(
            "invalid meta config type for trusted_persistent_local_state; expected bool"
        )
    return {_META_CONFIG_TRUST_KEY.canonical: trusted}


def get_meta_config_value(workspace: MetaWorkspace, key: str) -> bool:
    canonical = normalize_meta_config_key(key)
    return read_meta_config(workspace)[canonical]


def set_meta_config_value(workspace: MetaWorkspace, key: str, raw_value: str) -> bool:
    canonical = normalize_meta_config_key(key)
    bool_value = parse_meta_config_bool(raw_value)
    _set_meta_config_canonical(workspace, canonical, bool_value)
    return bool_value


def unset_meta_config_value(workspace: MetaWorkspace, key: str) -> bool:
    canonical = normalize_meta_config_key(key)
    _set_meta_config_canonical(workspace, canonical, False)
    return False


def _set_meta_config_canonical(
    workspace: MetaWorkspace, canonical_key: str, value: bool
) -> None:
    text = _workspace_config_text(workspace)
    key_line = f"{canonical_key} = {'true' if value else 'false'}"
    pattern = re.compile(rf"(?m)^\s*{re.escape(canonical_key)}\s*=\s*(true|false)\s*$")
    if pattern.search(text):
        updated = pattern.sub(key_line, text, count=1)
        workspace.config_path.write_text(updated, encoding="utf-8")
        return

    lines = text.splitlines()
    meta_header_index: int | None = None
    next_header_index: int | None = None
    for index, raw_line in enumerate(lines):
        stripped = raw_line.strip()
        if stripped == "[meta]":
            meta_header_index = index
            continue
        if (
            meta_header_index is not None
            and stripped.startswith("[")
            and stripped.endswith("]")
        ):
            next_header_index = index
            break

    if meta_header_index is None:
        updated = text.rstrip() + "\n\n[meta]\n" + key_line + "\n"
    else:
        insert_at = next_header_index if next_header_index is not None else len(lines)
        new_lines = [*lines[:insert_at], key_line, *lines[insert_at:]]
        updated = "\n".join(new_lines)
        if text.endswith("\n"):
            updated += "\n"
    workspace.config_path.write_text(updated, encoding="utf-8")


def storage_policy_for_workspace(workspace: MetaWorkspace):
    from lrh.meta import local_state_model

    trusted = get_meta_config_value(workspace, _META_CONFIG_TRUST_KEY.canonical)
    return local_state_model.storage_policy_from_trust(
        trusted_persistent_local_state=trusted
    )


@dataclasses.dataclass(frozen=True)
class MetaInspectResult:
    """Typed inspection payload for one selected project plus workspace context."""

    workspace: MetaWorkspace
    record: MetaProjectRecord
    resolved_repo_path: pathlib.Path | None
    repo_path_exists: bool | None
    resolved_project_path: pathlib.Path | None
    project_path_exists: bool | None
    source_state: str | None = None
    resolved_repo_path_source: str | None = None
    trusted_persistent_local_state: bool = False
    checkout_binding_storage: str = "none"
    observation_storage: str = "private"
    repo_locator_check: dict[str, str] | None = None
    local_repo_path_check: dict[str, str] | None = None
    project_path_check: dict[str, str] | None = None


def meta_workspace_where_payload(
    workspace: MetaWorkspace,
    *,
    lrh_version: str | None = None,
) -> dict[str, object]:
    """Build a structured diagnostics payload for ``lrh meta where`` output."""
    path_scope = _workspace_path_scope(workspace)
    normalized_lrh_version = lrh_version if lrh_version is not None else "unknown"
    workspace_root = (
        str(workspace.workspace_root) if workspace.workspace_root is not None else None
    )
    trusted_local_state = get_meta_config_value(
        workspace, _META_CONFIG_TRUST_KEY.canonical
    )
    return {
        "lrh_version": normalized_lrh_version,
        "mode": workspace.mode,
        "resolution_source": workspace.resolution_source,
        "config_path": str(workspace.config_path),
        "config_dir": str(workspace.config_dir),
        "catalog_root": str(workspace.catalog_root),
        "workspace_root": workspace_root,
        "projects_dir": str(workspace.projects_dir),
        "state_dir": str(workspace.state_dir),
        "cache_dir": str(workspace.cache_dir),
        "trusted_persistent_local_state": trusted_local_state,
        "path_scope": {
            "catalog": path_scope["catalog"],
            "config": path_scope["config"],
            "state": path_scope["state"],
            "cache": path_scope["cache"],
            "runtime_note": path_scope["runtime_note"],
        },
    }


def format_meta_workspace_where(
    workspace: MetaWorkspace,
    *,
    lrh_version: str | None = None,
) -> str:
    """Render user-facing diagnostics for resolved meta workspace context."""
    data = meta_workspace_where_payload(workspace, lrh_version=lrh_version)
    path_scope = data["path_scope"]
    lines = [
        "Active LRH meta workspace",
        "",
        f"lrh version: {data['lrh_version']}",
        f"mode: {data['mode']}",
        f"resolution source: {data['resolution_source']}",
        f"config: {data['config_path']} ({path_scope['config']})",
        f"config dir: {data['config_dir']}",
        f"catalog root: {data['catalog_root']} ({path_scope['catalog']})",
        f"projects: {data['projects_dir']} ({path_scope['catalog']})",
        f"state: {data['state_dir']} ({path_scope['state']})",
        f"cache: {data['cache_dir']} ({path_scope['cache']})",
        f"runtime: {path_scope['runtime_note']}",
        "trusted persistent local state: "
        f"{'true' if data['trusted_persistent_local_state'] else 'false'}",
    ]
    if data["workspace_root"] is not None:
        lines.append(f"workspace root: {data['workspace_root']}")
    return "\n".join(lines)


def _workspace_path_scope(workspace: MetaWorkspace) -> dict[str, str]:
    """Return path ownership/scope labels for each supported workspace mode."""
    mode = workspace.mode
    if mode == "local":
        return {
            "catalog": "local",
            "config": "local",
            "state": "local/private",
            "cache": "local/private",
            "runtime_note": "private/runtime state is local to this workspace root",
        }
    if mode == "hybrid":
        config_scope = "global/user"
        if _is_path_within(workspace.config_path, workspace.catalog_root):
            config_scope = "local/workspace"
        return {
            "catalog": "local/shareable",
            "config": config_scope,
            "state": "global/private",
            "cache": "global/private",
            "runtime_note": (
                "catalog is local/shareable; runtime state/cache are global+private"
            ),
        }
    return {
        "catalog": "global/user",
        "config": "global/user",
        "state": "global/private",
        "cache": "global/private",
        "runtime_note": "all paths resolve under global user locations",
    }


def _is_path_within(path: pathlib.Path, parent: pathlib.Path) -> bool:
    """Return true when ``path`` is inside ``parent`` (or equal)."""
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


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

    root = _normalize_path(root)
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
        mode="local",
        catalog_root=root,
        projects_dir=root / "projects",
        config_dir=root / ".lrh",
        state_dir=root / "private" / "state",
        cache_dir=root / "private" / "cache",
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


def init_hybrid_workspace(
    root: pathlib.Path,
    *,
    spec: MetaWorkspaceSpec,
    force: bool = False,
    environ: dict[str, str] | None = None,
) -> MetaInitResult:
    """Initialize a hybrid LRH workspace (local catalog + global runtime paths)."""
    if environ is None:
        environ = dict(os.environ)

    root = _normalize_path(root)
    config_path = _xdg_config_path(environ)
    config_dir = _normalize_path(config_path.parent)
    state_root = _normalize_path(_xdg_state_path(environ))
    cache_root = _normalize_path(_xdg_cache_path(environ))

    created: list[pathlib.Path] = []
    updated: list[pathlib.Path] = []
    unchanged: list[pathlib.Path] = []

    _ensure_directory(root / ".lrh", force=force, created=created)
    _ensure_directory(root / "projects", force=force, created=created)
    _ensure_directory(config_dir, force=force, created=created)
    _ensure_directory(state_root, force=force, created=created)
    _ensure_directory(state_root / "private", force=force, created=created)
    _ensure_directory(state_root / "private" / "state", force=force, created=created)
    _ensure_directory(cache_root, force=force, created=created)
    _ensure_directory(cache_root / "cache", force=force, created=created)

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
        mode="hybrid",
        catalog_root=root,
        projects_dir=root / "projects",
        config_dir=config_dir,
        state_dir=state_root / "private" / "state",
        cache_dir=cache_root / "cache",
        force=force,
        created=created,
        updated=updated,
        unchanged=unchanged,
    )
    _write_global_config(
        config_path,
        workspace_name=spec.workspace_name,
        mode="hybrid",
        catalog_root=root,
        projects_dir=root / "projects",
        config_dir=config_dir,
        state_dir=state_root / "private" / "state",
        cache_dir=cache_root / "cache",
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


def init_global_workspace(
    *,
    spec: MetaWorkspaceSpec,
    force: bool = False,
    environ: dict[str, str] | None = None,
) -> MetaInitResult:
    """Initialize a global (XDG-style) LRH workspace."""
    if environ is None:
        environ = dict(os.environ)

    config_path = _normalize_path(_xdg_config_path(environ))
    config_dir = _normalize_path(config_path.parent)
    state_root = _normalize_path(_xdg_state_path(environ))
    cache_root = _normalize_path(_xdg_cache_path(environ))

    created: list[pathlib.Path] = []
    updated: list[pathlib.Path] = []
    unchanged: list[pathlib.Path] = []

    _ensure_directory(config_dir, force=force, created=created)
    _ensure_directory(state_root, force=force, created=created)
    _ensure_directory(state_root / "projects", force=force, created=created)
    _ensure_directory(state_root / "private", force=force, created=created)

    for private_dir in ("logs", "chats", "state", "secrets"):
        _ensure_directory(
            state_root / "private" / private_dir,
            force=force,
            created=created,
        )

    _ensure_directory(cache_root, force=force, created=created)
    _ensure_directory(cache_root / "cache", force=force, created=created)
    _ensure_directory(cache_root / "tmp", force=force, created=created)

    _write_global_config(
        config_path,
        workspace_name=spec.workspace_name,
        mode="global",
        catalog_root=state_root,
        projects_dir=state_root / "projects",
        config_dir=config_dir,
        state_dir=state_root / "private" / "state",
        cache_dir=cache_root / "cache",
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
        try:
            _remove_existing_path(path)
        except OSError as err:
            raise MetaInitError(f"unable to replace path at {path}: {err}") from err
    if not path.exists():
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as err:
            raise MetaInitError(f"unable to create directory at {path}: {err}") from err
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
    mode: Literal["hybrid", "local", "global"],
    catalog_root: pathlib.Path,
    projects_dir: pathlib.Path,
    config_dir: pathlib.Path,
    state_dir: pathlib.Path,
    cache_dir: pathlib.Path,
    force: bool,
    created: list[pathlib.Path],
    updated: list[pathlib.Path],
    unchanged: list[pathlib.Path],
) -> None:
    content = _config_text(
        workspace_name=workspace_name,
        mode=mode,
        catalog_root=catalog_root,
        projects_dir=projects_dir,
        config_dir=config_dir,
        state_dir=state_dir,
        cache_dir=cache_dir,
    )
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


def _write_global_config(
    path: pathlib.Path,
    *,
    workspace_name: str,
    mode: Literal["hybrid", "global"],
    catalog_root: pathlib.Path,
    projects_dir: pathlib.Path,
    config_dir: pathlib.Path,
    state_dir: pathlib.Path,
    cache_dir: pathlib.Path,
    force: bool,
    created: list[pathlib.Path],
    updated: list[pathlib.Path],
    unchanged: list[pathlib.Path],
) -> None:
    content = _global_config_text(
        workspace_name=workspace_name,
        mode=mode,
        catalog_root=catalog_root,
        projects_dir=projects_dir,
        config_dir=config_dir,
        state_dir=state_dir,
        cache_dir=cache_dir,
    )
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
            f"found existing config with different content at {path}; "
            "rerun with --force to replace managed config"
        )

    path.write_text(content, encoding="utf-8")
    updated.append(path)


def _global_config_text(
    *,
    workspace_name: str,
    mode: Literal["hybrid", "global"],
    catalog_root: pathlib.Path,
    projects_dir: pathlib.Path,
    config_dir: pathlib.Path,
    state_dir: pathlib.Path,
    cache_dir: pathlib.Path,
) -> str:
    encoded_workspace_name = _toml_basic_string(workspace_name)
    encoded_catalog_root = _toml_basic_string(str(catalog_root))
    encoded_projects_dir = _toml_basic_string(str(projects_dir))
    encoded_config_dir = _toml_basic_string(str(config_dir))
    encoded_state_dir = _toml_basic_string(str(state_dir))
    encoded_cache_dir = _toml_basic_string(str(cache_dir))
    return (
        'schema_version = "0.1"\n\n'
        "[workspace]\n"
        f"name = {encoded_workspace_name}\n"
        f"mode = {_toml_basic_string(mode)}\n\n"
        "[paths]\n"
        f"catalog_root = {encoded_catalog_root}\n"
        f"projects_dir = {encoded_projects_dir}\n"
        f"config_dir = {encoded_config_dir}\n"
        f"state_dir = {encoded_state_dir}\n"
        f"cache_dir = {encoded_cache_dir}\n\n"
        "[meta]\n"
        'authority = "catalog_only"\n'
    )


def _config_text(
    *,
    workspace_name: str,
    mode: Literal["hybrid", "local", "global"],
    catalog_root: pathlib.Path,
    projects_dir: pathlib.Path,
    config_dir: pathlib.Path,
    state_dir: pathlib.Path,
    cache_dir: pathlib.Path,
) -> str:
    encoded_workspace_name = _toml_basic_string(workspace_name)
    encoded_catalog_root = _toml_basic_string(str(catalog_root))
    encoded_projects_dir = _toml_basic_string(str(projects_dir))
    encoded_config_dir = _toml_basic_string(str(config_dir))
    encoded_state_dir = _toml_basic_string(str(state_dir))
    encoded_cache_dir = _toml_basic_string(str(cache_dir))
    return (
        'schema_version = "0.1"\n\n'
        "[workspace]\n"
        f"name = {encoded_workspace_name}\n"
        f"mode = {_toml_basic_string(mode)}\n\n"
        "[paths]\n"
        f"catalog_root = {encoded_catalog_root}\n"
        f"projects_dir = {encoded_projects_dir}\n"
        f"config_dir = {encoded_config_dir}\n"
        f"state_dir = {encoded_state_dir}\n"
        f"cache_dir = {encoded_cache_dir}\n\n"
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
            mode_override=options.mode,
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
        if not config_path.exists():
            return _global_workspace_from_defaults(
                config_path=config_path,
                environ=environ,
                source="flag(--mode=global)+built_in_defaults",
            )
        return _workspace_from_config_path(
            config_path=config_path,
            mode_override="global",
            source="flag(--mode=global)+global_discovery",
            resolution_error=resolution_error,
            environ=environ,
        )
    if options.mode == "hybrid":
        config_path = _xdg_config_path(environ)
        if not config_path.exists():
            raise resolution_error
        return _workspace_from_config_path(
            config_path=config_path,
            mode_override="hybrid",
            source="flag(--mode=hybrid)+global_discovery",
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
    mode_override: Literal["hybrid", "local", "global"] | None,
    source: str,
    resolution_error: MetaWorkspaceResolutionError,
    environ: dict[str, str] | None = None,
) -> MetaWorkspace:
    config_path = _normalize_path(config_path)
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
    if mode == "hybrid":
        return _build_hybrid_workspace(
            config_path=config_path,
            parsed=parsed,
            source=source,
            environ=environ or dict(os.environ),
        )
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


def _mode_for_config_path(
    config_path: pathlib.Path,
) -> Literal["hybrid", "local", "global"]:
    if config_path.parent.name == ".lrh":
        return "local"
    return "global"


def _config_mode(
    parsed: dict[str, object],
) -> Literal["hybrid", "local", "global"] | None:
    workspace_data = parsed.get("workspace")
    if not isinstance(workspace_data, dict):
        return None
    raw_mode = workspace_data.get("mode")
    if raw_mode in ("hybrid", "local", "global"):
        return raw_mode
    return None


def _build_hybrid_workspace(
    *,
    config_path: pathlib.Path,
    parsed: dict[str, object],
    source: str,
    environ: dict[str, str],
) -> MetaWorkspace:
    config_path = _normalize_path(config_path)
    state_root = _normalize_path(_xdg_state_path(environ))
    cache_root = _normalize_path(_xdg_cache_path(environ))
    config_dir = _configured_path(
        parsed=parsed,
        key="config_dir",
        base_dir=config_path.parent,
        default=config_path.parent,
    )
    catalog_root = _configured_path(
        parsed=parsed,
        key="catalog_root",
        base_dir=config_path.parent,
        default=config_path.parent,
    )
    projects_dir = _configured_path(
        parsed=parsed,
        key="projects_dir",
        base_dir=catalog_root,
        default=catalog_root / "projects",
    )
    state_dir = _configured_path(
        parsed=parsed,
        key="state_dir",
        base_dir=config_dir,
        default=state_root / "private" / "state",
    )
    cache_dir = _configured_path(
        parsed=parsed,
        key="cache_dir",
        base_dir=config_dir,
        default=cache_root / "cache",
    )
    return MetaWorkspace(
        mode="hybrid",
        config_path=config_path,
        projects_dir=projects_dir,
        state_dir=state_dir,
        cache_dir=cache_dir,
        catalog_root=catalog_root,
        workspace_root=catalog_root,
        config_dir=config_dir,
        resolution_source=source,
    )


def _build_local_workspace(
    *,
    config_path: pathlib.Path,
    parsed: dict[str, object],
    source: str,
) -> MetaWorkspace:
    workspace_root = _normalize_path(config_path.parent.parent)
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
        catalog_root=workspace_root,
        workspace_root=workspace_root,
        config_dir=_configured_path(
            parsed=parsed,
            key="config_dir",
            base_dir=workspace_root,
            default=workspace_root / ".lrh",
        ),
        resolution_source=source,
    )


def _build_global_workspace(
    *,
    config_path: pathlib.Path,
    parsed: dict[str, object],
    source: str,
    environ: dict[str, str],
) -> MetaWorkspace:
    config_path = _normalize_path(config_path)
    state_root = _normalize_path(_xdg_state_path(environ))
    cache_root = _normalize_path(_xdg_cache_path(environ))
    config_dir = _configured_path(
        parsed=parsed,
        key="config_dir",
        base_dir=config_path.parent,
        default=config_path.parent,
    )
    catalog_root = _configured_path(
        parsed=parsed,
        key="catalog_root",
        base_dir=config_path.parent,
        default=state_root,
    )
    projects_dir = _configured_path(
        parsed=parsed,
        key="projects_dir",
        base_dir=config_path.parent,
        default=catalog_root / "projects",
    )
    state_dir = _configured_path(
        parsed=parsed,
        key="state_dir",
        base_dir=config_path.parent,
        default=state_root / "private" / "state",
    )
    cache_dir = _configured_path(
        parsed=parsed,
        key="cache_dir",
        base_dir=config_path.parent,
        default=cache_root / "cache",
    )
    return MetaWorkspace(
        mode="global",
        config_path=config_path,
        projects_dir=projects_dir,
        state_dir=state_dir,
        cache_dir=cache_dir,
        catalog_root=catalog_root,
        workspace_root=None,
        config_dir=config_dir,
        resolution_source=source,
    )


def _global_workspace_from_defaults(
    *,
    config_path: pathlib.Path,
    environ: dict[str, str],
    source: str,
) -> MetaWorkspace:
    return _build_global_workspace(
        config_path=config_path,
        parsed={},
        source=source,
        environ=environ,
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
        return _normalize_path(default)
    value = paths_data.get(key)
    if not isinstance(value, str) or not value.strip():
        return _normalize_path(default)
    path_value = pathlib.Path(value).expanduser()
    if path_value.is_absolute():
        return _normalize_path(path_value)
    return _normalize_path(base_dir / path_value)


def _discover_local_config(cwd: pathlib.Path) -> pathlib.Path | None:
    current = cwd.expanduser().resolve()
    for candidate in (current, *current.parents):
        config_path = candidate / ".lrh" / "config.toml"
        if config_path.exists() and config_path.is_file():
            return config_path
    return None


def _normalize_path(path: pathlib.Path) -> pathlib.Path:
    """Return a canonical absolute path for stable cross-platform comparisons."""
    return path.expanduser().resolve()


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
        "To initialize a hybrid workspace (default):\n"
        "  lrh meta init\n\n"
        "To initialize a global workspace:\n"
        "  lrh meta init --mode global\n\n"
        "To initialize a local workspace:\n"
        "  lrh meta init --mode local\n\n"
        "To override resolution explicitly:\n"
        "  lrh meta where --config /path/to/config.toml\n"
        "  lrh meta where --workspace /path/to/workspace\n"
        "  lrh meta where --mode {hybrid,local,global}"
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
        catalog_root=root,
        workspace_root=root,
        config_dir=root / ".lrh",
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
    projects_dir = _require_projects_dir(workspace.projects_dir, mode=workspace.mode)

    requested_repo_locator = _normalized_required_value(
        "repo_locator", spec.repo_locator
    )
    inferred = _infer_project_metadata(repo_locator=requested_repo_locator, spec=spec)
    repo_locator = inferred.repo_locator
    project_dir = inferred.project_dir
    directory_name = inferred.directory_name
    short_name = inferred.short_name
    display_name = inferred.display_name

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

    checks = _build_observations(
        repo_locator=repo_locator,
        project_dir=project_dir,
        workspace=workspace,
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
            checks=checks,
        ),
        encoding="utf-8",
    )

    return MetaRegisterResult(
        directory_name=directory_name,
        project_id=project_id,
        setup_state=setup_state,
        record_path=record_path,
    )


def _now_utc_iso() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


def _check_repo_locator(
    repo_locator: str,
    *,
    workspace: MetaWorkspace,
    resolved_repo_path: pathlib.Path | None,
) -> str:
    del workspace
    locator = _analyze_locator(repo_locator)
    if locator.kind == "local_path":
        if resolved_repo_path is None:
            return "invalid"
        return "valid" if resolved_repo_path.is_dir() else "invalid"
    if locator.kind == "github_url":
        return "skipped"
    if locator.kind == "url":
        return "unsupported"
    return "unknown"


def _check_local_repo_path(path: pathlib.Path | None) -> str:
    if path is None:
        return "unknown"
    try:
        return "exists" if path.is_dir() else "missing"
    except OSError:
        return "inaccessible"


def _check_project_path(
    *,
    resolved_repo_path: pathlib.Path | None,
    project_dir: str,
) -> str:
    if resolved_repo_path is None:
        return "unknown"
    project_subpath = pathlib.Path(project_dir)
    if project_subpath.is_absolute():
        return "inaccessible"
    resolved_project_path = _normalize_path(resolved_repo_path / project_subpath)
    try:
        resolved_project_path.relative_to(resolved_repo_path)
    except ValueError:
        return "inaccessible"
    if resolved_project_path is None:
        return "inaccessible"
    try:
        return "exists" if resolved_project_path.is_dir() else "missing"
    except OSError:
        return "inaccessible"


def _build_observations(
    *,
    repo_locator: str,
    project_dir: str,
    workspace: MetaWorkspace,
) -> dict[str, dict[str, str]]:
    now = _now_utc_iso()
    locator = _analyze_locator(repo_locator)
    resolved_repo_path = _resolved_local_repo_path(repo_locator, workspace=workspace)

    checks = {
        "repo_locator_check": {
            "status": _check_repo_locator(
                repo_locator,
                workspace=workspace,
                resolved_repo_path=resolved_repo_path,
            ),
            "checked_as_of": now,
        }
    }

    if locator.kind == "local_path":
        checks["local_repo_path_check"] = {
            "status": _check_local_repo_path(resolved_repo_path),
            "checked_as_of": now,
        }
        checks["project_path_check"] = {
            "status": _check_project_path(
                resolved_repo_path=resolved_repo_path,
                project_dir=project_dir,
            ),
            "checked_as_of": now,
        }
    else:
        checks["local_repo_path_check"] = {
            "status": "skipped",
            "checked_as_of": now,
        }
        checks["project_path_check"] = {
            "status": "skipped",
            "checked_as_of": now,
        }

    return checks


def _project_record_text(
    *,
    directory_name: str,
    short_name: str,
    display_name: str,
    project_id: str,
    repo_locator: str,
    project_dir: str,
    setup_state: str,
    checks: dict[str, dict[str, str]] | None = None,
) -> str:
    checks = checks or {}
    repo_locator_check = checks.get("repo_locator_check", {})
    local_repo_path_check = checks.get("local_repo_path_check", {})
    project_path_check = checks.get("project_path_check", {})
    repo_locator_check_status = repo_locator_check.get("status", "unknown")
    repo_locator_check_checked_as_of = repo_locator_check.get("checked_as_of", "")
    local_repo_path_check_status = local_repo_path_check.get("status", "unknown")
    local_repo_path_check_checked_as_of = local_repo_path_check.get("checked_as_of", "")
    project_path_check_status = project_path_check.get("status", "unknown")
    project_path_check_checked_as_of = project_path_check.get("checked_as_of", "")
    obs_lines = [
        f"repo_locator_check_status = {_toml_basic_string(repo_locator_check_status)}",
        "repo_locator_check_checked_as_of = "
        f"{_toml_basic_string(repo_locator_check_checked_as_of)}",
        "local_repo_path_check_status = "
        f"{_toml_basic_string(local_repo_path_check_status)}",
        "local_repo_path_check_checked_as_of = "
        f"{_toml_basic_string(local_repo_path_check_checked_as_of)}",
        f"project_path_check_status = {_toml_basic_string(project_path_check_status)}",
        "project_path_check_checked_as_of = "
        f"{_toml_basic_string(project_path_check_checked_as_of)}",
    ]

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
            "[observations]",
            *obs_lines,
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


def _infer_project_metadata(
    *, repo_locator: str, spec: MetaRegisterSpec
) -> InferredProjectMetadata:
    analysis = _analyze_locator(repo_locator)
    project_dir_override = _normalized_optional_value(spec.project_dir)
    project_dir = project_dir_override or analysis.project_dir_hint or "project"
    project_dir = _normalized_required_value("project_dir", project_dir)
    normalized_repo_locator = _normalized_repo_locator(
        repo_locator,
        analysis,
        project_dir_override,
    )

    inferred_base_name = _best_locator_name_candidate(analysis)

    directory_name = _normalized_directory_name(spec.directory_name, inferred_base_name)
    short_name = _normalized_optional_value(spec.short_name) or directory_name
    display_name = _normalized_optional_value(spec.display_name) or _display_from_name(
        short_name
    )

    return InferredProjectMetadata(
        repo_locator=normalized_repo_locator,
        directory_name=directory_name,
        short_name=short_name,
        display_name=display_name,
        project_dir=project_dir,
    )


def _normalized_repo_locator(
    repo_locator: str,
    analysis: LocatorAnalysis,
    project_dir_override: str | None,
) -> str:
    """Normalize GitHub tree locators so repo identity excludes project subpaths."""
    if project_dir_override is not None:
        return repo_locator
    if analysis.kind != "github_url" or analysis.repo_ref is None:
        return repo_locator
    if analysis.repo_subpath is None:
        return repo_locator

    parsed = urllib.parse.urlsplit(repo_locator)
    subpath_suffix = "/" + analysis.repo_subpath.strip("/")
    if not parsed.path.endswith(subpath_suffix):
        return repo_locator
    normalized_path = parsed.path[: -len(subpath_suffix)].rstrip("/")
    normalized_segments = [segment for segment in normalized_path.split("/") if segment]
    if len(normalized_segments) < 4 or normalized_segments[2] != "tree":
        return repo_locator
    return urllib.parse.urlunsplit(
        (
            parsed.scheme,
            parsed.netloc,
            normalized_path,
            parsed.query,
            parsed.fragment,
        )
    )


def _normalized_directory_name(
    directory_name: str | None, inferred_base_name: str | None
) -> str:
    requested = _normalized_optional_value(directory_name)
    if requested is None:
        requested = inferred_base_name or "project"
    normalized = _normalized_slug_token(requested)
    if not normalized:
        raise MetaRegistryError("unable to derive a valid registry directory name")
    return normalized


def _analyze_locator(repo_locator: str) -> LocatorAnalysis:
    parsed = urllib.parse.urlsplit(repo_locator)
    if parsed.scheme and parsed.netloc:
        return _analyze_url_locator(parsed)
    if "://" in repo_locator:
        return LocatorAnalysis(kind="unknown")
    return _analyze_local_locator(repo_locator)


def _analyze_url_locator(parsed: urllib.parse.SplitResult) -> LocatorAnalysis:
    path_segments = [segment for segment in parsed.path.split("/") if segment]
    path_tail = path_segments[-1] if path_segments else None
    host = (parsed.hostname or parsed.netloc).lower()

    if host.endswith("github.com") and len(path_segments) >= 2:
        owner = path_segments[0]
        repo_slug = _clean_repo_slug(path_segments[1])
        repo_ref = None
        repo_subpath = None
        project_dir_hint = None
        if len(path_segments) >= 4 and path_segments[2] == "tree":
            repo_ref = path_segments[3]
            project_tail_segments = path_segments[4:]
            if project_tail_segments:
                repo_subpath = "/".join(project_tail_segments)
                project_dir_hint = repo_subpath
        return LocatorAnalysis(
            kind="github_url",
            host=host,
            repo_owner=owner,
            repo_slug=repo_slug,
            repo_ref=repo_ref,
            repo_subpath=repo_subpath,
            path_tail=path_tail,
            project_dir_hint=project_dir_hint,
        )

    return LocatorAnalysis(
        kind="url",
        host=host,
        path_tail=path_tail,
    )


def _analyze_local_locator(repo_locator: str) -> LocatorAnalysis:
    stripped = repo_locator.strip()
    if not stripped:
        return LocatorAnalysis(kind="unknown")
    local_path = pathlib.Path(stripped).expanduser()
    local_name = local_path.name or local_path.parent.name
    return LocatorAnalysis(
        kind="local_path",
        local_basename=local_name if local_name else None,
        path_tail=local_name if local_name else None,
    )


def _clean_repo_slug(segment: str) -> str | None:
    cleaned = segment.strip()
    if cleaned.endswith(".git"):
        cleaned = cleaned[:-4]
    cleaned = cleaned.strip()
    return cleaned if cleaned else None


def _best_locator_name_candidate(analysis: LocatorAnalysis) -> str | None:
    preferred = _normalized_slug_token(analysis.repo_slug)
    if preferred:
        return preferred
    local_name = _normalized_slug_token(analysis.local_basename)
    if local_name:
        return local_name
    tail = analysis.path_tail
    normalized_tail = _normalized_slug_token(tail)
    if normalized_tail and normalized_tail not in _GENERIC_NAME_SEGMENTS:
        return normalized_tail
    return None


_GENERIC_NAME_SEGMENTS = frozenset(
    {
        "main",
        "project",
        "repo",
        "root",
        "src",
    }
)


def _normalized_slug_token(value: str | None) -> str | None:
    normalized = _normalized_optional_value(value)
    if normalized is None:
        return None
    collapsed = normalized.lower()
    collapsed = re.sub(r"[^a-z0-9._-]+", "-", collapsed)
    collapsed = collapsed.strip(".-_")
    return collapsed if collapsed else None


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
    locator = _analyze_locator(repo_locator)
    if locator.kind != "local_path":
        return "not_checked"
    repo_path = pathlib.Path(repo_locator).expanduser()
    if repo_path.is_dir() and (repo_path / project_dir).is_dir():
        return "lrh_project_present"
    return "not_set_up"


def _stable_project_id(repo_locator: str, project_dir: str) -> str:
    source = f"{repo_locator}\n{project_dir}".encode("utf-8")
    digest = hashlib.sha256(source).hexdigest()
    return f"proj-{digest[:16]}"


def set_project_fields_in_workspace(
    workspace: MetaWorkspace,
    *,
    selector: str,
    local_repo_path: str | None = None,
    project_dir: str | None = None,
    short_name: str | None = None,
    display_name: str | None = None,
) -> MetaSetResult:
    normalized_selector = selector.strip()
    if not normalized_selector:
        raise MetaRegistryError("project selector must not be empty")

    record = _resolve_single_record(workspace, selector=normalized_selector)
    if record.project_id is None:
        raise MetaRegistryError("selected record is missing project_id")
    updates = 0
    canonical_local_repo_path: str | None = None
    validated_project_dir: str | None = None
    normalized_short_name: str | None = None
    normalized_display_name: str | None = None

    if local_repo_path is not None:
        canonical_local_repo_path = _canonical_local_repo_path(local_repo_path)
    if project_dir is not None:
        validated_project_dir = _validate_project_dir(project_dir)
    if short_name is not None:
        normalized_short_name = _normalized_required_value("short_name", short_name)
    if display_name is not None:
        normalized_display_name = _normalized_required_value(
            "display_name", display_name
        )

    binding_paths: tuple[pathlib.Path, ...] = ()
    if local_repo_path is not None:
        binding_path = _set_checkout_binding(
            workspace=workspace,
            project_id=record.project_id,
            canonical_local_repo_path=canonical_local_repo_path,
        )
        binding_paths = (binding_path,)
        updates += 1

    record_path = workspace.projects_dir / record.registry_name / "project.toml"
    updated_record = False
    if any(value is not None for value in (project_dir, short_name, display_name)):
        _update_project_record_fields(
            record_path=record_path,
            project_dir=validated_project_dir,
            short_name=normalized_short_name,
            display_name=normalized_display_name,
        )
        updated_record = True
        updates += 1

    if updates == 0:
        raise MetaRegistryError("meta set requires at least one field flag")

    return MetaSetResult(
        selector=selector,
        record_path=record_path,
        project_id=record.project_id,
        updated_record=updated_record,
        binding_paths=binding_paths,
    )


def unset_project_fields_in_workspace(
    workspace: MetaWorkspace,
    *,
    selector: str,
    local_repo_path: bool = False,
) -> MetaSetResult:
    normalized_selector = selector.strip()
    if not normalized_selector:
        raise MetaRegistryError("project selector must not be empty")
    if not local_repo_path:
        raise MetaRegistryError("meta unset requires at least one field flag")

    record = _resolve_single_record(workspace, selector=normalized_selector)
    if record.project_id is None:
        raise MetaRegistryError("selected record is missing project_id")
    binding_paths = _unset_checkout_binding(
        workspace=workspace, project_id=record.project_id
    )
    return MetaSetResult(
        selector=selector,
        record_path=workspace.projects_dir / record.registry_name / "project.toml",
        project_id=record.project_id,
        updated_record=False,
        binding_paths=binding_paths,
    )


def _resolve_single_record(
    workspace: MetaWorkspace, *, selector: str
) -> MetaProjectRecord:
    records = list_registered_projects_in_workspace(workspace)
    candidates = _matching_records(records, selector=selector)
    if not candidates:
        raise MetaRegistryError(
            "no registered project matched selector "
            f"{selector!r} (checked project_id, short_name, registry_name)"
        )
    if len(candidates) > 1:
        matched_names = ", ".join(record.registry_name for record in candidates)
        raise MetaRegistryError(
            "ambiguous project selector "
            f"{selector!r}; matching registry entries: {matched_names}"
        )
    return candidates[0]


def _validate_project_dir(value: str) -> str:
    normalized = _normalized_required_value("project_dir", value)
    path = pathlib.Path(normalized)
    if path.is_absolute():
        raise MetaRegistryError("project_dir must be relative to repo root")
    if any(segment == ".." for segment in path.parts):
        raise MetaRegistryError(
            "project_dir must not contain traversal segments ('..')"
        )
    return normalized


def _canonical_local_repo_path(raw_path: str) -> str:
    normalized = _normalized_required_value("local_repo_path", raw_path)
    return str(pathlib.Path(normalized).expanduser().resolve())


def _update_project_record_fields(
    *,
    record_path: pathlib.Path,
    project_dir: str | None,
    short_name: str | None,
    display_name: str | None,
) -> None:
    parsed = tomllib.loads(record_path.read_text(encoding="utf-8"))
    project_data = _required_table(parsed, record_path, "project")
    locators_data = _required_table(parsed, record_path, "locators")

    if project_dir is not None:
        locators_data["project_dir"] = project_dir
    if short_name is not None:
        project_data["short_name"] = short_name
    if display_name is not None:
        project_data["display_name"] = display_name

    _write_project_record_tables(record_path, parsed)


def _write_project_record_tables(
    record_path: pathlib.Path, parsed: dict[str, object]
) -> None:
    project_data = _required_table(parsed, record_path, "project")
    identity_data = _required_table(parsed, record_path, "identity")
    locators_data = _required_table(parsed, record_path, "locators")
    registry_data = _required_table(parsed, record_path, "registry")
    obs_data = _required_table(parsed, record_path, "observations")

    content = _project_record_text(
        directory_name=_normalized_required_value(
            "directory_name", str(registry_data["directory_name"])
        ),
        short_name=_normalized_required_value(
            "short_name", str(project_data["short_name"])
        ),
        display_name=_normalized_required_value(
            "display_name", str(project_data["display_name"])
        ),
        project_id=_normalized_required_value(
            "project_id", str(identity_data["project_id"])
        ),
        repo_locator=_normalized_required_value(
            "repo_locator", str(locators_data["repo_locator"])
        ),
        project_dir=_normalized_required_value(
            "project_dir", str(locators_data["project_dir"])
        ),
        setup_state=_normalized_required_value(
            "setup_state", str(project_data.get("setup_state", "not_checked"))
        ),
        checks={
            "repo_locator_check": {
                "status": str(obs_data.get("repo_locator_check_status", "unknown")),
                "checked_as_of": str(
                    obs_data.get("repo_locator_check_checked_as_of", "")
                ),
            },
            "local_repo_path_check": {
                "status": str(obs_data.get("local_repo_path_check_status", "unknown")),
                "checked_as_of": str(
                    obs_data.get("local_repo_path_check_checked_as_of", "")
                ),
            },
            "project_path_check": {
                "status": str(obs_data.get("project_path_check_status", "unknown")),
                "checked_as_of": str(
                    obs_data.get("project_path_check_checked_as_of", "")
                ),
            },
        },
    )
    record_path.write_text(content, encoding="utf-8")


def _bindings_file_path(workspace: MetaWorkspace, *, trusted: bool) -> pathlib.Path:
    if trusted:
        return workspace.catalog_root / ".lrh" / "trusted_local_state.toml"
    return workspace.state_dir / "local_state.toml"


def _set_checkout_binding(
    *, workspace: MetaWorkspace, project_id: str, canonical_local_repo_path: str | None
) -> pathlib.Path:
    if canonical_local_repo_path is None:
        raise MetaRegistryError("local_repo_path must not be empty")
    trusted = read_meta_config(workspace)["trusted_persistent_local_state"]
    binding_path = _bindings_file_path(workspace, trusted=trusted)
    _write_binding(binding_path, project_id, canonical_local_repo_path)
    return binding_path


def _unset_checkout_binding(
    *, workspace: MetaWorkspace, project_id: str
) -> tuple[pathlib.Path, ...]:
    updated_paths: list[pathlib.Path] = []
    for trusted in (False, True):
        binding_path = _bindings_file_path(workspace, trusted=trusted)
        did_write = _write_binding(binding_path, project_id, None)
        if did_write:
            updated_paths.append(binding_path)
    return tuple(updated_paths)


def _write_binding(
    path: pathlib.Path, project_id: str, local_repo_path: str | None
) -> bool:
    data: dict[str, str] = {}
    if path.exists():
        parsed = tomllib.loads(path.read_text(encoding="utf-8"))
        raw_bindings = parsed.get("bindings", {})
        if isinstance(raw_bindings, dict):
            for key, value in raw_bindings.items():
                if isinstance(key, str) and isinstance(value, str):
                    data[key] = value
    elif local_repo_path is None:
        return False
    previous = data.get(project_id)
    if local_repo_path is None:
        data.pop(project_id, None)
    else:
        data[project_id] = local_repo_path
    if previous == local_repo_path:
        return False
    if local_repo_path is None and project_id not in data and previous is None:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ['schema_version = "0.1"', "", "[bindings]"]
    for key in sorted(data):
        lines.append(f"{_toml_basic_string(key)} = {_toml_basic_string(data[key])}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def refresh_project_observations_in_workspace(
    workspace: MetaWorkspace,
    *,
    selector: str,
) -> MetaRefreshResult:
    normalized_selector = selector.strip()
    if not normalized_selector:
        raise MetaRegistryError("project selector must not be empty")

    records = list_registered_projects_in_workspace(workspace)
    candidates = _matching_records(records, selector=normalized_selector)
    if not candidates:
        raise MetaRegistryError(
            "no registered project matched selector "
            f"{normalized_selector!r} (checked project_id, short_name, registry_name)"
        )
    if len(candidates) > 1:
        matched_names = ", ".join(record.registry_name for record in candidates)
        raise MetaRegistryError(
            "ambiguous project selector "
            f"{normalized_selector!r}; matching registry entries: {matched_names}"
        )

    record = candidates[0]
    if record.repo_locator is None or record.project_dir is None:
        raise MetaRegistryError("selected record is missing locator fields")
    setup_state = _detect_setup_state(record.repo_locator, record.project_dir)
    checks = _build_observations(
        repo_locator=record.repo_locator,
        project_dir=record.project_dir,
        workspace=workspace,
    )
    record_path = workspace.projects_dir / record.registry_name / "project.toml"
    _update_observations_block(
        record_path=record_path,
        setup_state=setup_state,
        checks=checks,
    )
    return MetaRefreshResult(
        selector=selector,
        record_path=record_path,
        setup_state=setup_state,
        checks=checks,
    )


def _update_observations_block(
    *,
    record_path: pathlib.Path,
    setup_state: str,
    checks: dict[str, dict[str, str]],
) -> None:
    content = record_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    def _section_range(section_name: str) -> tuple[int, int] | None:
        header = f"[{section_name}]"
        start = None
        for index, line in enumerate(lines):
            if line.strip() == header:
                start = index
                break
        if start is None:
            return None
        end = len(lines)
        for index in range(start + 1, len(lines)):
            stripped = lines[index].strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                end = index
                break
        return start, end

    project_range = _section_range("project")
    if project_range is not None:
        start, end = project_range
        for index in range(start + 1, end):
            if lines[index].strip().startswith("setup_state"):
                lines[index] = f"setup_state = {_toml_basic_string(setup_state)}"
                break

    now = _now_utc_iso()
    repo_locator_check = checks.get("repo_locator_check", {})
    local_repo_path_check = checks.get("local_repo_path_check", {})
    project_path_check = checks.get("project_path_check", {})

    new_obs_block = [
        "[observations]",
        "repo_locator_check_status = "
        f"{_toml_basic_string(repo_locator_check.get('status', 'unknown'))}",
        "repo_locator_check_checked_as_of = "
        f"{_toml_basic_string(repo_locator_check.get('checked_as_of', now))}",
        "local_repo_path_check_status = "
        f"{_toml_basic_string(local_repo_path_check.get('status', 'skipped'))}",
        "local_repo_path_check_checked_as_of = "
        f"{_toml_basic_string(local_repo_path_check.get('checked_as_of', now))}",
        "project_path_check_status = "
        f"{_toml_basic_string(project_path_check.get('status', 'skipped'))}",
        "project_path_check_checked_as_of = "
        f"{_toml_basic_string(project_path_check.get('checked_as_of', now))}",
    ]

    obs_range = _section_range("observations")
    if obs_range is None:
        registry_range = _section_range("registry")
        if registry_range is None:
            lines.extend([""] + new_obs_block + [""])
        else:
            start, _ = registry_range
            lines = lines[:start] + new_obs_block + [""] + lines[start:]
    else:
        start, end = obs_range
        lines = lines[:start] + new_obs_block + lines[end:]

    record_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def list_registered_projects(root: pathlib.Path) -> tuple[MetaProjectRecord, ...]:
    """Load project records from ``root/projects`` in stable directory order."""
    local_workspace = MetaWorkspace(
        mode="local",
        config_path=root / ".lrh" / "config.toml",
        projects_dir=root / "projects",
        state_dir=root / "private" / "state",
        cache_dir=root / "private" / "cache",
        catalog_root=root,
        workspace_root=root,
        config_dir=root / ".lrh",
        resolution_source="legacy(root)",
    )
    return list_registered_projects_in_workspace(local_workspace)


def list_registered_projects_in_workspace(
    workspace: MetaWorkspace,
) -> tuple[MetaProjectRecord, ...]:
    """Load project records in stable directory order from workspace projects_dir."""
    results = list_registered_project_loads_in_workspace(workspace)
    records: list[MetaProjectRecord] = []
    for result in results:
        if result.record is None:
            raise MetaRegistryError(
                result.error or "project record could not be loaded"
            )
        records.append(result.record)
    return tuple(records)


def list_registered_project_loads_in_workspace(
    workspace: MetaWorkspace,
) -> tuple[MetaProjectLoadResult, ...]:
    """Load project records in stable order while isolating per-record failures."""

    projects_dir = _require_projects_dir(workspace.projects_dir, mode=workspace.mode)

    try:
        project_entries = sorted(projects_dir.iterdir(), key=lambda entry: entry.name)
    except OSError as err:
        raise MetaRegistryError(
            f"unable to enumerate registry directory {projects_dir}: {err}"
        ) from err

    results: list[MetaProjectLoadResult] = []
    for record_dir in project_entries:
        if not record_dir.is_dir():
            continue
        try:
            record = _load_project_record(record_dir)
        except MetaRegistryError as err:
            results.append(
                MetaProjectLoadResult(
                    registry_name=record_dir.name,
                    record=None,
                    error=str(err),
                )
            )
        else:
            results.append(
                MetaProjectLoadResult(
                    registry_name=record.registry_name,
                    record=record,
                )
            )
    return tuple(results)


def _require_projects_dir(
    projects_dir: pathlib.Path,
    *,
    mode: Literal["hybrid", "local", "global"] | None = None,
) -> pathlib.Path:
    if not projects_dir.exists():
        local_guidance = (
            "run `lrh meta init --mode local` to initialize a local workspace"
        )
        if mode == "global":
            guidance = (
                "run `lrh meta init --mode global` "
                "to initialize the global workspace"
            )
        elif mode == "local":
            guidance = local_guidance
        elif mode == "hybrid":
            guidance = "run `lrh meta init` to initialize a hybrid workspace"
        else:
            guidance = (
                f"{local_guidance}, run `lrh meta init` for hybrid defaults, "
                "or run `lrh meta init --mode global`"
            )
        raise MetaRegistryError(
            f"missing projects directory at {projects_dir}; {guidance}"
        )
    if not projects_dir.is_dir():
        raise MetaRegistryError(f"expected directory at {projects_dir}")
    return projects_dir


def format_project_records(
    records: tuple[MetaProjectRecord, ...],
    *,
    workspace: MetaWorkspace | None = None,
) -> str:
    """Render records as plain, inspectable text for ``lrh meta list``."""
    if not records:
        return "No registered projects found under projects/."

    lines: list[str] = []
    for index, record in enumerate(records, start=1):
        if index > 1:
            lines.append("")
        lines.extend(
            _format_project_record_lines(
                index=index,
                record=record,
                workspace=workspace,
            )
        )
    return "\n".join(lines)


def _format_project_record_lines(
    *, index: int, record: MetaProjectRecord, workspace: MetaWorkspace | None
) -> list[str]:
    lines = [
        f"[{index}] {record.registry_name}",
        f"  registry_name: {record.registry_name}",
        f"  short_name: {_display_value(record.short_name)}",
        f"  display_name: {_display_value(record.display_name)}",
        f"  project_id: {_display_value(record.project_id)}",
        f"  repo_locator: {_display_value(record.repo_locator)}",
        f"  project_dir: {_display_value(record.project_dir)}",
        f"  setup_state: {_display_value(record.setup_state)}",
    ]
    if workspace is None:
        return lines
    observations = _read_project_observations(
        workspace, registry_name=record.registry_name
    )
    setup_checked_as_of = _lookup_latest_checked_as_of(observations)
    checkout_storage = _resolve_checkout_storage(
        workspace=workspace,
        project_id=record.project_id,
    )
    lines.extend(
        [
            f"  setup_checked_as_of: {setup_checked_as_of}",
            f"  checkout_storage: {checkout_storage}",
        ]
    )
    return lines


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


def inspect_registered_project_in_workspace(
    workspace: MetaWorkspace,
    *,
    selector: str,
) -> MetaInspectResult:
    """Inspect one registered project selected by exact id/short-name/registry-name."""
    normalized_selector = selector.strip()
    if not normalized_selector:
        raise MetaRegistryError("project selector must not be empty")

    records = list_registered_projects_in_workspace(workspace)
    candidates = _matching_records(records, selector=normalized_selector)
    if not candidates:
        raise MetaRegistryError(
            "no registered project matched selector "
            f"{normalized_selector!r} (checked project_id, short_name, registry_name)"
        )
    if len(candidates) > 1:
        matched_names = ", ".join(record.registry_name for record in candidates)
        raise MetaRegistryError(
            "ambiguous project selector "
            f"{normalized_selector!r}; matching registry entries: {matched_names}"
        )

    record = candidates[0]
    from lrh.meta import local_state_model

    trusted_persistent_local_state = get_meta_config_value(
        workspace, _META_CONFIG_TRUST_KEY.canonical
    )
    storage_policy = storage_policy_for_workspace(workspace)
    observations = _read_project_observations(
        workspace, registry_name=record.registry_name
    )
    checks = _observations_to_checks(observations)

    private_binding = _read_checkout_binding(
        workspace, project_id=record.project_id, trusted=False
    )
    trusted_binding = _read_checkout_binding(
        workspace, project_id=record.project_id, trusted=True
    )
    resolved_context = local_state_model.resolve_project_context(
        record,
        workspace_context=workspace,
        request=local_state_model.ResolveContextRequest(
            private_checkout_binding=private_binding,
            trusted_checkout_binding=trusted_binding,
            storage_policy=storage_policy,
        ),
    )
    resolved_repo_path = resolved_context.resolved_repo_path
    repo_exists = (
        resolved_repo_path.exists() if resolved_repo_path is not None else None
    )
    resolved_project_path = resolved_context.resolved_project_path
    project_exists = (
        resolved_project_path.exists() if resolved_project_path is not None else None
    )
    checks = _effective_checks_from_resolved_paths(
        checks=checks,
        repo_exists=repo_exists,
        project_exists=project_exists,
    )
    checkout_binding_storage = "none"
    if private_binding is not None:
        checkout_binding_storage = "private"
    elif trusted_binding is not None and trusted_persistent_local_state:
        checkout_binding_storage = "workspace"
    observation_storage = "workspace" if trusted_persistent_local_state else "private"

    return MetaInspectResult(
        workspace=workspace,
        record=record,
        resolved_repo_path=resolved_repo_path,
        repo_path_exists=repo_exists,
        resolved_project_path=resolved_project_path,
        project_path_exists=project_exists,
        source_state=resolved_context.source_state,
        resolved_repo_path_source=resolved_context.resolved_repo_path_source,
        trusted_persistent_local_state=trusted_persistent_local_state,
        checkout_binding_storage=checkout_binding_storage,
        observation_storage=observation_storage,
        repo_locator_check=checks["repo_locator_check"],
        local_repo_path_check=checks["local_repo_path_check"],
        project_path_check=checks["project_path_check"],
    )


def _matching_records(
    records: tuple[MetaProjectRecord, ...],
    *,
    selector: str,
) -> tuple[MetaProjectRecord, ...]:
    return tuple(
        record
        for record in records
        if selector in (record.project_id, record.short_name, record.registry_name)
    )


def _resolved_local_repo_path(
    repo_locator: str | None,
    *,
    workspace: MetaWorkspace,
) -> pathlib.Path | None:
    if repo_locator is None:
        return None
    parsed = urllib.parse.urlsplit(repo_locator)
    if parsed.scheme and parsed.netloc:
        return None
    if "://" in repo_locator:
        return None
    repo_path = pathlib.Path(repo_locator).expanduser()
    if repo_path.is_absolute():
        return _normalize_path(repo_path)

    base_dir = workspace.workspace_root
    if base_dir is None:
        base_dir = workspace.config_path.parent
    return _normalize_path(base_dir / repo_path)


def format_project_inspect(result: MetaInspectResult) -> str:
    """Render inspect output with stored record fields and minimal derived context."""
    workspace_data = result.workspace
    record = result.record
    lines = [
        "Workspace:",
        f"  mode: {workspace_data.mode}",
        f"  resolution_source: {workspace_data.resolution_source}",
        f"  projects_dir: {workspace_data.projects_dir}",
        "",
        "Identity:",
        f"  registry_name: {record.registry_name}",
        f"  project_id: {_display_value(record.project_id)}",
        f"  short_name: {_display_value(record.short_name)}",
        f"  display_name: {_display_value(record.display_name)}",
        f"  repo_locator: {_display_value(record.repo_locator)}",
        "  repo_locator_check: " f"{_format_check_value(result.repo_locator_check)}",
        "",
        "Checkout:",
        f"  local_repo_path: {_display_path(result.resolved_repo_path)}",
        f"  storage: {result.checkout_binding_storage}",
        "  resolved_repo_path_source: "
        f"{_display_value(result.resolved_repo_path_source)}",
        "  local_repo_path_check: "
        f"{_format_check_value(result.local_repo_path_check)}",
        "",
        "Project:",
        f"  project_dir: {_display_value(record.project_dir)}",
        f"  resolved_repo_path: {_display_path(result.resolved_repo_path)}",
        f"  resolved_project_path: {_display_path(result.resolved_project_path)}",
        "  project_path_check: " f"{_format_check_value(result.project_path_check)}",
        "",
        "Storage:",
        "  trusted_persistent_local_state: "
        f"{str(result.trusted_persistent_local_state).lower()}",
        f"  checkout_binding_storage: {result.checkout_binding_storage}",
        f"  observation_storage: {result.observation_storage}",
        "",
        "Setup:",
        f"  source_state: {_display_value(result.source_state)}",
        f"  setup_state: {_display_value(record.setup_state)}",
    ]
    if workspace_data.workspace_root is not None:
        lines.insert(4, f"  workspace_root: {workspace_data.workspace_root}")
    return "\n".join(lines)


def _display_optional_bool(value: bool | None) -> str:
    if value is None:
        return "<not_applicable>"
    return "true" if value else "false"


def _display_path(path: pathlib.Path | None) -> str:
    if path is None:
        return "<not_applicable>"
    return str(path)


def _read_checkout_binding(
    workspace: MetaWorkspace, *, project_id: str | None, trusted: bool
):
    if not project_id:
        return None
    binding_path = _bindings_file_path(workspace, trusted=trusted)
    if not binding_path.exists():
        return None
    parsed = _read_toml_file(binding_path, context="checkout bindings")
    raw_bindings = parsed.get("bindings", {})
    if not isinstance(raw_bindings, dict):
        return None
    local_repo_path = raw_bindings.get(project_id)
    if not isinstance(local_repo_path, str):
        return None
    from lrh.meta import local_state_model

    return local_state_model.CheckoutBinding(
        local_repo_path=pathlib.Path(local_repo_path),
        storage_source="trusted_workspace" if trusted else "private_runtime",
    )


def _format_check_value(check: dict[str, str] | None) -> str:
    if check is None:
        return "<unknown>"
    status = check.get("status", "unknown")
    checked = check.get("checked_as_of", "")
    if checked:
        return f"{status} as of {checked}"
    return status


def _read_project_observations(
    workspace: MetaWorkspace, *, registry_name: str
) -> dict[str, str]:
    project_file = workspace.projects_dir / registry_name / "project.toml"
    parsed = _read_toml_file(project_file, context="project record")
    observations = _optional_table(parsed, "observations")
    if observations is None:
        return {}
    return {str(key): str(value) for key, value in observations.items()}


def _read_toml_file(path: pathlib.Path, *, context: str) -> dict[str, object]:
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as err:
        raise MetaRegistryError(f"{context} is not valid UTF-8: {path}") from err
    except OSError as err:
        raise MetaRegistryError(f"unable to read {context} file {path}: {err}") from err
    try:
        parsed = tomllib.loads(content)
    except tomllib.TOMLDecodeError as err:
        raise MetaRegistryError(f"invalid TOML in {path}: {err}") from err
    if not isinstance(parsed, dict):
        raise MetaRegistryError(f"expected TOML table in {path}")
    return parsed


def _observations_to_checks(observations: dict[str, str]) -> dict[str, dict[str, str]]:
    return {
        "repo_locator_check": {
            "status": observations.get("repo_locator_check_status", "unknown"),
            "checked_as_of": observations.get("repo_locator_check_checked_as_of", ""),
        },
        "local_repo_path_check": {
            "status": observations.get("local_repo_path_check_status", "unknown"),
            "checked_as_of": observations.get(
                "local_repo_path_check_checked_as_of", ""
            ),
        },
        "project_path_check": {
            "status": observations.get("project_path_check_status", "unknown"),
            "checked_as_of": observations.get("project_path_check_checked_as_of", ""),
        },
    }


def _optional_table(parsed: dict[str, object], key: str) -> dict[str, object] | None:
    value = parsed.get(key)
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    raise MetaRegistryError(f"expected [{key}] table to be a mapping")


def _effective_checks_from_resolved_paths(
    *,
    checks: dict[str, dict[str, str]],
    repo_exists: bool | None,
    project_exists: bool | None,
) -> dict[str, dict[str, str]]:
    effective = dict(checks)
    now = datetime.datetime.now(datetime.UTC).isoformat()
    if repo_exists is not None:
        effective["local_repo_path_check"] = {
            "status": "exists" if repo_exists else "missing",
            "checked_as_of": now,
        }
    if project_exists is not None:
        effective["project_path_check"] = {
            "status": "exists" if project_exists else "missing",
            "checked_as_of": now,
        }
    return effective


def _lookup_latest_checked_as_of(observations: dict[str, str]) -> str:
    values = [
        observations.get("repo_locator_check_checked_as_of", ""),
        observations.get("local_repo_path_check_checked_as_of", ""),
        observations.get("project_path_check_checked_as_of", ""),
    ]
    non_empty = sorted(value for value in values if value)
    return non_empty[-1] if non_empty else "<unknown>"


def _resolve_checkout_storage(
    *, workspace: MetaWorkspace, project_id: str | None
) -> str:
    if _read_checkout_binding(workspace, project_id=project_id, trusted=False):
        return "private"
    if _read_checkout_binding(workspace, project_id=project_id, trusted=True):
        if get_meta_config_value(workspace, _META_CONFIG_TRUST_KEY.canonical):
            return "workspace"
    return "none"
