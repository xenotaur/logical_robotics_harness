"""Installed-wheel smoke validation for LRH release workflows."""

from __future__ import annotations

import argparse
import collections.abc
import dataclasses
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]


@dataclasses.dataclass(frozen=True)
class DiagnosticCommandResult:
    """Captured output for a diagnostic command."""

    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


@dataclasses.dataclass(frozen=True)
class PthFileDiagnostic:
    """Diagnostic snapshot for one .pth file in the smoke venv."""

    path: pathlib.Path
    contents: str


@dataclasses.dataclass(frozen=True)
class IsolationDiagnostics:
    """Diagnostic snapshot for a smoke-test virtual environment."""

    python_executable: pathlib.Path
    pyvenv_cfg: str
    pip_version: DiagnosticCommandResult
    site: DiagnosticCommandResult
    interpreter: DiagnosticCommandResult
    pip_show: DiagnosticCommandResult
    lrh_spec: DiagnosticCommandResult
    pth_files: tuple[PthFileDiagnostic, ...]
    environment: tuple[tuple[str, str], ...]


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
    parser.add_argument(
        "--diagnose",
        action="store_true",
        help=(
            "Print temporary-venv isolation diagnostics before installing the wheel."
        ),
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


def _capture_diagnostic_command(command: list[str]) -> DiagnosticCommandResult:
    try:
        completed = subprocess.run(
            command,
            check=False,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        return DiagnosticCommandResult(
            command=tuple(command),
            returncode=127,
            stdout="",
            stderr=f"command not found: {error}",
        )
    except OSError as error:
        return DiagnosticCommandResult(
            command=tuple(command),
            returncode=126,
            stdout="",
            stderr=f"failed to execute command: {error}",
        )

    return DiagnosticCommandResult(
        command=tuple(command),
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _is_relevant_environment_name(name: str) -> bool:
    upper_name = name.upper()
    return (
        upper_name.startswith("PYTHON")
        or "PYTHON" in upper_name
        or upper_name.startswith("PIP")
        or "PIP" in upper_name
        or upper_name.startswith("CONDA")
        or "CONDA" in upper_name
        or upper_name.startswith("VIRTUAL_ENV")
        or "VIRTUAL_ENV" in upper_name
        or upper_name.startswith("LRH")
        or "LRH" in upper_name
    )


def _looks_sensitive(name: str, value: str) -> bool:
    candidate = f"{name}={value}".lower()
    sensitive_markers = (
        "secret",
        "token",
        "password",
        "passwd",
        "credential",
        "apikey",
        "api_key",
        "private_key",
    )
    if any(marker in candidate for marker in sensitive_markers):
        return True
    return "://" in value and "@" in value


def _filtered_environment(
    environ: collections.abc.Mapping[str, str],
) -> tuple[tuple[str, str], ...]:
    filtered: list[tuple[str, str]] = []
    for name, value in environ.items():
        if not _is_relevant_environment_name(name):
            continue
        if _looks_sensitive(name, value):
            filtered.append((name, "<redacted>"))
        else:
            filtered.append((name, value))
    return tuple(sorted(filtered))


def _discover_pth_files(venv_path: pathlib.Path) -> tuple[PthFileDiagnostic, ...]:
    candidates = [
        *venv_path.glob("lib/python*/site-packages/*.pth"),
        *venv_path.glob("Lib/site-packages/*.pth"),
    ]
    diagnostics: list[PthFileDiagnostic] = []
    for pth_path in sorted(set(candidates)):
        try:
            contents = pth_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            contents = pth_path.read_text(encoding="utf-8", errors="replace")
        except OSError as error:
            contents = f"<unable to read: {error}>"
        diagnostics.append(PthFileDiagnostic(path=pth_path, contents=contents))
    return tuple(diagnostics)


def collect_isolation_diagnostics(
    venv_path: pathlib.Path,
    python_bin: pathlib.Path,
    *,
    environ: collections.abc.Mapping[str, str] | None = None,
) -> IsolationDiagnostics:
    """Collect diagnostics that explain pre-install package visibility."""
    if environ is None:
        environ = os.environ

    pyvenv_cfg_path = venv_path / "pyvenv.cfg"
    try:
        pyvenv_cfg = pyvenv_cfg_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        pyvenv_cfg = "<missing>"
    except OSError as error:
        pyvenv_cfg = f"<unable to read: {error}>"

    interpreter_code = (
        "import pprint, sys; "
        "print('sys.executable = ' + sys.executable); "
        "print('sys.prefix = ' + sys.prefix); "
        "print('sys.base_prefix = ' + sys.base_prefix); "
        "print('sys.path ='); pprint.pp(sys.path)"
    )
    lrh_spec_code = (
        "import importlib.util; "
        "spec = importlib.util.find_spec('lrh'); "
        "print(spec)"
    )

    return IsolationDiagnostics(
        python_executable=python_bin,
        pyvenv_cfg=pyvenv_cfg,
        pip_version=_capture_diagnostic_command(
            [str(python_bin), "-m", "pip", "--version"]
        ),
        site=_capture_diagnostic_command([str(python_bin), "-m", "site"]),
        interpreter=_capture_diagnostic_command(
            [str(python_bin), "-c", interpreter_code]
        ),
        pip_show=_capture_diagnostic_command(
            [str(python_bin), "-m", "pip", "show", "-f", "logical-robotics-harness"]
        ),
        lrh_spec=_capture_diagnostic_command([str(python_bin), "-c", lrh_spec_code]),
        pth_files=_discover_pth_files(venv_path),
        environment=_filtered_environment(environ),
    )


def _format_command_result(result: DiagnosticCommandResult) -> str:
    lines = [f"$ {' '.join(result.command)}", f"returncode: {result.returncode}"]
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    if stdout:
        lines.extend(["stdout:", stdout])
    else:
        lines.append("stdout: <empty>")
    if stderr:
        lines.extend(["stderr:", stderr])
    else:
        lines.append("stderr: <empty>")
    return "\n".join(lines)


def render_isolation_diagnostics(diagnostics: IsolationDiagnostics) -> str:
    """Render release-smoke isolation diagnostics as grouped text."""
    lines = [
        "== Release smoke isolation diagnostics ==",
        "",
        "-- Virtual environment --",
        f"Python executable: {diagnostics.python_executable}",
        "pyvenv.cfg:",
    ]
    if diagnostics.pyvenv_cfg.strip():
        lines.extend(
            f"  {line}" for line in diagnostics.pyvenv_cfg.rstrip().splitlines()
        )
    else:
        lines.append("  <empty>")

    sections = (
        ("pip --version", diagnostics.pip_version),
        ("python -m site", diagnostics.site),
        ("interpreter identity and sys.path", diagnostics.interpreter),
        ("pip show -f logical-robotics-harness", diagnostics.pip_show),
        ('importlib.util.find_spec("lrh")', diagnostics.lrh_spec),
    )
    for title, result in sections:
        lines.extend(["", f"-- {title} --", _format_command_result(result)])

    lines.extend(["", "-- .pth files --"])
    if diagnostics.pth_files:
        for pth_file in diagnostics.pth_files:
            lines.append(f"{pth_file.path}:")
            if pth_file.contents.strip():
                lines.extend(
                    f"  {line}" for line in pth_file.contents.rstrip().splitlines()
                )
            else:
                lines.append("  <empty>")
    else:
        lines.append("<none found>")

    lines.extend(["", "-- Relevant environment variables --"])
    if diagnostics.environment:
        for name, value in diagnostics.environment:
            lines.append(f"{name}={value}")
    else:
        lines.append("<none found>")

    return "\n".join(lines)


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


def run_release_smoke(
    expected_version: str, *, preserve: bool, diagnose: bool = False
) -> int:
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

        if diagnose:
            diagnostics = collect_isolation_diagnostics(venv_path, python_bin)
            print(render_isolation_diagnostics(diagnostics))

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
        return run_release_smoke(
            args.expected_version, preserve=args.preserve, diagnose=args.diagnose
        )
    except ReleaseSmokeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
