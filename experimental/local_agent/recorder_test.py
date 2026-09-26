import pathlib
import stat
import tempfile
import unittest

from local_agent import recorder, testing_support


class StoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = pathlib.Path(self._tmp.name)
        self.store = recorder.Store(
            self.base / "store", clock=testing_support.SteppingClock()
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_refuses_root_inside_git_worktree(self) -> None:
        repo = self.base / "repo"
        repo.mkdir()
        testing_support.make_repo(repo)
        with self.assertRaisesRegex(recorder.StoreError, "inside Git worktree"):
            recorder.Store(repo / "logs")

    def test_private_permissions(self) -> None:
        run_id = self.store.start_run({"outcome": None})
        self.store.append_event(run_id, "attempt_started")
        run_dir = self.store.run_dir(run_id)
        for directory in (self.store.root, run_dir.parent, run_dir):
            self.assertEqual(stat.S_IMODE(directory.stat().st_mode), 0o700)
        for name in ("run.json", "events.jsonl"):
            self.assertEqual(stat.S_IMODE((run_dir / name).stat().st_mode), 0o600)

    def test_default_root_honours_env_override(self) -> None:
        root = recorder.default_store_root({"LRH_LOCAL_AGENT_STORE": "/x/y"})
        self.assertEqual(root, pathlib.Path("/x/y"))

    def test_truncated_tail_detected_and_recovered_as_incomplete(self) -> None:
        run_id = self.store.start_run({"outcome": None})
        self.store.append_event(run_id, "attempt_started")
        events_path = self.store.run_dir(run_id) / "events.jsonl"
        with events_path.open("a", encoding="utf-8") as handle:
            handle.write('{"seq": 2, "type": "model_req')
        events, truncated = self.store.events(run_id)
        self.assertEqual(len(events), 1)
        self.assertTrue(truncated)
        with self.assertRaises(recorder.StoreError):
            self.store.append_event(run_id, "outcome")

        manifest = self.store.recover_run(run_id)
        self.assertEqual(manifest["outcome"], "incomplete")
        self.assertTrue(manifest["recovered_truncated_tail"])
        tail = (self.store.run_dir(run_id) / "events.truncated_tail").read_text()
        self.assertIn("model_req", tail)
        events, truncated = self.store.events(run_id)
        self.assertFalse(truncated)
        self.assertEqual(events[-1]["type"], "recovered")

    def test_recover_leaves_completed_run_unchanged(self) -> None:
        run_id = self.store.start_run({"outcome": None})
        self.store.update_run(run_id, outcome="completed")
        self.assertEqual(self.store.recover_run(run_id)["outcome"], "completed")

    def test_corrupt_middle_line_is_an_error(self) -> None:
        run_id = self.store.start_run({"outcome": None})
        path = self.store.run_dir(run_id) / "events.jsonl"
        path.write_text('{"seq": 1}\nnot json\n{"seq": 3}\n', encoding="utf-8")
        with self.assertRaises(recorder.StoreError):
            self.store.events(run_id)

    def test_invalid_packet_sha_rejected(self) -> None:
        for bad in ("../../etc", "F" * 64, "abc"):
            with self.assertRaises(recorder.StoreError):
                self.store.packet_dir(bad)

    def test_invalid_run_id_rejected(self) -> None:
        with self.assertRaises(recorder.StoreError):
            self.store.run_dir("../escape")


if __name__ == "__main__":
    unittest.main()
