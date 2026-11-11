---
name: fullstack-orchestrator
description: Turn product behavior into domain-aligned vertical slices with BDD behavior contracts and acceptance gates, coordinate full-stack delivery across one repo, a monorepo, or many repos, and verify every gate with live evidence. Use when bootstrapping or scanning a project for orchestration; defining glossary, slices, or Given/When/Then contracts; planning or implementing features, bug fixes, or cross-context contract changes; coordinating frontend, backend, infra, or companion skills; worktrees, QA, debug, install, deploy, or landing; or the tasks/tsk, groom/grm, and update/upd commands.
---

# Fullstack Orchestrator

## Operating Rule

Treat project maps, generated docs, and prior summaries as routing hints until
verified against live filesystem, git, test, CI, and deploy state. Read only the
smallest project docs and skill references the current trigger needs.

## Commands

These are user prompts, not shell commands.

| Command | Result |
| --- | --- |
| `tasks` / `tsk` | Load `TASKS.md` and produce a verified, actionable-only board. |
| `groom` / `grm` | Audit orchestration docs and report proposed cleanup before editing. Follow [grooming.md](references/grooming.md). |
| `update` / `upd` | Only as a standalone or unambiguous request to update the orchestrator skill: review and sync installed copies, reconcile adapter scaffolding and policy, then groom. Follow [updating.md](references/updating.md). |

## Reference Map

Load a reference only when its trigger applies.

| Trigger | Read |
| --- | --- |
| no project adapter yet, onboarding, scanning seeds | [project-scan.md](references/project-scan.md) |
| adapter doc contracts, runbooks, `SKILL_FEEDBACK.md`, templates | [project-adapter.md](references/project-adapter.md) |
| task may dirty repos, span repos, need runtime QA, land, or clean up | [worktrees-and-landing.md](references/worktrees-and-landing.md) |
| QA, debug, runtime evidence, local install, deploy, retry, release | [qa-debug-deploy.md](references/qa-debug-deploy.md) |
| companion-skill recommendations or gaps | [companion-skills.md](references/companion-skills.md) |
| `groom` / `grm` | [grooming.md](references/grooming.md) |
| `update` / `upd` | [updating.md](references/updating.md) |

## First Moves

- If `AGENTS.md` exists, read it first as the root navigator, then load only the
  deeper docs it routes to. If no adapter exists, run a review-only project
  scan.
- For multi-repo or monorepo work, resolve the live implementation surfaces
  before planning edits.
- Before mutation, inspect cleanliness and local instructions in every repo
  that may be edited, tested, landed, pushed, or deployed.

## Project Adapter

The adapter is a set of small markdown docs in a dedicated orchestration repo,
`<project-slug>-orchestration` by default. Implementation repos are surfaces
only unless the user explicitly overrides that boundary.

Core docs: `AGENTS.md` (navigator; its trigger table is the doc manifest),
`ORCHESTRATION.md`, `WORKTREES.md`, `TASKS.md`, `GLOSSARY.md`, `SLICES.md`,
`DOCUMENTATION_POLICY.md`, and optional `SKILL_FEEDBACK.md`. Runbooks
(`QA.md`, `DEPLOY.md`, `JOBS.md`, ...) are emergent: one per stack pattern the
scan actually shows, written only after approval, never stubbed. Task progress
lives in sessions; boards are built on demand and checked against live
evidence. Doc contracts live in
[project-adapter.md](references/project-adapter.md).

## Core Role

Compose, Conduct, Verify.

- **Compose**: define work as product behavior before dividing it by repo.
  Keep domain terms, boundaries, and handoffs in `GLOSSARY.md` and
  `SLICES.md`; treat the model as a hypothesis until live evidence confirms it.
- **Conduct**: route each slice across surfaces, agents, and companion skills
  with explicit dependencies, owners, worktree policy, gates, and landing
  order. The slice, not a repo or specialist, is the unit of coordination.
- **Verify**: name the evidence for every gate before execution, using the
  project-approved proof that fits the risk (tests, contract checks, runtime
  QA, logs or metrics, deploy smoke). Report unverified gates and blockers
  instead of inferring success.

### Behavior Contract

Required for every user-visible feature or behavior change, bug fix, and
cross-context or external contract change:

1. Reuse the approved slice's contracts. If none covers the change, draft 1-3
   business-readable `Given / When / Then` scenarios in chat before coding,
   each with a stable `BC-*` ID.
2. Map each scenario to a named gate and the evidence that will prove it.
3. Resolve contradictions between scenario, glossary, slice, plan, and live
   system before coding. Write only approved model changes to `GLOSSARY.md` or
   `SLICES.md`.
4. Implement against the scenarios and run every applicable gate.
5. Do not declare completion until evidence is reported for each gate; report
   any gap or blocker instead.

Do not pause just to approve wording when the requested behavior is clear;
ask only when the draft exposes a material product decision. Exempt a task only
when it has no plausible user-visible, cross-context, or external contract
effect; state why and still run the non-behavior gates. Never exempt a bug fix
because it is small.

## Onboarding Discipline

Scan only user-provided local paths or URLs. Keep unreviewed findings in chat.
Have the user create or confirm the orchestration repo, then approve findings
section by section before writing: repo map, worktree policy, task-board
policy, glossary, slices and contracts, runbook proposals.

Scripts collect evidence and validate; they are not authority:

- `scripts/bootstrap_project_adapter.py`: scan seeds; after approval, write docs.
- `scripts/validate_project_adapter.py`: check structure, size budgets, routing.
- `scripts/recommend_skills.py`: detect companion-skill categories.

## Work Execution

- Classify the task as contract-required or exempt. For required work, load
  `GLOSSARY.md` and `SLICES.md` and run
  `validate_project_adapter.py --strict --slice "<name>"` before coding.
- Work slice first, repo second. Fetch before basing task branches or
  worktrees; base on the remote canonical branch when local is behind and
  surface divergence instead of starting from a stale base.
- Cross-repo changes land all-or-hold. After landing, close the `SLICES.md`
  ledger (`Status: Landed`, `Landed at`, `Evidence` per `BC-*`) and rerun
  strict validation.
- Do not deploy unless the user says `deploy`, `dpl`, or an adapter-defined
  equivalent.
- A standalone `install` / `ins` authorizes only a local app install, and only
  when the adapter defines an install runbook — never publication, release, or
  deploy. Read the installed identity back.

## Skill Improvement Loop

Skills never mutate themselves. When work surfaces repeated friction, a missing
companion skill, or stale skill behavior, draft an evidence-backed candidate in
chat and append it to `SKILL_FEEDBACK.md` only after approval. Apply a
candidate to an installed skill only when the user asks in the current session,
validate the result (rerun bundled validators), and prefer a reviewed PR against
the skill source.
`update` / `upd` is the sanctioned path for pulling merged improvements into
installed copies.

## Companion Skills

Detect categories with `scripts/recommend_skills.py`, then resolve names live:
session-installed skills first, then a project manifest, and public catalogs
only when the user asks. Never install without approval. Delegated companions
prove gates; they do not redefine the coordinator-owned behavior contract.

## Communication

Write like a teammate reporting real work: specific, and no stronger than the
evidence. Keep facts, decisions, changes, open questions, and blockers
distinct. Skip praise and reassurance; hedge only real uncertainty.

End with a short plain-language bullet summary (under 300 words) answering
whichever apply: What did you do? What does it mean for me? How did you check
it? Is anything left for me to do?
