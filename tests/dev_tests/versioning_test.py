import io
import unittest
from unittest import mock

from lrh.dev import versioning


class VersioningTests(unittest.TestCase):
    def test_main_without_subcommand_prints_lrh_version(self) -> None:
        with mock.patch("lrh.version.format_cli_version", return_value="lrh 1.2.3"):
            stdout = io.StringIO()
            with mock.patch("sys.stdout", new=stdout):
                result = versioning.main([])

        self.assertEqual(result, 0)
        self.assertEqual(stdout.getvalue().strip(), "lrh 1.2.3")

    def test_verify_release_validates_tag_and_runs_checks(self) -> None:
        run_results = [
            mock.Mock(returncode=0, stdout=""),
            mock.Mock(returncode=0, stdout=""),
            mock.Mock(returncode=0),
            mock.Mock(returncode=0),
            mock.Mock(returncode=0),
        ]
        with mock.patch("lrh.dev.versioning.shutil.which", return_value="/usr/bin/git"):
            with mock.patch(
                "lrh.dev.versioning._run_command", side_effect=run_results
            ) as run_mock:
                versioning.verify_release("v1.0.0")

        called_commands = [call.args[0] for call in run_mock.call_args_list]
        self.assertEqual(
            called_commands,
            [
                ["git", "check-ref-format", "refs/tags/v1.0.0"],
                ["git", "status", "--porcelain"],
                ["scripts/lint"],
                ["scripts/format", "--check"],
                ["scripts/test"],
            ],
        )

    def test_verify_release_fails_on_dirty_tree(self) -> None:
        with mock.patch("lrh.dev.versioning.shutil.which", return_value="/usr/bin/git"):
            with mock.patch(
                "lrh.dev.versioning._run_command",
                side_effect=[mock.Mock(returncode=0, stdout=" M scripts/version\n")],
            ):
                with self.assertRaisesRegex(
                    versioning.VersioningError, "working tree must be clean"
                ):
                    versioning.verify_release("")

    def test_create_tag_is_idempotent_when_tag_exists_on_head(self) -> None:
        with mock.patch("lrh.dev.versioning._ensure_valid_tag"):
            with mock.patch(
                "lrh.dev.versioning._resolve_head_commit", return_value="abc123"
            ):
                with mock.patch(
                    "lrh.dev.versioning._resolve_local_tag_commit",
                    return_value="abc123",
                ):
                    with mock.patch("lrh.dev.versioning.verify_release") as verify_mock:
                        with mock.patch("lrh.dev.versioning._run_command") as run_mock:
                            versioning.create_tag("v1.2.3")

        verify_mock.assert_not_called()
        run_mock.assert_not_called()

    def test_create_tag_fails_if_existing_tag_points_elsewhere(self) -> None:
        with mock.patch("lrh.dev.versioning._ensure_valid_tag"):
            with mock.patch(
                "lrh.dev.versioning._resolve_head_commit", return_value="abc123"
            ):
                with mock.patch(
                    "lrh.dev.versioning._resolve_local_tag_commit",
                    return_value="def456",
                ):
                    with self.assertRaisesRegex(
                        versioning.VersioningError, "already exists"
                    ):
                        versioning.create_tag("v1.2.3")

    def test_push_tag_is_idempotent_when_remote_matches_local(self) -> None:
        with mock.patch("lrh.dev.versioning._ensure_valid_tag"):
            with mock.patch(
                "lrh.dev.versioning._resolve_local_tag_commit", return_value="abc123"
            ):
                with mock.patch(
                    "lrh.dev.versioning._resolve_remote_tag_commit",
                    return_value="abc123",
                ):
                    with mock.patch("lrh.dev.versioning._run_command") as run_mock:
                        versioning.push_tag("v1.2.3")

        run_mock.assert_not_called()

    def test_push_tag_fails_when_remote_tag_differs(self) -> None:
        with mock.patch("lrh.dev.versioning._ensure_valid_tag"):
            with mock.patch(
                "lrh.dev.versioning._resolve_local_tag_commit", return_value="abc123"
            ):
                with mock.patch(
                    "lrh.dev.versioning._resolve_remote_tag_commit",
                    return_value="def456",
                ):
                    with self.assertRaisesRegex(
                        versioning.VersioningError, "remote tag"
                    ):
                        versioning.push_tag("v1.2.3")


if __name__ == "__main__":
    unittest.main()
