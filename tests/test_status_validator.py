from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_PATH = (
    REPO_ROOT / "fullstack-orchestrator" / "scripts" / "bootstrap_project_adapter.py"
)
VALIDATOR_PATH = (
    REPO_ROOT / "fullstack-orchestrator" / "scripts" / "validate_project_adapter.py"
)
TEMPLATE_ROOT = REPO_ROOT / "fullstack-orchestrator" / "assets" / "project-adapter"
EMPTY_STATUS = """\
# Test Orchestration Status

## Current

| ID | State | Owner | Checked | Condition | Evidence | Next action |
| --- | --- | --- | --- | --- | --- | --- |
"""


class StatusValidatorTests(unittest.TestCase):
    def _validate(
        self,
        status: str,
        *,
        strict: bool = False,
        policy: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for template in TEMPLATE_ROOT.glob("*.md.template"):
                (root / template.name.removesuffix(".template")).write_text(
                    template.read_text().replace("{project_name}", "Test")
                )
            (root / "SLICES.md").write_text("""\
# Test Slices

## Restore access

- Status: Approved

### BC-001 - Restore customer access

- Given: a customer has a verified email
- When: the customer requests account recovery
- Then: the customer receives a recovery link
- Gate: tests/test_recovery.py
""")
            (root / "STATUS.md").write_text(status)
            if policy is not None:
                (root / "DOCUMENTATION_POLICY.md").write_text(policy)
            args = [sys.executable, str(VALIDATOR_PATH), str(root)]
            if strict:
                args.append("--strict")
            result = subprocess.run(args, capture_output=True, text=True, check=False)
            self.assertEqual(status, (root / "STATUS.md").read_text())
            return result

    @staticmethod
    def _row(**changes: str) -> str:
        fields = {
            "ID": "device-sign-in",
            "State": "needs-verification",
            "Owner": "Hung",
            "Checked": "2026-01-01",
            "Condition": "Physical-device sign-in has no confirmed result.",
            "Evidence": "[Device gate](SLICES.md#sign-in)",
            "Next action": "Run the device gate and record its result.",
        }
        fields.update(changes)
        return "| " + " | ".join(fields.values()) + " |\n"

    def _status_with_words(self, words: int) -> str:
        topics = [
            {"ID": f"topic-{index}", "Condition": "condition", "Next action": "verify"}
            for index in range(10)
        ]
        remaining = words - len((EMPTY_STATUS + "".join(self._row(**topic) for topic in topics)).split())
        for topic in topics:
            for field in ("Condition", "Next action"):
                extra = min(remaining, 24)
                topic[field] += " detail" * extra
                remaining -= extra
        self.assertEqual(0, remaining)
        return EMPTY_STATUS + "".join(self._row(**topic) for topic in topics)

    def _assert_invalid(self, status: str, message: str) -> None:
        result = self._validate(status)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn(message, result.stdout)

    def test_default_cli_rejects_accumulated_history(self) -> None:
        history = "\n".join(
            f"## Deployment {index}\n\nReceipt for completed deployment.\n"
            for index in range(20)
        )
        status = (EMPTY_STATUS + "\n" + history).splitlines()
        status.extend([""] * (92 - len(status)))

        result = self._validate("\n".join(status) + "\n")

        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("STATUS.md has 92 lines; hard limit is 40", result.stdout)
        self.assertIn("reconcile", result.stdout.lower())


    def test_empty_snapshot_is_valid(self) -> None:
        result = self._validate(EMPTY_STATUS)

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("Adapter structure is valid.", result.stdout)

    def test_fresh_bootstrap_emits_a_valid_empty_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            seed = root / "seed"
            seed.mkdir()
            coordinator = root / "test-orchestration"
            bootstrap = subprocess.run(
                [sys.executable, str(BOOTSTRAP_PATH), str(seed), "--write",
                 "--coordinator", str(coordinator), "--project-name", "Test"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(0, bootstrap.returncode, bootstrap.stdout + bootstrap.stderr)
            self.assertEqual(EMPTY_STATUS, (coordinator / "STATUS.md").read_text())

            result = subprocess.run(
                [sys.executable, str(VALIDATOR_PATH), str(coordinator)],
                capture_output=True, text=True, check=False,
            )

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertIn("Adapter structure is valid.", result.stdout)

    def test_each_unresolved_state_and_linked_evidence_is_valid(self) -> None:
        for state, evidence in (
            ("pending", "[Release lock](RELEASE_LOCKS.md)"),
            ("blocked", "[Ticket](https://example.com/tickets/42)"),
            ("needs-verification", "[Gate](../api/evidence/check.md#device)"),
        ):
            with self.subTest(state=state):
                result = self._validate(
                    EMPTY_STATUS + self._row(State=state, Evidence=evidence), strict=True
                )
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_multiple_distinct_topics_and_encoded_pipes_are_valid(self) -> None:
        status = EMPTY_STATUS + self._row(
            Condition="Check the sign-in &#124; account recovery gate.",
            Evidence="[Gate](https://example.com/gates/sign-in%7Crecovery)",
        ) + self._row(ID="release-verification")

        result = self._validate(status)

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_timezone_skew_allows_a_check_one_day_ahead(self) -> None:
        status = EMPTY_STATUS + self._row(
            Checked=(date.today() + timedelta(days=1)).isoformat()
        )

        result = self._validate(status)

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_escaped_pipes_respect_backslash_parity(self) -> None:
        for condition in (r"Check sign-in \| recovery.", r"Check sign-in \\\| recovery."):
            with self.subTest(condition=condition):
                result = self._validate(EMPTY_STATUS + self._row(Condition=condition))
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self._assert_invalid(
            EMPTY_STATUS + self._row(Condition=r"Check sign-in \\| recovery."),
            "seven cells",
        )

    def test_conditions_and_next_actions_have_a_25_word_limit(self) -> None:
        for field in ("Condition", "Next action"):
            with self.subTest(field=field):
                valid = self._validate(
                    EMPTY_STATUS + self._row(**{field: " ".join(["word"] * 25)})
                )
                self.assertEqual(0, valid.returncode, valid.stdout + valid.stderr)
                self._assert_invalid(
                    EMPTY_STATUS + self._row(**{field: " ".join(["word"] * 26)}),
                    f"{field} exceeds 25 words",
                )

    def test_owner_has_a_six_word_limit(self) -> None:
        valid = self._validate(
            EMPTY_STATUS + self._row(Owner=" ".join(["name"] * 6))
        )

        self.assertEqual(0, valid.returncode, valid.stdout + valid.stderr)
        self._assert_invalid(
            EMPTY_STATUS + self._row(Owner=" ".join(["name"] * 7)),
            "Owner exceeds 6 words",
        )

    def test_evidence_has_a_15_word_limit_including_markdown(self) -> None:
        valid = self._validate(
            EMPTY_STATUS + self._row(Evidence="[" + " ".join(["gate"] * 15) + "](SLICES.md)")
        )

        self.assertEqual(0, valid.returncode, valid.stdout + valid.stderr)
        self._assert_invalid(
            EMPTY_STATUS + self._row(Evidence="[" + " ".join(["gate"] * 16) + "](SLICES.md)"),
            "Evidence exceeds 15 words",
        )

    def test_alignment_colons_are_valid(self) -> None:
        status = EMPTY_STATUS.replace(
            "| --- | --- | --- | --- | --- | --- | --- |",
            "| :--- | ---: | :---: | --- | --- | --- | --- |",
        )

        result = self._validate(status)

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_duplicate_topic_id_is_rejected(self) -> None:
        self._assert_invalid(
            EMPTY_STATUS + self._row() + self._row(), "duplicate ID: device-sign-in"
        )

    def test_malformed_topic_ids_are_rejected(self) -> None:
        for topic_id in ("Device-sign-in", "device_sign_in", "device--sign-in", "1device", "a" * 65):
            with self.subTest(topic_id=topic_id):
                self._assert_invalid(
                    EMPTY_STATUS + self._row(ID=topic_id), "invalid ID"
                )

    def test_missing_and_placeholder_fields_are_rejected(self) -> None:
        for field in ("Owner", "Checked", "Condition", "Evidence", "Next action"):
            for value in ("", "TODO", "Pending", "<name>"):
                with self.subTest(field=field, value=value):
                    self._assert_invalid(
                        EMPTY_STATUS + self._row(**{field: value}), field
                    )

    def test_unknown_and_resolved_states_are_rejected(self) -> None:
        for state in ("completed", "superseded", "abandoned", "landed", "PENDING", ""):
            with self.subTest(state=state):
                self._assert_invalid(
                    EMPTY_STATUS + self._row(State=state), "invalid State"
                )

    def test_invalid_and_future_check_dates_are_rejected(self) -> None:
        for checked in (
            "2026-02-30", "2026-1-01", "20260101", "2026-01-01T12:00:00Z",
            (date.today() + timedelta(days=2)).isoformat(),
        ):
            with self.subTest(checked=checked):
                self._assert_invalid(
                    EMPTY_STATUS + self._row(Checked=checked), "Checked"
                )

    def test_evidence_requires_a_relative_or_https_inline_link(self) -> None:
        for evidence in (
            "SLICES.md#sign-in", "[Gate]()", "[Gate](#)", "[Gate](#sign-in)",
            "[Gate](http://example.com/check)", "[Gate](javascript:alert)",
            "[Gate](file:///tmp/check.md)", "[Gate](/tmp/check.md)",
            "[Gate](https://)", "[](SLICES.md)", "[TODO](SLICES.md)", "[Gate](TODO)",
            "![Screenshot](evidence/device.png)",
        ):
            with self.subTest(evidence=evidence):
                self._assert_invalid(
                    EMPTY_STATUS + self._row(Evidence=evidence), "Evidence"
                )

    def test_evidence_accepts_multiple_links_and_separator_characters(self) -> None:
        for separator in (" ", ", ", "; ", " ,; "):
            with self.subTest(separator=separator):
                evidence = separator.join((
                    "[Gate](SLICES.md#sign-in)",
                    "[Receipt](https://example.com/check)",
                ))
                result = self._validate(EMPTY_STATUS + self._row(Evidence=evidence))
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_evidence_rejects_prose_comments_and_fences_outside_links(self) -> None:
        for evidence in (
            "[Gate](SLICES.md) deployment passed",
            "Receipt [Gate](SLICES.md)",
            "[Gate](SLICES.md) <!-- old receipt -->",
            "<!-- receipt --> [Gate](SLICES.md)",
            "[Gate](SLICES.md) ```",
        ):
            with self.subTest(evidence=evidence):
                self._assert_invalid(EMPTY_STATUS + self._row(Evidence=evidence), "Evidence")

    def test_each_evidence_link_requires_a_meaningful_label_and_allowed_target(self) -> None:
        for bad_link in (
            "[TODO](SLICES.md)", "[Gate](http://example.com/check)",
            "[Gate](TODO)", "[](SLICES.md)",
        ):
            for evidence in (
                f"[Gate](SLICES.md), {bad_link}",
                f"{bad_link}; [Gate](SLICES.md)",
            ):
                with self.subTest(evidence=evidence):
                    self._assert_invalid(EMPTY_STATUS + self._row(Evidence=evidence), "Evidence")

    def test_fixed_shape_rejects_missing_or_changed_structure(self) -> None:
        for status in (
            "", EMPTY_STATUS.replace("# Test Orchestration Status", "# Status"),
            EMPTY_STATUS.replace("# Test Orchestration Status", "# Orchestration Status"),
            EMPTY_STATUS.replace("# Test Orchestration Status", "# {project_name} Orchestration Status"),
            EMPTY_STATUS.replace("## Current", "## History"),
            EMPTY_STATUS.replace("| ID | State |", "| State | ID |"),
            EMPTY_STATUS.replace("| --- | --- | --- | --- | --- | --- | --- |", "| --- | --- |"),
        ):
            with self.subTest(status=status):
                self._assert_invalid(status, "snapshot shape")

    def test_blank_line_between_table_header_and_separator_is_rejected(self) -> None:
        status = EMPTY_STATUS.replace(
            "| Next action |\n| ---", "| Next action |\n\n| ---"
        )

        self._assert_invalid(status, "snapshot shape")

    def test_blank_lines_between_table_rows_are_rejected(self) -> None:
        for status in (
            EMPTY_STATUS + "\n" + self._row(),
            EMPTY_STATUS + self._row() + "\n" + self._row(ID="other-topic"),
        ):
            with self.subTest(status=status):
                self._assert_invalid(status, "contiguous")

    def test_indented_code_blocks_cannot_represent_the_snapshot(self) -> None:
        for prefix in ("    ", "\t"):
            with self.subTest(prefix=prefix):
                status = "\n".join(prefix + line for line in EMPTY_STATUS.splitlines()) + "\n"
                self._assert_invalid(status, "snapshot shape")
        self._assert_invalid(EMPTY_STATUS + "    " + self._row(), "table row")

    def test_free_prose_comments_and_history_outside_rows_are_rejected(self) -> None:
        for extra in (
            "Updated: 2026-01-01", "## History", "Deployment finished.",
            "<!-- Old receipts -->", "```markdown",
        ):
            with self.subTest(extra=extra):
                self._assert_invalid(EMPTY_STATUS + extra + "\n", "table row")

    def test_literal_pipe_in_a_cell_is_rejected(self) -> None:
        for changes in (
            {"Condition": "Check sign-in | recovery."},
            {"Evidence": "[Gate](https://example.com/sign-in|recovery)"},
        ):
            with self.subTest(changes=changes):
                self._assert_invalid(
                    EMPTY_STATUS + self._row(**changes), "seven cells"
                )

    def test_hard_line_limit_counts_blank_lines_and_accepts_boundary(self) -> None:
        status = EMPTY_STATUS + "\n" * (40 - len(EMPTY_STATUS.splitlines()))
        valid = self._validate(status)
        invalid = self._validate(status + "\n")

        self.assertEqual(0, valid.returncode, valid.stdout + valid.stderr)
        self.assertEqual(1, invalid.returncode, invalid.stdout + invalid.stderr)
        self.assertIn("STATUS.md has 41 lines; hard limit is 40", invalid.stdout)
        self.assertIn("remove proven resolved rows", invalid.stdout)
        self.assertNotIn("archive historical evidence", invalid.stdout)

    def test_hard_word_limit_cannot_be_evaded_with_long_lines(self) -> None:
        status = self._status_with_words(600)
        valid = self._validate(status)
        invalid = self._validate(self._status_with_words(601))

        self.assertEqual(0, valid.returncode, valid.stdout + valid.stderr)
        self.assertEqual(1, invalid.returncode, invalid.stdout + invalid.stderr)
        self.assertIn("STATUS.md has 601 words; hard limit is 600", invalid.stdout)
        self.assertIn("whitespace", invalid.stdout.lower())
        self.assertIn("Markdown", invalid.stdout)

    def test_policy_override_cannot_weaken_hard_limits(self) -> None:
        policy = "# Policy\n\n## Grooming\n\n| STATUS.md | 1000 |\n"
        for status, diagnostic in (
            (EMPTY_STATUS + "\n" * 40, "hard limit is 40"),
            (self._status_with_words(601), "hard limit is 600"),
        ):
            with self.subTest(diagnostic=diagnostic):
                result = self._validate(status, policy=policy)
                self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                self.assertIn(diagnostic, result.stdout)

    def test_smaller_policy_budget_retains_strict_behavior(self) -> None:
        policy = "# Policy\n\n## Grooming\n\n| STATUS.md | 5 |\n"
        normal = self._validate(EMPTY_STATUS, policy=policy)
        strict = self._validate(EMPTY_STATUS, strict=True, policy=policy)

        self.assertEqual(0, normal.returncode, normal.stdout + normal.stderr)
        self.assertIn("STATUS.md has 6 lines; budget is 5", normal.stdout)
        self.assertEqual(1, strict.returncode, strict.stdout + strict.stderr)
        self.assertIn("STATUS.md has 6 lines; budget is 5", strict.stdout)


if __name__ == "__main__":
    unittest.main()
