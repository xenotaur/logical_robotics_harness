"""Resolve assist templates from overrides with package fallback."""

import dataclasses
import importlib.resources as resources
import os
import pathlib

_PACKAGE_TEMPLATE_RESOURCE = "lrh.assist.templates"


@dataclasses.dataclass(frozen=True)
class TemplateResolution:
    """Metadata for a resolved assist template."""

    logical_name: str
    source: str
    origin: str
    path: pathlib.Path | None = None


class TemplateResolver:
    """Resolve assist templates using explicit, environment, and default sources."""

    def __init__(
        self,
        *,
        template_dirs: list[pathlib.Path | str] | None = None,
        project_root: pathlib.Path | str | None = None,
        environ: dict[str, str] | None = None,
    ) -> None:
        self._explicit_template_dirs = _coerce_paths(template_dirs or [])
        self._project_root = pathlib.Path(project_root) if project_root else None
        self._use_process_home_fallback = environ is None
        self._environ = dict(os.environ if environ is None else environ)

    def resolve(self, logical_name: str) -> TemplateResolution:
        """Resolve ``logical_name`` to the first matching template source."""
        normalized_name = normalize_logical_name(logical_name)
        parts = normalized_name.split("/")
        checked_roots: list[str] = []

        for source, template_dir in self._filesystem_sources():
            checked_roots.append(f"{source}: {template_dir}")
            candidate = template_dir.joinpath(*parts)
            safe_candidate = _safe_filesystem_template_path(
                template_dir=template_dir,
                candidate=candidate,
            )
            if safe_candidate is not None:
                return TemplateResolution(
                    logical_name=normalized_name,
                    source=source,
                    origin=str(candidate),
                    path=safe_candidate,
                )

        checked_roots.append(f"package: {_PACKAGE_TEMPLATE_RESOURCE}")
        package_file = resources.files(_PACKAGE_TEMPLATE_RESOURCE).joinpath(*parts)
        if package_file.is_file():
            return TemplateResolution(
                logical_name=normalized_name,
                source="package",
                origin=f"{_PACKAGE_TEMPLATE_RESOURCE}/{normalized_name}",
            )

        raise FileNotFoundError(
            f"Template not found: {normalized_name}\n"
            "Checked template roots:\n"
            + "\n".join(f"- {root}" for root in checked_roots)
        )

    def read_text(self, logical_name: str) -> str:
        """Resolve and read ``logical_name`` as UTF-8 template text."""
        resolution = self.resolve(logical_name)
        if resolution.path is not None:
            return resolution.path.read_text(encoding="utf-8")

        package_file = resources.files(_PACKAGE_TEMPLATE_RESOURCE).joinpath(
            *resolution.logical_name.split("/")
        )
        return package_file.read_text(encoding="utf-8")

    def list_logical_names(self) -> list[str]:
        """Return all available logical template names from known sources."""
        names: set[str] = set()
        for _source, template_dir in self._filesystem_sources():
            names.update(_filesystem_logical_names(template_dir))

        package_root = resources.files(_PACKAGE_TEMPLATE_RESOURCE)
        names.update(_resource_logical_names(package_root))
        return sorted(names)

    def _filesystem_sources(self) -> list[tuple[str, pathlib.Path]]:
        """Return filesystem template sources in deterministic precedence order."""
        sources: list[tuple[str, pathlib.Path]] = []

        for template_dir in self._explicit_template_dirs:
            sources.append(("explicit", template_dir))

        env_template_dir = self._environ.get("LRH_TEMPLATE_DIR")
        if env_template_dir:
            sources.append(("environment", pathlib.Path(env_template_dir)))

        if self._project_root is not None:
            sources.append(("project", self._project_root / ".lrh" / "templates"))

        user_config_dir = _user_config_template_dir(
            self._environ,
            use_process_home_fallback=self._use_process_home_fallback,
        )
        if user_config_dir is not None:
            sources.append(("user", user_config_dir))
        return sources


def normalize_logical_name(logical_name: str) -> str:
    """Validate and normalize a POSIX-style relative template name."""
    if not logical_name:
        raise ValueError("Template logical name must not be empty.")
    if "\\" in logical_name:
        raise ValueError(
            "Template logical name must use POSIX '/' separators, not backslashes."
        )

    path = pathlib.PurePosixPath(logical_name)
    windows_path = pathlib.PureWindowsPath(logical_name)
    if path.is_absolute() or windows_path.is_absolute() or windows_path.drive:
        raise ValueError(f"Unsafe template logical name: {logical_name}")

    parts = logical_name.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"Unsafe template logical name: {logical_name}")

    return "/".join(parts)


def _coerce_paths(paths: list[pathlib.Path | str]) -> list[pathlib.Path]:
    """Coerce path-like template directories to pathlib paths."""
    return [pathlib.Path(path) for path in paths]


def _safe_filesystem_template_path(
    *,
    template_dir: pathlib.Path,
    candidate: pathlib.Path,
) -> pathlib.Path | None:
    """Return a resolved candidate only when it stays under ``template_dir``."""
    try:
        resolved_candidate = candidate.resolve(strict=True)
    except (FileNotFoundError, OSError):
        return None

    if not resolved_candidate.is_file():
        return None

    resolved_template_dir = template_dir.resolve(strict=False)
    try:
        resolved_candidate.relative_to(resolved_template_dir)
    except ValueError as exc:
        raise PermissionError(
            "Template candidate escapes template root: "
            f"{candidate} -> {resolved_candidate}"
        ) from exc
    return resolved_candidate


def _filesystem_logical_names(template_dir: pathlib.Path) -> set[str]:
    """Return safe logical template names under a filesystem template root."""
    if not template_dir.is_dir():
        return set()

    names: set[str] = set()
    for candidate in template_dir.rglob("*.md"):
        try:
            safe_candidate = _safe_filesystem_template_path(
                template_dir=template_dir,
                candidate=candidate,
            )
        except PermissionError:
            continue
        if safe_candidate is None:
            continue
        names.add(candidate.relative_to(template_dir).as_posix())
    return names


def _resource_logical_names(
    root: resources.abc.Traversable,
    *,
    prefix: str = "",
) -> set[str]:
    """Return logical template names under a package-resource root."""
    names: set[str] = set()
    for child in root.iterdir():
        child_name = f"{prefix}/{child.name}" if prefix else child.name
        if child.is_dir():
            names.update(_resource_logical_names(child, prefix=child_name))
            continue
        if child.is_file() and child.name.endswith(".md"):
            names.add(child_name)
    return names


def _user_config_template_dir(
    environ: dict[str, str],
    *,
    use_process_home_fallback: bool,
) -> pathlib.Path | None:
    """Return the default user-global assist template directory, if configured."""
    xdg_config_home = environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        return pathlib.Path(xdg_config_home) / "lrh" / "templates"

    home = environ.get("HOME")
    if home:
        return pathlib.Path(home) / ".config" / "lrh" / "templates"
    if use_process_home_fallback:
        return pathlib.Path.home() / ".config" / "lrh" / "templates"
    return None
