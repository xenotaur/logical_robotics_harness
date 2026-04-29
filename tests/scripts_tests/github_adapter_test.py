import importlib.machinery
import importlib.util
import pathlib
import sys
import unittest
from unittest import mock


def load_github_adapter() -> object:
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    script_path = repo_root / "scripts" / "adapters" / "github"
    loader = importlib.machinery.SourceFileLoader("github_adapter", str(script_path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise RuntimeError("Could not load github adapter script.")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class GithubAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = load_github_adapter()

    def test_normalize_legacy_pull_threads_state_unresolved(self) -> None:
        args = self.adapter._normalize(["pull", "threads", "--state", "unresolved", "a/b", "1"])
        self.assertEqual(args, ["unresolved", "a/b", "1"])

    def test_normalize_pull_url(self) -> None:
        args = self.adapter._normalize(["threads", "https://github.com/octo/repo/pull/9", "ignored"])
        self.assertEqual(args, ["threads", "octo/repo", "9"])

    def test_main_delegates_to_lrh_cli(self) -> None:
        with mock.patch.object(sys, "argv", ["github", "comments", "a/b", "3"]):
            with mock.patch("lrh.cli.github.run_github_cli", return_value=0) as run_cli:
                self.adapter.github.run_github_cli(self.adapter._normalize(sys.argv[1:]), prog="scripts/adapters/github")
        run_cli.assert_called_once_with(["comments", "a/b", "3"], prog="scripts/adapters/github")


if __name__ == "__main__":
    unittest.main()
