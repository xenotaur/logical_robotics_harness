import pathlib
import tempfile
import unittest

from lrh.design import organize as design_organize


class DesignProposalOrganizeTest(unittest.TestCase):
    def test_dry_run_does_not_move_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            source = _write_proposal(root, "DP-0002-example.md", "adopted")

            plan = design_organize.plan_organization(root)
            report = design_organize.build_text_report(plan)

            self.assertTrue(source.exists())
            self.assertFalse(
                (root / "project/design/proposals/adopted/DP-0002-example.md").exists()
            )
            self.assertIn("Would move:", report)
            self.assertNotIn("Moved:", report)

    def test_apply_moves_file_to_expected_bucket(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            source = _write_proposal(root, "DP-0003-example.md", "rejected")

            plan = design_organize.plan_organization(root)
            design_organize.apply_plan(plan)

            target = root / "project/design/proposals/rejected/DP-0003-example.md"
            self.assertFalse(source.exists())
            self.assertTrue(target.exists())
            self.assertIn("status: rejected", target.read_text(encoding="utf-8"))

    def test_accepted_maps_to_adopted_bucket_without_rewriting_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _write_proposal(root, "DP-0004-example.md", "accepted")

            plan = design_organize.plan_organization(root)
            design_organize.apply_plan(plan)

            target = root / "project/design/proposals/adopted/DP-0004-example.md"
            self.assertTrue(target.exists())
            self.assertIn("status: accepted", target.read_text(encoding="utf-8"))

    def test_noop_when_already_organized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _write_proposal(root, "proposed/DP-0005-example.md", "proposed")

            plan = design_organize.plan_organization(root)
            report = design_organize.build_text_report(plan)

            self.assertEqual(report, "Design proposals already organized.")

    def test_collision_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _write_proposal(root, "DP-0006-example.md", "adopted")
            _write_proposal(root, "adopted/DP-0006-example.md", "adopted")

            plan = design_organize.plan_organization(root)
            report = design_organize.build_text_report(plan)

            self.assertIn("Blocked:", report)
            self.assertIn("target collision: target file already exists", report)
            with self.assertRaises(ValueError):
                design_organize.apply_plan(plan)

    def test_invalid_proposal_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            source = _write_proposal(root, "DP-0007-example.md", "done")

            plan = design_organize.plan_organization(root)
            report = design_organize.build_text_report(plan)
            design_organize.apply_plan(plan)

            self.assertTrue(source.exists())
            self.assertIn("Skipped:", report)
            self.assertIn("unsupported status 'done'", report)

    def test_readme_index_and_non_proposal_markdown_are_not_moved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            proposals_dir = root / "project/design/proposals"
            proposals_dir.mkdir(parents=True)
            (proposals_dir / "README.md").write_text("# Readme\n", encoding="utf-8")
            (proposals_dir / "index.md").write_text("# Index\n", encoding="utf-8")
            (proposals_dir / "notes.md").write_text(
                "---\nid: NOTE-1\nstatus: adopted\n---\n",
                encoding="utf-8",
            )

            plan = design_organize.plan_organization(root)

            self.assertEqual(len(plan.inspected), 0)
            self.assertTrue((proposals_dir / "README.md").exists())
            self.assertTrue((proposals_dir / "index.md").exists())
            self.assertTrue((proposals_dir / "notes.md").exists())

    def test_output_is_deterministically_sorted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _write_proposal(root, "DP-B.md", "rejected")
            _write_proposal(root, "DP-A.md", "adopted")

            report = design_organize.build_text_report(
                design_organize.plan_organization(root)
            )

            self.assertLess(report.index("DP-A.md"), report.index("DP-B.md"))


def _write_proposal(
    root: pathlib.Path, relative_path: str, status: str
) -> pathlib.Path:
    path = root / "project/design/proposals" / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    proposal_id = pathlib.Path(relative_path).stem
    path.write_text(
        f"---\nid: {proposal_id}\ntype: design_proposal\nstatus: {status}\n---\n\n"
        f"# {proposal_id}\n",
        encoding="utf-8",
    )
    return path
