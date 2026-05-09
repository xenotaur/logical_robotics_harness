import tempfile
import unittest
from pathlib import Path

from lrh.control.loader import load_design_proposals, load_project
from lrh.control.validator import validate_project


class TestDesignProposalControlPlane(unittest.TestCase):
    def test_load_design_proposal_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            _write_design_proposal(
                root,
                "adopted/DP-1.md",
                """---
id: DP-1
type: design_proposal
title: Proposal One
status: adopted
implementation_status: implemented
implemented_by:
  - WI-1
evidence:
  - EV-1
supersedes: []
superseded_by: null
---

# Proposal One
""",
            )
            _write_work_item(root, "WI-1")
            _write_evidence(root, "EV-1")

            proposals = load_design_proposals(root)
            state = load_project(root)

            self.assertEqual(len(proposals), 1)
            proposal = proposals[0]
            self.assertEqual(proposal.id, "DP-1")
            self.assertEqual(proposal.title, "Proposal One")
            self.assertEqual(proposal.status, "adopted")
            self.assertEqual(proposal.implementation_status, "implemented")
            self.assertEqual(proposal.implemented_by, ("WI-1",))
            self.assertEqual(proposal.evidence, ("EV-1",))
            self.assertIsNone(proposal.superseded_by)
            self.assertIn("DP-1", state.design_proposals_by_id)

    def test_valid_design_proposal_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            _write_work_item(root, "WI-1")
            _write_evidence(root, "EV-1")
            _write_design_proposal(
                root,
                "adopted/DP-VALID.md",
                _proposal_frontmatter(
                    proposal_id="DP-VALID",
                    status="adopted",
                    implementation_status="implemented",
                    implemented_by=["WI-1"],
                    evidence=["EV-1"],
                ),
            )

            report = validate_project(root / "project")

            self.assertFalse(
                [
                    issue
                    for issue in report.issues
                    if issue.code.startswith("DESIGN_PROPOSAL")
                ]
            )

    def test_legacy_accepted_status_warns_but_uses_adopted_bucket(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            _write_design_proposal(
                root,
                "adopted/PROP-ACCEPTED.md",
                _proposal_frontmatter(
                    proposal_id="PROP-ACCEPTED",
                    status="accepted",
                    implementation_status="not_started",
                ),
            )

            report = validate_project(root / "project")

            self.assertIn(
                "DESIGN_PROPOSAL_LEGACY_ACCEPTED_STATUS",
                _warning_codes(report),
            )
            self.assertNotIn(
                "DESIGN_PROPOSAL_BUCKET_STATUS_MISMATCH",
                _warning_codes(report),
            )

    def test_untyped_frontmatter_doc_under_proposals_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            _write_design_proposal(
                root,
                "proposed/DP-TYPED.md",
                _proposal_frontmatter(proposal_id="DP-TYPED"),
            )
            _write_design_proposal(
                root,
                "notes/companion.md",
                """---
id: AUX-NOTE
title: Companion notes
status: draft
---

# Companion notes
""",
            )

            report = validate_project(root / "project")

            self.assertNotIn("DESIGN_PROPOSAL_TYPE_MISSING", _error_codes(report))
            self.assertNotIn("DESIGN_PROPOSAL_STATUS_INVALID", _error_codes(report))

    def test_invalid_status_is_error(self) -> None:
        report = _validate_single_proposal(
            _proposal_frontmatter(proposal_id="DP-BAD", status="done")
        )

        self.assertIn("DESIGN_PROPOSAL_STATUS_INVALID", _error_codes(report))

    def test_invalid_implementation_status_is_error(self) -> None:
        report = _validate_single_proposal(
            _proposal_frontmatter(
                proposal_id="DP-BAD", implementation_status="finished"
            )
        )

        self.assertIn(
            "DESIGN_PROPOSAL_IMPLEMENTATION_STATUS_INVALID",
            _error_codes(report),
        )

    def test_duplicate_proposal_id_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            for name in ("proposed/DP-A.md", "proposed/DP-B.md"):
                _write_design_proposal(
                    root,
                    name,
                    _proposal_frontmatter(proposal_id="DP-DUPLICATE"),
                )

            report = validate_project(root / "project")

            self.assertIn("DUPLICATE_DESIGN_PROPOSAL_ID", _error_codes(report))

    def test_type_kind_conflict_is_error(self) -> None:
        report = _validate_single_proposal("""---
id: DP-CONFLICT
type: design_proposal
kind: investigation
status: proposed
---
""")

        self.assertIn("DESIGN_PROPOSAL_TYPE_KIND_CONFLICT", _error_codes(report))

    def test_implemented_without_traceability_warns(self) -> None:
        report = _validate_single_proposal(
            _proposal_frontmatter(
                proposal_id="DP-IMPLEMENTED",
                implementation_status="implemented",
            )
        )

        self.assertIn(
            "DESIGN_PROPOSAL_IMPLEMENTED_TRACEABILITY_MISSING",
            _warning_codes(report),
        )

    def test_superseded_without_superseded_by_warns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            _write_design_proposal(
                root,
                "superseded/DP-OLD.md",
                _proposal_frontmatter(proposal_id="DP-OLD", status="superseded"),
            )

            report = validate_project(root / "project")

            self.assertIn(
                "DESIGN_PROPOSAL_SUPERSEDED_BY_MISSING",
                _warning_codes(report),
            )

    def test_broken_references_are_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            _write_design_proposal(
                root,
                "superseded/DP-BROKEN.md",
                """---
id: DP-BROKEN
type: design_proposal
status: superseded
implementation_status: partial
implemented_by:
  - WI-MISSING
evidence:
  - EV-MISSING
supersedes:
  - DP-MISSING-OLD
superseded_by: DP-MISSING-NEW
---
""",
            )

            report = validate_project(root / "project")

            self.assertIn("UNKNOWN_DESIGN_PROPOSAL_WORK_ITEM", _error_codes(report))
            self.assertIn("UNKNOWN_DESIGN_PROPOSAL_EVIDENCE", _error_codes(report))
            self.assertIn("UNKNOWN_DESIGN_PROPOSAL_SUPERSEDES", _error_codes(report))
            self.assertIn("UNKNOWN_DESIGN_PROPOSAL_SUPERSEDED_BY", _error_codes(report))

    def test_invalid_collection_fields_are_errors(self) -> None:
        report = _validate_single_proposal("""---
id: DP-BAD-FIELDS
type: design_proposal
status: proposed
implemented_by: WI-1
evidence: EV-1
supersedes: DP-1
superseded_by:
  - DP-2
---
""")

        self.assertEqual(
            _error_codes(report).count("DESIGN_PROPOSAL_LIST_FIELD_INVALID"), 3
        )
        self.assertIn("DESIGN_PROPOSAL_SUPERSEDED_BY_INVALID", _error_codes(report))

    def test_validation_message_order_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _write_project_scaffold(Path(tmp_dir))
            _write_design_proposal(
                root,
                "proposed/DP-A.md",
                _proposal_frontmatter(proposal_id="DP-A", status="invalid-a"),
            )
            _write_design_proposal(
                root,
                "proposed/DP-B.md",
                _proposal_frontmatter(proposal_id="DP-B", status="invalid-b"),
            )

            first = validate_project(root / "project")
            second = validate_project(root / "project")

            self.assertEqual(
                [(issue.file, issue.code, issue.message) for issue in first.issues],
                [(issue.file, issue.code, issue.message) for issue in second.issues],
            )


def _validate_single_proposal(content: str):
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = _write_project_scaffold(Path(tmp_dir))
        _write_design_proposal(root, "proposed/DP-ONE.md", content)
        return validate_project(root / "project")


def _write_project_scaffold(root: Path) -> Path:
    project = root / "project"
    (project / "focus").mkdir(parents=True)
    (project / "work_items" / "active").mkdir(parents=True)
    (project / "contributors").mkdir(parents=True)
    (project / "design" / "proposals").mkdir(parents=True)
    (project / "focus" / "current_focus.md").write_text(
        "---\nid: FOCUS-1\ntitle: Focus\nstatus: active\n---\n",
        encoding="utf-8",
    )
    return root


def _write_design_proposal(root: Path, relative_path: str, content: str) -> None:
    path = root / "project" / "design" / "proposals" / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_work_item(root: Path, work_item_id: str) -> None:
    path = root / "project" / "work_items" / "active" / f"{work_item_id}.md"
    path.write_text(
        f"""---
id: {work_item_id}
title: Work Item
type: deliverable
status: active
blocked: false
blocked_reason: null
resolution: null
---
""",
        encoding="utf-8",
    )


def _write_evidence(root: Path, evidence_id: str) -> None:
    path = root / "project" / "evidence" / f"{evidence_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\nid: {evidence_id}\n---\n", encoding="utf-8")


def _proposal_frontmatter(
    proposal_id: str,
    status: str = "proposed",
    implementation_status: str | None = None,
    implemented_by: list[str] | None = None,
    evidence: list[str] | None = None,
) -> str:
    lines = [
        "---",
        f"id: {proposal_id}",
        "type: design_proposal",
        f"status: {status}",
    ]
    if implementation_status is not None:
        lines.append(f"implementation_status: {implementation_status}")
    if implemented_by is not None:
        lines.append("implemented_by:")
        lines.extend(f"  - {work_item_id}" for work_item_id in implemented_by)
    if evidence is not None:
        lines.append("evidence:")
        lines.extend(f"  - {evidence_id}" for evidence_id in evidence)
    lines.extend(["supersedes: []", "superseded_by: null", "---", ""])
    return "\n".join(lines)


def _error_codes(report) -> list[str]:
    return [issue.code for issue in report.errors]


def _warning_codes(report) -> list[str]:
    return [issue.code for issue in report.warnings]


if __name__ == "__main__":
    unittest.main()
