import contextlib
import io
import json
import pathlib
import tempfile
import unittest
import unittest.mock
from typing import Any

from lrh import desktop_supervisor


def _ready(project_root: pathlib.Path, **overrides: Any) -> dict[str, Any]:
    message: dict[str, Any] = {
        "protocol": "lrh-desktop-server",
        "protocol_version": 1,
        "type": "ready",
        "launch_id": "launch-1",
        "backend": {"name": "lrh", "version": "0.0.0", "python": "3.11.0"},
        "pid": 1234,
        "workspace": {
            "requested_project_root": str(project_root),
            "project_root": str(project_root.resolve()),
            "project_dir": str(project_root.resolve() / "project"),
        },
        "endpoint": {
            "scheme": "http",
            "host": "127.0.0.1",
            "port": 50123,
            "url": "http://127.0.0.1:50123/",
        },
        "read_only": True,
        "execution_authority": False,
    }
    message.update(overrides)
    return message


class VerifyReadyTest(unittest.TestCase):
    def setUp(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.root = pathlib.Path(temp_dir.name)

    def test_verified_handshake_exposes_endpoint(self) -> None:
        handshake = desktop_supervisor.verify_ready(
            _ready(self.root), "launch-1", self.root
        )

        self.assertEqual(handshake.url, "http://127.0.0.1:50123/")
        self.assertEqual(handshake.port, 50123)
        self.assertEqual(handshake.backend["name"], "lrh")

    def test_project_control_dir_configuration_is_accepted(self) -> None:
        control_dir = self.root / "project"
        message = _ready(self.root)
        message["workspace"]["requested_project_root"] = str(control_dir)

        handshake = desktop_supervisor.verify_ready(message, "launch-1", control_dir)

        self.assertEqual(handshake.workspace["project_root"], str(self.root.resolve()))

    def test_requested_workspace_must_be_echoed(self) -> None:
        message = _ready(self.root)
        message["workspace"]["requested_project_root"] = "/somewhere/else"

        with self.assertRaises(desktop_supervisor.SupervisorError) as ctx:
            desktop_supervisor.verify_ready(message, "launch-1", self.root)

        self.assertEqual(ctx.exception.code, "workspace_mismatch")

    def test_ipv6_loopback_url_is_bracketed(self) -> None:
        message = _ready(self.root)
        message["endpoint"]["host"] = "::1"

        handshake = desktop_supervisor.verify_ready(message, "launch-1", self.root)

        self.assertEqual(handshake.url, "http://[::1]:50123/")

    def test_rejections_have_stable_codes(self) -> None:
        other_root = self.root / "other"
        other_root.mkdir()
        cases = {
            "incompatible_backend": _ready(self.root, protocol_version=2),
            "incompatible_backend (bool)": _ready(self.root, protocol_version=True),
            "launch_id_mismatch": _ready(self.root, launch_id="launch-0"),
            "workspace_mismatch": {
                **_ready(self.root),
                "workspace": _ready(other_root)["workspace"]
                | {"requested_project_root": str(self.root)},
            },
            "non_loopback_endpoint": _ready(
                self.root, endpoint={"host": "0.0.0.0", "port": 50123}
            ),
            "malformed_handshake": _ready(
                self.root, endpoint={"host": "127.0.0.1", "port": 0}
            ),
        }
        for code, message in cases.items():
            with self.subTest(code=code):
                with self.assertRaises(desktop_supervisor.SupervisorError) as ctx:
                    desktop_supervisor.verify_ready(message, "launch-1", self.root)
                self.assertEqual(ctx.exception.code, code.split(" ")[0])

    def test_control_dir_root_must_be_its_parent(self) -> None:
        control_dir = self.root / "project"
        unrelated = self.root / "unrelated"
        message = _ready(self.root)
        message["workspace"] = {
            "requested_project_root": str(control_dir),
            "project_root": str(unrelated.resolve()),
            "project_dir": str(control_dir.resolve()),
        }

        with self.assertRaises(desktop_supervisor.SupervisorError) as ctx:
            desktop_supervisor.verify_ready(message, "launch-1", control_dir)

        self.assertEqual(ctx.exception.code, "workspace_mismatch")

    def test_repo_root_requires_matching_control_dir(self) -> None:
        message = _ready(self.root)
        message["workspace"]["project_dir"] = "/elsewhere/project"

        with self.assertRaises(desktop_supervisor.SupervisorError) as ctx:
            desktop_supervisor.verify_ready(message, "launch-1", self.root)

        self.assertEqual(ctx.exception.code, "workspace_mismatch")


class MessageBuilderTest(unittest.TestCase):
    def test_start_request_carries_explicit_workspace_and_launch_id(self) -> None:
        request = desktop_supervisor.build_start_request(
            "abc", pathlib.Path("/work/repo")
        )

        self.assertEqual(
            request,
            {
                "protocol": "lrh-desktop-server",
                "protocol_version": 1,
                "type": "start",
                "launch_id": "abc",
                "workspace": {"project_root": "/work/repo"},
            },
        )

    def test_launch_ids_are_unique(self) -> None:
        self.assertNotEqual(
            desktop_supervisor.new_launch_id(), desktop_supervisor.new_launch_id()
        )


class OwnedServerTest(unittest.TestCase):
    def test_missing_executable_fails_to_spawn(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            owned = desktop_supervisor.OwnedServer(
                [str(pathlib.Path(temp_dir) / "no-such-lrh")], pathlib.Path(temp_dir)
            )

            with self.assertRaises(desktop_supervisor.SupervisorError) as ctx:
                owned.start()

        self.assertEqual(ctx.exception.code, "spawn_failed")
        self.assertEqual(owned.state, desktop_supervisor.STATE_FAILED)

    def test_command_appends_explicit_desktop_mode(self) -> None:
        owned = desktop_supervisor.OwnedServer(
            ["/opt/lrh/bin/lrh"], pathlib.Path("/work/repo")
        )

        self.assertEqual(
            owned.command, ["/opt/lrh/bin/lrh", "serve", "--desktop-protocol"]
        )

    def test_exited_child_is_not_running(self) -> None:
        owned = desktop_supervisor.OwnedServer(["lrh"], pathlib.Path("/work/repo"))
        owned.state = desktop_supervisor.STATE_RUNNING
        owned.process = unittest.mock.Mock()
        owned.process.poll.return_value = 1

        self.assertFalse(owned.is_running())
        self.assertEqual(owned.state, desktop_supervisor.STATE_FAILED)

    def test_example_reports_failed_json_when_health_check_fails(self) -> None:
        handshake = desktop_supervisor.verify_ready(
            _ready(pathlib.Path("/work/repo")), "launch-1", pathlib.Path("/work/repo")
        )
        owned = unittest.mock.Mock()
        owned.start.return_value = handshake
        owned.stop.return_value = desktop_supervisor.StopResult(0, "none", "x")
        stdout = io.StringIO()

        with (
            unittest.mock.patch.object(
                desktop_supervisor, "OwnedServer", return_value=owned
            ),
            unittest.mock.patch.object(
                desktop_supervisor, "fetch_health", side_effect=ConnectionRefusedError()
            ),
            contextlib.redirect_stdout(stdout),
        ):
            exit_code = desktop_supervisor.main(
                ["--lrh-executable", "/opt/lrh", "--project-root", "/work/repo"]
            )

        events = [json.loads(line)["event"] for line in stdout.getvalue().splitlines()]
        self.assertEqual(exit_code, 1)
        self.assertEqual(events, ["ready", "failed", "stopped"])
        owned.stop.assert_called_once_with()

    def test_stop_before_start_is_a_no_op(self) -> None:
        owned = desktop_supervisor.OwnedServer(["lrh"], pathlib.Path("/work/repo"))

        result = owned.stop()

        self.assertIsNone(result.exit_code)
        self.assertEqual(result.escalation, "none")


if __name__ == "__main__":
    unittest.main()
