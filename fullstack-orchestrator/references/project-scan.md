# Project Scan

## Goal

Build a reviewed project adapter from evidence, not guesses. The default
onboarding mode is review-only: scan explicit seeds, present compact findings in
chat, and write docs only after the user approves a section.

## Inputs

Accept only explicit user-provided seeds:

- local repo paths
- local monorepo roots
- local coordinator docs
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

1. repo map
2. glossary candidates and term conflicts
3. vertical slice candidates
4. QA/debug/deploy gates
5. companion skill recommendations

## Approval Rules

Ask for approval section by section. Unreviewed findings stay in chat and must
not be written to `ORCHESTRATION.md`, `GLOSSARY.md`, or `SLICES.md`.

When writing docs after approval:

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
