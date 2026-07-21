# Project Adapter

## Purpose

The adapter teaches this skill how a specific project is organized without
loading every project rule into precontext. Keep shared orchestration docs in a
dedicated orchestration repo, usually named `<project-slug>-orchestration`.
Keep repo-specific implementation notes inside the implementation repos.
Implementation repos are surfaces only by default.

The adapter has two tiers. Core coordination docs exist in every project:
`AGENTS.md`, `ORCHESTRATION.md`, `TASKS.md`, `WORKTREES.md`, `GLOSSARY.md`,
`SLICES.md`, `DOCUMENTATION_POLICY.md`, `STATUS.md` (plus optional
`SKILL_FEEDBACK.md`). Runbooks are emergent: one pattern-named doc per stack
pattern the project actually has, created on approval — never a fixed set of
stubs.

## AGENTS.md

`AGENTS.md` is the root navigator. It should usually be under 60 lines.

It must contain:

- one sentence describing the orchestrator role
- a trigger table mapping task signals to deeper docs
- default discipline: verify live repo state before mutation, read only
  triggered docs, do not preload everything

It must not contain long runbooks, credentials, full glossary terms, detailed
slice specs, status history, schemas, migrations, or implementation specs.

The trigger table is the adapter's doc manifest. Router integrity is the
contract that replaces a fixed doc list: every adapter doc is routed from
this table, and every routed doc exists. `validate_project_adapter.py`
enforces both directions, which keeps emergent runbooks discoverable.

Recommended trigger rows:

| Trigger | Read |
| --- | --- |
| repo map, aliases, ownership, multi-repo work | `ORCHESTRATION.md` |
| tasks, tsk, task board, continue/abort candidates | `TASKS.md` |
| task branches, worktrees, landing, cleanup | `WORKTREES.md` |
| domain language, user-facing copy, data boundaries | `GLOSSARY.md` |
| feature implementation, behavior change, bug fix, cross-context or external contract | `GLOSSARY.md`, `SLICES.md` |
| slice planning, behavior contracts, BDD, gates, dependencies, merge order | `SLICES.md` |
| current pending state, blockers, landing, deploy state | `STATUS.md` |
| documentation placement or canonical ownership | `DOCUMENTATION_POLICY.md` |
| groom, grm, doc bloat, size budgets | `DOCUMENTATION_POLICY.md` |
| missing skills, stale skills, reusable workflow patterns, skill PRs | `SKILL_FEEDBACK.md` |
| editing an implementation repo | that repo's local instructions |

Add one row per runbook as runbooks are created, e.g. `QA, qa, runtime
evidence | QA.md` or `background jobs, workers, queues | JOBS.md`.

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
- row status labels, including `Needs behavior contract`
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

- lifecycle status: `Proposed`, `Approved`, or `Landed`
- intent
- implementation surfaces
- dependencies
- relevant glossary terms
- 1-3 behavior contracts for every approved user-visible feature, bug fix, or
  cross-context or external contract change
- a stable, unique `BC-*` ID plus `Given / When / Then / Gate` for each
  behavior contract
- durable `Evidence` for every landed behavior contract
- data/privacy/security boundary when relevant
- merge or landing order

Keep a slice `Proposed` while its behavior is being discovered. `Approved`
authorizes implementation and requires complete contracts. `Landed` requires
durable `repo@commit` references. Grooming a landed slice may remove detailed
setup, but must retain every stable behavior-contract ID, its observable
`Then`, named `Gate`, and durable `Evidence`. Never renumber or reuse an ID.
Format evidence as `test|contract|qa|runtime|smoke: <durable locator> |
<successful outcome>` using a commit reference, URL, test selector, runbook
anchor, or artifact path. Use an unambiguously successful terminal outcome such
as `passed`, `verified`, `observed`, `successful`, or `healthy`.
Before implementing or landing a known slice, run the adapter validator with
`--strict --slice "<slice name>"`; global readiness alone can be satisfied by
an unrelated approved or landed slice.

## STATUS.md

Keep current state small. It is not a history log or worker scratchpad. Use it
for pending work, blockers, deploy state, verification state, and next action.

## Runbooks

Runbooks are pattern-named operational docs created only when the stack shows
the pattern: `QA.md`, `DEBUG.md`, `DEPLOY.md`, `JOBS.md`, or a new name for a
new pattern (`MODEL_EVAL.md`, `MIGRATIONS.md`, `DEVICE_QA.md`, ...). A stack
without a pattern gets no stub for it — empty scaffolding is noise the
Operating Rule exists to avoid.

Every runbook follows one contract:

- **Trigger**: the task signals that route here (mirrored in `AGENTS.md`)
- **Preconditions**: approved state required before running
- **Steps**: numbered, verifiable, with exact project-specific commands
- **Evidence**: scan findings or observed surfaces that justify the runbook
- **Rollback / Escape**: how to stop, revert, or safely abandon a failed run

Creation flow: the project scan proposes runbooks from evidence
(`bootstrap_project_adapter.py` writes the approved set via `--runbooks`);
new patterns discovered later go through the same review — propose in chat,
user approves, write the doc from the runbook contract, add its `AGENTS.md`
trigger row. One canonical runbook per pattern; do not fork variants of the
same pattern into multiple docs.

Keep generic doctrine (QA method choice, deploy discipline, retry budgets) in
the orchestrator skill references; runbooks hold only project-specific
commands, gates, and owners.

## SKILL_FEEDBACK.md

`SKILL_FEEDBACK.md` turns hardened project experience — experience from an
orchestration repo whose adapter docs are approved and validated — into
reviewed skill improvements without silently changing the agent. It is a
review surface, not an automatic mutation channel.

Each candidate entry should record:

- observed task or friction
- concrete evidence: repo paths, docs, logs, QA results, issues, or PRs
- affected skill or proposed new skill
- proposed change
- validation gate
- review or PR status

Write policy:

- Draft candidates in chat; append to `SKILL_FEEDBACK.md` only after the user
  approves the entry.
- Do not install, update, or publish skills from this file without explicit
  user approval in the current session.
- Prefer reviewed PRs against the skill source when a remote source exists.

## Documentation Policy

Use `DOCUMENTATION_POLICY.md` to prevent duplicated truth:

- glossary terms live in `GLOSSARY.md`
- topology lives in `ORCHESTRATION.md`
- task-board command policy lives in `TASKS.md`
- slices, behavior contracts, and gates live in `SLICES.md`
- runbooks live in their pattern-named docs, one canonical runbook per pattern
- evidence-backed skill-improvement candidates live in `SKILL_FEEDBACK.md`
- implementation specs, schemas, migrations, and code-level docs live in the
  relevant implementation repo

It also owns the grooming policy for the `groom`/`grm` trigger:

- a Size Budgets table with soft per-doc line budgets, enforced as validator
  warnings (errors with `--strict`); missing approved or landed behavior
  contracts also warn and become errors with `--strict`
- report-first grooming: propose findings in chat, apply only approved moves
- archive over delete: stale content moves to `archive/` under date-stamped
  names; `AGENTS.md` must never route into `archive/`

The groom procedure and bloat patterns live in
[grooming.md](grooming.md).
