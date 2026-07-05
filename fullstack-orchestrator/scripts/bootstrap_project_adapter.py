#!/usr/bin/env python3
"""Scan explicit project seeds and optionally write orchestration adapter docs."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / "assets" / "project-adapter"
SKIP_DIRS = {
    ".git",
    ".next",
    ".turbo",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "vendor",
}
ROLE_SUFFIXES = {
    "android",
    "api",
    "app",
    "backend",
    "client",
    "docs",
    "frontend",
    "infra",
    "ios",
    "job",
    "jobs",
    "mobile",
    "orchestration",
    "orchestrator",
    "server",
    "service",
    "web",
    "worker",
    "workers",
}
GENERIC_PARENT_NAMES = {"code", "dev", "projects", "repos", "source", "src", "work", "workspace", "workspaces"}
IMPLEMENTATION_MARKERS = {"package.json", "go.mod", "pyproject.toml", "Cargo.toml", "Dockerfile"}


@dataclass
class RepoFinding:
    path: Path
    alias: str
    role: str
    remote: str
    branch: str
    evidence: list[str] = field(default_factory=list)
    verification: list[str] = field(default_factory=list)
    debug: list[str] = field(default_factory=list)
    deploy: list[str] = field(default_factory=list)
    terms: list[str] = field(default_factory=list)


def run(cmd: list[str], cwd: Path | None = None) -> str:
    try:
        return subprocess.check_output(cmd, cwd=cwd, stderr=subprocess.DEVNULL, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https", "ssh", "git"} or value.startswith("git@")


def repo_name_from_url(url: str) -> str:
    name = url.rstrip("/").split("/")[-1]
    if name.endswith(".git"):
        name = name[:-4]
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", name) or "repo"


def clone_remote(url: str, clone_dir: Path) -> Path:
    clone_dir.mkdir(parents=True, exist_ok=True)
    dest = clone_dir / repo_name_from_url(url)
    if dest.exists():
        return dest
    subprocess.check_call(["git", "clone", "--depth", "1", url, str(dest)])
    return dest


def git_root(path: Path) -> Path | None:
    out = run(["git", "-C", str(path), "rev-parse", "--show-toplevel"])
    return Path(out).resolve() if out else None


def walk_limited(root: Path, max_depth: int = 4) -> Iterable[Path]:
    root = root.resolve()
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        rel_depth = len(current_path.relative_to(root).parts)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".cache")]
        if rel_depth >= max_depth:
            dirs[:] = []
        for name in files:
            yield current_path / name


def find_repos(seed: Path) -> list[Path]:
    seed = seed.resolve()
    if not seed.exists():
        return []
    if seed.is_file():
        seed = seed.parent
    root = git_root(seed)
    if root:
        return [root]
    roots: set[Path] = set()
    for current, dirs, _files in os.walk(seed):
        current_path = Path(current)
        rel_depth = len(current_path.relative_to(seed).parts)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        if ".git" in dirs:
            roots.add(current_path.resolve())
            dirs.remove(".git")
        if rel_depth >= 3:
            dirs[:] = []
    return sorted(roots)


def load_package_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def collect_files(path: Path) -> list[Path]:
    files = list(walk_limited(path))
    files.sort()
    return files[:1500]


def package_signals(repo: Path, finding: RepoFinding) -> None:
    package_file = repo / "package.json"
    if not package_file.exists():
        return
    finding.evidence.append("package.json")
    package = load_package_json(package_file)
    deps = {}
    for key in ("dependencies", "devDependencies"):
        deps.update(package.get(key, {}) if isinstance(package.get(key), dict) else {})
    dep_names = set(deps)
    scripts = package.get("scripts", {}) if isinstance(package.get("scripts"), dict) else {}

    if dep_names & {"next", "vite", "react", "vue", "svelte", "@angular/core"}:
        add_role(finding, "frontend")
    if dep_names & {"expo", "react-native"}:
        add_role(finding, "mobile")
    if dep_names & {"express", "fastify", "@nestjs/core", "koa", "hono"}:
        add_role(finding, "backend")

    for name, command in scripts.items():
        if name in {"test", "lint", "typecheck", "tsc", "build"} or re.search(r"test|lint|type|build", name):
            finding.verification.append(f"package script: {name} -> {command}")
        if re.search(r"dev|start|serve|debug", name):
            finding.debug.append(f"package script: {name} -> {command}")
        if re.search(r"deploy|release|publish", name):
            finding.deploy.append(f"package script: {name} -> {command}")


def add_role(finding: RepoFinding, role: str) -> None:
    roles = {part.strip() for part in finding.role.split(",") if part.strip() and part.strip() != "unknown"}
    roles.add(role)
    finding.role = ", ".join(sorted(roles))


def infer_terms(files: list[Path], repo: Path) -> list[str]:
    terms: set[str] = set()
    for file in files:
        rel = file.relative_to(repo).as_posix()
        if file.name in {"README.md", "CONTEXT.md", "GLOSSARY.md"} or "docs/" in rel:
            try:
                text = file.read_text(errors="ignore")[:6000]
            except OSError:
                continue
            for heading in re.findall(r"^#{1,3}\s+(.+)$", text, flags=re.MULTILINE):
                cleaned = re.sub(r"[^A-Za-z0-9 /_-]", "", heading).strip()
                if 2 <= len(cleaned) <= 60:
                    terms.add(cleaned)
        if re.search(r"(model|schema|entity|migration|route|controller|handler)", rel, re.I):
            stem = re.sub(r"[-_]+", " ", file.stem).strip()
            if 3 <= len(stem) <= 40:
                terms.add(stem)
    return sorted(terms)[:16]


def analyze_repo(repo: Path) -> RepoFinding:
    remote = run(["git", "config", "--get", "remote.origin.url"], repo) or "(none)"
    branch = run(["git", "branch", "--show-current"], repo) or run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], repo
    ) or "main"
    finding = RepoFinding(
        path=repo.resolve(),
        alias=repo.name,
        role="unknown",
        remote=remote,
        branch=branch,
    )
    files = collect_files(repo)
    names = {f.name for f in files}
    rels = {f.relative_to(repo).as_posix() for f in files}

    package_signals(repo, finding)

    if "go.mod" in names:
        add_role(finding, "backend")
        finding.evidence.append("go.mod")
        finding.verification.extend(["go test ./...", "go build ./..."])
    if "pyproject.toml" in names:
        add_role(finding, "backend")
        finding.evidence.append("pyproject.toml")
        finding.verification.append("pytest")
    if "Cargo.toml" in names:
        add_role(finding, "backend")
        finding.evidence.append("Cargo.toml")
        finding.verification.append("cargo test")
    if "Dockerfile" in names or any(name.startswith("docker-compose") for name in names):
        finding.evidence.append("Docker config")
        finding.deploy.append("Docker build/deploy surface detected")
    if any(rel.startswith(".github/workflows/") for rel in rels):
        finding.evidence.append(".github/workflows")
        finding.deploy.append("GitHub Actions workflows detected")
    if any(rel.startswith(("terraform/", "infra/", "helm/", "charts/")) for rel in rels):
        add_role(finding, "infra")
        finding.evidence.append("infra files")
    if any(re.search(r"(worker|job|queue|cron)", rel, re.I) for rel in rels):
        add_role(finding, "worker")
    if any(re.search(r"(api|server|handler|controller|route)", rel, re.I) for rel in rels):
        add_role(finding, "backend")
    if any(re.search(r"(page|component|screen|view|css|tsx|jsx)", rel, re.I) for rel in rels):
        add_role(finding, "frontend")

    finding.terms = infer_terms(files, repo)
    dedupe_lists(finding)
    return finding


def dedupe_lists(finding: RepoFinding) -> None:
    for attr in ("evidence", "verification", "debug", "deploy", "terms"):
        values = list(dict.fromkeys(getattr(finding, attr)))
        setattr(finding, attr, values)


def role_confidence(finding: RepoFinding) -> str:
    if finding.role == "unknown":
        return "low"
    if len(finding.evidence) >= 3:
        return "high"
    return "medium"


def split_name(value: str) -> list[str]:
    return [part for part in re.split(r"[^a-z0-9]+", value.lower()) if part]


def common_parent(findings: list[RepoFinding]) -> Path | None:
    if not findings:
        return None
    parents = [finding.path.parent for finding in findings]
    try:
        return Path(os.path.commonpath([str(parent) for parent in parents]))
    except ValueError:
        return None


def derive_project_slug(findings: list[RepoFinding], parent: Path | None) -> str:
    if not findings:
        return "project"
    token_counts: dict[str, int] = {}
    ordered_tokens: list[str] = []
    for finding in findings:
        seen: set[str] = set()
        for token in split_name(finding.path.name):
            if token in ROLE_SUFFIXES or token in seen:
                continue
            seen.add(token)
            if token not in token_counts:
                ordered_tokens.append(token)
            token_counts[token] = token_counts.get(token, 0) + 1
    shared = [token for token in ordered_tokens if token_counts.get(token, 0) > 1]
    if shared:
        return shared[0]
    if len(findings) == 1:
        tokens = [token for token in split_name(findings[0].path.name) if token not in ROLE_SUFFIXES]
        if tokens:
            return "-".join(tokens)
    if parent and parent.name.lower() not in GENERIC_PARENT_NAMES:
        return re.sub(r"[^a-z0-9]+", "-", parent.name.lower()).strip("-") or "project"
    return "project"


def suggested_orchestration_path(findings: list[RepoFinding]) -> Path:
    parent = common_parent(findings)
    slug = derive_project_slug(findings, parent)
    base = parent or Path.cwd()
    return base / f"{slug}-orchestration"


def suggested_worktree_root(findings: list[RepoFinding]) -> Path:
    parent = common_parent(findings)
    slug = derive_project_slug(findings, parent)
    base = parent or Path.cwd()
    return base / "wt-tasks" / slug


def is_dedicated_orchestration_repo(path: Path) -> bool:
    name = path.name.lower()
    if any(token in name for token in ("orchestration", "orchestrator", "coordination")):
        return True
    has_orchestration_docs = (path / "ORCHESTRATION.md").exists() and (path / "AGENTS.md").exists()
    has_implementation_markers = any((path / marker).exists() for marker in IMPLEMENTATION_MARKERS)
    if has_orchestration_docs and not has_implementation_markers:
        return True
    return False


def scanned_repo_paths(findings: list[RepoFinding]) -> set[Path]:
    return {finding.path.resolve() for finding in findings}


def render_scan(findings: list[RepoFinding], skipped_urls: list[str]) -> str:
    orchestration_path = suggested_orchestration_path(findings)
    worktree_root = suggested_worktree_root(findings)
    lines: list[str] = []
    lines.append("# Fullstack Orchestrator Project Scan")
    lines.append("")
    lines.append("Default mode is review-only. Review these findings before writing adapter docs.")
    lines.append("")
    lines.append("## Recommended Orchestration Repo")
    lines.append("")
    lines.append(f"- Suggested path: {orchestration_path}")
    lines.append("- Purpose: keep orchestration docs separate from implementation repos.")
    lines.append("- Naming convention: `<project-slug>-orchestration`.")
    lines.append("- Do not use an app, API, web, worker, or infra repo as the coordinator by default.")
    lines.append("")
    lines.append("## Recommended Worktree Policy")
    lines.append("")
    lines.append(f"- Suggested task worktree root: {worktree_root}")
    lines.append("- Suggested task branch convention: `task/<short-slice>`.")
    lines.append("- Treat canonical local branches as clean pickup points unless the project says otherwise.")
    lines.append("- Use task worktrees for cross-repo work, codegen, deploy-input changes, and runtime QA.")
    lines.append("- Default cross-repo landing: all-or-hold.")
    lines.append("")
    lines.append("## Recommended Task Board Policy")
    lines.append("")
    lines.append("- `tasks` or `tsk` should produce an actionable-only board.")
    lines.append("- Suggested sources: STATUS.md, SLICES.md, WORKTREES.md, thread state when available, and live git/worktree state.")
    lines.append("- Do not update STATUS.md, archive threads, delete worktrees, or delete branches while generating the board.")
    lines.append("- Treat abort/cleanup rows as recommendation-only until the user confirms the specific action.")
    lines.append("")
    if skipped_urls:
        lines.append("## Remote Seeds Needing Approval")
        lines.append("")
        for url in skipped_urls:
            lines.append(f"- {url} (not cloned; rerun with --allow-clone after approval)")
        lines.append("")
    lines.append("## Repo Map Candidates")
    lines.append("")
    if not findings:
        lines.append("- No local git repos found under the explicit seeds.")
    for finding in findings:
        lines.append(f"### {finding.alias}")
        lines.append("")
        lines.append(f"- Confidence: {role_confidence(finding)}")
        lines.append(f"- Path: {finding.path}")
        lines.append(f"- Remote: {finding.remote}")
        lines.append(f"- Branch: {finding.branch}")
        lines.append(f"- Suggested role: {finding.role}")
        lines.append(f"- Evidence: {', '.join(finding.evidence) if finding.evidence else '(none)'}")
        if finding.verification:
            lines.append("- Verification candidates:")
            lines.extend(f"  - {item}" for item in finding.verification[:8])
        if finding.debug:
            lines.append("- Debug/runtime candidates:")
            lines.extend(f"  - {item}" for item in finding.debug[:8])
        if finding.deploy:
            lines.append("- Deploy candidates:")
            lines.extend(f"  - {item}" for item in finding.deploy[:8])
        if finding.terms:
            lines.append("- Glossary candidates:")
            lines.extend(f"  - {term}" for term in finding.terms[:10])
        lines.append("")
    lines.append("## Vertical Slice Prompts")
    lines.append("")
    lines.append("Use the repo evidence above to ask the user which end-to-end capabilities matter.")
    lines.append("For each accepted slice, capture intent, surfaces, dependencies, terms, BDD scenarios, gates, and merge order.")
    lines.append("")
    lines.append("## Review Checklist")
    lines.append("")
    lines.append("- Dedicated orchestration repo created or confirmed")
    lines.append("- Task worktree root and landing policy approved")
    lines.append("- `tasks`/`tsk` task-board policy approved")
    lines.append("- Repo map approved")
    lines.append("- Glossary terms approved")
    lines.append("- Vertical slices approved with BDD scenarios and acceptance gates")
    lines.append("- QA/debug/deploy gates approved")
    lines.append("- Companion skill recommendations reviewed")
    lines.append("")
    lines.append("## Recommended Next Steps")
    lines.append("")
    lines.append("Option A — Create or confirm the dedicated orchestration repo")
    lines.append(f"- Use `{orchestration_path}` unless you already have a dedicated orchestration/docs repo.")
    lines.append("- Write AGENTS.md, ORCHESTRATION.md, TASKS.md, WORKTREES.md, GLOSSARY.md, SLICES.md, QA.md, DEBUG.md, DEPLOY.md, DOCUMENTATION_POLICY.md, STATUS.md, and SKILL_FEEDBACK.md there.")
    lines.append(f"- Approve `{worktree_root}` or pass `--worktree-root` with the chosen task worktree root.")
    lines.append("- Keep scanned implementation repos as surfaces only.")
    lines.append("")
    lines.append("Option B — Review the proposed project map and slices")
    lines.append("- Correct aliases, roles, missing repos, glossary terms, and slice boundaries before writing docs.")
    return "\n".join(lines)


def repo_rows(findings: list[RepoFinding]) -> str:
    if not findings:
        return "| TODO | TODO | TODO | TODO | TODO | TODO | TODO |"
    rows = []
    for finding in findings:
        rows.append(
            "| {alias} | {role} | {path} | {remote} | {branch} | TODO | evidence: {evidence} |".format(
                alias=finding.alias,
                role=finding.role,
                path=finding.path,
                remote=finding.remote,
                branch=finding.branch,
                evidence=", ".join(finding.evidence[:4]) or "none",
            )
        )
    return "\n".join(rows)


def write_docs(
    coordinator: Path,
    project_name: str,
    findings: list[RepoFinding],
    force: bool,
    worktree_root: str,
    task_branch_convention: str,
    landing_policy: str,
) -> list[Path]:
    coordinator.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    values = {
        "project_name": project_name,
        "repo_rows": repo_rows(findings),
        "worktree_root": worktree_root,
        "task_branch_convention": task_branch_convention,
        "landing_policy": landing_policy,
    }
    targets = [
        (template, coordinator / template.name.removesuffix(".template"))
        for template in sorted(TEMPLATE_DIR.glob("*.template"))
    ]
    if not force:
        conflicts = [target for _template, target in targets if target.exists()]
        if conflicts:
            listing = "\n".join(f"- {target}" for target in conflicts)
            raise SystemExit(
                "Refusing to write: these adapter docs already exist and nothing was written:\n"
                f"{listing}\n"
                "Review them first; rerun with --force only if overwriting all of them is intended."
            )
    for template, target in targets:
        content = template.read_text().format(**values)
        target.write_text(content)
        written.append(target)
    return written


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("seeds", nargs="*", help="Explicit local repo roots, monorepo roots, or Git URLs")
    parser.add_argument("--project-name", default="", help="Project name for generated docs")
    parser.add_argument("--coordinator", default="", help="Dedicated orchestration repo/directory for --write")
    parser.add_argument("--worktree-root", default="", help="Approved task worktree root for generated WORKTREES.md")
    parser.add_argument(
        "--task-branch-convention",
        default="task/<short-slice>",
        help="Approved task branch naming convention for generated WORKTREES.md",
    )
    parser.add_argument("--landing-policy", default="all-or-hold", help="Approved landing policy for generated WORKTREES.md")
    parser.add_argument("--write", action="store_true", help="Write adapter docs after user review")
    parser.add_argument("--force", action="store_true", help="Overwrite existing adapter docs")
    parser.add_argument(
        "--allow-implementation-coordinator",
        action="store_true",
        help="Allow writing into a scanned implementation repo; not recommended",
    )
    parser.add_argument("--allow-clone", action="store_true", help="Allow cloning URL seeds")
    parser.add_argument("--clone-dir", default=".tmp/fullstack-orchestrator-clones", help="Clone destination for URL seeds")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.seeds:
        print("No seeds supplied. Pass explicit local paths or Git URLs.", file=sys.stderr)
        return 2

    seeds: list[Path] = []
    skipped_urls: list[str] = []
    for seed in args.seeds:
        if is_url(seed):
            if not args.allow_clone:
                skipped_urls.append(seed)
                continue
            seeds.append(clone_remote(seed, Path(args.clone_dir)))
        else:
            seeds.append(Path(seed).expanduser())

    repos: dict[Path, RepoFinding] = {}
    for seed in seeds:
        for repo in find_repos(seed):
            repos[repo.resolve()] = analyze_repo(repo)
    findings = list(repos.values())
    findings.sort(key=lambda item: item.alias)

    print(render_scan(findings, skipped_urls))

    if args.write:
        if not args.coordinator:
            suggested = suggested_orchestration_path(findings)
            raise SystemExit(
                "Writing requires --coordinator pointing at a dedicated orchestration repo/directory. "
                f"Suggested path: {suggested}"
            )
        coordinator = Path(args.coordinator).expanduser().resolve()
        containing_repo = next(
            (
                repo
                for repo in scanned_repo_paths(findings)
                if coordinator == repo or repo in coordinator.parents
            ),
            None,
        )
        if containing_repo and not is_dedicated_orchestration_repo(containing_repo):
            if not args.allow_implementation_coordinator:
                raise SystemExit(
                    f"Refusing to write orchestration docs inside scanned implementation repo {containing_repo} "
                    f"(coordinator: {coordinator}). "
                    "Create or choose a dedicated <project-slug>-orchestration repo instead, "
                    "or rerun with --allow-implementation-coordinator if you intentionally want this."
                )
            print(f"Warning: writing into scanned implementation repo by explicit override: {coordinator}")
        project_name = args.project_name or coordinator.name
        worktree_root = args.worktree_root or str(suggested_worktree_root(findings))
        written = write_docs(
            coordinator,
            project_name,
            findings,
            args.force,
            worktree_root,
            args.task_branch_convention,
            args.landing_policy,
        )
        print("")
        print("## Written Adapter Docs")
        for path in written:
            print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
