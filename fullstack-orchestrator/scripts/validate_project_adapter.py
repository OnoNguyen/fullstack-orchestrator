#!/usr/bin/env python3
"""Validate a fullstack-orchestrator project adapter."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlsplit


# Core coordination docs every project needs. Runbooks (QA.md, DEPLOY.md, ...)
# are emergent per stack pattern and validated through router integrity below,
# not through a fixed name list.
REQUIRED_FILES = {
    "AGENTS.md": ["Trigger Router", "Default Discipline"],
    "ORCHESTRATION.md": ["Repositories"],
    "TASKS.md": ["Purpose", "Board Rules", "Status Labels"],
    "WORKTREES.md": ["Canonical Pickup Points", "Cross-Repo Landing"],
    "GLOSSARY.md": [],
    "SLICES.md": [],
    "DOCUMENTATION_POLICY.md": [],
    "STATUS.md": [],
}

OPTIONAL_FILES = {
    "SKILL_FEEDBACK.md": ["Skill Improvement Candidates"],
}

FORBIDDEN_MARKERS = ["reviewed: false", "unreviewed finding", "unreviewed:"]

# Soft per-doc line budgets; DOCUMENTATION_POLICY.md Size Budgets rows override.
DEFAULT_BUDGETS = {
    "AGENTS.md": 60,
    "STATUS.md": 40,
    "DOCUMENTATION_POLICY.md": 60,
    "ORCHESTRATION.md": 80,
    "TASKS.md": 80,
    "WORKTREES.md": 80,
    "QA.md": 120,
    "DEBUG.md": 120,
    "DEPLOY.md": 120,
    "GLOSSARY.md": 200,
    "SLICES.md": 300,
    "SKILL_FEEDBACK.md": 200,
}

BUDGET_ROW = re.compile(r"^\|\s*`?([A-Z_]+\.md)`?\s*\|\s*(\d+)\s*\|", re.MULTILINE)
DOC_ROUTE = re.compile(r"`([A-Za-z0-9_./-]+\.md)`")
ROUTED_DOC_PATTERN = re.compile(r"`([A-Za-z0-9][A-Za-z0-9_.-]*\.md)`")
SLICE_HEADING = re.compile(
    r"^ {0,3}##[ \t]+(?!#)(?P<title>\S.*?)[ \t]*$", re.MULTILINE
)
CONTRACT_HEADING = re.compile(
    r"^ {0,3}###[ \t]+(?P<id>BC-[A-Z0-9]+(?:-[A-Z0-9]+)*)[ \t]+(?:—|-)[ \t]+(?P<title>\S.*?)[ \t]*$",
    re.MULTILINE,
)
H3_HEADING = re.compile(r"^ {0,3}###[ \t]+(?!#)\S.*?[ \t]*$", re.MULTILINE)
FENCE_START = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})")
SLICE_STATUS = re.compile(
    r"^- Status:[ \t]*(?P<value>[^\r\n]*?)[ \t]*$", re.MULTILINE
)
CONTRACT_FIELDS = ("Given", "When", "Then", "Gate", "Evidence")
PLACEHOLDER_VALUE = re.compile(
    r"^(?:<.*>|TODO(?:\b.*)?|TBD(?:\b.*)?|Pending|N/?A|None|Placeholder|"
    r"Example|\?|\-|\.\.\.)$",
    re.IGNORECASE,
)
PLACEHOLDER_CONTRACT_IDS = {"BC-000", "BC-EXAMPLE", "BC-TBD", "BC-TODO", "BC-XXX"}
LANDING_REFS = re.compile(
    r"^[A-Za-z0-9_.-]+@[0-9A-Fa-f]{7,64}"
    r"(?:,[ \t]*[A-Za-z0-9_.-]+@[0-9A-Fa-f]{7,64})*$"
)
EVIDENCE_VALUE = re.compile(
    r"^(?:test|contract|qa|runtime|smoke):[ \t]+(?P<locator>\S.*?)[ \t]+\|[ \t]+"
    r"(?P<outcome>passed|passing|success|successful|verified|succeeded|observed|"
    r"approved|green|confirmed|complete|completed|healthy|ok|accepted)$",
    re.IGNORECASE,
)
DURABLE_EVIDENCE_LOCATOR = re.compile(
    r"(?:https?://\S+|[A-Za-z0-9_.-]+@[0-9A-Fa-f]{7,64}\b|"
    r"(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\.[A-Za-z0-9]{1,12}(?:#\S+|::\S+)?)",
    re.IGNORECASE,
)


STATUS_COLUMNS = ("ID", "State", "Owner", "Checked", "Condition", "Evidence", "Next action")
STATUS_ID = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")
STATUS_STATES = {"pending", "blocked", "needs-verification"}
STATUS_LINK = re.compile(r"(?<!!)\[([^\[\]\n]+)\]\(([^\s()]+)\)")
STATUS_WORD_LIMITS = {"Owner": 6, "Condition": 25, "Evidence": 15, "Next action": 25}
STATUS_SHAPE_ERROR = (
    "STATUS.md must use the snapshot shape. Expected '# <project> Orchestration Status', "
    "'## Current', and the contiguous seven-column current-items table. "
    "If migrating legacy content, archive its exact bytes and follow "
    "references/status-reconciliation.md in the skill directory before replacing the file; "
    "do not truncate unresolved work."
)


def read(path: Path) -> str:
    try:
        return path.read_text()
    except OSError:
        return ""


def load_budgets(root: Path) -> dict[str, int]:
    budgets = dict(DEFAULT_BUDGETS)
    for name, value in BUDGET_ROW.findall(read(root / "DOCUMENTATION_POLICY.md")):
        budgets[name] = int(value)
    return budgets


def is_missing_value(value: str) -> bool:
    value = value.strip()
    return not value or bool(PLACEHOLDER_VALUE.fullmatch(value))


def is_durable_evidence(value: str) -> bool:
    match = EVIDENCE_VALUE.fullmatch(value.strip())
    return bool(match and DURABLE_EVIDENCE_LOCATOR.search(match.group("locator")))


def status_cells(line: str) -> list[str]:
    if not line.startswith("|") or not line.endswith("|"):
        return []
    cells: list[str] = []
    start = 1
    backslashes = 0
    for index, character in enumerate(line[1:], 1):
        if character == "|" and backslashes % 2 == 0:
            cells.append(line[start:index].strip())
            start = index + 1
        backslashes = backslashes + 1 if character == "\\" else 0
    return cells if start == len(line) else []


def has_status_evidence(value: str) -> bool:
    links = list(STATUS_LINK.finditer(value))
    if not links:
        return False
    end = 0
    for match in links:
        if not re.fullmatch(r"[\s,;]*", value[end : match.start()]):
            return False
        label, target = match.groups()
        if is_missing_value(label) or is_missing_value(target):
            return False
        try:
            link = urlsplit(target)
        except ValueError:
            return False
        if not (link.scheme == "https" and link.hostname) and not (
            not link.scheme
            and not link.netloc
            and link.path
            and not link.path.startswith("/")
            and link.path not in {".", ".."}
        ):
            return False
        end = match.end()
    return bool(re.fullmatch(r"[\s,;]*", value[end:]))


def validate_status(content: str) -> list[str]:
    """Validate snapshot structure, not the truth or freshness of its claims."""
    errors: list[str] = []
    physical_lines = content.splitlines()
    if len(physical_lines) > 40:
        errors.append(
            f"STATUS.md has {len(physical_lines)} lines; hard limit is 40. "
            "Reconcile current rows, remove proven resolved rows, and move detail "
            "to its canonical source."
        )
    words = len(content.split())
    if words > 600:
        errors.append(
            f"STATUS.md has {words} words; hard limit is 600. "
            "Whitespace-separated words include Markdown table tokens. "
            "Reconcile current rows and link detailed evidence from its canonical source."
        )

    lines = [
        (number, line.rstrip())
        for number, line in enumerate(physical_lines, 1)
        if line.strip()
    ]
    if len(lines) < 4:
        return errors + [STATUS_SHAPE_ERROR]
    title = re.fullmatch(r"# (.+) Orchestration Status", lines[0][1])
    separator = status_cells(lines[3][1])
    if (
        not title
        or is_missing_value(title.group(1))
        or "{project_name}" in title.group(1)
        or lines[1][1] != "## Current"
        or status_cells(lines[2][1]) != list(STATUS_COLUMNS)
        or lines[3][0] != lines[2][0] + 1
        or len(separator) != 7
        or not all(re.fullmatch(r":?-{3,}:?", cell) for cell in separator)
    ):
        return errors + [STATUS_SHAPE_ERROR]

    seen_ids: set[str] = set()
    previous_line = lines[3][0]
    for line_number, line in lines[4:]:
        if line_number != previous_line + 1:
            errors.append(
                f"STATUS.md line {line_number} must be contiguous with the current-items "
                "table; remove blank lines between the separator and rows or between rows"
            )
        previous_line = line_number
        cells = status_cells(line)
        if len(cells) != 7:
            errors.append(
                f"STATUS.md line {line_number} must be a table row with exactly seven cells; "
                "move history or prose to its canonical source and escape cell pipes as \\| or encode them as &#124; or %7C."
            )
            continue
        item = dict(zip(STATUS_COLUMNS, cells))
        topic_id = item["ID"]
        location = f"STATUS.md line {line_number}"
        if not STATUS_ID.fullmatch(topic_id) or len(topic_id) > 64:
            errors.append(
                f"{location} has invalid ID; use a lowercase hyphenated topic slug "
                "of at most 64 characters"
            )
        if topic_id in seen_ids:
            errors.append(f"{location} has duplicate ID: {topic_id}")
        seen_ids.add(topic_id)
        if item["State"] not in STATUS_STATES:
            errors.append(
                f"{location} has invalid State; use pending, blocked, or "
                "needs-verification and remove resolved rows"
            )
        for field in ("Owner", "Checked", "Condition", "Evidence", "Next action"):
            if is_missing_value(item[field]):
                errors.append(f"{location} requires a meaningful {field} value")
        for field, limit in STATUS_WORD_LIMITS.items():
            if len(item[field].split()) > limit:
                errors.append(
                    f"{location} {field} exceeds {limit} words; link detailed context "
                    "from its canonical source"
                )
        checked = item["Checked"]
        try:
            checked_date = date.fromisoformat(checked)
        except ValueError:
            checked_date = None
        # A coordinator's local date can be one day ahead of the CI runner.
        if (
            not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", checked)
            or checked_date is None
            or checked_date > date.today() + timedelta(days=1)
        ):
            errors.append(
                f"{location} Checked must be a real YYYY-MM-DD date at most one day ahead"
            )
        if not has_status_evidence(item["Evidence"]):
            errors.append(
                f"{location} Evidence must contain only inline Markdown links "
                "with meaningful labels and relative source paths or HTTPS sources, "
                "separated by whitespace, commas, or semicolons"
            )
    return errors


def strip_nonrendered_blocks(content: str) -> str:
    output: list[str] = []
    active_character = ""
    active_length = 0
    in_comment = False
    for line in content.splitlines(keepends=True):
        line_ending = ""
        if line.endswith("\r\n"):
            line_ending = "\r\n"
        elif line.endswith(("\n", "\r")):
            line_ending = line[-1]
        visible = line[: -len(line_ending)] if line_ending else line

        if active_character:
            closing_fence = re.fullmatch(
                rf" {{0,3}}{re.escape(active_character)}{{{active_length},}}[ \t]*",
                visible,
            )
            if closing_fence:
                active_character = ""
                active_length = 0
            output.append(line_ending)
            continue

        if in_comment:
            comment_end = visible.find("-->")
            if comment_end < 0:
                output.append(line_ending)
                continue
            in_comment = False
            output.append(line_ending)
            continue

        match = FENCE_START.match(visible)
        if match:
            fence = match.group("fence")
            active_character = fence[0]
            active_length = len(fence)
            output.append(line_ending)
            continue

        search_from = 0
        while True:
            comment_start = visible.find("<!--", search_from)
            if comment_start < 0:
                break
            comment_end = visible.find("-->", comment_start + 4)
            if comment_end < 0:
                visible = visible[:comment_start] + " " * (len(visible) - comment_start)
                in_comment = True
                break
            end = comment_end + 3
            visible = visible[:comment_start] + " " * (end - comment_start) + visible[end:]
            search_from = end

        output.append(visible + line_ending)
    return "".join(output)


def behavior_contract_sections(content: str) -> list[tuple[str, str]]:
    headings = list(SLICE_HEADING.finditer(content))
    sections: list[tuple[str, str]] = []
    for index, heading in enumerate(headings):
        title = heading.group("title").strip()
        if normalize_heading(title) == "slices to confirm":
            continue
        end = headings[index + 1].start() if index + 1 < len(headings) else len(content)
        sections.append((title, content[heading.end() : end]))
    return sections


def normalize_heading(value: str) -> str:
    value = re.sub(r"[ \t]+#+[ \t]*$", "", value.strip())
    return " ".join(value.split()).casefold()


def validate_behavior_contracts(
    content: str, strict: bool, target_slice: str | None = None
) -> tuple[list[str], list[str]]:
    content = strip_nonrendered_blocks(content)
    errors: list[str] = []
    warnings: list[str] = []
    readiness_findings = errors if strict else warnings
    seen_contract_ids: set[str] = set()
    ready_contract_count = 0
    target_key = normalize_heading(target_slice) if target_slice else None
    target_matches = 0
    target_ready = False

    sections = behavior_contract_sections(content)
    for slice_title, section in sections:
        is_target = target_key is not None and normalize_heading(slice_title) == target_key
        if is_target:
            target_matches += 1
        statuses = [match.group("value").strip() for match in SLICE_STATUS.finditer(section)]
        if not statuses:
            readiness_findings.append(
                f"SLICES.md slice {slice_title!r} has legacy structure without Status; "
                "behavior contract validation skipped"
            )
            continue
        if len(statuses) > 1:
            errors.append(f"SLICES.md slice {slice_title!r} has duplicate Status fields")
            continue

        status = statuses[0].casefold()
        if status not in {"proposed", "approved", "landed"}:
            errors.append(
                f"SLICES.md slice {slice_title!r} has invalid Status: {statuses[0]!r}"
            )
            continue

        contract_headings = list(CONTRACT_HEADING.finditer(section))
        h3_starts = [heading.start() for heading in H3_HEADING.finditer(section)]
        for heading in contract_headings:
            contract_id = heading.group("id")
            if contract_id in PLACEHOLDER_CONTRACT_IDS:
                errors.append(
                    f"SLICES.md behavior contract ID is a placeholder: {contract_id}"
                )
            if contract_id in seen_contract_ids:
                errors.append(f"SLICES.md has duplicate behavior contract ID: {contract_id}")
            seen_contract_ids.add(contract_id)

        if status == "proposed":
            continue

        contract_count = len(contract_headings)
        ready_contract_count += contract_count
        if is_target and contract_count > 0:
            target_ready = True
        if not 1 <= contract_count <= 3:
            errors.append(
                f"SLICES.md slice {slice_title!r} must contain 1-3 behavior contracts; "
                f"found {contract_count}"
            )

        if status == "landed":
            landed_at = re.findall(
                r"^- Landed at:[ \t]*([^\r\n]*?)[ \t]*$", section, re.MULTILINE
            )
            if len(landed_at) != 1 or not LANDING_REFS.fullmatch(landed_at[0]):
                errors.append(
                    f"SLICES.md landed slice {slice_title!r} requires Landed at as repo@commit references"
                )

        for heading in contract_headings:
            contract_id = heading.group("id")
            end = next(
                (start for start in h3_starts if start > heading.start()), len(section)
            )
            contract = section[heading.end() : end]
            required_fields = (
                ("Given", "When", "Then", "Gate")
                if status == "approved"
                else ("Then", "Gate", "Evidence")
            )
            for field in CONTRACT_FIELDS:
                values = re.findall(
                    rf"^- {re.escape(field)}:[ \t]*([^\r\n]*?)[ \t]*$",
                    contract,
                    re.MULTILINE,
                )
                if field in required_fields and not values:
                    errors.append(f"SLICES.md {contract_id} missing {field} clause")
                    continue
                if len(values) > 1:
                    errors.append(f"SLICES.md {contract_id} has duplicate {field} clauses")
                    continue
                if field in required_fields and values and is_missing_value(values[0]):
                    errors.append(f"SLICES.md {contract_id} has blank {field} clause")
                    continue
                if (
                    field == "Evidence"
                    and field in required_fields
                    and values
                    and not is_durable_evidence(values[0])
                ):
                    errors.append(
                        f"SLICES.md {contract_id} Evidence requires '<gate kind>: <durable locator> | <successful outcome>'"
                    )

    if target_key is not None:
        if target_matches == 0:
            errors.append(f"SLICES.md target slice not found: {target_slice!r}")
        elif target_matches > 1:
            errors.append(f"SLICES.md target slice is ambiguous: {target_slice!r}")
        elif not target_ready:
            errors.append(
                f"SLICES.md target slice {target_slice!r} has no approved behavior contract"
            )
    elif ready_contract_count == 0:
        readiness_findings.append(
            "SLICES.md has no approved behavior contract; approve at least one before behavior implementation"
        )

    return errors, warnings


def validate(
    root: Path, strict: bool, target_slice: str | None = None
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for name, headings in REQUIRED_FILES.items():
        path = root / name
        if not path.exists():
            errors.append(f"missing {name}")
            continue
        content = read(path)
        for heading in headings:
            if heading not in content:
                errors.append(f"{name} missing heading text: {heading}")

    for name, headings in OPTIONAL_FILES.items():
        path = root / name
        if not path.exists():
            continue
        content = read(path)
        for heading in headings:
            if heading not in content:
                warnings.append(f"{name} missing heading text: {heading}")

    # Router integrity: AGENTS.md's trigger table is the doc manifest. Every
    # routed doc must exist, and every adapter doc must be routed, so emergent
    # runbooks stay discoverable without a fixed required-name list.
    root_docs = sorted(
        path.name
        for path in root.glob("*.md")
        if path.name not in {"AGENTS.md", "README.md"}
    )
    for name in root_docs:
        lowered = read(root / name).lower()
        for marker in FORBIDDEN_MARKERS:
            if marker in lowered:
                errors.append(f"{name} contains unreviewed marker: {marker}")

    budgets = load_budgets(root)
    for name, budget in budgets.items():
        path = root / name
        if not path.exists():
            continue
        count = len(read(path).splitlines())
        if count > budget:
            message = f"{name} has {count} lines; budget is {budget} (groom candidate)"
            (errors if strict else warnings).append(message)

    agents = root / "AGENTS.md"
    if agents.exists():
        agents_text = read(agents)
        for marker in FORBIDDEN_MARKERS:
            if marker in agents_text.lower():
                errors.append(f"AGENTS.md contains unreviewed marker: {marker}")
        lines = agents_text.splitlines()
        if len(lines) > 60:
            message = f"AGENTS.md has {len(lines)} lines; keep root navigator under 60"
            (errors if strict else warnings).append(message)
        routed: set[str] = set()
        for line in agents_text.splitlines():
            if line.strip().startswith("|"):
                routed.update(ROUTED_DOC_PATTERN.findall(line))
        routed -= {"AGENTS.md"}
        for doc in sorted(routed):
            if not (root / doc).exists():
                errors.append(f"AGENTS.md routes to missing doc: {doc}")
        for doc in root_docs:
            if doc in routed:
                continue
            # Word-boundary match so e.g. DEVICE_QA.md cannot satisfy QA.md.
            if not re.search(rf"(?<![A-Za-z0-9_-]){re.escape(doc)}", agents_text):
                warnings.append(f"AGENTS.md does not route to {doc}")
        for ref in sorted(set(DOC_ROUTE.findall(agents_text))):
            if not (root / ref).exists():
                warnings.append(f"AGENTS.md routes to missing doc: {ref}")
        if "archive/" in agents_text:
            warnings.append(
                "AGENTS.md routes into archive/; archived content must stay out of the routing path"
            )

    orchestration = root / "ORCHESTRATION.md"
    if orchestration.exists():
        text = read(orchestration)
        for column in ("Alias", "Role", "Local path", "Remote", "Default branch"):
            if column not in text:
                errors.append(f"ORCHESTRATION.md missing repository table column: {column}")

    glossary = root / "GLOSSARY.md"
    if glossary.exists() and read(glossary).count("\n## ") < 1:
        warnings.append("GLOSSARY.md has no term sections yet")

    slices = root / "SLICES.md"
    if slices.exists():
        slices_text = read(slices)
        if slices_text.count("\n## ") < 1:
            warnings.append("SLICES.md has no slice sections yet")
        behavior_errors, behavior_warnings = validate_behavior_contracts(
            slices_text, strict, target_slice
        )
        errors.extend(behavior_errors)
        warnings.extend(behavior_warnings)

    status = root / "STATUS.md"
    if status.exists():
        errors.extend(validate_status(read(status)))

    policy = root / "DOCUMENTATION_POLICY.md"
    if policy.exists() and "Grooming" not in read(policy):
        warnings.append(
            "DOCUMENTATION_POLICY.md has no Grooming section; groom/grm falls back to skill defaults"
        )

    return errors, warnings


def total_lines(root: Path) -> int:
    return sum(
        len(read(path).splitlines())
        for path in sorted(root.glob("*.md"))
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="Coordinator directory")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat budget and behavior-readiness warnings as errors",
    )
    parser.add_argument(
        "--slice",
        dest="target_slice",
        help="Require the named slice to have an approved behavior contract",
    )
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    errors, warnings = validate(root, args.strict, args.target_slice)
    print(f"Adapter: {root}")
    print(f"Total adapter lines (top-level docs, excluding archive/): {total_lines(root)}")
    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"- {warning}")
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("\nAdapter structure is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
