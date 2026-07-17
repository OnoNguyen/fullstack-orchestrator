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

### Simulator Pool And Memory Preflight

Before any Apple simulator QA session creates, boots, or reuses a device:

- inspect `xcrun simctl list devices -j`, memory pressure, swap activity,
  simulator processes, task helpers, and relevant listening ports
- treat available devices with a non-null `lastBootedAt` as the persistent
  simulator pool; never-booted Xcode device definitions are not pool members
- treat the default CoreSimulator device set as one host-wide pool shared by
  all local orchestration repos, cap it at four devices, and reuse a compatible
  inactive member before creating another device
- count a simulator as owned only when a live external task process or recent
  task terminal backs it; an app or system process running inside the simulator
  is not ownership evidence
- if compatibility requires a different device or runtime while the pool is
  full, shut down and delete the least-recently booted inactive member, then
  create its replacement; never delete an actively owned member
- if preflight finds more than four pool members, use
  `xcrun simctl delete <UDID>` on least-recently booted inactive members until
  four remain; defer owned members to the normal wait rule
- if all four members are owned, do not create a fifth device; recheck every
  five minutes for up to 30 minutes, then report the owners and stop

Parallel simulators are allowed only when `memory_pressure` reports at least
25% free, `Pages throttled` is `0`, and swapouts are not rapidly increasing.
If memory is blocked, prefer shutting down a clearly idle simulator and its
stale task helpers. Recheck memory every 60 seconds for up to five minutes;
then report the blocking processes and stop. Do not use `simctl shutdown all`
or kill low-RSS CoreSimulator services while a live task owns a simulator.

Simulator QA evidence must record the pool members and owners observed, reuse
or LRU replacement performed, memory result, and any task that exhausted its
wait budget.

## Debug

Debug requests may use dirty state only when the project adapter allows it and
only inside the task checkout/worktree it owns. Read `WORKTREES.md` when task
checkout ownership is unclear.

Before starting local runtimes:

- inspect active dev servers and ports
- avoid interrupting unrelated sessions
- prefer the current task checkout over canonical main
- report how the runtime was attached and how success was proven

## Local App Install

A project-defined standalone `install` / `ins` command may authorize a local app
install when the adapter routes that trigger to an install runbook. This lane is
separate from debug, QA, deployment, distribution, and release.

- Resolve the project, app variant, and target unambiguously before building.
- Default to the latest committed local canonical branch. Include a task
  checkout or dirty state only when the user explicitly selects it.
- Build the project-defined durable, self-contained configuration. It must not
  depend on a task-scoped development server or live development session.
- Verify the expected name, installed identity, environment, integrity, and
  target compatibility before installation.
- Install with supported platform tooling, then read the exact installed
  identity back from the target. Build success alone is not install success.
- Do not launch the app unless requested. Installation can therefore complete
  without the user opening or interacting with the target.
- Never bypass platform security, trust, signing, provisioning, or management
  controls. Report the exact one-time user action if the platform blocks an
  unattended install.
- Keep tracked preparation in the project-defined task worktree. Never commit
  generated build products or tool caches.
- Report whether the installed variant coexists with or replaces another app
  identity, plus any expiry that limits how long it remains launchable.

`install` never implies source publication, remote build execution, artifact
distribution, deployment, or release.

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
