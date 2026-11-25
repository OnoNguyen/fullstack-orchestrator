# Fullstack Orchestrator

[![skills.sh](https://skills.sh/b/OnoNguyen/fullstack-orchestrator)](https://skills.sh/OnoNguyen/fullstack-orchestrator)

An Agent Skill that composes product behavior, conducts full-stack delivery
across one repo, a monorepo, or multiple repositories, and verifies every gate
with live evidence.

It scans user-provided project surfaces, bootstraps a small adapter in a
dedicated orchestration repo, and turns user-visible changes into reviewed
behavior contracts before coordinating delivery, verification, landing, and
handoff.

## Install

```bash
npx skills add OnoNguyen/fullstack-orchestrator
```

## Run It Against Your Repo

In your agent, invoke the skill with the path to one repo of your stack:

```text
/fullstack-orchestrator /path/to/my-app
```

The agent scans the stack and shows its findings in chat. Once you approve
them, it creates a `<my-stack>-orchestration` folder next to your repos holding
the stack's vertical slices with their behavior contracts, plus the
fundamentals to fly on: repo map, glossary, worktree policy, and runbooks. Your
implementation repos stay untouched.

Run future sessions from the `<my-stack>-orchestration` folder, or invoke
`/fullstack-orchestrator` again from anywhere.

## Commands

Say these to the agent; they are prompts, not shell commands.

| Command | Result |
| --- | --- |
| `groom` / `grm` | Audit orchestration docs and propose cleanup before editing. |
| `update` / `upd` | As a standalone request, update the orchestrator skill, reconcile adapter scaffolding, then groom. |

## What It Creates

After a project scan and user review, the skill can write a project adapter into
a dedicated orchestration repo. Implementation repos stay as surfaces only:

- `AGENTS.md`: short root navigator and trigger router
- `ORCHESTRATION.md`: repo map, aliases, roles, ownership, branches
- `WORKTREES.md`: task branches/worktrees, pickup points, landing, cleanup
- `GLOSSARY.md`: canonical domain language
- `SLICES.md`: vertical slices, stable behavior contracts, gates, and merge
  order
- `DOCUMENTATION_POLICY.md`: placement rules, size budgets, grooming policy
- `SKILL_FEEDBACK.md`: reviewed skill-improvement candidates (skills never
  self-mutate)
- Pattern runbooks (`QA.md`, `DEBUG.md`, `DEPLOY.md`, `JOBS.md`, or new
  pattern names): proposed from scan evidence, written only for patterns the
  stack actually shows, each routed from `AGENTS.md`

Task progress stays in sessions, not in adapter docs.

## Project Scan First

By default, discovery prints compact project scan findings and writes nothing:

```bash
python3 fullstack-orchestrator/scripts/bootstrap_project_adapter.py /path/to/app /path/to/api
```

After reviewing the findings, write adapter docs:

```bash
mkdir -p /path/to/my-project-orchestration
python3 fullstack-orchestrator/scripts/bootstrap_project_adapter.py /path/to/app /path/to/api \
  --coordinator /path/to/my-project-orchestration \
  --worktree-root /path/to/wt-tasks/my-project \
  --project-name "My Project" \
  --write
```

Validate the adapter:

```bash
python3 fullstack-orchestrator/scripts/validate_project_adapter.py /path/to/orchestration
```

Use `--strict --slice "<slice name>"` before implementation or landing to
require that specific slice to have an approved or landed behavior contract and
enforce complete scenario clauses.

Detect companion-skill categories (names resolve live against installed
skills and optional project manifests — no bundled inventory):

```bash
python3 fullstack-orchestrator/scripts/recommend_skills.py --project /path/to/orchestration /path/to/app /path/to/api
```

## Safety Model

- Scans only user-provided local paths or URLs.
- Does not clone/fetch remote URLs unless explicitly run with clone approval.
- Keeps unreviewed findings in chat/project scan output, not canonical docs.
- Treats generated docs as routing hints until verified against live repo state.
- Deploy remains explicit only.

## License

MIT
