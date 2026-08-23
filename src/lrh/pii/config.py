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
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as err:
        raise PiiConfigError(f"{config_path} is not valid TOML: {err}") from err

    use_default = data.get("extend", {}).get("useDefault", True)

    path_globs = list(DEFAULT_PATH_GLOBS) if use_default else []
    path_globs.extend(data.get("path_globs", []))

    filename_keywords = list(DEFAULT_FILENAME_KEYWORDS) if use_default else []
    filename_keywords.extend(data.get("filename_keywords", []))

    return PiiConfig(
        path_globs=tuple(dict.fromkeys(path_globs)),
        filename_keywords=tuple(dict.fromkeys(filename_keywords)),
    )
