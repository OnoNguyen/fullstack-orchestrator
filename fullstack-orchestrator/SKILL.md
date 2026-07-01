---
name: fullstack-orchestrator
description: Coordinates reviewed full-stack project work across one repo, a monorepo, or multiple repositories by scanning project topology, routing through lazy orchestration docs, and managing slices, task boards, QA, debug, deploy, landing, and handoff. Use when bootstrapping project orchestration, onboarding a codebase, scanning user-provided repos, planning vertical slices, answering tasks/tsk task-board requests, coordinating frontend/backend/infra work, setting up AGENTS.md routing, or deciding which companion skills to recommend.
---

# Fullstack Orchestrator

## Operating Rule

Treat project maps, generated docs, and prior summaries as routing hints until
verified against live filesystem, git, test, CI, and deploy state. Read only the
smallest project docs needed for the current trigger.

## First Moves

- If no project adapter exists, run a review-only project scan. See
  [project-scan.md](references/project-scan.md).
- If `AGENTS.md` exists, read it first as the root navigator, then load only the
  deeper docs it routes to.
- For multi-repo or monorepo work, resolve the live implementation surfaces
  before planning edits.
- Before mutation, inspect repo cleanliness and local instructions in every
  repo that may be edited, tested, landed, pushed, or deployed.

## Project Adapter

The canonical adapter is small markdown docs in a dedicated orchestration repo.
Create or confirm a repo named `<project-slug>-orchestration` by default.
Implementation repos are surfaces only and should not hold shared orchestration
docs unless the user explicitly overrides that boundary.

- `AGENTS.md`: root navigator and lazy trigger router only.
- `ORCHESTRATION.md`: approved repo map, aliases, roles, remotes, branches,
  and ownership.
- `WORKTREES.md`: task checkout/worktree policy, canonical pickup points,
  landing, and cleanup.
- `TASKS.md`: `tasks`/`tsk` board policy and action classification.
- `GLOSSARY.md`: approved domain language and boundary terms.
- `SLICES.md`: approved vertical slices, surfaces, dependencies, gates, and
  merge order.
- `QA.md`, `DEBUG.md`, `DEPLOY.md`: project-specific runbooks.
- `DOCUMENTATION_POLICY.md`: canonical doc ownership and anti-duplication rules.
- `STATUS.md`: coordinator-owned current state, not worker scratchpad.

See [project-adapter.md](references/project-adapter.md) for doc contracts and
templates.

## Onboarding Discipline

Scan only user-provided local paths or URLs. Keep unreviewed findings in chat,
not canonical docs. Ask the user to create or confirm a dedicated orchestration
repo, then approve findings section by section before writing docs: repo map,
worktree policy, task-board policy, glossary, slices, QA/debug/deploy.

Use scripts as evidence collectors and validators, not as authority:

- `scripts/bootstrap_project_adapter.py`: scan user-provided seeds and, after
  approval, write adapter docs.
- `scripts/validate_project_adapter.py`: check adapter docs for required
  structure and low-precontext routing.
- `scripts/recommend_skills.py`: suggest companion skills for the project shape.

## Work Execution

- Work slice first, repo second: repos are implementation surfaces, not the
  product slice itself.
- When the user says `tasks` or `tsk`, load `TASKS.md` and produce an
  actionable-only board before recommending continuations.
- Prefer temporary task branches/worktrees when the project adapter defines
  them.
- For cross-repo changes, use all-or-hold landing: no repo lands until every
  affected surface rebases cleanly and passes its gates.
- Use [worktrees-and-landing.md](references/worktrees-and-landing.md) when a
  task may dirty multiple repos, needs runtime QA, or involves landing/cleanup.
- Do not deploy unless the user explicitly says `deploy`, `dpl`, or the
  project adapter defines an equivalent deploy trigger.
- Use [qa-debug-deploy.md](references/qa-debug-deploy.md) when QA, debug,
  runtime evidence, deploy, retry, or release state is involved.

## Companion Skills

Recommend companion skills when the project shape or task calls for specialized
help. Do not assume they are installed. Print install suggestions only when a
public source is verified or supplied by the project. See
[companion-skills.md](references/companion-skills.md).
