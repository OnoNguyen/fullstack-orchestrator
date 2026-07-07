# QA, Debug, Deploy, And Landing

This doctrine is generic; project-specific commands, gates, and owners live in
the adapter's pattern runbooks (`QA.md`, `DEBUG.md`, `DEPLOY.md`, ...) when
they exist. If the stack shows a pattern that has no runbook yet, propose
creating one from the runbook contract in
[project-adapter.md](project-adapter.md) instead of improvising.

## QA

QA and deployment are separate requests. When QA is requested:

- decide whether static verification, runtime QA, browser QA, simulator/device
  QA, or production readback is appropriate
- run the project's documented gates
- report method, commands, evidence, untested surfaces, and blockers

Runtime QA should use the exact task commit when the project policy requires
it. Do not treat a dev server being up as proof that the app or site works.

## Debug

Debug requests may use dirty state only when the project adapter allows it and
only inside the task checkout/worktree it owns. Read `WORKTREES.md` when task
checkout ownership is unclear.

Before starting local runtimes:

- inspect active dev servers and ports
- avoid interrupting unrelated sessions
- prefer the current task checkout over canonical main
- report how the runtime was attached and how success was proven

## Deploy

Deployment requires explicit user trigger: `deploy`, `dpl`, or a project-defined
equivalent. A deploy request is not a general QA request.

Deploy flow:

1. identify payload repos and commits
2. inspect dirty state, local main, remote main, and ahead/behind state
3. exclude unrelated local work unless explicitly included
4. run required gates
5. commit intended changes
6. push only payload repos
7. deploy only payload repos
8. verify live state
9. update `STATUS.md` with final success, final blocker, or exhausted retry
   budget

## Retry Budget

For deploy failures, retry only when the failing command, error output, and fix
are clear. Stop for auth failures, missing permissions, platform outages,
destructive git operations, or unclear product behavior.

## Landing

For cross-repo work, use all-or-hold landing when the adapter defines it. No repo
lands until all affected surfaces pass gates and rebase cleanly. Preserve user
changes and never discard unrelated dirty work without explicit approval. Use
`WORKTREES.md` for cleanup rules before deleting task worktrees or branches.

## Handoff

Recommend a handoff when work crosses a context or ownership boundary, such as:

- blocked work that should resume later
- partial deploy waiting on CI, app store, or cloud processing
- multiple repo branches/worktrees that must not be confused
- another agent, thread, or human taking over
- long context where decisions and next commands may get buried
- review, QA, or deploy owner taking over from implementation owner
