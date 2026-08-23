"""Repo-configurable rule config for `lrh pii scan`.

Auto-discovers `.lrh-pii.toml` at the scanned project root, the same
`[extend] useDefault = true` convention `gitleaks` uses for
`.gitleaks.toml` (`PROP-LRH-PII-SCAN` Decision 4) - a config-file
discovery pattern this repo has already validated in production via
LCATS's own live `.gitleaks.toml`. Built-in defaults are a disclosed,
reviewable starter list, not a claim of completeness.
"""

from __future__ import annotations

import dataclasses
import pathlib
import tomllib

CONFIG_FILENAME = ".lrh-pii.toml"

DEFAULT_PATH_GLOBS = (
    "*.pdf",
    "*.docx",
    "*.xlsx",
    "*.pem",
)

DEFAULT_FILENAME_KEYWORDS = (
    "statement",
    "ssn",
    "passport",
    "w-9",
    "medical",
)


@dataclasses.dataclass(frozen=True)
class PiiConfig:
    path_globs: tuple[str, ...]
    filename_keywords: tuple[str, ...]


class PiiConfigError(Exception):
    """Raised for a malformed `.lrh-pii.toml`."""


def load_config(project_root: pathlib.Path) -> PiiConfig:
    """Auto-discover `.lrh-pii.toml` at `project_root` and extend the
    built-in defaults per its `[extend] useDefault` setting (default
    `true`). Returns the built-in defaults unmodified if no config file
    exists."""
    config_path = project_root / CONFIG_FILENAME
    if not config_path.exists():
        return PiiConfig(
            path_globs=DEFAULT_PATH_GLOBS,
            filename_keywords=DEFAULT_FILENAME_KEYWORDS,
        )

    try:
        raw_text = config_path.read_text(encoding="utf-8")
    except OSError as err:
        raise PiiConfigError(f"{config_path} could not be read: {err}") from err

    try:
        data = tomllib.loads(raw_text)
    except tomllib.TOMLDecodeError as err:
        raise PiiConfigError(f"{config_path} is not valid TOML: {err}") from err

    extend_table = data.get("extend", {})
    if not isinstance(extend_table, dict):
        raise PiiConfigError(
            f"{config_path}: [extend] must be a table, got {extend_table!r}"
        )

    use_default = extend_table.get("useDefault", True)
    if not isinstance(use_default, bool):
        raise PiiConfigError(
            f"{config_path}: [extend].useDefault must be a boolean, "
            f"got {use_default!r}"
        )

    path_globs = list(DEFAULT_PATH_GLOBS) if use_default else []
    path_globs.extend(_require_string_list(data, "path_globs", config_path))

    filename_keywords = list(DEFAULT_FILENAME_KEYWORDS) if use_default else []
    filename_keywords.extend(
        _require_string_list(data, "filename_keywords", config_path)
    )

    return PiiConfig(
        path_globs=tuple(dict.fromkeys(path_globs)),
        filename_keywords=tuple(dict.fromkeys(filename_keywords)),
    )


def _require_string_list(
    data: dict[str, object], key: str, config_path: pathlib.Path
) -> list[str]:
    value = data.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise PiiConfigError(
            f"{config_path}: {key} must be a list of strings, got {value!r}"
        )
    return value
