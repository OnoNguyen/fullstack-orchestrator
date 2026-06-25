# Project Adapter

## Purpose

The adapter teaches this skill how a specific project is organized without
loading every project rule into precontext. Keep shared orchestration docs in a
chosen coordinator repo. Keep repo-specific implementation notes inside the
implementation repos.

## AGENTS.md

`AGENTS.md` is the root navigator. It should usually be under 60 lines.

It must contain:

- one sentence describing the coordinator role
- a trigger table mapping task signals to deeper docs
- default discipline: verify live repo state before mutation, read only
  triggered docs, do not preload everything

It must not contain long runbooks, credentials, full glossary terms, detailed
slice specs, status history, schemas, migrations, or implementation specs.

Recommended trigger rows:

| Trigger | Read |
| --- | --- |
| repo map, aliases, ownership, multi-repo work | `ORCHESTRATION.md` |
| domain language, user-facing copy, data boundaries | `GLOSSARY.md` |
| slice planning, gates, dependencies, merge order | `SLICES.md` |
| QA, runtime evidence, browser/device/simulator checks | `QA.md` |
| debug or live runtime attach loops | `DEBUG.md` |
| deploy, release, push, production verification | `DEPLOY.md` |
| current pending state, blockers, landing, deploy state | `STATUS.md` |
| documentation placement or canonical ownership | `DOCUMENTATION_POLICY.md` |
| editing an implementation repo | that repo's local instructions |

## ORCHESTRATION.md

Record only approved repo topology:

| Alias | Role | Local path | Remote | Default branch | Owner | Notes |
| --- | --- | --- | --- | --- | --- | --- |

Also include branch/worktree policy, landing authority, deploy authority, and
cross-repo all-or-hold rules when they exist.

## GLOSSARY.md

`GLOSSARY.md` is required. Each entry should define:

- canonical term
- definition
- user-facing usage
- internal usage
- related terms
- terms it must not be conflated with
- data, privacy, or security implications when relevant

Do not store implementation details here. Existing `CONTEXT.md` files may be
read as input, but this adapter writes `GLOSSARY.md`.

## SLICES.md

Vertical slices describe user/business capability, not repo ownership. Each
slice should include:

- intent
- implementation surfaces
- dependencies
- relevant glossary terms
- data/privacy/security boundary when relevant
- verification gates
- merge or landing order

## STATUS.md

Keep current state small. It is not a history log or worker scratchpad. Use it
for pending work, blockers, deploy state, verification state, and next action.

## Documentation Policy

Use `DOCUMENTATION_POLICY.md` to prevent duplicated truth:

- glossary terms live in `GLOSSARY.md`
- topology lives in `ORCHESTRATION.md`
- slices and gates live in `SLICES.md`
- QA/debug/deploy runbooks live in their matching docs
- implementation specs, schemas, migrations, and code-level docs live in the
  relevant implementation repo
