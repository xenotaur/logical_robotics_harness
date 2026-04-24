"""Helpers for request-template interpolation variable preparation."""

import pathlib


def find_repo_root(start: pathlib.Path | None = None) -> pathlib.Path | None:
    """Find the nearest repository root by looking for a .git marker."""
    current = (start or pathlib.Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def normalize_target_for_gha(target_input: str | None) -> str:
    """
    Normalize an input path into repo-root style module path:
        src/lrh/<...>.py

    Accepts inputs like:
        src/lrh/analysis/foo.py -> src/lrh/analysis/foo.py
        lrh/analysis/foo.py     -> src/lrh/analysis/foo.py
        analysis/foo.py         -> src/lrh/analysis/foo.py
                                   (assumed relative to src/lrh/)

    If target_input is empty or None, returns an empty string.
    """
    if not target_input:
        return ""

    target = target_input.strip().replace("\\", "/")
    target = target.lstrip("./")

    if not target.startswith("src/lrh/"):
        if target.startswith("lrh/"):
            target = f"src/{target}"
        else:
            target = f"src/lrh/{target}"

    if target.startswith("src/lrh/"):
        return target

    if target.startswith("src/"):
        return "src/lrh/" + target[len("src/") :]

    return target


def compute_suggested_test_path(target_module_gha: str) -> str:
    """
    Given:
        src/lrh/<subdir>/<...>/<name>.py
    Suggest:
        tests/<subdir>/<...>/<name>_test.py
    """
    if not target_module_gha:
        return ""

    target_path = pathlib.Path(target_module_gha)
    parts = target_path.parts
    if len(parts) < 3 or parts[0] != "src" or parts[1] != "lrh":
        stem = target_path.stem
        return str(pathlib.Path("tests") / f"{stem}_test.py").replace("\\", "/")

    subdir = parts[2]
    rest_dirs = parts[3:-1]
    stem = target_path.stem

    test_dir = pathlib.Path("tests") / subdir
    if rest_dirs:
        test_dir = test_dir.joinpath(*rest_dirs)

    return str(test_dir / f"{stem}_test.py").replace("\\", "/")


def read_optional_text(path_str: str | None) -> str:
    """Read a UTF-8 text file if provided, otherwise return an empty string."""
    if not path_str:
        return ""

    path = pathlib.Path(path_str)
    try:
        return path.read_text(encoding="utf-8").strip()
    except FileNotFoundError as error:
        raise FileNotFoundError(f"Context file not found: {path}") from error
    except OSError as error:
        raise OSError(f"Could not read context file {path}: {error}") from error


def normalize_file_reference(path_str: str | None) -> str:
    """Return a normalized, repo-relative-when-possible path reference string."""
    if not path_str:
        return ""

    path = pathlib.Path(path_str)
    try:
        resolved_path = path.resolve()
        repo_root = find_repo_root()
        if repo_root is not None:
            relative_path = resolved_path.relative_to(repo_root)
            return str(relative_path).replace("\\", "/")
    except (ValueError, OSError):
        pass

    normalized = path_str.strip().replace("\\", "/")
    if normalized.startswith("./"):
        return normalized[2:]
    return normalized


def infer_repo_name(target_input: str | None, repo_name: str | None) -> str:
    """Prefer explicit repo_name. Otherwise infer a reasonable repository name."""
    if repo_name:
        return repo_name

    if target_input:
        candidate = pathlib.Path(target_input).name
        if candidate:
            return candidate

    return pathlib.Path.cwd().name
