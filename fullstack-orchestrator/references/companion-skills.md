# Companion Skills

## Principle

Recommend companion skills from what the stack needs, not from a shipped
inventory. Skill names and marketplaces change faster than this skill
releases, so a bundled catalog can only decay; capability categories are the
stable knowledge. This skill therefore ships the category taxonomy and
resolves actual skill names live.

## Resolution Order

1. **Session-installed skills.** The agent can see which skills are actually
   available in the current session. Match detected categories against that
   list first — never recommend installing something already present, and
   never assume something absent is installed.
2. **Project-supplied manifest.** Teams may curate their own inventory in the
   orchestration repo and pass it to `scripts/recommend_skills.py --manifest`.
   This is the one legitimately static source, because the team maintains it.
3. **Public catalogs.** Search skills.sh or marketplace listings only when the
   user asks for install suggestions. Print install commands only from a
   verified source or the project manifest.

Never install, update, or enable a skill without explicit user approval.
Prefer well-known publishers when suggesting from public catalogs, and say
when a suggestion is unvetted.

When a detected category has no installed or discoverable skill that fits,
that gap is a `SKILL_FEEDBACK.md` candidate: record the category, the
evidence, and what a fitting skill would do.

## Category Taxonomy

`scripts/recommend_skills.py` detects these categories from repo evidence:

- **core** (every project): git workflow, planning and task breakdown, code
  review, test-driven development, documentation/ADR capture.
- **frontend** (UI, mobile, browser, CSS, accessibility surfaces): UI
  engineering, browser/device runtime QA, performance optimization,
  prototyping.
- **backend** (API, service, auth, database, queue, schema surfaces): API and
  interface design, security hardening, debugging and diagnosis,
  source-grounded framework work.
- **delivery** (CI, deploy, release, cloud, packaging surfaces): CI/CD
  automation, shipping and launch, GitHub workflow, incremental landing.
- **planning** (ambiguous, strategic, architecture-heavy work): spec writing,
  idea refinement, requirement interviews, adversarial design review,
  architecture improvement.
- **handoff** (work-item and ownership boundaries): triage, PRD/issue
  conversion, agent-to-agent handoff, skill discovery.

## Project Manifest Schema

A project manifest is JSON with a `skills` list; each entry may set `name`,
`category` (one of the taxonomy categories), `priority` (high/medium/low),
`when`, `notes`, and `install_command`. Multiple `--manifest` files merge by
name, later files winning.
