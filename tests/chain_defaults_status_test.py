import datetime
import json
import pathlib
import subprocess
import tempfile
import unittest
from unittest import mock

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
                status.fields,
                {name: None for name in chain_defaults_status.HUMAN_DECIDABLE_FIELDS},
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
            self.assertEqual(
                status.fields["chain_init_confirmation"], "skip_if_opted_in"
            )
            self.assertEqual(
                status.read_only_fields[chain_defaults_status.READ_ONLY_FIELD], True
            )

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
                _PROFILE_TEMPLATE.format(confirmed_commit=first_commit)
                + "extra: true\n"
            )
            _commit(root, "re-stamp")

            status = chain_defaults_status.compute_status(project_root=root)
            self.assertFalse(status.consent.valid)
            self.assertNotEqual(status.consent.stored_hash, status.consent.current_hash)


class FormatTest(unittest.TestCase):
    def test_format_text_missing_profile(self) -> None:
        status = chain_defaults_status.ChainDefaultsStatus(
            profile_exists=False,
            fields={
                name: None for name in chain_defaults_status.HUMAN_DECIDABLE_FIELDS
            },
            read_only_fields={chain_defaults_status.READ_ONLY_FIELD: None},
            consent=chain_defaults_status.ConsentStatus(
                stored_hash=None, current_hash="", valid=False
            ),
            staleness=None,
            staleness_error=None,
        )
        text = chain_defaults_status.format_text(status)
        self.assertIn("does not exist", text)

    def test_format_json_includes_all_files_not_just_stale(self) -> None:
        """Regression test: format_json must report every watched file with
        its own stale flag, matching gate_staleness.format_json()'s shape --
        not just the stale subset (copilot-pull-request-reviewer finding on
        PR #636)."""
        staleness = gate_staleness.StalenessResult(
            confirmed_commit="abc123",
            head="def456",
            stale=True,
            files=(
                gate_staleness.FileStaleness(
                    "src/lrh/skills/lrh-land/SKILL.md", stale=True, reason="touched"
                ),
                gate_staleness.FileStaleness(
                    "src/lrh/skills/lrh-execute/SKILL.md",
                    stale=False,
                    reason="no change",
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
        parsed = json.loads(chain_defaults_status.format_json(status))
        self.assertEqual(len(parsed["staleness"]["files"]), 2)
        by_path = {f["path"]: f for f in parsed["staleness"]["files"]}
        self.assertTrue(by_path["src/lrh/skills/lrh-land/SKILL.md"]["stale"])
        self.assertFalse(by_path["src/lrh/skills/lrh-execute/SKILL.md"]["stale"])


_FIXED_NOW = datetime.datetime(2026, 3, 4, 5, 6, 7, tzinfo=datetime.timezone.utc)


def _install_user_scope(home: pathlib.Path, body: str = "Wait.") -> None:
    for name in gate_staleness.INSTALLED_CANONICAL_SKILL_NAMES:
        path = home / ".claude" / "skills" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "<!-- GATE-DEFINITION -->\n" + body + "\n<!-- /GATE-DEFINITION -->\n"
        )


def _grant_consent(root: pathlib.Path) -> None:
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


class RestampTest(unittest.TestCase):
    """`lrh chain-defaults restamp` in a client repo where every watch
    target is a user-scope (fingerprint-kind) install under a fake HOME."""

    def _client_repo(self, root: pathlib.Path) -> str:
        _init_repo(root)
        (root / "README.md").write_text("v1\n")
        first = _commit(root, "initial")
        _write_profile(root, confirmed_commit=first)
        _commit(root, "add profile")
        return first

    def test_dry_run_writes_nothing_and_previews_stale_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as h:
            root = pathlib.Path(tmp)
            self._client_repo(root)
            home = pathlib.Path(h)
            _install_user_scope(home)
            profile_before = (
                root / chain_defaults_status.CHAIN_DEFAULTS_PATH
            ).read_text()
            with mock.patch.object(pathlib.Path, "home", return_value=home):
                plan = chain_defaults_status.plan_restamp(root, now=_FIXED_NOW)
            self.assertTrue(plan.staleness.stale)
            self.assertEqual(
                {e.comparison for e in plan.fingerprint_plan.entries}, {"new"}
            )
            self.assertEqual(plan.new_confirmed_at, "2026-03-04T05:06:07Z")
            self.assertEqual(len(plan.new_confirmed_commit), 40)
            self.assertFalse(gate_staleness.fingerprint_store_path(root).exists())
            self.assertEqual(
                (root / chain_defaults_status.CHAIN_DEFAULTS_PATH).read_text(),
                profile_before,
            )
            payload = json.loads(chain_defaults_status.format_restamp_json(plan, True))
            self.assertTrue(payload["dry_run"])
            self.assertTrue(payload["staleness"]["stale_files"])

    def test_restamp_reads_fresh_and_invalidates_consent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as h:
            root = pathlib.Path(tmp)
            self._client_repo(root)
            home = pathlib.Path(h)
            _install_user_scope(home)
            _grant_consent(root)
            profile_path = root / chain_defaults_status.CHAIN_DEFAULTS_PATH
            before_lines = profile_path.read_text().splitlines()
            with mock.patch.object(pathlib.Path, "home", return_value=home):
                self.assertTrue(
                    chain_defaults_status.compute_status(root).staleness.stale
                )
                plan = chain_defaults_status.plan_restamp(root, now=_FIXED_NOW)
                chain_defaults_status.apply_restamp(root, plan)
                status = chain_defaults_status.compute_status(root)
            self.assertFalse(status.staleness.stale)
            self.assertFalse(status.consent.valid)
            after_lines = profile_path.read_text().splitlines()
            changed = [(a, b) for a, b in zip(before_lines, after_lines) if a != b]
            self.assertEqual(len(before_lines), len(after_lines))
            self.assertEqual(
                [b for _, b in changed],
                [
                    f"confirmed_commit: {plan.new_confirmed_commit}",
                    "confirmed_at: 2026-03-04T05:06:07Z",
                ],
            )

    def test_missing_installed_target_refuses_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as h:
            root = pathlib.Path(tmp)
            self._client_repo(root)
            home = pathlib.Path(h)
            _install_user_scope(home)
            one = gate_staleness.INSTALLED_CANONICAL_SKILL_NAMES[0]
            (home / ".claude" / "skills" / one).unlink()
            profile_before = (
                root / chain_defaults_status.CHAIN_DEFAULTS_PATH
            ).read_text()
            with mock.patch.object(pathlib.Path, "home", return_value=home):
                with self.assertRaises(chain_defaults_status.ChainDefaultsStatusError):
                    chain_defaults_status.plan_restamp(root, now=_FIXED_NOW)
            self.assertFalse(gate_staleness.fingerprint_store_path(root).exists())
            self.assertEqual(
                (root / chain_defaults_status.CHAIN_DEFAULTS_PATH).read_text(),
                profile_before,
            )

    def test_store_without_committed_profile_fails_closed(self) -> None:
        """A failed profile write or a declined push leaves the new store
        beside the old profile. In a fingerprint-only repo that must read
        stale, with the old consent untouched -- not fresh."""
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as h:
            root = pathlib.Path(tmp)
            self._client_repo(root)
            home = pathlib.Path(h)
            _install_user_scope(home)
            _grant_consent(root)
            with mock.patch.object(pathlib.Path, "home", return_value=home):
                plan = chain_defaults_status.plan_restamp(root, now=_FIXED_NOW)
                chain_defaults_status.apply_restamp(root, plan)
                _run(
                    [
                        "git",
                        "checkout",
                        "--",
                        chain_defaults_status.CHAIN_DEFAULTS_PATH,
                    ],
                    root,
                )
                status = chain_defaults_status.compute_status(root)
            self.assertTrue(status.staleness.stale)
            self.assertTrue(status.consent.valid)
            for stale_file in status.staleness.stale_files:
                self.assertIn("different confirmation stamp", stale_file.reason)

    def test_status_and_raw_text_paths_agree_on_confirmed_at(self) -> None:
        """`status` reads confirmed_at through yaml.safe_load (a datetime);
        the shell snippet passes the raw text. Both must accept the store."""
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as h:
            root = pathlib.Path(tmp)
            self._client_repo(root)
            home = pathlib.Path(h)
            _install_user_scope(home)
            with mock.patch.object(pathlib.Path, "home", return_value=home):
                plan = chain_defaults_status.plan_restamp(root, now=_FIXED_NOW)
                chain_defaults_status.apply_restamp(root, plan)
                profile = chain_defaults_status.load_profile(root)
                self.assertIsInstance(profile["confirmed_at"], datetime.datetime)
                self.assertFalse(
                    chain_defaults_status.compute_status(root).staleness.stale
                )
                for raw in ("2026-03-04T05:06:07Z", "2026-03-04T05:06:07+00:00"):
                    with self.subTest(raw=raw):
                        result = gate_staleness.check_gate_staleness(
                            project_root=root,
                            confirmed_commit=plan.new_confirmed_commit,
                            confirmed_at=raw,
                        )
                        self.assertFalse(result.stale)

                # A hand-quoted profile value loads as a str, not a datetime.
                profile_path = root / chain_defaults_status.CHAIN_DEFAULTS_PATH
                profile_path.write_text(
                    profile_path.read_text().replace(
                        "confirmed_at: 2026-03-04T05:06:07Z",
                        'confirmed_at: "2026-03-04T05:06:07Z"',
                    )
                )
                self.assertIsInstance(
                    chain_defaults_status.load_profile(root)["confirmed_at"], str
                )
                self.assertFalse(
                    chain_defaults_status.compute_status(root).staleness.stale
                )

    def test_second_worktree_with_old_profile_reads_stale(self) -> None:
        with (
            tempfile.TemporaryDirectory() as tmp,
            tempfile.TemporaryDirectory() as other,
            tempfile.TemporaryDirectory() as h,
        ):
            root = pathlib.Path(tmp)
            self._client_repo(root)
            worktree = pathlib.Path(other) / "wt"
            _run(["git", "worktree", "add", "-q", "--detach", str(worktree)], root)
            home = pathlib.Path(h)
            _install_user_scope(home)
            with mock.patch.object(pathlib.Path, "home", return_value=home):
                plan = chain_defaults_status.plan_restamp(root, now=_FIXED_NOW)
                chain_defaults_status.apply_restamp(root, plan)
                self.assertFalse(
                    chain_defaults_status.compute_status(root).staleness.stale
                )
                self.assertTrue(
                    chain_defaults_status.compute_status(worktree).staleness.stale
                )

    def test_profile_without_stamp_lines_refuses_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as h:
            root = pathlib.Path(tmp)
            self._client_repo(root)
            profile_path = root / chain_defaults_status.CHAIN_DEFAULTS_PATH
            profile_path.write_text(
                "\n".join(
                    line
                    for line in profile_path.read_text().splitlines()
                    if not line.startswith("confirmed_at:")
                )
                + "\n"
            )
            home = pathlib.Path(h)
            _install_user_scope(home)
            with mock.patch.object(pathlib.Path, "home", return_value=home):
                plan = chain_defaults_status.plan_restamp(root, now=_FIXED_NOW)
                with self.assertRaises(chain_defaults_status.ChainDefaultsStatusError):
                    chain_defaults_status.apply_restamp(root, plan)
            self.assertFalse(gate_staleness.fingerprint_store_path(root).exists())

    def test_harness_repo_restamps_profile_without_writing_store(self) -> None:
        """With every watch target git-tracked (a repo carrying its own
        src/lrh/skills tree) and nothing stored, the stamp is still written
        but no fingerprint store is created."""
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _init_repo(root)
            for path in gate_staleness.DEFAULT_WATCHED_FILES:
                (root / path).parent.mkdir(parents=True, exist_ok=True)
                (root / path).write_text("# skill\n")
            first = _commit(root, "initial")
            _write_profile(root, confirmed_commit=first)
            _commit(root, "add profile")
            plan = chain_defaults_status.plan_restamp(root, now=_FIXED_NOW)
            self.assertTrue(plan.fingerprint_plan.nothing_to_do)
            chain_defaults_status.apply_restamp(root, plan)
            profile = chain_defaults_status.load_profile(root)
            self.assertEqual(profile["confirmed_commit"], plan.new_confirmed_commit)
            self.assertFalse(gate_staleness.fingerprint_store_path(root).exists())

    def test_expect_digest_mismatch_refuses_and_match_applies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as h:
            root = pathlib.Path(tmp)
            self._client_repo(root)
            home = pathlib.Path(h)
            _install_user_scope(home)
            profile_path = root / chain_defaults_status.CHAIN_DEFAULTS_PATH
            before = profile_path.read_text()
            with mock.patch.object(pathlib.Path, "home", return_value=home):
                preview = chain_defaults_status.plan_restamp(root, now=_FIXED_NOW)
                one = gate_staleness.INSTALLED_CANONICAL_SKILL_NAMES[0]
                (home / ".claude" / "skills" / one).write_text("changed after preview")
                current = chain_defaults_status.plan_restamp(root, now=_FIXED_NOW)
                self.assertNotEqual(preview.digest, current.digest)
                with self.assertRaises(chain_defaults_status.ChainDefaultsStatusError):
                    chain_defaults_status.apply_restamp(
                        root, current, expect_digest=preview.digest
                    )
                self.assertEqual(profile_path.read_text(), before)
                self.assertFalse(gate_staleness.fingerprint_store_path(root).exists())

                later = datetime.datetime(
                    2026, 3, 4, 5, 6, 8, tzinfo=datetime.timezone.utc
                )
                again = chain_defaults_status.plan_restamp(root, now=later)
                self.assertEqual(again.digest, current.digest)  # time excluded
                chain_defaults_status.apply_restamp(
                    root, again, expect_digest=current.digest
                )
                self.assertFalse(
                    chain_defaults_status.compute_status(root).staleness.stale
                )

    def test_failed_staleness_check_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as h:
            root = pathlib.Path(tmp)
            self._client_repo(root)
            profile_path = root / chain_defaults_status.CHAIN_DEFAULTS_PATH
            profile = chain_defaults_status.load_profile(root)
            profile_path.write_text(
                profile_path.read_text().replace(
                    profile["confirmed_commit"], "deadbeef" * 5
                )
            )
            home = pathlib.Path(h)
            _install_user_scope(home)
            with mock.patch.object(pathlib.Path, "home", return_value=home):
                with self.assertRaises(
                    chain_defaults_status.ChainDefaultsStatusError
                ) as ctx:
                    chain_defaults_status.plan_restamp(root, now=_FIXED_NOW)
            self.assertIn("staleness check failed", str(ctx.exception))

    def test_unreadable_installed_target_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as h:
            root = pathlib.Path(tmp)
            self._client_repo(root)
            home = pathlib.Path(h)
            _install_user_scope(home)
            real_read = pathlib.Path.read_bytes

            def flaky_read(path: pathlib.Path) -> bytes:
                if path.is_relative_to(home):
                    raise PermissionError("unreadable")
                return real_read(path)

            with (
                mock.patch.object(pathlib.Path, "home", return_value=home),
                mock.patch.object(pathlib.Path, "read_bytes", flaky_read),
            ):
                with self.assertRaises(
                    chain_defaults_status.ChainDefaultsStatusError
                ) as ctx:
                    chain_defaults_status.plan_restamp(root, now=_FIXED_NOW)
            self.assertIn("cannot read installed target", str(ctx.exception))

    def test_unreadable_target_with_existing_store_fails_closed(self) -> None:
        """With a store already recorded, the staleness check itself reads
        each installed file. An unreadable file must read stale in status
        and make restamp refuse -- never escape as a raw OSError."""
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as h:
            root = pathlib.Path(tmp)
            self._client_repo(root)
            home = pathlib.Path(h)
            _install_user_scope(home)
            real_read = pathlib.Path.read_bytes

            def flaky_read(path: pathlib.Path) -> bytes:
                if path.is_relative_to(home):
                    raise PermissionError("unreadable")
                return real_read(path)

            with mock.patch.object(pathlib.Path, "home", return_value=home):
                plan = chain_defaults_status.plan_restamp(root, now=_FIXED_NOW)
                chain_defaults_status.apply_restamp(root, plan)
                _run(["git", "add", "-A"], root)
                _run(["git", "commit", "-q", "-m", "restamp"], root)
                self.assertFalse(
                    chain_defaults_status.compute_status(root).staleness.stale
                )
                with mock.patch.object(pathlib.Path, "read_bytes", flaky_read):
                    status = chain_defaults_status.compute_status(root)
                    later = datetime.datetime(
                        2026, 3, 4, 5, 7, 0, tzinfo=datetime.timezone.utc
                    )
                    with self.assertRaises(
                        chain_defaults_status.ChainDefaultsStatusError
                    ) as ctx:
                        chain_defaults_status.plan_restamp(root, now=later)
            self.assertTrue(status.staleness.stale)
            for stale_file in status.staleness.stale_files:
                self.assertIn("unreadable", stale_file.reason)
            self.assertIn("cannot read installed target", str(ctx.exception))

    def test_identical_stamp_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as h:
            root = pathlib.Path(tmp)
            self._client_repo(root)
            home = pathlib.Path(h)
            _install_user_scope(home)
            with mock.patch.object(pathlib.Path, "home", return_value=home):
                plan = chain_defaults_status.plan_restamp(root, now=_FIXED_NOW)
                chain_defaults_status.apply_restamp(root, plan)
                with self.assertRaises(chain_defaults_status.ChainDefaultsStatusError):
                    chain_defaults_status.plan_restamp(root, now=_FIXED_NOW)

    def test_profile_replace_failure_after_store_write_fails_closed(self) -> None:
        """The store is written, then replacing the profile fails: the
        error is raised cleanly, the old profile and consent stay intact,
        and user-scope targets stay fail-closed (store stamp matches no
        profile)."""
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as h:
            root = pathlib.Path(tmp)
            self._client_repo(root)
            home = pathlib.Path(h)
            _install_user_scope(home)
            _grant_consent(root)
            profile_path = root / chain_defaults_status.CHAIN_DEFAULTS_PATH
            before = profile_path.read_text()
            real_replace = chain_defaults_status.os.replace

            def failing_replace(src, dst, *args, **kwargs):
                if pathlib.Path(dst).name == profile_path.name:
                    raise OSError("disk full")
                return real_replace(src, dst, *args, **kwargs)

            with mock.patch.object(pathlib.Path, "home", return_value=home):
                plan = chain_defaults_status.plan_restamp(root, now=_FIXED_NOW)
                with mock.patch.object(
                    chain_defaults_status.os, "replace", failing_replace
                ):
                    with self.assertRaises(
                        chain_defaults_status.ChainDefaultsStatusError
                    ) as ctx:
                        chain_defaults_status.apply_restamp(root, plan)
                self.assertIn("fail-closed", str(ctx.exception))
                self.assertTrue(gate_staleness.fingerprint_store_path(root).exists())
                self.assertEqual(profile_path.read_text(), before)
                status = chain_defaults_status.compute_status(root)
            self.assertTrue(status.consent.valid)
            self.assertTrue(status.staleness.stale)
            for stale_file in status.staleness.stale_files:
                self.assertIn("different confirmation stamp", stale_file.reason)

    def test_missing_profile_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _init_repo(root)
            (root / "README.md").write_text("v1\n")
            _commit(root, "initial")
            with self.assertRaises(chain_defaults_status.ChainDefaultsStatusError):
                chain_defaults_status.plan_restamp(root)


if __name__ == "__main__":
    unittest.main()
