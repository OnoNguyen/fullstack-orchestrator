# Updating The Skill And Project Docs

## Purpose

The orchestrator skill evolves: templates gain sections, conventions change,
directives get added. Two things then fall behind — the installed skill itself,
and a project's already-generated orchestration docs that were rendered from the
old templates. `update`/`upd` is the counter-pressure: a review-first pipeline
that brings the skill current in every install location, reconciles the current
project's docs to the new templates, then grooms the result.

`update` is the only directive that mutates the installed skill, and it does so
only on the user's explicit command, pulling the reviewed, merged remote — never a
self-initiated edit. It is the sanctioned form of the Skill Improvement Loop's
"apply to an installed skill only when the user asks" rule.

## Trigger

- The user gives `update` or `upd` as an explicit standalone command, or says
  something unambiguous like "update the orchestrator skill".
- This is a scoped directive, not a match on the common verb "update". Requests
  that merely contain the word — "update the API docs", "update dependencies",
  "update the task board" — are ordinary project edits and MUST NOT enter this
  pipeline. When intent is ambiguous, ask before starting, because Phase 1 mutates
  installed skill files.
- Recommend (do not run) an update when the installed skill is known to lag its
  remote, or after a new skill release, before starting fresh project work.

## Source Of Truth

- Repo: `git@github.com:OnoNguyen/fullstack-orchestrator.git`
  (https: `https://github.com/OnoNguyen/fullstack-orchestrator.git`).
- Skill subtree within the repo: `fullstack-orchestrator/`.
- Canonical ref: `origin/main` — reviewed and merged only, never a feature branch.
- Install roots are discovered, not assumed: check every skills directory that
  holds a real `fullstack-orchestrator/` copy — commonly `~/.claude/skills/` and
  `~/.agents/skills/`, plus any project-local `.claude/skills/`. A symlinked copy
  shares one source and needs no separate sync.

## Principles

- Review first: write nothing until approved — same discipline as `groom`.
- Reviewed remote only: pull `origin/main`, never local or unmerged work.
- Preserve content: reconciliation migrates structure and policy, never approved
  project content (repo map, slices, glossary).
- Every install root is a target: copies drift independently across roots; sync
  all of them or none, and report which lagged.
- Independent phases: each phase below is separately approvable; the user may take
  the skill pull and decline the doc reconcile, or the reverse.

## Phases

Run in order; gate each on user approval; skip any phase the user declines.

### Phase 1 — Pull the latest skill into every install root

1. Fetch the source repo's `origin/main` (clone to a temp dir, or fetch if a
   local clone already exists).
2. Enumerate install roots holding a real `fullstack-orchestrator/` copy.
3. For each root, diff the incoming subtree against the installed copy; report a
   per-root change summary (files added, removed, changed) in chat.
4. On approval, sync each approved root to match `origin/main` exactly, including
   deletions. Leave declined roots untouched and note the resulting drift.
5. A skill's new behavior loads on restart; on-disk changes are not live in the
   current session.

### Phase 2 — Reconcile the current project's docs to the new templates

1. Compare each generated adapter doc against its updated template and policy:
   new required sections, renamed or removed docs, changed size budgets, and new
   rules (for example the fetch-and-surface worktree policy).
2. Report drift in chat as a table, writing nothing yet:

   | Doc | Upstream change | Proposed migration |
   | --- | --- | --- |

3. Apply only approved rows. Migrations touch scaffolding and policy only — add,
   rename, or split sections and update policy lines — and NEVER rewrite approved
   project content. When a template change would alter content, surface it as a
   note for the user to edit by hand, not an automatic edit.
4. Read templates from disk (freshly synced in Phase 1), not from in-session
   skill behavior.

### Phase 3 — Groom

Run the `groom` procedure as a final lean-up so the reconciled docs stay within
budget and the router stays light. See [grooming.md](grooming.md).

## Action Boundary

- `update` mutates installed skill files only on the explicit `update`/`upd`
  command, only from reviewed `origin/main`, and only after per-root approval.
- Reconciliation and groom touch only the orchestration repo, never implementation
  repos, and never approved project content.
- No writes before the user approves the specific phase or rows.
