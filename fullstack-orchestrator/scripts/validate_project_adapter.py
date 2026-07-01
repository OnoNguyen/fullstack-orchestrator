#!/usr/bin/env python3
"""Validate a fullstack-orchestrator project adapter."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_FILES = {
    "AGENTS.md": ["Trigger Router", "Default Discipline"],
    "ORCHESTRATION.md": ["Repositories"],
    "TASKS.md": ["Purpose", "Board Rules", "Status Labels"],
    "WORKTREES.md": ["Canonical Pickup Points", "Cross-Repo Landing"],
    "GLOSSARY.md": [],
    "SLICES.md": [],
    "QA.md": [],
    "DEBUG.md": [],
    "DEPLOY.md": [],
    "DOCUMENTATION_POLICY.md": [],
    "STATUS.md": [],
}

FORBIDDEN_MARKERS = ["reviewed: false", "unreviewed finding", "unreviewed:"]


def read(path: Path) -> str:
    try:
        return path.read_text()
    except OSError:
        return ""


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
        lowered = content.lower()
        for marker in FORBIDDEN_MARKERS:
            if marker in lowered:
                errors.append(f"{name} contains unreviewed marker: {marker}")

    agents = root / "AGENTS.md"
    if agents.exists():
        lines = read(agents).splitlines()
        if len(lines) > 60:
            message = f"AGENTS.md has {len(lines)} lines; keep root navigator under 60"
            (errors if strict else warnings).append(message)
        agents_text = read(agents)
        for doc in REQUIRED_FILES:
            if doc != "AGENTS.md" and doc not in agents_text:
                warnings.append(f"AGENTS.md does not route to {doc}")

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

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="Coordinator directory")
    parser.add_argument("--strict", action="store_true", help="Treat line-count warnings as errors")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    errors, warnings = validate(root, args.strict)
    print(f"Adapter: {root}")
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
