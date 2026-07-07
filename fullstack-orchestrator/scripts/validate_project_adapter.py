#!/usr/bin/env python3
"""Validate a fullstack-orchestrator project adapter."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


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


def validate(root: Path, strict: bool) -> tuple[list[str], list[str]]:
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
        routed = set(ROUTED_DOC_PATTERN.findall(agents_text)) - {"AGENTS.md"}
        for doc in sorted(routed):
            if not (root / doc).exists():
                errors.append(f"AGENTS.md routes to missing doc: {doc}")
        for doc in root_docs:
            if doc not in agents_text:
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
    if slices.exists() and read(slices).count("\n## ") < 1:
        warnings.append("SLICES.md has no slice sections yet")

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
    parser.add_argument("--strict", action="store_true", help="Treat line-count warnings as errors")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    errors, warnings = validate(root, args.strict)
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
    print("\nAdapter is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
