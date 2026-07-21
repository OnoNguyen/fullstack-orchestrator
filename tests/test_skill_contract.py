from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = REPO_ROOT / "fullstack-orchestrator" / "SKILL.md"
AGENTS_TEMPLATE_PATH = (
    REPO_ROOT
    / "fullstack-orchestrator"
    / "assets"
    / "project-adapter"
    / "AGENTS.md.template"
)
GROOMING_PATH = (
    REPO_ROOT / "fullstack-orchestrator" / "references" / "grooming.md"
)
LANDING_PATH = (
    REPO_ROOT
    / "fullstack-orchestrator"
    / "references"
    / "worktrees-and-landing.md"
)


class SkillContractTests(unittest.TestCase):
    def test_core_role_is_compose_conduct_verify(self) -> None:
        skill = SKILL_PATH.read_text()
        core_role = re.search(
            r"(?ms)^## Core Role\s*$\n(?P<body>.*?)(?=^## |\Z)", skill
        )

        self.assertIsNotNone(core_role, "SKILL.md must define a Core Role section")
        self.assertIn("Compose, Conduct, Verify", core_role.group("body"))

    def test_feature_bug_and_cross_context_work_route_to_slices(self) -> None:
        agents_template = AGENTS_TEMPLATE_PATH.read_text()
        slices_rows = "\n".join(
            line
            for line in agents_template.splitlines()
            if line.strip().startswith("|") and "`SLICES.md`" in line
        ).lower()

        self.assertIn("feature", slices_rows)
        self.assertIn("bug", slices_rows)
        self.assertRegex(slices_rows, r"cross[- ]context")

    def test_completion_requires_evidence_against_each_behavior_gate(self) -> None:
        skill = SKILL_PATH.read_text()
        paragraphs = re.split(r"\n\s*\n", skill)

        self.assertTrue(
            any(
                "completion" in paragraph.lower()
                and "evidence" in paragraph.lower()
                and "gate" in paragraph.lower()
                and ("each" in paragraph.lower() or "every" in paragraph.lower())
                for paragraph in paragraphs
            ),
            "SKILL.md must require completion evidence against each behavior gate",
        )

    def test_grooming_preserves_behavior_contract_ids_and_gate_evidence(self) -> None:
        grooming = GROOMING_PATH.read_text()
        paragraphs = re.split(r"\n\s*\n", grooming)

        preserves_ids = any(
            "preserv" in paragraph.lower()
            and re.search(
                r"(?:BC|behavior[- ]contract|scenario)[- ]IDs?",
                paragraph,
                re.IGNORECASE,
            )
            for paragraph in paragraphs
        )
        preserves_evidence = any(
            "preserv" in paragraph.lower()
            and "gate" in paragraph.lower()
            and "evidence" in paragraph.lower()
            for paragraph in paragraphs
        )
        self.assertTrue(
            preserves_ids,
            "grooming.md must preserve stable behavior-contract/scenario IDs",
        )
        self.assertTrue(
            preserves_evidence,
            "grooming.md must preserve behavior-gate evidence",
        )

    def test_landing_closes_the_behavior_contract_ledger(self) -> None:
        landing = LANDING_PATH.read_text().lower()

        self.assertIn("status: landed", landing)
        self.assertIn("landed at", landing)
        self.assertIn("evidence", landing)
        self.assertIn("--strict --slice", landing)


if __name__ == "__main__":
    unittest.main()
