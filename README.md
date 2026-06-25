# Fullstack Orchestrator

[![skills.sh](https://skills.sh/b/OnoNguyen/fullstack-orchestrator)](https://skills.sh/OnoNguyen/fullstack-orchestrator)

An Agent Skill for audited full-stack project orchestration across one repo, a
monorepo, or multiple repositories.

The skill bootstraps a small project adapter, keeps `AGENTS.md` as a lazy root
navigator, records approved repo topology and domain language, proposes vertical
slices from evidence, and coordinates QA, debug, deploy, landing, and handoff.

## Install

```bash
npx skills add OnoNguyen/fullstack-orchestrator
```

## What It Creates

After an audit and user review, the skill can write a project adapter into a
chosen coordinator repo:

- `AGENTS.md`: short root navigator and trigger router
- `ORCHESTRATION.md`: repo map, aliases, roles, ownership, branches
- `GLOSSARY.md`: canonical domain language
- `SLICES.md`: vertical slices, surfaces, gates, merge order
- `QA.md`, `DEBUG.md`, `DEPLOY.md`: project-specific runbooks
- `DOCUMENTATION_POLICY.md`: doc ownership
- `STATUS.md`: current state

## Audit First

By default, discovery prints a compact audit report and writes nothing:

```bash
python3 fullstack-orchestrator/scripts/bootstrap_project_adapter.py /path/to/app /path/to/api
```

After reviewing the findings, write adapter docs:

```bash
python3 fullstack-orchestrator/scripts/bootstrap_project_adapter.py /path/to/app /path/to/api \
  --coordinator /path/to/orchestration \
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
- Keeps unreviewed findings in chat/audit output, not canonical docs.
- Treats generated docs as routing hints until verified against live repo state.
- Deploy remains explicit only.

## License

MIT
