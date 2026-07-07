#!/usr/bin/env python3
"""Detect companion-skill categories for a project shape.

This script names capability categories from stack evidence; it deliberately
ships no skill inventory. Skill names rot faster than skill packages release,
so name resolution happens live: the session's installed skills first, then a
project-supplied manifest (--manifest), then public catalogs only when the
user asks for install suggestions.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any


SKIP_DIRS = {".git", "node_modules", ".next", "dist", "build", "target", ".venv", "__pycache__"}

CATEGORY_GUIDANCE = {
    "core": "git workflow, planning/task breakdown, code review, test-driven development, docs/ADR skills",
    "frontend": "UI engineering, browser/device runtime QA, performance skills",
    "backend": "API/interface design, security hardening, debugging/diagnosis skills",
    "delivery": "CI/CD, release and launch, GitHub workflow skills",
    "planning": "spec and idea refinement, architecture review, adversarial design-review skills",
    "handoff": "triage, PRD/issue conversion, agent handoff skills",
}


def load_manifest(path: Path) -> list[dict[str, Any]]:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Could not load manifest {path}: {exc}") from exc
    skills = data.get("skills", [])
    if not isinstance(skills, list):
        raise SystemExit(f"Manifest {path} must contain a skills list")
    return [item for item in skills if isinstance(item, dict)]


def merge_skills(manifests: list[Path]) -> list[dict[str, Any]]:
    by_name: dict[str, dict[str, Any]] = {}
    for manifest in manifests:
        for skill in load_manifest(manifest):
            name = skill.get("name")
            if isinstance(name, str):
                by_name[name] = {**by_name.get(name, {}), **skill}
    return list(by_name.values())


def iter_files(root: Path, max_depth: int = 4):
    if not root.exists():
        return
    if root.is_file():
        yield root
        return
    root = root.resolve()
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        rel_depth = len(current_path.relative_to(root).parts)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        if rel_depth >= max_depth:
            dirs[:] = []
        for name in files:
            yield current_path / name


def detect_categories(paths: list[Path]) -> set[str]:
    categories = {"core"}
    text_chunks: list[str] = []
    names: set[str] = set()
    rels: set[str] = set()
    for root in paths:
        for file in iter_files(root):
            names.add(file.name)
            try:
                rels.add(file.relative_to(root).as_posix())
            except ValueError:
                rels.add(file.as_posix())
            if file.suffix.lower() in {".md", ".json", ".toml", ".yaml", ".yml"}:
                try:
                    text_chunks.append(file.read_text(errors="ignore")[:2000])
                except OSError:
                    pass
    text = "\n".join(text_chunks).lower()
    rel_text = "\n".join(sorted(rels)).lower()

    if names & {"package.json", "vite.config.ts", "next.config.js", "next.config.mjs"}:
        categories.add("frontend")
    if re.search(r"(component|screen|page|view|css|tsx|jsx|react|vue|svelte|mobile)", rel_text + text):
        categories.add("frontend")
    if names & {"go.mod", "pyproject.toml", "Cargo.toml"}:
        categories.add("backend")
    if re.search(r"(api|server|handler|controller|route|schema|migration|auth|database|worker|queue)", rel_text + text):
        categories.add("backend")
    if re.search(r"(deploy|release|workflow|docker|terraform|helm|kubernetes|github actions|ci)", rel_text + text):
        categories.add("delivery")
    if re.search(r"(prd|spec|roadmap|adr|architecture|glossary|domain|slice)", rel_text + text):
        categories.add("planning")
    if re.search(r"(issue|triage|handoff|blocked|status|support)", rel_text + text):
        categories.add("handoff")
    return categories


def priority_rank(priority: str) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(priority, 3)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Repo, monorepo, or coordinator paths to inspect")
    parser.add_argument("--project", action="append", default=[], help="Coordinator/project path to inspect")
    parser.add_argument("--manifest", action="append", default=[], help="Additional companion skill manifest")
    parser.add_argument("--category", action="append", default=[], help="Force include a category")
    args = parser.parse_args()

    paths = [Path(p).expanduser().resolve() for p in [*args.project, *args.paths]]
    categories = detect_categories(paths) if paths else {"core"}
    categories.update(args.category)

    print("# Companion Skill Categories")
    print("")
    print("Detected categories: " + ", ".join(sorted(categories)))
    print("")
    for category in sorted(categories):
        guidance = CATEGORY_GUIDANCE.get(category, "specialized skills for this category")
        print(f"- {category}: {guidance}")
    print("")
    print("## Resolve Names Live")
    print("")
    print("This catalog ships no skill inventory by design. Resolve in order:")
    print("")
    print("1. Skills already installed in the session — check before recommending.")
    print("2. A project-supplied manifest (`--manifest`), curated by the team.")
    print("3. Public catalogs (skills.sh, marketplaces) only when the user asks")
    print("   for install suggestions; never install without approval.")
    print("")
    print("Record category gaps no live source can fill as `SKILL_FEEDBACK.md`")
    print("candidates.")

    manifests = [Path(p).expanduser().resolve() for p in args.manifest]
    if manifests:
        skills = merge_skills(manifests)
        selected = [s for s in skills if s.get("category") in categories]
        selected.sort(key=lambda item: (priority_rank(str(item.get("priority", ""))), str(item.get("category")), str(item.get("name"))))
        print("")
        print("## Project Manifest Matches")
        print("")
        for skill in selected:
            print(f"### {skill.get('name')}")
            print("")
            print(f"- Category: {skill.get('category')}")
            print(f"- Priority: {skill.get('priority')}")
            print(f"- When: {skill.get('when')}")
            notes = skill.get("notes")
            if notes:
                print(f"- Notes: {notes}")
            command = skill.get("install_command")
            if command:
                print(f"- Install: `{command}`")
            else:
                print("- Install: no install source in the project manifest")
            print("")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
