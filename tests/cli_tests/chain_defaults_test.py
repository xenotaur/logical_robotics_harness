import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

from lrh import chain_defaults_status, gate_staleness

_PROFILE = """\
completion_condition: "done"
stop_work_condition: "stop"
chain_init_confirmation: skip_if_opted_in
closeout_with_merge: true
confirm_fixes_batch: always_confirm
confirmed_commit: {confirmed_commit}
confirmed_at: 2026-01-01T00:00:00Z
"""


def _git(args: list[str], cwd: pathlib.Path) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


class ChainDefaultsCliTest(unittest.TestCase):
    """`lrh chain-defaults restamp` and `check-staleness --confirmed-at`, run
    as a subprocess against a client repo whose only watch targets are a
    user-scope install under a temporary HOME."""

    def _repo_root(self) -> pathlib.Path:
        return pathlib.Path(__file__).resolve().parents[2]

    def _lrh(self, args: list[str], home: pathlib.Path) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env["HOME"] = str(home)
        src = str(self._repo_root() / "src")
        env["PYTHONPATH"] = src + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run(
            [sys.executable, "-m", "lrh.cli.main", *args],
            check=False,
            capture_output=True,
            text=True,
            env=env,
            cwd=self._repo_root(),
        )

    def _client_repo(self, root: pathlib.Path, home: pathlib.Path) -> None:
        _git(["init", "-q"], root)
        _git(["config", "user.email", "test@example.com"], root)
        _git(["config", "user.name", "Test"], root)
        (root / "README.md").write_text("v1\n")
        _git(["add", "-A"], root)
        _git(["commit", "-q", "-m", "initial"], root)
        first = _git(["rev-parse", "HEAD"], root)
        profile = root / chain_defaults_status.CHAIN_DEFAULTS_PATH
        profile.parent.mkdir(parents=True)
        profile.write_text(_PROFILE.format(confirmed_commit=first))
        _git(["add", "-A"], root)
        _git(["commit", "-q", "-m", "profile"], root)
        for name in gate_staleness.INSTALLED_CANONICAL_SKILL_NAMES:
            path = home / ".claude" / "skills" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "<!-- GATE-DEFINITION -->\nWait.\n<!-- /GATE-DEFINITION -->\n"
            )

    def test_restamp_dry_run_json_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as h:
            root, home = pathlib.Path(tmp), pathlib.Path(h)
            self._client_repo(root, home)
            before = (root / chain_defaults_status.CHAIN_DEFAULTS_PATH).read_text()
            completed = self._lrh(
                [
                    "chain-defaults",
                    "restamp",
                    "--project-root",
                    str(root),
                    "--dry-run",
                    "--format",
                    "json",
                ],
                home,
            )
            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertTrue(payload["dry_run"])
            self.assertEqual(
                {e["comparison"] for e in payload["fingerprints"]["entries"]}, {"new"}
            )
            self.assertTrue(payload["staleness"]["stale"])
            self.assertEqual(
                (root / chain_defaults_status.CHAIN_DEFAULTS_PATH).read_text(), before
            )
            self.assertFalse(gate_staleness.fingerprint_store_path(root).exists())

    def test_restamp_then_check_staleness_with_confirmed_at(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as h:
            root, home = pathlib.Path(tmp), pathlib.Path(h)
            self._client_repo(root, home)
            preview = self._lrh(
                [
                    "chain-defaults",
                    "restamp",
                    "--project-root",
                    str(root),
                    "--dry-run",
                    "--format",
                    "json",
                ],
                home,
            )
            digest = json.loads(preview.stdout)["plan_digest"]
            completed = self._lrh(
                [
                    "chain-defaults",
                    "restamp",
                    "--project-root",
                    str(root),
                    "--expect-digest",
                    digest,
                ],
                home,
            )
            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            self.assertIn("Re-stamped:", completed.stdout)

            profile = (root / chain_defaults_status.CHAIN_DEFAULTS_PATH).read_text()
            values = dict(
                line.split(": ", 1)
                for line in profile.splitlines()
                if line.startswith(("confirmed_commit:", "confirmed_at:"))
            )
            base = [
                "chain-defaults",
                "check-staleness",
                "--project-root",
                str(root),
                "--confirmed-commit",
                values["confirmed_commit"],
            ]
            fresh = self._lrh([*base, "--confirmed-at", values["confirmed_at"]], home)
            self.assertEqual(fresh.returncode, 0, msg=fresh.stdout + fresh.stderr)
            missing_at = self._lrh(base, home)
            self.assertEqual(missing_at.returncode, 1, msg=missing_at.stdout)
            self.assertIn("no confirmed_at supplied", missing_at.stdout)

            status = self._lrh(
                [
                    "chain-defaults",
                    "status",
                    "--project-root",
                    str(root),
                    "--format",
                    "json",
                ],
                home,
            )
            self.assertEqual(status.returncode, 0, msg=status.stderr)
            self.assertFalse(json.loads(status.stdout)["staleness"]["stale"])

    def test_restamp_refuses_with_exit_2_on_missing_installed_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as h:
            root, home = pathlib.Path(tmp), pathlib.Path(h)
            self._client_repo(root, home)
            one = gate_staleness.INSTALLED_CANONICAL_SKILL_NAMES[0]
            (home / ".claude" / "skills" / one).unlink()
            before = (root / chain_defaults_status.CHAIN_DEFAULTS_PATH).read_text()
            completed = self._lrh(
                [
                    "chain-defaults",
                    "restamp",
                    "--project-root",
                    str(root),
                    "--format",
                    "json",
                ],
                home,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertEqual(completed.stdout, "")
            self.assertIn("refusing to re-stamp", completed.stderr)
            self.assertEqual(
                (root / chain_defaults_status.CHAIN_DEFAULTS_PATH).read_text(), before
            )
            self.assertFalse(gate_staleness.fingerprint_store_path(root).exists())

    def test_restamp_expect_digest_mismatch_exits_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as h:
            root, home = pathlib.Path(tmp), pathlib.Path(h)
            self._client_repo(root, home)
            before = (root / chain_defaults_status.CHAIN_DEFAULTS_PATH).read_text()
            completed = self._lrh(
                [
                    "chain-defaults",
                    "restamp",
                    "--project-root",
                    str(root),
                    "--expect-digest",
                    "0" * 64,
                ],
                home,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("plan changed since the approved preview", completed.stderr)
            self.assertEqual(
                (root / chain_defaults_status.CHAIN_DEFAULTS_PATH).read_text(), before
            )
            self.assertFalse(gate_staleness.fingerprint_store_path(root).exists())


if __name__ == "__main__":
    unittest.main()
