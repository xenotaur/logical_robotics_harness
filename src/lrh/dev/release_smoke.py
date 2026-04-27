"""Installed-wheel smoke validation for LRH release workflows."""

from __future__ import annotations

import argparse
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]


class ReleaseSmokeError(RuntimeError):
    """Raised when release smoke validation fails."""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build LRH and smoke-test the installed wheel in a temporary venv.",
    )
    parser.add_argument(
        "expected_version",
        nargs="?",
        default="",
        help="Optional expected release version (for example: v0.2.0 or 0.2.0).",
    )
    parser.add_argument(
        "--preserve",
        action="store_true",
        help="Preserve temporary venv for debugging.",
    )
    return parser


def normalize_version(expected_version: str) -> str:
    """Normalize optional v-prefixed tags to plain version text."""
    candidate = expected_version.strip()
    if not candidate:
        return ""
    if candidate.startswith("v"):
        candidate = candidate[1:]
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:[A-Za-z0-9_.+-]*)?", candidate):
        raise ReleaseSmokeError(
            "expected version must look like vMAJOR.MINOR.PATCH or MAJOR.MINOR.PATCH"
        )
    return candidate


def _run(command: list[str], *, cwd: pathlib.Path | None = None) -> str:
    if cwd is None:
        cwd = REPO_ROOT

    printable = " ".join(command)
    print(f"Running: {printable}")
    try:
        completed = subprocess.run(
            command,
            check=False,
            cwd=cwd,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise ReleaseSmokeError(f"required command not found: {command[0]}") from error
    except OSError as error:
        raise ReleaseSmokeError(f"failed to execute command: {printable}") from error

    if completed.returncode != 0:
        raise ReleaseSmokeError(
            f"command failed ({completed.returncode}): {printable}\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
    if completed.stdout:
        print(completed.stdout.rstrip())
    if completed.stderr:
        print(completed.stderr.rstrip(), file=sys.stderr)
    return completed.stdout.strip()


def _resolve_wheel_path(expected_version: str) -> pathlib.Path:
    wheel_paths = sorted((REPO_ROOT / "dist").glob("*.whl"))
    if not wheel_paths:
        raise ReleaseSmokeError("no wheel found in dist/ after build")

    if expected_version:
        version_fragment = expected_version.replace("-", "_")
        wheel_paths = [
            wheel_path
            for wheel_path in wheel_paths
            if f"-{version_fragment}-" in wheel_path.name
        ]
        if not wheel_paths:
            raise ReleaseSmokeError(
                f"no wheel in dist/ matched expected version {expected_version}"
            )

    if len(wheel_paths) != 1:
        wheel_names = "\n".join(f"- {wheel_path.name}" for wheel_path in wheel_paths)
        raise ReleaseSmokeError(
            "expected exactly one wheel artifact in dist/; found:\n" f"{wheel_names}"
        )

    return wheel_paths[0]


def run_release_smoke(expected_version: str, *, preserve: bool) -> int:
    normalized_version = normalize_version(expected_version)

    _run(["scripts/clean"])
    _run(["scripts/build"])
    wheel_path = _resolve_wheel_path(normalized_version)
    print(f"Using wheel: {wheel_path.relative_to(REPO_ROOT)}")

    venv_root = pathlib.Path(tempfile.mkdtemp(prefix="lrh-release-smoke-"))
    venv_path = venv_root / "venv"
    python_bin = venv_path / "bin" / "python"
    lrh_bin = venv_path / "bin" / "lrh"

    try:
        _run([sys.executable, "-m", "venv", str(venv_path)])
        _run([str(python_bin), "-m", "pip", "--version"])

        preinstalled_name = "logical-robotics-harness"
        preinstall_check = subprocess.run(
            [
                str(python_bin),
                "-m",
                "pip",
                "show",
                preinstalled_name,
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        if preinstall_check.returncode == 0:
            print(
                f"WARNING: {preinstalled_name} is already visible before install:\n"
                f"{preinstall_check.stdout.strip()}",
                file=sys.stderr,
            )

        _run(
            [
                str(python_bin),
                "-m",
                "pip",
                "install",
                "--force-reinstall",
                str(wheel_path),
            ]
        )
        if not lrh_bin.exists():
            raise ReleaseSmokeError(
                f"installed console script is missing: {lrh_bin}\n"
                "inspect wheel metadata/entry points "
                "(for example: unzip -p <wheel>.whl '*.dist-info/entry_points.txt')"
            )
        version_output = _run([str(lrh_bin), "--version"])
        _run([str(lrh_bin), "snapshot", "--help"])

        if normalized_version:
            expected_line = f"lrh {normalized_version}"
            if version_output.splitlines()[-1].strip() != expected_line:
                raise ReleaseSmokeError(
                    "installed CLI version mismatch: "
                    f"expected '{expected_line}', got '{version_output}'"
                )
    finally:
        if preserve:
            print(f"Preserved smoke environment: {venv_root}")
        else:
            shutil.rmtree(venv_root, ignore_errors=True)

    print("release smoke passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        return run_release_smoke(args.expected_version, preserve=args.preserve)
    except ReleaseSmokeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
