import pathlib
import tempfile
import unittest

from local_agent import tasks


class TasksTest(unittest.TestCase):
    def test_preregistered_corpus_loads(self) -> None:
        loaded = tasks.load_tasks()
        self.assertEqual(len(loaded), 12)
        splits = [task.split for task in loaded.values()]
        self.assertEqual(splits.count("tuning"), 8)
        self.assertEqual(splits.count("held_out"), 4)
        self.assertTrue(all(len(task.commit) == 40 for task in loaded.values()))
        self.assertEqual(loaded["T11"].work_item, "WI-EVENT-0079")
        self.assertEqual(loaded["T11"].project_dir, "lcats")
        self.assertEqual(loaded["T01"].project_dir, ".")

    def test_unknown_task(self) -> None:
        with self.assertRaisesRegex(tasks.TaskError, "unknown task T99"):
            tasks.resolve_task("T99")

    def test_missing_fields_and_file_are_task_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "tasks.yaml"
            with self.assertRaisesRegex(tasks.TaskError, "cannot read"):
                tasks.load_tasks(path)
            path.write_text(
                "repos:\n  LRH:\n    project_dir: '.'\n"
                "tasks:\n  - repo: LRH\n    commit: x\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(tasks.TaskError, "missing"):
                tasks.load_tasks(path)

    def test_malformed_containers_are_task_errors(self) -> None:
        documents = {
            "non-mapping task": "repos:\n  LRH:\n    project_dir: '.'\ntasks: [7]\n",
            "null task": "repos:\n  LRH:\n    project_dir: '.'\ntasks:\n  - null\n",
            "string task": "repos:\n  LRH:\n    project_dir: '.'\ntasks:\n  - T01\n",
            "tasks not a list": "repos:\n  LRH:\n    project_dir: '.'\ntasks: 5\n",
            "repo not a mapping": "repos:\n  LRH: lrh\ntasks: []\n",
            "repos not a mapping": "repos: [LRH]\ntasks: []\n",
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "tasks.yaml"
            for label, text in documents.items():
                path.write_text(text, encoding="utf-8")
                with self.subTest(label):
                    with self.assertRaises(tasks.TaskError):
                        tasks.load_tasks(path)

    def test_short_commit_pin_rejected(self) -> None:
        text = (
            "repos:\n  LRH:\n    project_dir: '.'\n"
            "tasks:\n  - id: T01\n    split: tuning\n    repo: LRH\n"
            "    commit: 9919582b\n    work_item: WI-X\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "tasks.yaml"
            path.write_text(text, encoding="utf-8")
            with self.assertRaisesRegex(tasks.TaskError, "full 40-char"):
                tasks.load_tasks(path)


if __name__ == "__main__":
    unittest.main()
