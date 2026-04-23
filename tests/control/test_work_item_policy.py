import tempfile
import unittest
from pathlib import Path

from lrh.control import work_item_policy


class TestWorkItemPolicy(unittest.TestCase):
    def _make_project(self) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / "work_items" / "active").mkdir(parents=True)
        (root / "work_items" / "proposed").mkdir(parents=True)
        (root / "work_items" / "resolved").mkdir(parents=True)
        (root / "work_items" / "abandoned").mkdir(parents=True)
        return root

    def test_valid_active_item(self) -> None:
        root = self._make_project()
        path = root / "work_items" / "active" / "WI-0001.md"
        metadata = {
            "id": "WI-0001",
            "title": "Test",
            "status": "active",
            "blocked": False,
            "created_on": "2026-04-22",
            "updated_on": "2026-04-22",
        }

        result = work_item_policy.validate_work_item_policy(root, path, metadata)

        self.assertTrue(result.is_valid)

    def test_bucket_status_mismatch_is_error(self) -> None:
        root = self._make_project()
        path = root / "work_items" / "proposed" / "WI-0001.md"
        metadata = {
            "id": "WI-0001",
            "title": "Test",
            "status": "active",
        }

        result = work_item_policy.validate_work_item_policy(root, path, metadata)

        codes = {issue.code for issue in result.errors}
        self.assertIn("WORK_ITEM_BUCKET_STATUS_MISMATCH", codes)

    def test_terminal_status_requires_resolution(self) -> None:
        root = self._make_project()
        path = root / "work_items" / "resolved" / "WI-0002.md"
        metadata = {
            "id": "WI-0002",
            "title": "Done",
            "status": "resolved",
        }

        result = work_item_policy.validate_work_item_policy(root, path, metadata)

        codes = {issue.code for issue in result.errors}
        self.assertIn("WORK_ITEM_RESOLUTION_REQUIRED", codes)

    def test_non_terminal_status_requires_null_resolution(self) -> None:
        root = self._make_project()
        path = root / "work_items" / "active" / "WI-0002.md"
        metadata = {
            "id": "WI-0002",
            "title": "In flight",
            "status": "active",
            "resolution": "Completed",
        }

        result = work_item_policy.validate_work_item_policy(root, path, metadata)

        codes = {issue.code for issue in result.errors}
        self.assertIn("WORK_ITEM_RESOLUTION_NON_TERMINAL", codes)

    def test_blocked_requires_active_and_reason(self) -> None:
        root = self._make_project()
        path = root / "work_items" / "proposed" / "WI-0003.md"
        metadata = {
            "id": "WI-0003",
            "title": "Blocked",
            "status": "proposed",
            "blocked": True,
        }

        result = work_item_policy.validate_work_item_policy(root, path, metadata)

        codes = {issue.code for issue in result.errors}
        self.assertIn("WORK_ITEM_BLOCKED_STATUS_INVALID", codes)
        self.assertIn("WORK_ITEM_BLOCKED_REASON_REQUIRED", codes)

    def test_root_work_items_file_is_invalid_bucket(self) -> None:
        root = self._make_project()
        path = root / "work_items" / "WI-0004.md"
        metadata = {
            "id": "WI-0004",
            "title": "Flat",
            "status": "active",
        }

        result = work_item_policy.validate_work_item_policy(root, path, metadata)

        codes = {issue.code for issue in result.errors}
        self.assertIn("WORK_ITEM_BUCKET_INVALID", codes)

    def test_file_outside_work_items_is_invalid_bucket(self) -> None:
        root = self._make_project()
        path = root / "focus" / "WI-0005.md"
        metadata = {
            "id": "WI-0005",
            "title": "Misplaced",
            "status": "active",
        }

        result = work_item_policy.validate_work_item_policy(root, path, metadata)

        codes = {issue.code for issue in result.errors}
        self.assertIn("WORK_ITEM_BUCKET_INVALID", codes)

    def test_collection_handles_out_of_tree_path(self) -> None:
        root = self._make_project()
        items = [
            (
                root / "work_items" / "active" / "WI-0001.md",
                {"id": "WI-0001", "title": "A", "status": "active"},
            ),
            (
                root / "focus" / "WI-0009.md",
                {"id": "WI-0009", "title": "B", "status": "proposed"},
            ),
        ]

        result = work_item_policy.validate_work_item_collection(root, items)

        codes = {issue.code for issue in result.errors}
        self.assertIn("WORK_ITEM_BUCKET_INVALID", codes)

    def test_collection_duplicate_ids(self) -> None:
        root = self._make_project()
        items = [
            (
                root / "work_items" / "active" / "WI-0001.md",
                {"id": "WI-0001", "title": "A", "status": "active"},
            ),
            (
                root / "work_items" / "proposed" / "WI-0001.md",
                {"id": "WI-0001", "title": "B", "status": "proposed"},
            ),
        ]

        result = work_item_policy.validate_work_item_collection(root, items)

        codes = {issue.code for issue in result.errors}
        self.assertIn("WORK_ITEM_ID_DUPLICATE", codes)


if __name__ == "__main__":
    unittest.main()
