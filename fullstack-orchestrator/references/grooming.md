# Grooming The Orchestration Repo

## Purpose

Orchestration docs rot toward bloat: status history piles up, landed slices
keep full specs, runbooks absorb one-off incident notes. Bloat is a precontext
tax paid on every future task. `groom`/`grm` is the counter-pressure: a
review-first audit that keeps `AGENTS.md` a lightweight router and the rest of
the adapter a lazy-loading tree of small, single-owner docs.

## Trigger

- The user says `groom` or `grm`.
- Recommend (do not run) a groom when the validator reports budget warnings,
  after a slice or milestone lands, or before a handoff.

## Principles

- Router, not manual: `AGENTS.md` holds one-line trigger rows only. Prose that
  changes behavior belongs in the leaf doc that owns the trigger.
- Lazy tree: hub docs route, leaf docs act. Content needed by only one trigger
  lives in that trigger's doc, not in a hub.
- One truth, one home: the same fact stated in two docs is a bug. Keep the
  canonical copy per `DOCUMENTATION_POLICY.md` ownership; replace the rest
  with a one-line pointer.
- Archive over delete: move stale content to `archive/` in the orchestration
  repo under date-stamped names such as `archive/STATUS-2026-07.md`. Deletion
  needs explicit approval. Never route `archive/` from `AGENTS.md`.
- Verify before pruning: a repo, branch, worktree, or slice reference is stale
  only after checking live state, per the Operating Rule.
- Budgets, not vibes: judge size against the budgets in
  `DOCUMENTATION_POLICY.md`, measured by the validator.

## Procedure

1. Measure: run `scripts/validate_project_adapter.py` on the orchestration
   repo; note total adapter lines, per-doc budget violations, and routing
   warnings.
2. Diagnose: read only over-budget or flagged docs; classify findings with the
   bloat patterns below; cross-check suspected stale references against live
   git and filesystem state.
3. Report in chat, writing nothing:

   | Doc | Lines / budget | Finding | Proposed move |
   | --- | --- | --- | --- |

4. Apply only approved rows, section by section. Prefer moves (demote to leaf
   doc, merge into canonical owner, archive) over rewrites.
5. Re-run the validator and report before/after totals.

## Bloat Patterns

| Doc | Common rot | Groom move |
| --- | --- | --- |
| `AGENTS.md` | runbook steps or policy prose creep into the router | demote to the owning leaf doc; keep rows one line |
| `STATUS.md` | history log accretes | trim to current state; archive the rest |
| `TASKS.md` | becomes a backlog of stored tasks | keep command policy only; tasks live in live state |
| `SLICES.md` | landed slices keep full setup detail | compact each landed slice while preserving its stable behavior-contract IDs, observable outcomes, gate evidence, and landing commits |
| `GLOSSARY.md` | implementation detail creeps in | move detail to the implementation repo |
| `QA.md`, `DEBUG.md`, `DEPLOY.md` | one-off incident notes accumulate | keep repeatable steps; archive incident notes |
| `ORCHESTRATION.md` | dead repos, renamed branches | verify live state, then prune |
| `SKILL_FEEDBACK.md` | shipped or rejected candidates linger | archive resolved candidates |

## Action Boundary

- Groom touches only the orchestration repo, never implementation repos.
- No writes before the user approves the report or specific rows.
- Friction caused by this skill itself becomes a `SKILL_FEEDBACK.md`
  candidate, not an inline skill edit.
- Never groom away stable behavior-contract IDs or the gate evidence that
  preserves traceability from promised behavior to verification.
