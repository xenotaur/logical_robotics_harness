"""Tier-0 checks over the optional desktop app's configuration.

These run in the default Python suite with no Rust toolchain. They guard the
pins and the security-relevant Tauri configuration under apps/desktop/.
"""

import json
import pathlib
import re
import tomllib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
DESKTOP_DIR = REPO_ROOT / "apps" / "desktop"
SRC_TAURI = DESKTOP_DIR / "src-tauri"

# Permission families that would give pages native process, filesystem, or
# shell reach. L0 grants none of them to any window.
FORBIDDEN_PERMISSION_PREFIXES = ("shell:", "fs:", "process:", "opener:", "http:")


class DesktopAppPinsTest(unittest.TestCase):
    def test_rust_toolchain_is_pinned_to_an_exact_version(self) -> None:
        toolchain = tomllib.loads(
            (DESKTOP_DIR / "rust-toolchain.toml").read_text(encoding="utf-8")
        )["toolchain"]

        self.assertRegex(toolchain["channel"], r"^\d+\.\d+\.\d+$")
        self.assertIn("rustfmt", toolchain["components"])
        self.assertIn("clippy", toolchain["components"])

    def test_tauri_cli_is_pinned_to_an_exact_version(self) -> None:
        pins = (DESKTOP_DIR / "toolchain.env").read_text(encoding="utf-8")

        match = re.search(r"^TAURI_CLI_VERSION=(\S+)$", pins, re.MULTILINE)
        self.assertIsNotNone(match)
        assert match is not None
        self.assertRegex(match.group(1), r"^\d+\.\d+\.\d+$")

    def test_tauri_crates_are_exact_pinned_with_committed_lockfile(self) -> None:
        manifest = tomllib.loads((SRC_TAURI / "Cargo.toml").read_text(encoding="utf-8"))

        self.assertTrue(manifest["dependencies"]["tauri"]["version"].startswith("="))
        self.assertTrue(
            manifest["build-dependencies"]["tauri-build"]["version"].startswith("=")
        )
        self.assertTrue((SRC_TAURI / "Cargo.lock").is_file())

    def test_no_cargo_workspace_at_repository_root(self) -> None:
        self.assertFalse((REPO_ROOT / "Cargo.toml").exists())

    def test_no_node_toolchain_in_desktop_app(self) -> None:
        self.assertEqual(list(DESKTOP_DIR.rglob("package.json")), [])


class DesktopAppSecurityConfigTest(unittest.TestCase):
    def _config(self) -> dict:
        return json.loads((SRC_TAURI / "tauri.conf.json").read_text(encoding="utf-8"))

    def _capabilities(self) -> list[dict]:
        paths = sorted((SRC_TAURI / "capabilities").glob("*.json"))
        self.assertTrue(paths, "expected at least one capability file")
        return [json.loads(path.read_text(encoding="utf-8")) for path in paths]

    def test_capabilities_are_local_only(self) -> None:
        for capability in self._capabilities():
            with self.subTest(capability=capability["identifier"]):
                self.assertIs(capability.get("local", True), True)
                self.assertNotIn("remote", capability)

    def test_capabilities_grant_no_shell_filesystem_or_process_access(self) -> None:
        for capability in self._capabilities():
            for permission in capability["permissions"]:
                identifier = (
                    permission
                    if isinstance(permission, str)
                    else permission["identifier"]
                )
                with self.subTest(permission=identifier):
                    self.assertFalse(
                        identifier.startswith(FORBIDDEN_PERMISSION_PREFIXES),
                        f"{identifier} grants native reach to pages",
                    )

    def test_csp_is_set_without_unsafe_script_sources(self) -> None:
        csp = self._config()["app"]["security"]["csp"]

        self.assertIn("default-src 'self'", csp)
        self.assertNotIn("unsafe-eval", csp)
        script_src = re.search(r"script-src ([^;]*)", csp)
        assert script_src is not None
        self.assertNotIn("unsafe-inline", script_src.group(1))

    def test_bundled_frontend_is_local(self) -> None:
        frontend = self._config()["build"]["frontendDist"]

        self.assertFalse(frontend.startswith(("http://", "https://")))
        self.assertTrue((SRC_TAURI / frontend / "index.html").is_file())

    def test_global_tauri_api_is_not_injected_into_pages(self) -> None:
        self.assertFalse(self._config()["app"].get("withGlobalTauri", False))


if __name__ == "__main__":
    unittest.main()
