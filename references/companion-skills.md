# Companion Skills

## Principle

This skill recommends companion skills but does not bundle them or assume they
are installed. Print install commands only when a public source is verified or
the project supplies an override manifest with an install source.

Use the public catalog in `assets/companion-skills.json` as defaults. Teams may
add their own manifest in the coordinator repo and pass it to
`scripts/recommend_skills.py --manifest`.

## Core Orchestration

Recommend for most projects:

- `git-workflow-and-versioning`
- `context-engineering`
- `planning-and-task-breakdown`
- `documentation-and-adrs`
- `code-review-and-quality`
- `test-driven-development`

## Frontend And Product UI

Recommend when scanning frontend, mobile, design-system, browser, CSS, canvas,
accessibility, or product UI surfaces:

- `frontend-ui-engineering`
- `browser-testing-with-devtools`
- `performance-optimization`
- `prototype`
- `vocabulary`

## Backend And API

Recommend when scanning API, service, auth, database, queue, schema, worker, or
integration surfaces:

- `api-and-interface-design`
- `security-and-hardening`
- `source-driven-development`
- `debugging-and-error-recovery`
- `diagnose`

## Delivery And Ops

Recommend when scanning CI, deploy, release, cloud, packaging, infra, GitHub, or
workflow automation:

- `ci-cd-and-automation`
- `shipping-and-launch`
- `github`
- `incremental-implementation`

## Planning And Product Thinking

Recommend when work is ambiguous, strategic, cross-domain, architecture-heavy,
or needs sharper product/domain language:

- `spec-driven-development`
- `idea-refine`
- `interview-me`
- `grill-with-docs`
- `doubt-driven-development`
- `improve-codebase-architecture`

## Issue And Handoff Work

Recommend when turning plans into work items, triaging queues, preparing another
agent, or preserving state:

- `triage`
- `to-prd`
- `to-issues`
- `handoff`
- `find-skills`
