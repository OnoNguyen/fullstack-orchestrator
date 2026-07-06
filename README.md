# Fullstack Orchestrator

[![skills.sh](https://skills.sh/b/OnoNguyen/fullstack-orchestrator)](https://skills.sh/OnoNguyen/fullstack-orchestrator)

An Agent Skill for reviewed full-stack project orchestration across one repo, a
monorepo, or multiple repositories.

The skill runs a project scan, bootstraps a small project adapter in a dedicated
orchestration repo, keeps `AGENTS.md` as a lazy root navigator, records approved
repo topology and domain language, proposes vertical slices from evidence, and
coordinates task boards, QA, debug, deploy, landing, and handoff.

## Install

```bash
npx skills add OnoNguyen/fullstack-orchestrator
```

## What It Creates

After a project scan and user review, the skill can write a project adapter into
a dedicated orchestration repo. Implementation repos stay as surfaces only:

- `AGENTS.md`: short root navigator and trigger router
- `ORCHESTRATION.md`: repo map, aliases, roles, ownership, branches
- `TASKS.md`: `tasks`/`tsk` board policy and action boundaries
- `WORKTREES.md`: task branches/worktrees, pickup points, landing, cleanup
- `GLOSSARY.md`: canonical domain language
- `SLICES.md`: vertical slices, surfaces, BDD acceptance scenarios, gates,
  merge order
- `QA.md`, `DEBUG.md`, `DEPLOY.md`: project-specific runbooks
- `DOCUMENTATION_POLICY.md`: doc ownership
- `STATUS.md`: current state
- `SKILL_FEEDBACK.md`: reviewed skill-improvement candidates (skills never
  self-mutate)

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

Recommend companion skills:

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
