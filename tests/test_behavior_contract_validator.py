from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = (
    REPO_ROOT / "fullstack-orchestrator" / "scripts" / "validate_project_adapter.py"
)
VALIDATOR_SPEC = importlib.util.spec_from_file_location(
    "validate_project_adapter", VALIDATOR_PATH
)
if VALIDATOR_SPEC is None or VALIDATOR_SPEC.loader is None:
    raise RuntimeError(f"Unable to load validator from {VALIDATOR_PATH}")
VALIDATOR = importlib.util.module_from_spec(VALIDATOR_SPEC)
VALIDATOR_SPEC.loader.exec_module(VALIDATOR)


class BehaviorContractValidatorTests(unittest.TestCase):
    def _validate(
        self,
        slices: str,
        *,
        strict: bool = False,
        slice_name: str | None = None,
    ) -> tuple[list[str], list[str]]:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            documents = {
                "AGENTS.md": """\
# Test Orchestration Agent Rules

## Trigger Router

| Trigger | Read |
| --- | --- |
| repo map | `ORCHESTRATION.md` |
| tasks | `TASKS.md` |
| worktrees | `WORKTREES.md` |
| terms | `GLOSSARY.md` |
| behavior | `SLICES.md` |
| documentation | `DOCUMENTATION_POLICY.md` |
| status | `STATUS.md` |

## Default Discipline

- Verify live state.
""",
                "ORCHESTRATION.md": """\
# Test Orchestration

## Repositories

| Alias | Role | Local path | Remote | Default branch |
| --- | --- | --- | --- | --- |
| app | application | /tmp/app | local | main |
""",
                "TASKS.md": """\
# Tasks

## Purpose

Test policy.

## Board Rules

Only actionable work.

## Status Labels

Ready.
""",
                "WORKTREES.md": """\
# Worktrees

## Canonical Pickup Points

Use main.

## Cross-Repo Landing

Use all-or-hold.
""",
                "GLOSSARY.md": """\
# Glossary

## Customer

The person using the product.
""",
                "SLICES.md": slices,
                "DOCUMENTATION_POLICY.md": """\
# Documentation Policy

## Grooming

Keep canonical documents concise.
""",
                "STATUS.md": "# Status\n",
            }
            for name, content in documents.items():
                (root / name).write_text(content)
            return VALIDATOR.validate(root, strict, slice_name)

    @staticmethod
    def _behavior_contracts(
        count: int,
        *,
        ids: list[str] | None = None,
        blank_clause: str | None = None,
        missing_clause: str | None = None,
    ) -> str:
        contract_ids = ids or [f"BC-{index:03d}" for index in range(1, count + 1)]
        lines = [
            "# Test Slices",
            "",
            "## Recover Account Access",
            "",
            "- Status: Approved",
            "- Intent: Let a customer recover access safely.",
            "- Implementation surfaces: web, API, email",
            "- Depends on: customer identity",
            "- Domain terms: Customer",
            "- Behavior contracts:",
        ]
        values = {
            "Given": "a customer has a verified email address",
            "When": "the customer requests an account recovery link",
            "Then": "the customer receives a single-use recovery link",
            "Gate": "automated account-recovery contract test",
        }
        for index, contract_id in enumerate(contract_ids, start=1):
            lines.extend(["", f"### {contract_id} — Recovery outcome {index}", ""])
            for clause, value in values.items():
                if missing_clause == clause:
                    continue
                rendered_value = "" if blank_clause == clause else value
                lines.append(f"- {clause}: {rendered_value}")
        lines.extend(
            [
                "",
                "- Data/privacy/security boundary: Recovery tokens are secret.",
                "- Verification: Run the mapped contract tests.",
                "- Merge status/order: API, email, web.",
            ]
        )
        return "\n".join(lines)

    def test_default_validation_warns_when_no_approved_behavior_contract_exists(self) -> None:
        slices = """\
# Test Slices

## Slices To Confirm

- None yet.
"""

        errors, warnings = self._validate(slices)

        self.assertEqual([], errors)
        self.assertTrue(
            any(
                "approved" in warning.lower()
                and "behavior contract" in warning.lower()
                for warning in warnings
            ),
            warnings,
        )

    def test_strict_validation_errors_when_no_approved_behavior_contract_exists(self) -> None:
        slices = """\
# Test Slices

## Slices To Confirm

- None yet.
"""

        errors, _warnings = self._validate(slices, strict=True)

        self.assertTrue(
            any(
                "approved" in error.lower() and "behavior contract" in error.lower()
                for error in errors
            ),
            errors,
        )

    def test_one_to_three_complete_behavior_contracts_pass(self) -> None:
        for count in (1, 2, 3):
            with self.subTest(count=count):
                errors, warnings = self._validate(self._behavior_contracts(count))

                self.assertEqual([], errors)
                self.assertFalse(
                    any("behavior contract" in warning.lower() for warning in warnings),
                    warnings,
                )

    def test_approved_contract_allows_pending_evidence(self) -> None:
        slices = self._behavior_contracts(1).replace(
            "- Gate: automated account-recovery contract test",
            "- Gate: automated account-recovery contract test\n- Evidence: Pending",
        )

        errors, _warnings = self._validate(slices)

        self.assertEqual([], errors)

    def test_blank_behavior_contract_clause_fails(self) -> None:
        for clause in ("Given", "When", "Then", "Gate"):
            with self.subTest(clause=clause):
                errors, _warnings = self._validate(
                    self._behavior_contracts(1, blank_clause=clause)
                )

                self.assertTrue(
                    any("BC-001" in error and clause.lower() in error.lower() for error in errors),
                    errors,
                )

    def test_missing_behavior_contract_clause_fails(self) -> None:
        for clause in ("Given", "When", "Then", "Gate"):
            with self.subTest(clause=clause):
                errors, _warnings = self._validate(
                    self._behavior_contracts(1, missing_clause=clause)
                )

                self.assertTrue(
                    any("BC-001" in error and clause.lower() in error.lower() for error in errors),
                    errors,
                )

    def test_more_than_three_behavior_contracts_per_slice_fails(self) -> None:
        errors, _warnings = self._validate(self._behavior_contracts(4))

        self.assertTrue(
            any("behavior contract" in error.lower() and "3" in error for error in errors),
            errors,
        )

    def test_duplicate_behavior_contract_ids_fail(self) -> None:
        errors, _warnings = self._validate(
            self._behavior_contracts(2, ids=["BC-001", "BC-001"])
        )

        self.assertTrue(
            any("duplicate" in error.lower() and "BC-001" in error for error in errors),
            errors,
        )

    def test_proposed_contract_does_not_authorize_behavior_work(self) -> None:
        slices = self._behavior_contracts(1).replace(
            "- Status: Approved", "- Status: Proposed"
        )

        errors, warnings = self._validate(slices)

        self.assertEqual([], errors)
        self.assertTrue(
            any("approved" in warning.lower() for warning in warnings), warnings
        )

    def test_targeted_readiness_rejects_proposed_slice_when_another_is_landed(self) -> None:
        slices = """\
# Test Slices

## Existing Recovery

- Status: Landed
- Landed at: api@abc1234

### BC-001 — Existing recovery works

- Then: the customer can recover access
- Gate: tests/account_recovery.py::test_recovery_link
- Evidence: test: api@abc1234 tests/account_recovery.py::test_recovery_link | passed

## New Recovery UI

- Status: Proposed

### BC-002 — New recovery UI

- Given: <initial state>
- When: <action>
- Then: <outcome>
- Gate: <gate>
- Evidence: Pending
"""

        errors, _warnings = self._validate(
            slices, strict=True, slice_name="New Recovery UI"
        )

        self.assertTrue(
            any(
                "New Recovery UI" in error
                and "approved" in error.lower()
                and "behavior contract" in error.lower()
                for error in errors
            ),
            errors,
        )

    def test_targeted_slice_matches_heading_with_closing_atx_markers(self) -> None:
        slices = self._behavior_contracts(1).replace(
            "## Recover Account Access", "## Recover Account Access ##"
        )

        errors, _warnings = self._validate(
            slices, strict=True, slice_name="Recover Account Access"
        )

        self.assertEqual([], errors)

    def test_compact_landed_contract_retains_outcome_and_gate(self) -> None:
        slices = """\
# Test Slices

## Recover Account Access

- Status: Landed
- Intent: Let a customer recover access safely.
- Implementation surfaces: web, API, email
- Landed at: api@abc1234, web@def5678

### BC-001 — Recovery succeeds

- Then: the customer receives a single-use recovery link
- Gate: tests/account_recovery.py::test_recovery_link
- Evidence: test: api@abc1234 tests/account_recovery.py::test_recovery_link | passed
"""

        errors, warnings = self._validate(slices)

        self.assertEqual([], errors)
        self.assertFalse(
            any("behavior contract" in warning.lower() for warning in warnings),
            warnings,
        )

    def test_landed_contract_requires_landing_references(self) -> None:
        slices = """\
# Test Slices

## Recover Account Access

- Status: Landed

### BC-001 — Recovery succeeds

- Then: the customer receives a single-use recovery link
- Gate: tests/account_recovery.py::test_recovery_link
"""

        errors, _warnings = self._validate(slices)

        self.assertTrue(
            any("landed at" in error.lower() for error in errors), errors
        )

    def test_landed_contract_requires_gate_evidence(self) -> None:
        slices = """\
# Test Slices

## Recover Account Access

- Status: Landed
- Landed at: api@abc1234

### BC-001 — Recovery succeeds

- Then: the customer receives a single-use recovery link
- Gate: tests/account_recovery.py::test_recovery_link
"""

        errors, _warnings = self._validate(slices)

        self.assertTrue(
            any("BC-001" in error and "evidence" in error.lower() for error in errors),
            errors,
        )

    def test_landed_contract_rejects_nondurable_references(self) -> None:
        slices = """\
# Test Slices

## Recover Account Access

- Status: Landed
- Landed at: trust me

### BC-001 — Recovery succeeds

- Then: the customer receives a single-use recovery link
- Gate: tests/account_recovery.py::test_recovery_link
- Evidence: trust me
"""

        errors, _warnings = self._validate(slices)

        self.assertTrue(
            any("landed at" in error.lower() for error in errors), errors
        )
        self.assertTrue(
            any("BC-001" in error and "evidence" in error.lower() for error in errors),
            errors,
        )

    def test_fenced_contract_does_not_satisfy_approved_slice(self) -> None:
        slices = """\
# Test Slices

## Recover Account Access

- Status: Approved

```markdown
### BC-001 — Example only
- Given: a customer exists
- When: recovery is requested
- Then: a link is sent
- Gate: tests/account_recovery.py::test_recovery_link
```
"""

        errors, _warnings = self._validate(
            slices, strict=True, slice_name="Recover Account Access"
        )

        self.assertTrue(
            any("1-3 behavior contracts" in error for error in errors), errors
        )

    def test_fence_text_with_suffix_does_not_close_fenced_example(self) -> None:
        slices = """\
# Test Slices

## Recover Account Access

- Status: Approved

```markdown
```not-a-closing-fence
### BC-001 — Example only
- Given: a customer exists
- When: recovery is requested
- Then: a link is sent
- Gate: tests/account_recovery.py::test_recovery_link
```
"""

        errors, _warnings = self._validate(
            slices, strict=True, slice_name="Recover Account Access"
        )

        self.assertTrue(
            any("1-3 behavior contracts" in error for error in errors), errors
        )

    def test_commented_contract_does_not_satisfy_approved_slice(self) -> None:
        slices = """\
# Test Slices

## Recover Account Access

- Status: Approved

<!--
### BC-001 — Disabled example
- Given: a customer exists
- When: recovery is requested
- Then: a link is sent
- Gate: tests/account_recovery.py::test_recovery_link
-->
"""

        errors, _warnings = self._validate(
            slices, strict=True, slice_name="Recover Account Access"
        )

        self.assertTrue(
            any("1-3 behavior contracts" in error for error in errors), errors
        )

    def test_contract_after_multiline_comment_closer_is_not_rendered(self) -> None:
        slices = """\
# Test Slices

## Recover Account Access

- Status: Approved

<!-- Disabled example
-->### BC-001 — Still inside the HTML block
- Given: a customer exists
- When: recovery is requested
- Then: a link is sent
- Gate: tests/account_recovery.py::test_recovery_link
"""

        errors, _warnings = self._validate(
            slices, strict=True, slice_name="Recover Account Access"
        )

        self.assertTrue(
            any("1-3 behavior contracts" in error for error in errors), errors
        )

    def test_fence_marker_inside_comment_does_not_hide_real_contract(self) -> None:
        slices = """\
# Test Slices

## Recover Account Access

- Status: Approved

<!--
```markdown
-->
### BC-001 — Real contract
- Given: a customer exists
- When: recovery is requested
- Then: a link is sent
- Gate: tests/account_recovery.py::test_recovery_link
"""

        errors, _warnings = self._validate(
            slices, strict=True, slice_name="Recover Account Access"
        )

        self.assertEqual([], errors)

    def test_comment_marker_inside_fence_does_not_hide_real_contract(self) -> None:
        slices = """\
# Test Slices

## Recover Account Access

- Status: Approved

```markdown
<!--
```
### BC-001 — Real contract
- Given: a customer exists
- When: recovery is requested
- Then: a link is sent
- Gate: tests/account_recovery.py::test_recovery_link
"""

        errors, _warnings = self._validate(
            slices, strict=True, slice_name="Recover Account Access"
        )

        self.assertEqual([], errors)

    def test_contract_fields_do_not_leak_from_sibling_h3_section(self) -> None:
        slices = """\
# Test Slices

## Recover Account Access

- Status: Approved

### BC-001 — Recovery starts
- Given: a customer exists
- When: recovery is requested

  ###  Slice notes
- Then: this belongs to notes, not BC-001
- Gate: this also belongs to notes
"""

        errors, _warnings = self._validate(slices)

        self.assertTrue(
            any("BC-001" in error and "Then" in error for error in errors), errors
        )
        self.assertTrue(
            any("BC-001" in error and "Gate" in error for error in errors), errors
        )

    def test_contract_fields_do_not_leak_from_multi_space_h2_section(self) -> None:
        slices = """\
# Test Slices

## Recover Account Access

- Status: Approved

### BC-001 — Recovery starts
- Given: a customer exists
- When: recovery is requested

##  Another Slice
- Status: Proposed
- Then: this belongs to another slice
- Gate: this also belongs to another slice
"""

        errors, _warnings = self._validate(slices)

        self.assertTrue(
            any("BC-001" in error and "Then" in error for error in errors), errors
        )
        self.assertTrue(
            any("BC-001" in error and "Gate" in error for error in errors), errors
        )

    def test_placeholder_contract_id_fails(self) -> None:
        slices = """\
# Test Slices

## Recover Account Access

- Status: Approved

### BC-TODO — Placeholder
- Given: a customer exists
- When: recovery is requested
- Then: a link is sent
- Gate: tests/account_recovery.py::test_recovery_link
"""

        errors, _warnings = self._validate(slices)

        self.assertTrue(
            any("BC-TODO" in error and "placeholder" in error.lower() for error in errors),
            errors,
        )

    def test_placeholder_contract_clauses_fail(self) -> None:
        originals = {
            "Given": "a customer has a verified email address",
            "When": "the customer requests an account recovery link",
            "Then": "the customer receives a single-use recovery link",
            "Gate": "automated account-recovery contract test",
        }
        placeholders = {"Given": "N/A", "When": "none", "Then": "placeholder", "Gate": "?"}
        for clause, placeholder in placeholders.items():
            with self.subTest(clause=clause, placeholder=placeholder):
                slices = self._behavior_contracts(1).replace(
                    f"- {clause}: {originals[clause]}",
                    f"- {clause}: {placeholder}",
                )

                errors, _warnings = self._validate(slices)

                self.assertTrue(
                    any(
                        "BC-001" in error and clause.lower() in error.lower()
                        for error in errors
                    ),
                    errors,
                )

    def test_landed_evidence_requires_durable_locator_and_outcome(self) -> None:
        slices = """\
# Test Slices

## Recover Account Access

- Status: Landed
- Landed at: api@abc1234

### BC-001 — Recovery succeeds
- Then: the customer receives a single-use recovery link
- Gate: QA.md#recovery
- Evidence: qa: yes/no
"""

        errors, _warnings = self._validate(slices)

        self.assertTrue(
            any("BC-001" in error and "evidence" in error.lower() for error in errors),
            errors,
        )

    def test_landed_evidence_accepts_common_success_outcomes(self) -> None:
        for outcome in ("success", "successful", "passing", "healthy"):
            with self.subTest(outcome=outcome):
                slices = f"""\
# Test Slices

## Recover Account Access

- Status: Landed
- Landed at: api@abc1234

### BC-001 — Recovery succeeds
- Then: the customer receives a single-use recovery link
- Gate: runtime: https://observability.example/recovery
- Evidence: runtime: https://observability.example/recovery | {outcome}
"""

                errors, _warnings = self._validate(slices)

                self.assertFalse(
                    any("evidence" in error.lower() for error in errors), errors
                )

    def test_landed_evidence_rejects_failed_or_negated_outcomes(self) -> None:
        for evidence in (
            "test: https://ci.example/run/1 | failed",
            "qa: QA.md#recovery | not verified",
        ):
            with self.subTest(evidence=evidence):
                slices = f"""\
# Test Slices

## Recover Account Access

- Status: Landed
- Landed at: api@abc1234

### BC-001 — Recovery succeeds
- Then: the customer receives a single-use recovery link
- Gate: QA.md#recovery
- Evidence: {evidence}
"""

                errors, _warnings = self._validate(slices)

                self.assertTrue(
                    any("evidence" in error.lower() for error in errors), errors
                )


if __name__ == "__main__":
    unittest.main()
