# Worktrees And Landing

Use this reference when a task may dirty implementation repos, run codegen,
require runtime QA, span repos, or land/push changes.

## Core Model

- The orchestration repo owns shared policy and current coordination state.
- Implementation repos are surfaces. Do not put project-wide worktree policy in
  app, API, web, worker, or infra repos.
- Canonical local branches are clean pickup points unless the adapter says
  otherwise.
- Mutable work should happen on a task branch or task worktree when edits may
  conflict with other local work or need isolated runtime QA.

## Project Policy

During project scan, ask the user to approve:

- canonical branch per implementation repo
- task worktree root, for example `<common-parent>/wt-tasks/<project-slug>`
- branch naming convention, for example `task/<short-slice>`
- when worktrees are required versus optional
- whether cross-repo landing is all-or-hold
- cleanup rule for merged task worktrees and stale branches

Record approved answers in `WORKTREES.md`.

## Start Checklist

Before editing a repo:

1. Read the root navigator and only the triggered deeper docs.
2. Inspect live repo path, active branch, dirty state, ahead/behind state, and
   local repo instructions.
3. Create or reuse a task checkout/worktree when the task meets the project
   threshold.
4. Preserve unrelated dirty files and user changes.
5. Keep runtime processes attached to the task checkout/worktree that owns them.

## Cross-Repo Work

For a vertical slice spanning multiple repos:

- use one task branch name across affected repos when practical
- record surface list and merge order in `SLICES.md`
- keep each repo independently testable
- do not land any repo until all affected repos pass their gates
- report partial blockers with exact repo, branch/worktree, command, and status

Use `TASKS.md` when the user asks for a task board rather than immediate
implementation or landing.

## Landing And Cleanup

Default landing policy is all-or-hold for cross-repo changes:

1. Rebase or merge each task branch onto its canonical pickup branch.
2. Run required gates in every affected repo.
3. Land repos in the order approved by `SLICES.md` or `WORKTREES.md`.
4. Push only the intended payload repos.
5. Remove merged task worktrees and stale task branches only after successful
   landing, unless the user asks to preserve them.

Never discard unrelated work or delete an unmerged worktree without explicit
approval.
