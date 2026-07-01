# Project Adapter

## Purpose

The adapter teaches this skill how a specific project is organized without
loading every project rule into precontext. Keep shared orchestration docs in a
dedicated orchestration repo, usually named `<project-slug>-orchestration`.
Keep repo-specific implementation notes inside the implementation repos.
Implementation repos are surfaces only by default.

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
| tasks, tsk, task board, continue/abort candidates | `TASKS.md` |
| task branches, worktrees, landing, cleanup | `WORKTREES.md` |
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

Keep branch/worktree details in `WORKTREES.md`; `ORCHESTRATION.md` may link to
that policy but should stay focused on topology.

## WORKTREES.md

Record approved mutation and landing policy:

- canonical pickup branch per repo
- task worktree root
- task branch naming convention
- when task worktrees are required
- dirty-state preservation rules
- runtime ownership rules
- cross-repo all-or-hold policy
- landing and cleanup rules

## TASKS.md

Record the approved `tasks`/`tsk` command behavior:

- task-board sources such as `STATUS.md`, `SLICES.md`, `WORKTREES.md`, threads,
  worktrees, and branch state
- actionable-only inclusion rules
- row status labels
- board columns
- ranking policy
- action boundary for cleanup, aborts, thread archiving, and status updates

`TASKS.md` is command policy, not a backlog. Do not store every task there.

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
- task-board command policy lives in `TASKS.md`
- slices and gates live in `SLICES.md`
- QA/debug/deploy runbooks live in their matching docs
- implementation specs, schemas, migrations, and code-level docs live in the
  relevant implementation repo
