"""Initialize LRH workspace/meta-control directory layouts."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import pathlib
import shutil

GITIGNORE_BEGIN = "# --- lrh meta init managed block ---"
GITIGNORE_END = "# --- end lrh meta init managed block ---"


class MetaInitError(RuntimeError):
    """Raised when workspace initialization cannot proceed safely."""


class MetaRegisterError(RuntimeError):
    """Raised when project registration cannot proceed safely."""


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
class MetaRegisterResult:
    """Summary of registration actions for CLI reporting and tests."""

    project_id: str
    record_path: pathlib.Path
    existed: bool


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


def register_project(
    workspace_root: pathlib.Path,
    *,
    repo_locator: str,
    force: bool = False,
) -> MetaRegisterResult:
    """Register a repository in an initialized LRH workspace catalog."""
    projects_dir = workspace_root / "projects"
    config_path = workspace_root / ".lrh" / "config.toml"
    if not projects_dir.is_dir() or not config_path.is_file():
        raise MetaRegisterError(
            f"{workspace_root} does not appear to be an initialized LRH workspace. "
            "Run `lrh meta init` first."
        )

    resolved_repo_path = _resolve_repo_path(repo_locator)
    canonical_locator = str(resolved_repo_path)
    project_id = _project_id_from_locator(canonical_locator)
    record_path = projects_dir / f"{project_id}.toml"

    if record_path.exists() and not force:
        raise MetaRegisterError(
            f"project already registered at {record_path}; rerun with --force "
            "to replace the managed record"
        )

    setup_state = _detect_setup_state(resolved_repo_path)
    short_name = _derive_short_name(resolved_repo_path)
    display_name = short_name.replace("-", " ").title() or "Unnamed Project"
    record_content = _project_record_text(
        project_id=project_id,
        short_name=short_name,
        display_name=display_name,
        repo_locator=canonical_locator,
        setup_state=setup_state,
    )

    existed = record_path.exists()
    record_path.write_text(record_content, encoding="utf-8")
    return MetaRegisterResult(
        project_id=project_id, record_path=record_path, existed=existed
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


def _resolve_repo_path(repo_locator: str) -> pathlib.Path:
    candidate = pathlib.Path(repo_locator).expanduser().resolve()
    if not candidate.exists():
        raise MetaRegisterError(
            f"repo locator does not exist or is not accessible: {repo_locator}"
        )
    if not candidate.is_dir():
        raise MetaRegisterError(f"repo locator is not a directory: {repo_locator}")
    return candidate


def _project_id_from_locator(canonical_locator: str) -> str:
    digest = hashlib.sha256(canonical_locator.encode("utf-8")).hexdigest()
    return f"proj-{digest[:12]}"


def _detect_setup_state(repo_path: pathlib.Path) -> str:
    if (repo_path / "project").is_dir():
        return "lrh_project_present"
    return "not_set_up"


def _derive_short_name(repo_path: pathlib.Path) -> str:
    raw_name = repo_path.name.strip().lower()
    if not raw_name:
        return "project"
    normalized = []
    for character in raw_name:
        if character.isalnum():
            normalized.append(character)
        else:
            normalized.append("-")
    collapsed = "".join(normalized).strip("-")
    return collapsed or "project"


def _project_record_text(
    *,
    project_id: str,
    short_name: str,
    display_name: str,
    repo_locator: str,
    setup_state: str,
) -> str:
    encoded_project_id = _toml_basic_string(project_id)
    encoded_short_name = _toml_basic_string(short_name)
    encoded_display_name = _toml_basic_string(display_name)
    encoded_repo_locator = _toml_basic_string(repo_locator)
    encoded_setup_state = _toml_basic_string(setup_state)
    encoded_repo_uri = _toml_basic_string(_path_to_file_uri(repo_locator))
    return (
        'schema_version = "0.1"\n\n'
        "[project]\n"
        f"project_id = {encoded_project_id}\n"
        f"short_name = {encoded_short_name}\n"
        f"display_name = {encoded_display_name}\n"
        f"setup_state = {encoded_setup_state}\n\n"
        "[locator]\n"
        f"repo = {encoded_repo_locator}\n"
        'project_dir = "project"\n\n'
        "[identity]\n"
        f"canonical_url = {encoded_repo_uri}\n"
    )


def _path_to_file_uri(path_text: str) -> str:
    return pathlib.Path(path_text).as_uri()


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
