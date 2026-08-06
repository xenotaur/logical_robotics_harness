"""Install LRH skills from canonical sources to agent skills directories."""

from __future__ import annotations

import difflib
import importlib.resources
import importlib.resources.abc
import shutil
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Protocol

import yaml

_SKILLS_PACKAGE = "lrh.skills"
_AGENT_SKILLS_CONFIG = Path("project") / "agent_skills.yaml"


class SkillTarget(str, Enum):
    CLAUDE = "claude"
    CODEX = "codex"


class TargetSelection(str, Enum):
    CLAUDE = "claude"
    CODEX = "codex"
    ALL = "all"


class SkillSourceKind(str, Enum):
    PACKAGE = "lrh-package"
    CURRENT_REPO = "current-repo"
    PATH = "path"


class SkillStatus(str, Enum):
    INSTALLED = "installed"
    UP_TO_DATE = "up_to_date"
    USER_MODIFIED = "user_modified"
    FORCED = "forced"


class SkillInspectionStatus(str, Enum):
    MISSING = "missing"
    UP_TO_DATE = "up_to_date"
    MODIFIED = "modified"
    SOURCE_ERROR = "source_error"


@dataclass(frozen=True)
class SkillResult:
    name: str
    status: SkillStatus


@dataclass(frozen=True)
class SkillCheckIssue:
    skill_name: str
    code: str
    message: str


@dataclass(frozen=True)
class SkillInspectionResult:
    name: str
    status: SkillInspectionStatus
    issues: list[SkillCheckIssue]


@dataclass(frozen=True)
class InstallTarget:
    target: SkillTarget
    skills_dir: Path

    @property
    def restart_name(self) -> str:
        if self.target is SkillTarget.CLAUDE:
            return "Claude Code"
        return "Codex"


@dataclass(frozen=True)
class AgentSkillsConfig:
    config_path: Path
    source: str | None = None
    target: TargetSelection | None = None
    local: bool | None = None


@dataclass(frozen=True)
class AgentSkillsInstallPlan:
    source: str | Path | SkillSource
    target: TargetSelection
    local: bool


class SkillSourceError(ValueError):
    """Raised when a requested skill source cannot be resolved."""


class SkillTreeNode(Protocol):
    name: str

    def iterdir(self) -> Iterable["SkillTreeNode"]: ...

    def is_dir(self) -> bool: ...

    def is_file(self) -> bool: ...

    def read_bytes(self) -> bytes: ...


class SkillRenderer(Protocol):
    """Render canonical skill files for a specific install target."""

    def render(
        self, skill_name: str, source_files: dict[str, bytes]
    ) -> dict[str, bytes]:
        """Return target-ready files for one skill."""


@dataclass(frozen=True)
class SkillSource:
    kind: SkillSourceKind
    root: SkillTreeNode
    label: str

    def skill_names(self) -> list[str]:
        result: list[str] = []
        for item in self.root.iterdir():
            if _is_symlink_node(item):
                raise SkillSourceError(f"skill source contains symlinked entry: {item}")
            if item.is_dir() and not item.name.startswith("_"):
                result.append(item.name)
        return sorted(result)

    def skill_root(self, skill_name: str) -> SkillTreeNode:
        root = self.root
        if hasattr(root, "joinpath"):
            return root.joinpath(skill_name)  # type: ignore[attr-defined]
        return Path(root) / skill_name


class RefreshStatus(str, Enum):
    REFRESHED = "refreshed"
    ABSENT = "absent"


@dataclass(frozen=True)
class TargetedRefreshResult:
    name: str
    status: RefreshStatus


@dataclass(frozen=True)
class InstallReport:
    results: list[SkillResult]
    newly_created_skills_dir: bool
    skills_dir: Path
    target: SkillTarget = SkillTarget.CLAUDE


@dataclass(frozen=True)
class SkillInspectionReport:
    results: list[SkillInspectionResult]
    skills_dir: Path
    target: SkillTarget = SkillTarget.CLAUDE


class ClaudeSkillRenderer:
    """Preserve canonical skill bytes for Claude installs."""

    def render(
        self, skill_name: str, source_files: dict[str, bytes]
    ) -> dict[str, bytes]:
        return dict(source_files)


class CodexSkillRenderer:
    """Render canonical skill bytes for Codex installs."""

    _SKILL_MD = "SKILL.md"
    _OPENAI_YAML = "agents/openai.yaml"
    _CODEX_STRIPPED_FRONTMATTER_KEYS = {
        "argument-hint",
        "disable-model-invocation",
    }

    def render(
        self, skill_name: str, source_files: dict[str, bytes]
    ) -> dict[str, bytes]:
        rendered = dict(source_files)
        skill_md = source_files.get(self._SKILL_MD)
        if skill_md is None:
            return rendered

        metadata, rewritten_skill_md = self._render_skill_md(skill_md)
        rendered[self._SKILL_MD] = rewritten_skill_md

        if metadata.get("disable-model-invocation") is True:
            rendered[self._OPENAI_YAML] = self._render_openai_yaml(
                source_files.get(self._OPENAI_YAML)
            )

        return rendered

    def _render_skill_md(self, content: bytes) -> tuple[dict[str, Any], bytes]:
        parsed = _parse_skill_frontmatter(content)
        if parsed is None:
            return {}, content
        metadata, parts, closing_index = parsed

        codex_metadata = {
            key: value
            for key, value in metadata.items()
            if key not in self._CODEX_STRIPPED_FRONTMATTER_KEYS
        }
        frontmatter = yaml.safe_dump(codex_metadata, sort_keys=False)
        rewritten = f"---\n{frontmatter}---\n{''.join(parts[closing_index + 1:])}"
        return metadata, rewritten.encode("utf-8")

    def _render_openai_yaml(self, source_content: bytes | None) -> bytes:
        metadata = self._load_openai_yaml(source_content)
        policy = metadata.get("policy")
        if not isinstance(policy, dict):
            if policy is not None:
                raise SkillSourceError("policy in agents/openai.yaml must be a mapping")
            policy = {}
            metadata["policy"] = policy
        policy.setdefault("allow_implicit_invocation", False)
        return yaml.safe_dump(metadata, sort_keys=False).encode("utf-8")

    def _load_openai_yaml(self, source_content: bytes | None) -> dict[str, Any]:
        if source_content is None:
            return {}
        try:
            loaded = yaml.safe_load(source_content.decode("utf-8")) or {}
        except (UnicodeDecodeError, yaml.YAMLError) as err:
            raise SkillSourceError(
                f"invalid Codex metadata in agents/openai.yaml: {err}"
            ) from err
        if not isinstance(loaded, dict):
            raise SkillSourceError(
                "Codex metadata in agents/openai.yaml must be a mapping"
            )
        return loaded


def _coerce_target(value: str | SkillTarget) -> SkillTarget:
    if isinstance(value, SkillTarget):
        return value
    return SkillTarget(value)


def _coerce_selection(value: str | SkillTarget | TargetSelection) -> TargetSelection:
    if isinstance(value, TargetSelection):
        return value
    if isinstance(value, SkillTarget):
        return TargetSelection(value.value)
    return TargetSelection(value)


def _config_path(project_root: Path | None = None) -> Path:
    root = project_root if project_root is not None else Path.cwd()
    return root / _AGENT_SKILLS_CONFIG


def load_agent_skills_config(
    project_root: Path | None = None,
) -> AgentSkillsConfig | None:
    """Load optional repository-local agent skill install configuration."""
    path = _config_path(project_root)
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file():
        raise SkillSourceError(f"agent skills config must be a real file: {path}")
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as err:
        raise SkillSourceError(f"invalid YAML in {path}: {err}") from err
    if loaded is None:
        return AgentSkillsConfig(config_path=path)
    if not isinstance(loaded, dict):
        raise SkillSourceError(f"agent skills config must be a mapping: {path}")

    _validate_schema_version(loaded, path)
    _validate_config_install_policy(loaded, path)
    return AgentSkillsConfig(
        config_path=path,
        source=_config_source(loaded, path),
        target=_config_target(loaded, path),
        local=_config_scope(loaded, path),
    )


def _validate_schema_version(data: dict[str, Any], path: Path) -> None:
    version = data.get("schema_version", 1)
    if version != 1:
        raise SkillSourceError(
            f"unsupported agent skills config schema_version in {path}: {version!r}"
        )


def _config_string_list(data: dict[str, Any], key: str, path: Path) -> list[str] | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise SkillSourceError(f"{key} in {path} must be a list of strings")
    if any(not item.strip() for item in value):
        raise SkillSourceError(f"{key} in {path} must not contain blank values")
    return value


def _config_source(data: dict[str, Any], path: Path) -> str | None:
    sources = _config_string_list(data, "sources", path)
    if sources is None:
        return None
    if len(sources) != 1:
        raise SkillSourceError(
            f"sources in {path} must contain exactly one source in this installer stage"
        )
    return sources[0]


def _config_target(data: dict[str, Any], path: Path) -> TargetSelection | None:
    targets = _config_string_list(data, "targets", path)
    if targets is None:
        return None
    normalized = {target.lower() for target in targets}
    if not normalized:
        raise SkillSourceError(f"targets in {path} must not be empty")
    if normalized == {"all"} or normalized == {"claude", "codex"}:
        return TargetSelection.ALL
    if normalized == {"claude"}:
        return TargetSelection.CLAUDE
    if normalized == {"codex"}:
        return TargetSelection.CODEX
    raise SkillSourceError(
        f"targets in {path} must be claude, codex, all, or both claude and codex"
    )


def _config_scope(data: dict[str, Any], path: Path) -> bool | None:
    scope = data.get("scope")
    if scope is None:
        return None
    if scope == "project":
        return True
    if scope == "user":
        return False
    raise SkillSourceError(f"scope in {path} must be user or project")


def _validate_config_install_policy(data: dict[str, Any], path: Path) -> None:
    install = data.get("install")
    if install is None:
        return
    if not isinstance(install, dict):
        raise SkillSourceError(f"install in {path} must be a mapping")
    overwrite = install.get("overwrite")
    if overwrite in (None, False, "skip", "preserve"):
        return
    raise SkillSourceError(
        f"install.overwrite in {path} cannot enable destructive overwrite;"
        " use the --force CLI flag for that"
    )


def _resolve_config_source(config: AgentSkillsConfig) -> str:
    if config.source is None:
        return SkillSourceKind.PACKAGE.value
    if config.source in {
        SkillSourceKind.PACKAGE.value,
        SkillSourceKind.CURRENT_REPO.value,
    }:
        return config.source
    source_path = Path(config.source)
    if source_path.is_absolute():
        return str(source_path)
    return str(config.config_path.parents[1] / source_path)


def resolve_agent_skills_install_plan(
    *,
    target: str | SkillTarget | TargetSelection | None = None,
    local: bool | None = None,
    source: str | Path | SkillSource | None = None,
    project_root: Path | None = None,
) -> AgentSkillsInstallPlan:
    """Resolve CLI-over-config-over-default install planning values."""
    config = load_agent_skills_config(project_root)
    resolved_source = (
        source
        if source is not None
        else (
            _resolve_config_source(config)
            if config is not None and config.source is not None
            else SkillSourceKind.PACKAGE.value
        )
    )
    resolved_target = (
        _coerce_selection(target)
        if target is not None
        else (
            config.target
            if config is not None and config.target is not None
            else TargetSelection.CLAUDE
        )
    )
    resolved_local = (
        local
        if local is not None
        else (
            config.local if config is not None and config.local is not None else False
        )
    )
    return AgentSkillsInstallPlan(
        source=resolved_source,
        target=resolved_target,
        local=resolved_local,
    )


def _default_skills_dir(target: SkillTarget) -> Path:
    if target is SkillTarget.CLAUDE:
        return Path.home() / ".claude" / "skills"
    return Path.home() / ".agents" / "skills"


def resolve_skill_source(
    source: str | Path | SkillSource = SkillSourceKind.PACKAGE.value,
    *,
    project_root: Path | None = None,
) -> SkillSource:
    if isinstance(source, SkillSource):
        return source
    if isinstance(source, Path):
        root = source
        label = str(source)
        kind = SkillSourceKind.PATH
    elif source == SkillSourceKind.PACKAGE.value:
        return SkillSource(
            kind=SkillSourceKind.PACKAGE,
            root=importlib.resources.files(_SKILLS_PACKAGE),
            label=SkillSourceKind.PACKAGE.value,
        )
    elif source == SkillSourceKind.CURRENT_REPO.value:
        root = (
            (project_root if project_root is not None else Path.cwd())
            / "src"
            / "lrh"
            / "skills"
        )
        label = SkillSourceKind.CURRENT_REPO.value
        kind = SkillSourceKind.CURRENT_REPO
    else:
        root = Path(source)
        label = str(source)
        kind = SkillSourceKind.PATH

    if not root.exists():
        raise SkillSourceError(f"skill source does not exist: {root}")
    if root.is_symlink() or not root.is_dir():
        raise SkillSourceError(f"skill source must be a real directory: {root}")
    return SkillSource(kind=kind, root=root, label=label)


def resolve_install_targets(
    target: str | SkillTarget | TargetSelection = TargetSelection.CLAUDE,
    *,
    local: bool = False,
    project_root: Path | None = None,
) -> list[InstallTarget]:
    selection = _coerce_selection(target)
    targets = (
        [SkillTarget.CLAUDE, SkillTarget.CODEX]
        if selection is TargetSelection.ALL
        else [_coerce_target(selection.value)]
    )
    root = project_root if project_root is not None else Path.cwd()
    result: list[InstallTarget] = []
    for selected in targets:
        if local:
            dirname = ".claude" if selected is SkillTarget.CLAUDE else ".agents"
            skills_dir = root / dirname / "skills"
        else:
            skills_dir = _default_skills_dir(selected)
        result.append(InstallTarget(target=selected, skills_dir=skills_dir))
    return result


def _is_symlink_node(node: SkillTreeNode) -> bool:
    return isinstance(node, Path) and node.is_symlink()


def _parse_skill_frontmatter(
    content: bytes,
) -> tuple[dict[str, Any], list[str], int] | None:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return None

    parts = text.splitlines(keepends=True)
    if len(parts) < 3 or parts[0].strip() != "---":
        return None

    closing_index = next(
        (
            index
            for index, line in enumerate(parts[1:], start=1)
            if line.strip() == "---"
        ),
        None,
    )
    if closing_index is None:
        return None

    frontmatter_text = "".join(parts[1:closing_index])
    try:
        metadata = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError as err:
        raise SkillSourceError(f"invalid YAML in SKILL.md frontmatter: {err}") from err
    if not isinstance(metadata, dict):
        raise SkillSourceError("SKILL.md frontmatter must be a mapping")
    return metadata, parts, closing_index


def _skill_names(source: SkillSource | None = None) -> list[str]:
    return (source or resolve_skill_source()).skill_names()


def _renderer_for_target(target: SkillTarget) -> SkillRenderer:
    if target is SkillTarget.CLAUDE:
        return ClaudeSkillRenderer()
    return CodexSkillRenderer()


def _render_skill_files(
    skill_name: str, source: SkillSource, target: SkillTarget
) -> dict[str, bytes]:
    source_files = _collect_source_files(source.skill_root(skill_name))
    return _renderer_for_target(target).render(skill_name, source_files)


def _collect_source_files(node: SkillTreeNode, prefix: str = "") -> dict[str, bytes]:
    if _is_symlink_node(node):
        raise SkillSourceError(f"skill source contains symlinked entry: {node}")
    result: dict[str, bytes] = {}
    for item in node.iterdir():
        if _is_symlink_node(item):
            raise SkillSourceError(f"skill source contains symlinked entry: {item}")
        rel = f"{prefix}/{item.name}" if prefix else item.name
        if item.is_file():
            result[rel] = item.read_bytes()
        elif item.is_dir():
            result.update(_collect_source_files(item, rel))
    return result


def _collect_pkg_files(
    node: importlib.resources.abc.Traversable, prefix: str = ""
) -> dict[str, bytes]:
    return _collect_source_files(node, prefix)


def _write_collected_files(files: dict[str, bytes], dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    for rel_path, content in files.items():
        target = dest_dir / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


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


def _skill_differs_from_source(
    skill_name: str, skills_dir: Path, source: SkillSource, target: SkillTarget
) -> bool:
    source_files = _render_skill_files(skill_name, source, target)
    skill_dir = skills_dir / skill_name
    fs_files = _collect_fs_files(skill_dir)
    if source_files != fs_files:
        return True
    # A nested symlink (e.g. an added file replaced by one) can leave the
    # byte dicts equal, since symlinks are excluded from both — but its
    # presence is itself a local modification that must not be masked as
    # up to date.
    return bool(_collect_fs_symlinks(skill_dir))


def _skill_differs_from_package(skill_name: str, skills_dir: Path) -> bool:
    return _skill_differs_from_source(
        skill_name, skills_dir, resolve_skill_source(), SkillTarget.CLAUDE
    )


def diff_skill(
    skill_name: str,
    skills_dir: Path,
    source: str | Path | SkillSource = SkillSourceKind.PACKAGE.value,
    *,
    project_root: Path | None = None,
    target: str | SkillTarget = SkillTarget.CLAUDE,
) -> str:
    """Return a unified-diff report of how an installed skill differs from source.

    Symlinked entries under the installed skill directory are reported but
    never dereferenced — their target contents are never read or diffed.
    """
    skill_source = resolve_skill_source(source, project_root=project_root)
    skill_dir = skills_dir / skill_name
    if skill_dir.is_symlink():
        return (
            f"{skill_name}: installed skill directory is a symlink — skipped"
            " (refusing to read through it)\n"
        )

    skill_target = _coerce_target(target)
    source_files = _render_skill_files(skill_name, skill_source, skill_target)
    fs_files = _collect_fs_files(skill_dir)
    fs_symlinks = _collect_fs_symlinks(skill_dir)

    segments: list[str] = []
    for rel_path in sorted(set(source_files) | set(fs_files) | fs_symlinks):
        if rel_path in fs_symlinks:
            segments.append(f"{rel_path}: symlink — skipped\n")
            continue
        in_pkg = rel_path in source_files
        in_fs = rel_path in fs_files
        if in_pkg and not in_fs:
            segments.append(
                f"{rel_path}: removed (present in source, missing on disk)\n"
            )
            continue
        if in_fs and not in_pkg:
            segments.append(f"{rel_path}: added (present on disk, not in source)\n")
            continue
        pkg_bytes = source_files[rel_path]
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
            fromfile=f"source/{rel_path}",
            tofile=f"installed/{rel_path}",
        )
        segments.append("".join(diff_lines))

    return "".join(segments)


def _copy_resource_tree(node: SkillTreeNode, dest_dir: Path) -> None:
    _write_collected_files(_collect_source_files(node), dest_dir)


def _copy_skill_from_source(
    skill_name: str, skills_dir: Path, source: SkillSource, target: SkillTarget
) -> None:
    dest = skills_dir / skill_name
    source_files = _render_skill_files(skill_name, source, target)
    if dest.is_symlink() or (dest.exists() and not dest.is_dir()):
        dest.unlink()
    elif dest.is_dir():
        shutil.rmtree(dest)
    _write_collected_files(source_files, dest)


def _copy_skill(skill_name: str, skills_dir: Path) -> None:
    _copy_skill_from_source(
        skill_name, skills_dir, resolve_skill_source(), SkillTarget.CLAUDE
    )


def install_skills(
    skills_dir: Path | None = None,
    dry_run: bool = False,
    force: bool = False,
    target: str | SkillTarget = SkillTarget.CLAUDE,
    source: str | Path | SkillSource = SkillSourceKind.PACKAGE.value,
    project_root: Path | None = None,
) -> InstallReport:
    """Copy LRH skills from one canonical source to one agent skills directory.

    Returns an InstallReport describing what was done (or would be done in dry-run).
    """
    skill_target = _coerce_target(target)
    skill_source = resolve_skill_source(source, project_root=project_root)
    target_dir = (
        skills_dir if skills_dir is not None else _default_skills_dir(skill_target)
    )
    newly_created = not target_dir.exists()
    results: list[SkillResult] = []

    for name in _skill_names(skill_source):
        dest = target_dir / name
        if not dest.exists():
            if not dry_run:
                target_dir.mkdir(parents=True, exist_ok=True)
                _copy_skill_from_source(name, target_dir, skill_source, skill_target)
            status = SkillStatus.INSTALLED
        elif _skill_differs_from_source(name, target_dir, skill_source, skill_target):
            if force:
                if not dry_run:
                    _copy_skill_from_source(
                        name, target_dir, skill_source, skill_target
                    )
                status = SkillStatus.FORCED
            else:
                status = SkillStatus.USER_MODIFIED
        else:
            status = SkillStatus.UP_TO_DATE
        results.append(SkillResult(name=name, status=status))

    return InstallReport(
        results=results,
        newly_created_skills_dir=newly_created,
        skills_dir=target_dir,
        target=skill_target,
    )


def install_skills_for_targets(
    target: str | SkillTarget | TargetSelection | None = None,
    *,
    local: bool | None = None,
    project_root: Path | None = None,
    dry_run: bool = False,
    force: bool = False,
    source: str | Path | SkillSource | None = None,
) -> list[InstallReport]:
    """Install skills for every selected target and scope."""
    plan = resolve_agent_skills_install_plan(
        target=target,
        local=local,
        source=source,
        project_root=project_root,
    )
    skill_source = resolve_skill_source(plan.source, project_root=project_root)
    return [
        install_skills(
            skills_dir=install_target.skills_dir,
            dry_run=dry_run,
            force=force,
            target=install_target.target,
            source=skill_source,
        )
        for install_target in resolve_install_targets(
            plan.target, local=plan.local, project_root=project_root
        )
    ]


def inspect_skills(
    skills_dir: Path | None = None,
    target: str | SkillTarget = SkillTarget.CLAUDE,
    source: str | Path | SkillSource = SkillSourceKind.PACKAGE.value,
    project_root: Path | None = None,
) -> SkillInspectionReport:
    """Inspect one agent skills directory without writing to it."""
    skill_target = _coerce_target(target)
    skill_source = resolve_skill_source(source, project_root=project_root)
    target_dir = (
        skills_dir if skills_dir is not None else _default_skills_dir(skill_target)
    )
    results: list[SkillInspectionResult] = []
    for name in _skill_names(skill_source):
        try:
            _render_skill_files(name, skill_source, skill_target)
            issues = _compatibility_issues(name, skill_source, skill_target)
        except SkillSourceError as err:
            results.append(
                SkillInspectionResult(
                    name=name,
                    status=SkillInspectionStatus.SOURCE_ERROR,
                    issues=[
                        SkillCheckIssue(
                            skill_name=name,
                            code="source_error",
                            message=str(err),
                        )
                    ],
                )
            )
            continue

        dest = target_dir / name
        if not dest.exists():
            status = SkillInspectionStatus.MISSING
        elif _skill_differs_from_source(name, target_dir, skill_source, skill_target):
            status = SkillInspectionStatus.MODIFIED
        else:
            status = SkillInspectionStatus.UP_TO_DATE
        results.append(SkillInspectionResult(name=name, status=status, issues=issues))

    return SkillInspectionReport(
        results=results,
        skills_dir=target_dir,
        target=skill_target,
    )


def inspect_skills_for_targets(
    target: str | SkillTarget | TargetSelection | None = None,
    *,
    local: bool | None = None,
    project_root: Path | None = None,
    source: str | Path | SkillSource | None = None,
) -> list[SkillInspectionReport]:
    """Inspect skills for every selected target and scope without writing."""
    plan = resolve_agent_skills_install_plan(
        target=target,
        local=local,
        source=source,
        project_root=project_root,
    )
    skill_source = resolve_skill_source(plan.source, project_root=project_root)
    return [
        inspect_skills(
            skills_dir=install_target.skills_dir,
            target=install_target.target,
            source=skill_source,
        )
        for install_target in resolve_install_targets(
            plan.target, local=plan.local, project_root=project_root
        )
    ]


def _compatibility_issues(
    skill_name: str, source: SkillSource, target: SkillTarget
) -> list[SkillCheckIssue]:
    if target is not SkillTarget.CODEX:
        return []
    source_files = _collect_source_files(source.skill_root(skill_name))
    issues: list[SkillCheckIssue] = []

    skill_md = source_files.get(CodexSkillRenderer._SKILL_MD)
    if skill_md is not None:
        parsed = _parse_skill_frontmatter(skill_md)
        if parsed is not None:
            metadata, _parts, _closing_index = parsed
            if "argument-hint" in metadata:
                issues.append(
                    SkillCheckIssue(
                        skill_name=skill_name,
                        code="unsupported_metadata",
                        message=(
                            "`argument-hint` has no Codex metadata equivalent"
                            " and will be stripped"
                        ),
                    )
                )

    openai_yaml = source_files.get(CodexSkillRenderer._OPENAI_YAML)
    if openai_yaml is not None:
        renderer = CodexSkillRenderer()
        try:
            metadata = renderer._load_openai_yaml(openai_yaml)
        except SkillSourceError as err:
            issues.append(
                SkillCheckIssue(
                    skill_name=skill_name,
                    code="invalid_codex_metadata",
                    message=str(err),
                )
            )
        else:
            policy = metadata.get("policy")
            if policy is not None and not isinstance(policy, dict):
                issues.append(
                    SkillCheckIssue(
                        skill_name=skill_name,
                        code="invalid_codex_metadata",
                        message="policy in agents/openai.yaml must be a mapping",
                    )
                )

    return issues


def inspection_report_has_failures(report: SkillInspectionReport) -> bool:
    return any(
        result.status is not SkillInspectionStatus.UP_TO_DATE or result.issues
        for result in report.results
    )


def install_named_skills(
    skill_names: Iterable[str], skills_dir: Path | None = None
) -> list[TargetedRefreshResult]:
    """Force-install exactly the given skill names, bypassing `USER_MODIFIED`.

    Unlike `install_skills(force=True)`, this does not touch any skill
    outside `skill_names` — every other installed skill's status is left
    completely uncomputed and unmodified. Each name is validated against
    the current package's `_skill_names()` *before* any destructive
    filesystem operation: a name absent from the package returns
    `RefreshStatus.ABSENT` without touching (in particular, without
    deleting) any existing installed directory for that name, since
    `_copy_skill` would otherwise `rmtree` the destination before
    discovering there is no package source to copy from. (`skills_dir`
    itself may still be created via `mkdir` if at least one name is
    valid — that's not destructive, so it isn't gated per-name.)

    `skill_names` accepts any iterable, including a one-shot one (e.g. a
    generator) — it is consumed exactly once, immediately, into a list.
    """
    if isinstance(skill_names, str):
        raise TypeError(
            "skill_names must be an iterable of skill name strings, not a"
            " single string (a bare string is itself Iterable[str] and"
            " would otherwise be iterated character by character)"
        )
    # Materialize once: this is used twice below (the intersection check,
    # then the main loop), and skill_names may be a one-shot iterable
    # (e.g. a generator) that would otherwise be silently consumed by the
    # first pass.
    names = list(skill_names)
    for name in names:
        if not isinstance(name, str):
            raise TypeError(
                f"skill_names must contain only strings, got {name!r}"
                f" ({type(name).__name__})"
            )
    target = (
        skills_dir
        if skills_dir is not None
        else _default_skills_dir(SkillTarget.CLAUDE)
    )
    valid_names = set(_skill_names())
    results: list[TargetedRefreshResult] = []
    if valid_names.intersection(names):
        target.mkdir(parents=True, exist_ok=True)
    for name in names:
        if name not in valid_names:
            results.append(
                TargetedRefreshResult(name=name, status=RefreshStatus.ABSENT)
            )
            continue
        _copy_skill(name, target)
        results.append(TargetedRefreshResult(name=name, status=RefreshStatus.REFRESHED))
    return results


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
        restart_name = InstallTarget(
            target=report.target, skills_dir=report.skills_dir
        ).restart_name
        lines.append(
            f"\nnote: {report.skills_dir} was newly created."
            f" Restart {restart_name} to discover the installed skills."
        )
    return "\n".join(lines)


def format_inspection_report(
    report: SkillInspectionReport, issue_label: str = "error"
) -> str:
    lines: list[str] = []
    for result in report.results:
        if result.status is SkillInspectionStatus.MISSING:
            lines.append(f"  missing: {result.name}")
        elif result.status is SkillInspectionStatus.UP_TO_DATE:
            lines.append(f"  up to date: {result.name}")
        elif result.status is SkillInspectionStatus.MODIFIED:
            lines.append(f"  modified: {result.name} differs from source")
        elif result.status is SkillInspectionStatus.SOURCE_ERROR:
            lines.append(f"  source error: {result.name}")
        for issue in result.issues:
            lines.append(f"  {issue_label}: {issue.skill_name}: {issue.message}")
    return "\n".join(lines)
