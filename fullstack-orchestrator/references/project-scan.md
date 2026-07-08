# Project Scan

## Goal

Build a reviewed project adapter from evidence, not guesses. The default
onboarding mode is review-only: scan explicit seeds, present compact findings in
chat, and write docs only after the user approves a section.

## Inputs

Accept only explicit user-provided seeds:

- local repo paths
- local monorepo roots
- local orchestration docs
- GitHub URLs

Do not scan sibling repos or GitHub orgs unless the user gives those exact
roots. For URLs, ask before cloning or fetching.

## Evidence Collection

Collect signals from:

- git roots, remotes, branches, and local instructions
- package/workspace files
- language manifests such as `go.mod`, `pyproject.toml`, `Cargo.toml`
- CI workflows, deploy config, Docker or infra files
- tests, scripts, Makefiles, task files
- app, API, worker, and route entrypoints
- README, ADR, domain, and product docs
- schema, model, migration, and UI copy files

Scripts may collect evidence. The agent synthesizes product slices and term
boundaries.

## Project Scan Findings

Keep the findings compact but reviewable:

- finding
- confidence: high, medium, or low
- evidence paths or commands
- unknowns or user confirmations needed

Report sections in this order:

1. recommended orchestration repo
2. recommended worktree policy
3. task-board command policy
4. repo map
5. glossary candidates and term conflicts
6. vertical slice candidates, with BDD acceptance scenarios for the
   important behavior in each accepted slice
7. runbook proposals from detected stack patterns, with QA/debug/deploy gates
8. companion skill categories (names resolve live; see
   [companion-skills.md](companion-skills.md))

## Approval Rules

Ask for approval section by section. Unreviewed findings stay in chat and must
not be written to `ORCHESTRATION.md`, `GLOSSARY.md`, `SLICES.md`, or
`SKILL_FEEDBACK.md`.

When writing docs after approval:

- create or confirm a dedicated `<project-slug>-orchestration` repo first
- keep implementation repos as surfaces only
- approve task worktree root, branch naming, and landing policy
- approve whether `tasks`/`tsk` should use thread tools, local git/worktrees, or
  both when producing its task board
- write only approved facts
- keep `AGENTS.md` as a router
- avoid `reviewed: false` markers in canonical docs
- preserve existing project docs unless the user approves replacement

## Remote Seeds

If a seed is a URL:

1. identify the URL as remote
2. propose a clone/fetch destination
3. ask for explicit approval before network or credential use
4. scan the local clone only after approval
