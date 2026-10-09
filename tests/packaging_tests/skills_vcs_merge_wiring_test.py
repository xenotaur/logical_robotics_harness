"""Regression coverage: the merge-gate skills route through `lrh vcs merge`."""

from __future__ import annotations

import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "src" / "lrh" / "skills"
MIRROR_ROOTS = (
    REPO_ROOT / ".claude" / "skills",
    REPO_ROOT / ".agents" / "skills",
)
SKILL_ROOTS = (SOURCE_ROOT, *MIRROR_ROOTS)
MERGE_SKILLS = ("lrh-confirm-fixes", "lrh-land")
WIRED_FILES = (
    "lrh-land/SKILL.md",
    "lrh-confirm-fixes/SKILL.md",
    "lrh-confirm-fixes/references/confirm-fixes-workflow.md",
    "lrh-review-response/references/review-response-workflow.md",
)
BARE_GH_MERGE_COMMAND = re.compile(r"gh\s+pr\s+merge\s+<")


class SkillsVcsMergeWiringTest(unittest.TestCase):
    def test_merge_skills_present_the_lrh_vcs_merge_command(self) -> None:
        for root in SKILL_ROOTS:
            for skill in MERGE_SKILLS:
                with self.subTest(root=str(root.relative_to(REPO_ROOT)), skill=skill):
                    content = (root / skill / "SKILL.md").read_text()
                    self.assertIn("lrh vcs merge <pr-url>", content)
                    self.assertIn("--match-head-commit", content)

    def test_merge_skills_no_longer_present_a_bare_gh_pr_merge_command(self) -> None:
        for root in SKILL_ROOTS:
            for skill in MERGE_SKILLS:
                with self.subTest(root=str(root.relative_to(REPO_ROOT)), skill=skill):
                    content = (root / skill / "SKILL.md").read_text()
                    self.assertIsNone(BARE_GH_MERGE_COMMAND.search(content))

    def test_lifecycle_references_name_the_new_one_liner(self) -> None:
        references = (
            "lrh-confirm-fixes/references/confirm-fixes-workflow.md",
            "lrh-review-response/references/review-response-workflow.md",
        )
        for root in SKILL_ROOTS:
            for reference in references:
                with self.subTest(root=str(root.relative_to(REPO_ROOT)), ref=reference):
                    content = (root / reference).read_text()
                    self.assertIn("lrh vcs merge one-liner", content)
                    self.assertNotIn("gh pr merge one-liner", content)

    def test_land_skill_leaves_host_level_denials_to_the_caller(self) -> None:
        content = (SOURCE_ROOT / "lrh-land" / "SKILL.md").read_text()
        self.assertIn("host-level denial", content)
        self.assertIn("do\nnot retry it in another form", content)

    def test_skills_say_exit_two_does_not_always_mean_nothing_merged(self) -> None:
        for root in SKILL_ROOTS:
            for skill in MERGE_SKILLS:
                with self.subTest(root=str(root.relative_to(REPO_ROOT)), skill=skill):
                    content = " ".join((root / skill / "SKILL.md").read_text().split())
                    self.assertIn("does not always mean nothing merged", content)

    def test_claude_mirror_is_byte_identical_for_the_wired_files(self) -> None:
        for relative in WIRED_FILES:
            with self.subTest(file=relative):
                self.assertEqual(
                    (SOURCE_ROOT / relative).read_bytes(),
                    (REPO_ROOT / ".claude" / "skills" / relative).read_bytes(),
                )


if __name__ == "__main__":
    unittest.main()
