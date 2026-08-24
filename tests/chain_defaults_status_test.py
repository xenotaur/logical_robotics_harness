import pathlib
import subprocess
import tempfile
import unittest

from lrh import chain_defaults_status, gate_staleness

_PROFILE_TEMPLATE = """\
completion_condition: "done"
stop_work_condition: "stop"
chain_init_confirmation: skip_if_opted_in
closeout_with_merge: true
confirm_fixes_batch: always_confirm
confirmed_commit: {confirmed_commit}
confirmed_at: "2026-01-01T00:00:00Z"
"""


def _run(args: list[str], cwd: pathlib.Path) -> None:
    subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)


def _init_repo(root: pathlib.Path) -> None:
    _run(["git", "init", "-q"], root)
    _run(["git", "config", "user.email", "test@example.com"], root)
    _run(["git", "config", "user.name", "Test"], root)


def _commit(root: pathlib.Path, message: str) -> str:
    _run(["git", "add", "-A"], root)
    _run(["git", "commit", "-q", "-m", message], root)
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _write_profile(root: pathlib.Path, confirmed_commit: str) -> None:
    path = root / chain_defaults_status.CHAIN_DEFAULTS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_PROFILE_TEMPLATE.format(confirmed_commit=confirmed_commit))


class LoadProfileTest(unittest.TestCase):
    def test_missing_file_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.assertIsNone(chain_defaults_status.load_profile(root))

    def test_non_mapping_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            path = root / chain_defaults_status.CHAIN_DEFAULTS_PATH
            path.parent.mkdir(parents=True)
            path.write_text("- just\n- a\n- list\n")
            with self.assertRaises(chain_defaults_status.ChainDefaultsStatusError):
                chain_defaults_status.load_profile(root)

    def test_invalid_yaml_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            path = root / chain_defaults_status.CHAIN_DEFAULTS_PATH
            path.parent.mkdir(parents=True)
            path.write_text("key: [unclosed\n")
            with self.assertRaises(chain_defaults_status.ChainDefaultsStatusError):
                chain_defaults_status.load_profile(root)


class ComputeStatusTest(unittest.TestCase):
    def test_missing_profile_reports_absent_not_raise(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _init_repo(root)
            (root / "README.md").write_text("v1\n")
            _commit(root, "initial")
            status = chain_defaults_status.compute_status(project_root=root)
            self.assertFalse(status.profile_exists)
            self.assertEqual(
                status.fields, {name: None for name in chain_defaults_status.HUMAN_DECIDABLE_FIELDS}
            )
            self.assertIsNone(status.consent.stored_hash)
            self.assertFalse(status.consent.valid)

    def test_no_confirmed_commit_yields_staleness_error_not_raise(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _init_repo(root)
            _write_profile(root, confirmed_commit="null")
            _commit(root, "initial")
            status = chain_defaults_status.compute_status(project_root=root)
            self.assertTrue(status.profile_exists)
            self.assertIsNone(status.staleness)
            self.assertIn("no prior confirmation", status.staleness_error)

    def test_valid_confirmed_commit_computes_staleness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _init_repo(root)
            (root / "README.md").write_text("v1\n")
            first_commit = _commit(root, "initial")
            _write_profile(root, confirmed_commit=first_commit)
            _commit(root, "add profile")

            status = chain_defaults_status.compute_status(project_root=root)
            self.assertIsNotNone(status.staleness)
            self.assertIsNone(status.staleness_error)
            self.assertEqual(status.fields["chain_init_confirmation"], "skip_if_opted_in")
            self.assertEqual(status.read_only_fields[chain_defaults_status.READ_ONLY_FIELD], True)

    def test_consent_hash_match_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _init_repo(root)
            (root / "README.md").write_text("v1\n")
            first_commit = _commit(root, "initial")
            _write_profile(root, confirmed_commit=first_commit)
            _commit(root, "add profile")

            current_hash = chain_defaults_status.hash_object(
                root, chain_defaults_status.CHAIN_DEFAULTS_PATH
            )
            _run(
                [
                    "git",
                    "config",
                    "--local",
                    chain_defaults_status.CONSENT_HASH_CONFIG_KEY,
                    current_hash,
                ],
                root,
            )

            status = chain_defaults_status.compute_status(project_root=root)
            self.assertTrue(status.consent.valid)
            self.assertEqual(status.consent.stored_hash, current_hash)

    def test_consent_hash_mismatch_after_edit_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _init_repo(root)
            (root / "README.md").write_text("v1\n")
            first_commit = _commit(root, "initial")
            _write_profile(root, confirmed_commit=first_commit)
            _commit(root, "add profile")

            stale_hash = chain_defaults_status.hash_object(
                root, chain_defaults_status.CHAIN_DEFAULTS_PATH
            )
            _run(
                [
                    "git",
                    "config",
                    "--local",
                    chain_defaults_status.CONSENT_HASH_CONFIG_KEY,
                    stale_hash,
                ],
                root,
            )

            # Re-stamp the profile -- this changes the file's blob hash,
            # simulating this session's own real re-stamp-invalidates-
            # consent scenario.
            _write_profile(root, confirmed_commit=first_commit)
            (root / chain_defaults_status.CHAIN_DEFAULTS_PATH).write_text(
                _PROFILE_TEMPLATE.format(confirmed_commit=first_commit) + "extra: true\n"
            )
            _commit(root, "re-stamp")

            status = chain_defaults_status.compute_status(project_root=root)
            self.assertFalse(status.consent.valid)
            self.assertNotEqual(status.consent.stored_hash, status.consent.current_hash)


class FormatTest(unittest.TestCase):
    def test_format_text_missing_profile(self) -> None:
        status = chain_defaults_status.ChainDefaultsStatus(
            profile_exists=False,
            fields={name: None for name in chain_defaults_status.HUMAN_DECIDABLE_FIELDS},
            read_only_fields={chain_defaults_status.READ_ONLY_FIELD: None},
            consent=chain_defaults_status.ConsentStatus(
                stored_hash=None, current_hash="", valid=False
            ),
            staleness=None,
            staleness_error=None,
        )
        text = chain_defaults_status.format_text(status)
        self.assertIn("does not exist", text)

    def test_format_json_round_trips_stale_files(self) -> None:
        staleness = gate_staleness.StalenessResult(
            confirmed_commit="abc123",
            head="def456",
            stale=True,
            files=(
                gate_staleness.FileStaleness(
                    "src/lrh/skills/lrh-land/SKILL.md", stale=True, reason="touched"
                ),
            ),
        )
        status = chain_defaults_status.ChainDefaultsStatus(
            profile_exists=True,
            fields={name: "x" for name in chain_defaults_status.HUMAN_DECIDABLE_FIELDS},
            read_only_fields={chain_defaults_status.READ_ONLY_FIELD: True},
            consent=chain_defaults_status.ConsentStatus(
                stored_hash="a", current_hash="a", valid=True
            ),
            staleness=staleness,
            staleness_error=None,
        )
        text = chain_defaults_status.format_json(status)
        self.assertIn("lrh-land/SKILL.md", text)
        self.assertIn('"stale": true', text)


if __name__ == "__main__":
    unittest.main()
