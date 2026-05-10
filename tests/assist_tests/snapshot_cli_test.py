import tempfile
import unittest
from pathlib import Path
from unittest import mock

from lrh.assist import snapshot_cli


class TestSnapshotCliWorkItemDiscovery(unittest.TestCase):
    def test_list_work_items_excludes_non_work_item_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir) / "project"
            (project_dir / "work_items" / "active").mkdir(parents=True)
            (project_dir / "work_items").mkdir(parents=True, exist_ok=True)
            (project_dir / "work_items" / "README.md").write_text(
                "# Work Items\n",
                encoding="utf-8",
            )
            target = project_dir / "work_items" / "active" / "WI-0001.md"
            target.write_text(
                (
                    "---\n"
                    "id: WI-0001\n"
                    "title: Example\n"
                    "type: deliverable\n"
                    "status: active\n"
                    "---\n"
                ),
                encoding="utf-8",
            )

            result = snapshot_cli.list_work_items(project_dir)

            self.assertEqual(result, [target])


class TestSnapshotCliHarnessMetadata(unittest.TestCase):
    def test_resolve_harness_version_returns_unknown_when_unavailable(self) -> None:
        with mock.patch(
            "lrh.version.get_installed_version",
            return_value=None,
        ):
            self.assertEqual(snapshot_cli.resolve_harness_version(), "unknown")

    def test_generate_project_context_includes_harness_metadata_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir) / "project"
            (project_dir / "principles").mkdir(parents=True)
            (project_dir / "goal").mkdir(parents=True)
            (project_dir / "design").mkdir(parents=True)
            (project_dir / "roadmap").mkdir(parents=True)
            (project_dir / "focus").mkdir(parents=True)
            (project_dir / "contributors").mkdir(parents=True)
            (project_dir / "work_items" / "active").mkdir(parents=True)

            (project_dir / "goal" / "project_goal.md").write_text(
                "# Goal\n",
                encoding="utf-8",
            )
            (project_dir / "design" / "design.md").write_text(
                "# Design\n",
                encoding="utf-8",
            )
            (project_dir / "roadmap" / "roadmap.md").write_text(
                "# Roadmap\n",
                encoding="utf-8",
            )
            (project_dir / "focus" / "current_focus.md").write_text(
                "---\nid: FOCUS-1\n---\n# Focus\n",
                encoding="utf-8",
            )
            (project_dir / "contributors" / "contributors.md").write_text(
                "# Contributors\n",
                encoding="utf-8",
            )

            args = snapshot_cli.build_parser(prog="snapshot").parse_args(["project"])
            with mock.patch(
                "lrh.version.get_installed_version",
                return_value="1.2.3",
            ):
                output = snapshot_cli.generate_project_context(project_dir, args)

            self.assertIn("Harness metadata:", output)
            self.assertIn("```yaml", output)
            self.assertIn("harness:", output)
            self.assertIn("name: lrh", output)
            self.assertIn("version: 1.2.3", output)


class TestSnapshotCliDesignProposals(unittest.TestCase):
    def test_project_context_includes_no_design_proposals_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = _write_snapshot_project_scaffold(Path(tmp_dir))
            args = snapshot_cli.build_parser(prog="snapshot").parse_args(["project"])

            output = snapshot_cli.generate_project_context(project_dir, args)

            self.assertIn("## Design Proposals", output)
            self.assertIn("- No design proposals found.", output)
            self.assertIn("## Current Focus", output)

    def test_project_context_groups_design_proposals_with_traceability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = _write_snapshot_project_scaffold(Path(tmp_dir))
            _write_design_proposal(
                project_dir,
                "adopted/z-not-started.md",
                proposal_id="PROP-0003",
                title="Not Started Design",
                status="adopted",
                implementation_status="not_started",
            )
            _write_design_proposal(
                project_dir,
                "adopted/b-partial.md",
                proposal_id="PROP-0002",
                title="Partial Design",
                status="adopted",
                implementation_status="partial",
                implemented_by=["WI-0002"],
                evidence=["EV-0002"],
            )
            _write_design_proposal(
                project_dir,
                "adopted/c-implemented.md",
                proposal_id="PROP-0001",
                title="Implemented Design",
                status="adopted",
                implementation_status="implemented",
                implemented_by=["WI-0001"],
                evidence=["EV-0001"],
            )
            _write_design_proposal(
                project_dir,
                "superseded/d-old.md",
                proposal_id="PROP-0005",
                title="Old Design",
                status="superseded",
                superseded_by="PROP-0006",
            )
            _write_design_proposal(
                project_dir,
                "adopted/a-accepted.md",
                proposal_id="PROP-0004",
                title="Legacy Accepted Design",
                status="accepted",
                implementation_status="deferred",
            )
            _write_design_proposal(
                project_dir,
                "adopted/e-unspecified.md",
                proposal_id="PROP-0007",
                title="Unspecified Design",
                status="adopted",
            )

            output = snapshot_cli.summarize_design_proposals(project_dir)

            self.assertIn("- Adopted / implemented:", output)
            self.assertIn("  - PROP-0001 Implemented Design", output)
            self.assertIn("    - implemented_by: WI-0001", output)
            self.assertIn("    - evidence: EV-0001", output)
            self.assertIn("- Adopted / partial:", output)
            self.assertIn("  - PROP-0002 Partial Design", output)
            self.assertIn("    - implemented_by: WI-0002", output)
            self.assertIn("    - evidence: EV-0002", output)
            self.assertIn("- Adopted / not_started:", output)
            self.assertIn("  - PROP-0003 Not Started Design", output)
            self.assertIn("- Adopted / deferred:", output)
            self.assertIn("  - PROP-0004 Legacy Accepted Design", output)
            self.assertIn("- Adopted / unspecified:", output)
            self.assertIn("  - PROP-0007 Unspecified Design", output)
            self.assertIn("- Superseded:", output)
            self.assertIn("  - PROP-0005 Old Design -> PROP-0006", output)

    def test_design_proposal_order_is_deterministic_by_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = _write_snapshot_project_scaffold(Path(tmp_dir))
            _write_design_proposal(
                project_dir,
                "adopted/z.md",
                proposal_id="PROP-0002",
                title="Second",
                status="adopted",
                implementation_status="implemented",
            )
            _write_design_proposal(
                project_dir,
                "adopted/a.md",
                proposal_id="PROP-0001",
                title="First",
                status="adopted",
                implementation_status="implemented",
            )

            output = snapshot_cli.summarize_design_proposals(project_dir)

            self.assertLess(
                output.index("PROP-0001 First"), output.index("PROP-0002 Second")
            )
            self.assertIn(
                "PROP-0001 claims implementation_status=implemented "
                "but has no evidence or implemented_by references.",
                output,
            )

    def test_malformed_design_proposal_notes_do_not_break_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = _write_snapshot_project_scaffold(Path(tmp_dir))
            _write_design_proposal(
                project_dir,
                "adopted/valid.md",
                proposal_id="PROP-0001",
                title="Valid Design",
                status="adopted",
                implementation_status="not_started",
            )
            notes_path = project_dir / "design" / "proposals" / "notes.md"
            notes_path.write_text("# Plain notes, not a proposal\n", encoding="utf-8")

            output = snapshot_cli.summarize_design_proposals(project_dir)

            self.assertIn("- Adopted / not_started:", output)
            self.assertIn("  - PROP-0001 Valid Design", output)
            self.assertIn("- Warnings:", output)
            self.assertIn("Skipped notes.md", output)


def _write_snapshot_project_scaffold(root: Path) -> Path:
    project_dir = root / "project"
    for relative_path in (
        "principles",
        "goal",
        "design/proposals",
        "roadmap",
        "focus",
        "work_items/active",
        "contributors",
    ):
        (project_dir / relative_path).mkdir(parents=True, exist_ok=True)
    (project_dir / "goal" / "project_goal.md").write_text("# Goal\n", encoding="utf-8")
    (project_dir / "design" / "design.md").write_text("# Design\n", encoding="utf-8")
    (project_dir / "roadmap" / "roadmap.md").write_text("# Roadmap\n", encoding="utf-8")
    (project_dir / "focus" / "current_focus.md").write_text(
        "---\nid: FOCUS-1\ntitle: Focus\nstatus: active\n---\n# Focus\n",
        encoding="utf-8",
    )
    (project_dir / "contributors" / "contributors.md").write_text(
        "# Contributors\n",
        encoding="utf-8",
    )
    return project_dir


def _write_design_proposal(
    project_dir: Path,
    relative_path: str,
    *,
    proposal_id: str,
    title: str,
    status: str,
    implementation_status: str | None = None,
    implemented_by: list[str] | None = None,
    evidence: list[str] | None = None,
    superseded_by: str | None = None,
) -> None:
    lines = [
        "---",
        f"id: {proposal_id}",
        "type: design_proposal",
        f"title: {title}",
        f"status: {status}",
    ]
    if implementation_status is not None:
        lines.append(f"implementation_status: {implementation_status}")
    if implemented_by:
        lines.append("implemented_by:")
        lines.extend(f"  - {work_item_id}" for work_item_id in implemented_by)
    if evidence:
        lines.append("evidence:")
        lines.extend(f"  - {evidence_id}" for evidence_id in evidence)
    if superseded_by is not None:
        lines.append(f"superseded_by: {superseded_by}")
    lines.extend(["---", "", f"# {title}", ""])
    path = project_dir / "design" / "proposals" / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
