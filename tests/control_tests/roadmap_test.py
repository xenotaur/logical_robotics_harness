import tempfile
import unittest
from pathlib import Path

from lrh.control import roadmap


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _phase(phase_id: str, order: str, *, parent: str = "ROADMAP-CORE") -> str:
    return (
        f"---\nid: {phase_id}\ntitle: {phase_id} title\nstatus: proposed\n"
        f"parent: {parent}\norder: {order}\n---\n\n# {phase_id}\n"
    )


ROOT = """---
id: ROADMAP-CORE
title: Roadmap
status: active
owner: human_agent
---

# Roadmap
"""


class TestLoadRoadmap(unittest.TestCase):
    def test_root_coexists_with_phases_without_a_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir)
            _write(project_dir / "roadmap" / "roadmap.md", ROOT)
            _write(project_dir / "roadmap" / "phase_02.md", _phase("PHASE-02", "2"))
            _write(project_dir / "roadmap" / "phase_01.md", _phase("PHASE-01", "1"))

            loaded = roadmap.load_roadmap(project_dir)

        self.assertEqual(loaded.diagnostics, ())
        self.assertIsNotNone(loaded.root)
        assert loaded.root is not None
        self.assertEqual(loaded.root.id, "ROADMAP-CORE")
        self.assertEqual(
            [phase.id for phase in loaded.phases], ["PHASE-01", "PHASE-02"]
        )
        self.assertNotIn("ROADMAP-CORE", [phase.id for phase in loaded.phases])

    def test_phases_sort_by_numeric_order_including_fractions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir)
            _write(project_dir / "roadmap" / "a.md", _phase("PHASE-02", "2"))
            _write(project_dir / "roadmap" / "b.md", _phase("PHASE-01A", "1.5"))
            _write(project_dir / "roadmap" / "c.md", _phase("PHASE-01", "1"))
            _write(project_dir / "roadmap" / "d.md", _phase("PHASE-10", "10"))

            loaded = roadmap.load_roadmap(project_dir)

        self.assertEqual(
            [(phase.id, phase.order) for phase in loaded.phases],
            [
                ("PHASE-01", 1.0),
                ("PHASE-01A", 1.5),
                ("PHASE-02", 2.0),
                ("PHASE-10", 10.0),
            ],
        )
        self.assertEqual(loaded.phase("PHASE-01A").title, "PHASE-01A title")
        self.assertIsNone(loaded.phase("PHASE-99"))

    def test_malformed_phase_files_become_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir)
            directory = project_dir / "roadmap"
            _write(directory / "roadmap.md", ROOT)
            _write(directory / "good.md", _phase("PHASE-01", "1"))
            _write(directory / "no_order.md", _phase("PHASE-X", "soon"))
            _write(directory / "bool_order.md", _phase("PHASE-Y", "true"))
            _write(directory / "no_frontmatter.md", "# Just a heading\n")
            _write(directory / "no_id.md", "---\ntitle: Nameless\n---\n")
            _write(directory / "second_root.md", ROOT.replace("CORE", "OTHER"))

            loaded = roadmap.load_roadmap(project_dir)

        self.assertEqual([phase.id for phase in loaded.phases], ["PHASE-01"])
        codes = sorted(
            (diagnostic.path.name, diagnostic.code) for diagnostic in loaded.diagnostics
        )
        self.assertEqual(
            codes,
            [
                ("bool_order.md", "ROADMAP_PHASE_ORDER"),
                ("no_frontmatter.md", "ROADMAP_UNREADABLE"),
                ("no_id.md", "ROADMAP_MISSING_ID"),
                ("no_order.md", "ROADMAP_PHASE_ORDER"),
                ("second_root.md", "ROADMAP_EXTRA_ROOT"),
            ],
        )

    def test_missing_directory_is_a_diagnostic_not_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            loaded = roadmap.load_roadmap(Path(tmp_dir))

        self.assertIsNone(loaded.root)
        self.assertEqual(loaded.phases, ())
        self.assertEqual(
            [diagnostic.code for diagnostic in loaded.diagnostics],
            ["ROADMAP_DIR_MISSING"],
        )

    def test_this_repository_roadmap_loads_cleanly(self) -> None:
        project_dir = Path(__file__).resolve().parents[2] / "project"

        loaded = roadmap.load_roadmap(project_dir)

        self.assertEqual(loaded.diagnostics, ())
        self.assertIsNotNone(loaded.root)
        self.assertIn("ROADMAP-PHASE-01A", [phase.id for phase in loaded.phases])


if __name__ == "__main__":
    unittest.main()
