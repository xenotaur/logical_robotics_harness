"""Default-vs-``--desktop`` behavior of the top-level scripts.

Every Rust tool is a stub on a sanitized PATH (the real ``~/.cargo/bin`` is
never visible) and HOME is a temporary directory, so these tests need no Rust
toolchain and never install anything. They prove that default runs never
invoke or probe the desktop toolchain, and that every ``--desktop`` mode fails
(never skips) on each missing or mismatched pin.
"""

import os
import pathlib
import re
import stat
import subprocess
import sys
import tempfile
import textwrap
import tomllib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
DESKTOP_DIR = REPO_ROOT / "apps" / "desktop"
RUST_PIN = tomllib.loads(
    (DESKTOP_DIR / "rust-toolchain.toml").read_text(encoding="utf-8")
)["toolchain"]["channel"]
TAURI_CLI_PIN = re.search(
    r"^TAURI_CLI_VERSION=(\S+)$",
    (DESKTOP_DIR / "toolchain.env").read_text(encoding="utf-8"),
    re.MULTILINE,
).group(1)
# A tiny, fast target so lint/format runs stay quick.
SMALL_PY_TARGET = "tests/scripts_tests/__init__.py"
TIMEOUT_SECONDS = 120

STUBS = {
    "rustup": """\
        echo "rustup $*" >> "$FAKE_LOG"
        case "$1" in
          --version) echo "rustup 1.29.0 (stub)" ;;
          toolchain)
            if [ "$2" = "list" ]; then printf '%s\\n' $FAKE_TOOLCHAINS; fi ;;
          component)
            if [ "$2" = "list" ]; then printf '%s\\n' $FAKE_COMPONENTS; fi ;;
        esac
        exit 0
        """,
    "rustc": """\
        echo "rustc $*" >> "$FAKE_LOG"
        echo "rustc $FAKE_RUSTC_VERSION (stub 2026-01-01)"
        """,
    "cargo": """\
        echo "cargo $*" >> "$FAKE_LOG"
        if [ "$1" = "tauri" ] && [ "$2" = "--version" ]; then
          if [ -z "$FAKE_TAURI_CLI" ]; then
            echo "error: no such command: tauri" >&2
            exit 101
          fi
          echo "tauri-cli $FAKE_TAURI_CLI"
          exit 0
        fi
        if [ "$1" = "--version" ]; then echo "cargo $FAKE_RUSTC_VERSION (stub)"; fi
        exit 0
        """,
    "xcode-select": """\
        echo "xcode-select $*" >> "$FAKE_LOG"
        echo /Library/Developer/CommandLineTools
        """,
    "pkg-config": """\
        echo "pkg-config $*" >> "$FAKE_LOG"
        exit 0
        """,
    # Linux build tools the preflight requires; stubbed so the test does not
    # depend on what the host has installed.
    "cc": "exit 0\n",
    "wget": "exit 0\n",
    "file": "exit 0\n",
    "curl": """\
        echo "curl $*" >> "$FAKE_LOG"
        echo 'echo "rustup-init $*" >> "$FAKE_LOG"'
        """,
    # Optional Python tools that plain `scripts/version tools` probes. They are
    # not under test here, and the real ones are slow to start.
    "pylint": """\
        echo "pylint 0.0.0 (stub)"
        """,
    "pyright": """\
        echo "pyright 0.0.0 (stub)"
        """,
    "conda": """\
        echo "conda 0.0.0 (stub)"
        """,
}
FAKE_PYTHON = """\
    echo "python $*" >> "$FAKE_LOG"
    exit 0
    """

# Each failure case: stubs to omit, environment overrides, and text the
# desktop error on stderr must contain.
FAILURE_CASES = {
    "rustup_absent": ({"rustup"}, {}, "rustup not found"),
    "cargo_absent": ({"cargo"}, {}, "cargo not found"),
    "toolchain_not_installed": (
        set(),
        {"FAKE_TOOLCHAINS": "stable-fake-host"},
        f"pinned Rust toolchain {RUST_PIN} is not installed",
    ),
    "toolchain_mismatched": (
        set(),
        {"FAKE_RUSTC_VERSION": "1.0.0"},
        f"expected {RUST_PIN}",
    ),
    "component_missing": (
        set(),
        {"FAKE_COMPONENTS": "rustfmt-fake-host"},
        "pinned component clippy is not installed",
    ),
    "tauri_cli_missing": (set(), {"FAKE_TAURI_CLI": ""}, "tauri-cli not installed"),
    "tauri_cli_mismatched": (
        set(),
        {"FAKE_TAURI_CLI": "0.0.1"},
        f"expected {TAURI_CLI_PIN}",
    ),
}

# Each --desktop mode: (argv, needs a fake `python` on PATH).
DESKTOP_MODES = {
    "develop": (["scripts/develop", "--desktop"], True),
    "test": (["scripts/test", "--desktop", SMALL_PY_TARGET], False),
    "lint": (["scripts/lint", "--desktop", SMALL_PY_TARGET], False),
    "format": (["scripts/format", "--check", "--desktop", SMALL_PY_TARGET], False),
    "version_tools": (["scripts/version", "tools", "--desktop"], False),
}


def _write_executable(path: pathlib.Path, body: str) -> None:
    path.write_text("#!/bin/sh\n" + textwrap.dedent(body), encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


class DesktopModesTestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # The interpreter's directory is on the sanitized PATH (for python,
        # ruff, black, pip). If it also held real Rust tools (e.g. a conda env
        # with conda-forge rust), the "absent" cases would be meaningless.
        interpreter_dir = pathlib.Path(sys.executable).parent
        leaked = [
            name
            for name in ("rustup", "cargo", "rustc")
            if (interpreter_dir / name).exists()
        ]
        if leaked:
            raise unittest.SkipTest(
                f"{interpreter_dir} contains real Rust tools {leaked}; run these "
                "tests from an environment without them"
            )

    def setUp(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.root = pathlib.Path(temp_dir.name)
        self.log = self.root / "calls.log"
        self.log.write_text("", encoding="utf-8")
        self.home = self.root / "home"
        self.home.mkdir()
        self.xdo_header = self.root / "xdo.h"
        self.xdo_header.write_text("", encoding="utf-8")

    def _run(
        self,
        argv: list[str],
        *,
        omit: set[str] = frozenset(),
        env_overrides: dict[str, str] | None = None,
        fake_python: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        stub_dir = self.root / "bin"
        stub_dir.mkdir(exist_ok=True)
        for name, body in STUBS.items():
            path = stub_dir / name
            if name in omit:
                path.unlink(missing_ok=True)
            else:
                _write_executable(path, body)
        fake_python_path = self.root / "fake-python" / "python"
        fake_python_path.parent.mkdir(exist_ok=True)
        _write_executable(fake_python_path, FAKE_PYTHON)

        path_entries = [str(stub_dir)]
        if fake_python:
            path_entries.append(str(fake_python_path.parent))
        # The real interpreter's directory supplies python/ruff/black/pip for
        # lint, format, and version; system dirs supply sh, sed, grep, uname.
        path_entries += [str(pathlib.Path(sys.executable).parent), "/usr/bin", "/bin"]
        env = {
            "PATH": os.pathsep.join(path_entries),
            "HOME": str(self.home),
            "FAKE_LOG": str(self.log),
            "LRH_DESKTOP_TEST_XDO_HEADER": str(self.xdo_header),
            "FAKE_TOOLCHAINS": f"{RUST_PIN}-fake-host",
            "FAKE_RUSTC_VERSION": RUST_PIN,
            "FAKE_COMPONENTS": "rustfmt-fake-host clippy-fake-host",
            "FAKE_TAURI_CLI": TAURI_CLI_PIN,
            "PYTHON": str(fake_python_path),
        }
        env.update(env_overrides or {})
        return subprocess.run(
            argv,
            check=False,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env=env,
            timeout=TIMEOUT_SECONDS,
        )

    def _rust_calls(self) -> list[str]:
        lines = self.log.read_text(encoding="utf-8").splitlines()
        return [
            line
            for line in lines
            if line.split(" ", 1)[0] in {"rustup", "rustc", "cargo", "curl"}
        ]


class DefaultRunsNeverTouchRustTest(DesktopModesTestBase):
    def test_default_scripts_never_invoke_rust_tools(self) -> None:
        for name, argv in {
            "test": ["scripts/test", SMALL_PY_TARGET],
            "lint": ["scripts/lint", SMALL_PY_TARGET],
            "format": ["scripts/format", "--check", SMALL_PY_TARGET],
            "version_tools": ["scripts/version", "tools"],
        }.items():
            with self.subTest(script=name):
                self.log.write_text("", encoding="utf-8")
                result = self._run(argv)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(self._rust_calls(), [])

    def test_default_test_prints_explicit_desktop_skip_line(self) -> None:
        result = self._run(["scripts/test", SMALL_PY_TARGET])

        self.assertIn(
            "desktop: SKIPPED (not requested; run scripts/test --desktop)",
            result.stdout,
        )

    def test_plain_version_tools_output_has_no_desktop_section(self) -> None:
        result = self._run(["scripts/version", "tools"])

        self.assertNotIn("tauri-cli", result.stdout)
        self.assertNotIn("Desktop pins", result.stdout)


class DesktopModesFailLoudlyTest(DesktopModesTestBase):
    def test_every_desktop_mode_fails_on_each_missing_or_mismatched_pin(
        self,
    ) -> None:
        for mode, (argv, fake_python) in DESKTOP_MODES.items():
            for case, (omit, overrides, expected_error) in FAILURE_CASES.items():
                with self.subTest(mode=mode, case=case):
                    result = self._run(
                        argv,
                        omit=omit,
                        env_overrides=overrides,
                        fake_python=fake_python,
                    )
                    self.assertNotEqual(
                        result.returncode, 0, result.stdout + result.stderr
                    )
                    # The failure must come from the desktop pin check, not
                    # from some unrelated step.
                    self.assertIn("desktop:", result.stderr)
                    self.assertIn(expected_error, result.stderr)
                    self.assertNotIn("desktop: SKIPPED", result.stdout)

    def test_desktop_modes_pass_and_run_rust_steps_when_pins_match(self) -> None:
        expected_calls = {
            "develop": "cargo tauri --version",
            "test": "cargo test --manifest-path src-tauri/Cargo.toml --locked",
            "lint": "cargo clippy --manifest-path src-tauri/Cargo.toml",
            "format": "cargo fmt --manifest-path src-tauri/Cargo.toml --all -- --check",
            "version_tools": "cargo tauri --version",
        }
        for mode, (argv, fake_python) in DESKTOP_MODES.items():
            with self.subTest(mode=mode):
                self.log.write_text("", encoding="utf-8")
                result = self._run(argv, fake_python=fake_python)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertTrue(
                    any(
                        call.startswith(expected_calls[mode])
                        for call in self._rust_calls()
                    ),
                    self._rust_calls(),
                )


class DevelopDesktopSetupTest(DesktopModesTestBase):
    def test_setup_reconciles_pinned_components(self) -> None:
        result = self._run(["scripts/develop", "--desktop"], fake_python=True)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(
            f"rustup component add --toolchain {RUST_PIN} rustfmt clippy",
            self.log.read_text(encoding="utf-8").splitlines(),
        )


class LinuxPrerequisitesTest(DesktopModesTestBase):
    """Exercise the Linux preflight on any host by stubbing `uname`."""

    def _run_as_linux(self, **kwargs) -> subprocess.CompletedProcess[str]:
        stub_dir = self.root / "bin"
        stub_dir.mkdir(exist_ok=True)
        _write_executable(stub_dir / "uname", "echo Linux\n")
        return self._run(["apps/desktop/scripts/run", "setup"], **kwargs)

    def test_linux_preflight_passes_with_stubbed_prerequisites(self) -> None:
        result = self._run_as_linux()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        # Prove the Linux branch ran, not the Darwin one.
        self.assertIn(
            "pkg-config --exists webkit2gtk-4.1",
            self.log.read_text(encoding="utf-8").splitlines(),
        )

    def test_linux_preflight_names_missing_libxdo_header(self) -> None:
        result = self._run_as_linux(
            env_overrides={"LRH_DESKTOP_TEST_XDO_HEADER": str(self.root / "absent.h")}
        )

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("libxdo (xdo.h)", result.stderr)


class FormatDesktopPreviewTest(DesktopModesTestBase):
    def test_diff_preview_never_runs_mutating_cargo_fmt(self) -> None:
        for flags in (["--diff"], ["--check"], ["--check", "--diff"]):
            with self.subTest(flags=flags):
                self.log.write_text("", encoding="utf-8")
                result = self._run(
                    ["scripts/format", *flags, "--desktop", SMALL_PY_TARGET]
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                fmt_calls = [c for c in self._rust_calls() if c.startswith("cargo fmt")]
                self.assertEqual(len(fmt_calls), 1, fmt_calls)
                self.assertTrue(fmt_calls[0].endswith("-- --check"), fmt_calls)


class DevelopDesktopFlagsTest(DesktopModesTestBase):
    def test_dry_run_runs_neither_pip_nor_rust_commands(self) -> None:
        result = self._run(
            ["scripts/develop", "--desktop", "--dry-run"], fake_python=True
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("python -m pip install -e .[dev]", result.stdout)
        self.assertIn("cargo install tauri-cli", result.stdout)
        calls = self.log.read_text(encoding="utf-8").splitlines()
        self.assertFalse(any(call.startswith("python") for call in calls), calls)
        self.assertEqual(self._rust_calls(), [])

    def test_missing_rustup_is_refused_without_install_rust(self) -> None:
        result = self._run(
            ["scripts/develop", "--desktop"], omit={"rustup"}, fake_python=True
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("https://sh.rustup.rs", result.stderr)
        self.assertIn("--install-rust", result.stderr)
        self.assertFalse(any(call.startswith("curl") for call in self._rust_calls()))

    def test_install_rust_runs_the_official_installer(self) -> None:
        result = self._run(
            ["scripts/develop", "--desktop", "--install-rust"],
            omit={"rustup"},
            fake_python=True,
        )

        curl_calls = [c for c in self._rust_calls() if c.startswith("curl")]
        self.assertEqual(len(curl_calls), 1, result.stdout + result.stderr)
        self.assertIn("https://sh.rustup.rs", curl_calls[0])
        self.assertIn(
            "rustup-init -y", self.log.read_text(encoding="utf-8"), result.stderr
        )

    def test_install_rust_without_desktop_is_a_usage_error(self) -> None:
        result = self._run(["scripts/develop", "--install-rust"], fake_python=True)

        self.assertEqual(result.returncode, 2)
        self.assertIn("--install-rust requires --desktop", result.stderr)
        self.assertEqual(self.log.read_text(encoding="utf-8"), "")


if __name__ == "__main__":
    unittest.main()
