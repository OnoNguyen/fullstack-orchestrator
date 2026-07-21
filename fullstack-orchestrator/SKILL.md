---
name: fullstack-orchestrator
description: Compose reviewed product behavior into domain-aligned vertical slices and acceptance gates, conduct full-stack delivery across one repo, a monorepo, or multiple repositories, and verify every gate with live evidence. Use when bootstrapping project orchestration; onboarding or scanning user-provided codebases; defining domain language, boundaries, slices, behavior contracts, or BDD acceptance scenarios; planning or implementing user-visible features; fixing bugs; changing cross-context or external contracts; coordinating frontend, backend, infrastructure, or companion-skill work; producing tasks/tsk boards; routing through AGENTS.md; managing worktrees, QA, debug, local install, deploy, landing, or handoff; grooming orchestration docs with groom/grm; reconciling the installed skill and project adapter with explicit update/upd; recording skill feedback; or recommending companion skills.
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

Core docs every project gets:

- `AGENTS.md`: root navigator and trigger router; its table is the doc
  manifest — every adapter doc is routed there, and every routed doc exists.
- `ORCHESTRATION.md`: approved repo map, aliases, roles, remotes, branches,
  and ownership.
- `WORKTREES.md`: task checkout/worktree policy, canonical pickup points,
  landing, and cleanup.
- `TASKS.md`: `tasks`/`tsk` board policy and action classification.
- `GLOSSARY.md`: approved domain language and boundary terms.
- `SLICES.md`: approved vertical slices, surfaces, dependencies, behavior
  contracts, gates, and merge order.
- `DOCUMENTATION_POLICY.md`: canonical doc ownership, anti-duplication rules,
  doc size budgets, and grooming policy.
- `STATUS.md`: coordinator-owned current state, not worker scratchpad.
- `SKILL_FEEDBACK.md` (optional): evidence-backed missing-skill, stale-skill,
  and reusable-pattern candidates that may become reviewed skill PRs.

Runbooks are emergent, not predefined: one pattern-named doc per stack
pattern the project actually shows (`QA.md`, `DEBUG.md`, `DEPLOY.md`,
`JOBS.md`, or a new name for a new pattern), proposed from scan evidence,
written only after user approval, and routed in `AGENTS.md`. A stack without
a pattern gets no stub for it.

See [project-adapter.md](references/project-adapter.md) for doc contracts,
the runbook contract, and templates.

## Core Role

Compose, Conduct, Verify.

### Compose

Define work as product behavior before dividing it by repository. Clarify
domain terms, bounded contexts, ownership, and handoffs in `GLOSSARY.md` and
`SLICES.md`. Express behavior as vertical slices with explicit acceptance
gates. Treat the model as a routing hypothesis until live evidence confirms it.

### Conduct

Route each slice across the required implementation surfaces, agents, and
companion skills. Make dependencies, owners, worktree policy, gates, and
landing order explicit. Keep the slice, not a repository or specialist, as the
unit of coordination.

### Verify

Name the evidence required for every gate before execution. Collect and report
evidence for each gate before declaring completion. Use the project-approved
proof that fits the risk: automated tests, contract checks, runtime QA, observed
logs or metrics, deploy smoke, or another observable result. Report unverified
gates and blockers instead of inferring success.

### Behavior Contract

Apply this contract to every user-visible feature or behavior change, bug fix,
and cross-context or external contract change:

1. Find the approved slice and its behavior contracts. If none covers the
   change, draft 1-3 business-readable `Given / When / Then` scenarios in chat
   before coding and give each a stable `BC-*` ID.
2. Map each scenario to a named verification gate and state the evidence that
   will prove it.
3. Resolve contradictions between the scenario, glossary, slice, plan, and
   live system before coding. Write approved model changes to `GLOSSARY.md` or
   `SLICES.md`; do not write unapproved findings as canonical facts.
4. Implement against the scenarios, run every applicable gate, and report the
   evidence for each gate.
5. Do not declare the behavior complete while a required gate lacks evidence;
   report the gap or blocker.

Do not pause merely to approve wording when the user's requested behavior is
clear; use the draft as the working contract and ask only when it exposes a
material product decision. Exempt a task only when it has no intended or
plausible user-visible, cross-context, or external contract effect. State the
reason for the exemption and still run the applicable non-behavior gates. Never
exempt a bug fix merely because it is small. The canonical contract lives in
[project-adapter.md](references/project-adapter.md).

## Onboarding Discipline

Scan only user-provided local paths or URLs. Keep unreviewed findings in chat,
not canonical docs. Ask the user to create or confirm a dedicated orchestration
repo, then approve findings section by section before writing docs: repo map,
worktree policy, task-board policy, glossary, slices and behavior contracts,
runbook proposals.

Use scripts as evidence collectors and validators, not as authority:

- `scripts/bootstrap_project_adapter.py`: scan user-provided seeds and, after
  approval, write adapter docs.
- `scripts/validate_project_adapter.py`: check adapter docs for required
  structure, doc size budgets, and low-precontext routing.
- `scripts/recommend_skills.py`: detect companion-skill categories from stack
  evidence; skill names resolve live per the Companion Skills section.

## Work Execution

- Before implementation, classify the task as behavior-contract required or
  exempt. For required work, load the relevant `GLOSSARY.md` and `SLICES.md`,
  then reuse or draft the contract before editing implementation surfaces. If
  the adapter validator is available, run it with `--strict --slice "<name>"`
  before coding so unrelated landed slices cannot mask a proposed target.
- Work slice first, repo second: repos are implementation surfaces, not the
  product slice itself.
- When the user says `tasks` or `tsk`, load `TASKS.md` and produce an
  actionable-only board before recommending continuations. Surface behavior
  work with no approved contract as `Needs behavior contract`.
- When the user says `groom` or `grm`, audit the orchestration repo for doc
  bloat and produce a review-first groom report before editing any doc. See
  [grooming.md](references/grooming.md).
- When the user gives `update` or `upd` as an explicit standalone command (or an
  unambiguous phrase like "update the orchestrator skill"), run the review-first
  update pipeline: pull the latest skill from its remote into every install root,
  reconcile the current project's docs to the new templates (scaffolding and
  policy only), then groom. This is a scoped skill directive, not a match on the
  common verb: ordinary requests that merely contain "update" ("update the API
  docs", "update dependencies", "update the board") are normal project edits and
  must not enter this pipeline. If intent is ambiguous, ask before starting — this
  path can mutate installed skill files. See [updating.md](references/updating.md).
- Prefer temporary task branches/worktrees when the project adapter defines
  them; fetch and reconcile against the remote before basing task work — base on
  the remote canonical branch when local is behind, and surface divergence
  instead of silently starting from a stale or mismatched base.
- For cross-repo changes, use all-or-hold landing: no repo lands until every
  affected surface rebases cleanly and every behavior gate has evidence.
- After successful landing, close the `SLICES.md` ledger: set `Status: Landed`,
  record `Landed at` repo commits and durable `Evidence` for every `BC-*`, then
  rerun targeted strict validation before reporting completion.
- Use [worktrees-and-landing.md](references/worktrees-and-landing.md) when a
  task may dirty multiple repos, needs runtime QA, or involves landing/cleanup.
- Do not deploy unless the user explicitly says `deploy`, `dpl`, or the
  project adapter defines an equivalent deploy trigger.
- Treat a standalone `install` / `ins` command as local app-install authority
  only when the project adapter defines an install runbook. It does not
  authorize source publication, artifact distribution, deployment, or release.
  Build the project-defined durable app variant, install it on the resolved
  target, and read the installed identity back.
- Use [qa-debug-deploy.md](references/qa-debug-deploy.md) when QA, debug,
  runtime evidence, local app install, deploy, retry, or release state is
  involved.

## Skill Improvement Loop

`SKILL_FEEDBACK.md` turns experience from an approved, validated orchestration
repo into reviewed skill improvements; skills never mutate themselves. When a
task surfaces repeated workflow friction, a missing companion skill, or stale
skill behavior, draft an evidence-backed candidate in chat and append it to
`SKILL_FEEDBACK.md` only after the user approves the entry. Apply a candidate
to an installed skill only when the user asks for it in the current session —
even if an upstream skill PR has already merged — validate the result (rerun
the skill's bundled validators, or confirm the updated skill still triggers
on a representative prompt without executing side effects), and prefer a
reviewed PR against the skill source when a remote exists. The candidate entry
shape and rules live in the SKILL_FEEDBACK contract in
[project-adapter.md](references/project-adapter.md). The `update`/`upd` directive
is the sanctioned path for pulling merged upstream improvements back into every
installed copy; see [updating.md](references/updating.md).

## Companion Skills

Detect capability categories from stack evidence
(`scripts/recommend_skills.py`), then resolve skill names live rather than
from a bundled catalog: check the skills actually installed in the session
first, then a project-supplied manifest, and search public catalogs only when
the user asks for install suggestions. Never install without approval; record
gaps no live source can fill as `SKILL_FEEDBACK.md` candidates. See
[companion-skills.md](references/companion-skills.md).

Keep the behavior contract coordinator-owned when delegating test mechanics to
a TDD, QA, or specialist companion skill. The companion proves a gate; it does
not redefine the promised behavior silently.
