import pathlib
import tempfile
import unittest

from lrh.meta import local_state_model, workspace


class TestMetaConfig(unittest.TestCase):
    def _workspace(self, root: pathlib.Path) -> workspace.MetaWorkspace:
        workspace.init_workspace(
            root,
            spec=workspace.MetaWorkspaceSpec(workspace_name="Demo"),
        )
        return workspace.resolve_meta_workspace(cwd=root)

    def test_default_value_is_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            ws = self._workspace(pathlib.Path(tmp_dir))
            self.assertFalse(
                workspace.get_meta_config_value(ws, "trusted-persistent-local-state")
            )

    def test_set_get_list_unset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            ws = self._workspace(pathlib.Path(tmp_dir))
            value = workspace.set_meta_config_value(
                ws, "trusted-persistent-local-state", "yes"
            )
            self.assertTrue(value)
            self.assertTrue(
                workspace.get_meta_config_value(ws, "trusted-persistent-local-state")
            )
            values = workspace.read_meta_config(ws)
            self.assertTrue(values["trusted_persistent_local_state"])
            workspace.unset_meta_config_value(ws, "trusted-persistent-local-state")
            self.assertFalse(
                workspace.get_meta_config_value(ws, "trusted-persistent-local-state")
            )

    def test_underscore_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            ws = self._workspace(pathlib.Path(tmp_dir))
            workspace.set_meta_config_value(ws, "trusted_persistent_local_state", "1")
            self.assertTrue(
                workspace.get_meta_config_value(ws, "trusted-persistent-local-state")
            )

    def test_invalid_key_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            ws = self._workspace(pathlib.Path(tmp_dir))
            with self.assertRaises(workspace.MetaRegistryError):
                workspace.get_meta_config_value(ws, "trusted-persistnt-local-state")

    def test_invalid_boolean_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            ws = self._workspace(pathlib.Path(tmp_dir))
            with self.assertRaises(workspace.MetaRegistryError):
                workspace.set_meta_config_value(
                    ws, "trusted-persistent-local-state", "maybe"
                )

    def test_storage_policy_reads_setting(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            ws = self._workspace(pathlib.Path(tmp_dir))
            policy = workspace.storage_policy_for_workspace(ws)
            self.assertEqual(policy, local_state_model.MetaStoragePolicy())
            workspace.set_meta_config_value(
                ws, "trusted-persistent-local-state", "true"
            )
            trusted_policy = workspace.storage_policy_for_workspace(ws)
            self.assertTrue(trusted_policy.trusted_persistent_local_state)


if __name__ == "__main__":
    unittest.main()
