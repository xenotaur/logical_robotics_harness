import datetime
import pathlib
import tempfile
import unittest

from lrh.meta import local_state_model, workspace


class TestLocalStateModelResolution(unittest.TestCase):
    def _workspace(self, root: pathlib.Path) -> workspace.MetaWorkspace:
        workspace.init_workspace(
            root,
            spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
        )
        return workspace.resolve_meta_workspace(cwd=root)

    def _record(
        self,
        *,
        repo_locator: str,
        project_dir: str = "project",
    ) -> workspace.MetaProjectRecord:
        return workspace.MetaProjectRecord(
            registry_name="demo",
            short_name="demo",
            display_name="Demo",
            project_id="proj-demo",
            repo_locator=repo_locator,
            project_dir=project_dir,
            setup_state="unknown",
        )

    def test_url_only_locator_resolves_remote_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            ws = self._workspace(root)
            record = self._record(repo_locator="https://github.com/example/demo.git")

            resolved = local_state_model.resolve_project_context(
                record, workspace_context=ws
            )

            self.assertIsNone(resolved.resolved_repo_path)
            self.assertEqual(
                resolved.resolved_repo_path_source, "repo_locator_remote_url"
            )
            self.assertEqual(resolved.source_state, "remote_only")

    def test_local_path_locator_resolves_local_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            repo = root / "repo"
            repo.mkdir()
            ws = self._workspace(root)
            record = self._record(repo_locator=str(repo))

            resolved = local_state_model.resolve_project_context(
                record, workspace_context=ws
            )

            self.assertEqual(resolved.resolved_repo_path, repo.resolve())
            self.assertEqual(
                resolved.resolved_repo_path_source, "repo_locator_local_path"
            )
            self.assertEqual(resolved.source_state, "local_available")

    def test_private_checkout_binding_overrides_url_only_locator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            bound_repo = root / "bound"
            bound_repo.mkdir()
            ws = self._workspace(root)
            record = self._record(repo_locator="https://github.com/example/demo.git")
            request = local_state_model.ResolveContextRequest(
                private_checkout_binding=local_state_model.CheckoutBinding(
                    local_repo_path=bound_repo,
                    storage_source="private_runtime",
                )
            )

            resolved = local_state_model.resolve_project_context(
                record,
                workspace_context=ws,
                request=request,
            )

            self.assertEqual(resolved.resolved_repo_path, bound_repo.resolve())
            self.assertEqual(
                resolved.resolved_repo_path_source, "private_checkout_binding"
            )
            self.assertEqual(resolved.source_state, "local_available")

    def test_trusted_checkout_binding_ignored_without_trust_toggle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            trusted_repo = root / "trusted"
            trusted_repo.mkdir()
            ws = self._workspace(root)
            record = self._record(repo_locator="https://github.com/example/demo.git")
            request = local_state_model.ResolveContextRequest(
                trusted_checkout_binding=local_state_model.CheckoutBinding(
                    local_repo_path=trusted_repo,
                    storage_source="trusted_workspace",
                )
            )

            resolved = local_state_model.resolve_project_context(
                record,
                workspace_context=ws,
                request=request,
            )

            self.assertIsNone(resolved.resolved_repo_path)
            self.assertEqual(
                resolved.resolved_repo_path_source, "repo_locator_remote_url"
            )

    def test_trusted_checkout_binding_used_when_trust_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            trusted_repo = root / "trusted"
            trusted_repo.mkdir()
            ws = self._workspace(root)
            record = self._record(repo_locator="https://github.com/example/demo.git")
            request = local_state_model.ResolveContextRequest(
                trusted_checkout_binding=local_state_model.CheckoutBinding(
                    local_repo_path=trusted_repo,
                    storage_source="trusted_workspace",
                ),
                storage_policy=local_state_model.storage_policy_from_trust(
                    trusted_persistent_local_state=True
                ),
            )

            resolved = local_state_model.resolve_project_context(
                record,
                workspace_context=ws,
                request=request,
            )

            self.assertEqual(resolved.resolved_repo_path, trusted_repo.resolve())
            self.assertEqual(
                resolved.resolved_repo_path_source,
                "trusted_workspace_checkout_binding",
            )

    def test_observation_check_serializes_status_and_checked_as_of(self) -> None:
        check = local_state_model.ObservationCheck(
            status="ok",
            checked_as_of=datetime.datetime(2026, 5, 19, 12, 0, tzinfo=datetime.UTC),
            detail="reachable",
            source="meta_refresh",
        )

        payload = check.to_json_dict()

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["checked_as_of"], "2026-05-19T12:00:00+00:00")
        self.assertEqual(payload["detail"], "reachable")
        self.assertEqual(payload["source"], "meta_refresh")

    def test_storage_policy_defaults_to_private_state(self) -> None:
        policy = local_state_model.MetaStoragePolicy()

        self.assertFalse(policy.trusted_persistent_local_state)
        self.assertEqual(policy.identity_storage, "registry_record")
        self.assertEqual(policy.checkout_binding_storage, "private_runtime")
        self.assertEqual(policy.observation_storage, "private_runtime")

    def test_trusted_persistent_local_state_switches_storage_source(self) -> None:
        policy = local_state_model.storage_policy_from_trust(
            trusted_persistent_local_state=True
        )

        self.assertTrue(policy.trusted_persistent_local_state)
        self.assertEqual(policy.identity_storage, "registry_record")
        self.assertEqual(policy.checkout_binding_storage, "trusted_workspace")
        self.assertEqual(policy.observation_storage, "trusted_workspace")

    def test_existing_registry_record_shape_remains_loadable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            ws = self._workspace(root)
            record_dir = ws.projects_dir / "legacy"
            record_dir.mkdir(parents=True)
            (record_dir / "project.toml").write_text(
                "\n".join(
                    [
                        'schema_version = "0.1"',
                        "",
                        "[project]",
                        'short_name = "legacy"',
                        'display_name = "Legacy Project"',
                        'setup_state = "lrh_project_present"',
                        "",
                        "[identity]",
                        'project_id = "proj-legacy"',
                        "",
                        "[locators]",
                        'repo_locator = "https://github.com/example/legacy.git"',
                        'project_dir = "project"',
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            records = workspace.list_registered_projects_in_workspace(ws)

            self.assertEqual(len(records), 1)
            resolved = local_state_model.resolve_project_context(
                records[0], workspace_context=ws
            )
            self.assertEqual(
                resolved.resolved_repo_path_source, "repo_locator_remote_url"
            )

    def test_absolute_project_dir_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            repo = root / "repo"
            repo.mkdir()
            ws = self._workspace(root)
            record = self._record(repo_locator=str(repo), project_dir="/etc")

            resolved = local_state_model.resolve_project_context(
                record,
                workspace_context=ws,
            )

            self.assertIsNone(resolved.resolved_project_path)

    def test_escaping_project_dir_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            repo = root / "repo"
            repo.mkdir()
            ws = self._workspace(root)
            record = self._record(repo_locator=str(repo), project_dir="../escape")

            resolved = local_state_model.resolve_project_context(
                record,
                workspace_context=ws,
            )

            self.assertIsNone(resolved.resolved_project_path)


if __name__ == "__main__":
    unittest.main()
