# Sid Skills & AI Guidelines

A personal collection of practical guidelines, workflows, and reusable skills for AI-assisted software development.

---

## 1. [Guidelines for Humans (HUMANS.md)](HUMANS.md)

Real-world reflections on working with AI coding agents, focusing on the human bottleneck: where attention is best spent, how to fight review fatigue, and how to stay in control of the codebase.

- **Risks & Mitigations**: Planning spirals, plan drift, review fatigue, and gating dependencies
- **Parallel Worktrees**: Running multi-agent streams without hitting review bottlenecks
- **Secrets & Sandboxing**: Practical isolation tiers (built-in, container, remote)
- **Project Lifecycle**: Shifting gates from *Discovery* (speed) to *Buildout* to *Production* (safety)
- **Hierarchy of Verification**: Five levels of review responsibility (CI ➔ Architecture ➔ Functionality ➔ Scope ➔ Intent)
- **Testing with Confidence**: Spotting test theatre, edge-only mocking, and verifying tests can fail

---

## 2. [Skills](skills/README.md)

Modular instruction sets conforming to the [Agent Skills specification](https://agentskills.io/) and installable via [skills.sh](https://skills.sh/) or the [skills CLI](https://github.com/vercel-labs/skills):

| Skill | Description |
| :--- | :--- |
| [`sid-scout`](skills/sid-scout/SKILL.md) | Read-only codebase explorer that outputs a minimal context snapshot. |
| [`sid-draft`](skills/sid-draft/SKILL.md) | Rapid first-pass component drafting prioritizing layout fidelity over completeness. |
| [`sid-review`](skills/sid-review/SKILL.md) | Opinionated frontend review targeting layout bugbears and common anti-patterns. |
| [`sid-health-check`](skills/sid-health-check/SKILL.md) | Structural maintainability audit for React / TypeScript / Tailwind v4. |
| [`sid-test`](skills/sid-test/SKILL.md) | Behaviour-driven test authoring using shared render helpers and edge mocks. |
| [`sid-test-review`](skills/sid-test-review/SKILL.md) | Sceptical test suite review looking for fake coverage and weakened assertions. |
| [`sid-a11y-review`](skills/sid-a11y-review/SKILL.md) | WCAG 2.2 AA accessibility audit for HTML structure, ARIA, focus, and contrast. |
| [`sid-pii-check`](skills/sid-pii-check/SKILL.md) | Scan git changes and code for personal info, local paths, client names, and secrets. |
| [`sid-summarise-activity`](skills/sid-summarise-activity/SKILL.md) | Git commit and PR activity summariser for sprint reviews and timesheets. |

### Quickstart

Install any skill using `npx skills`:

```bash
# Install a specific skill from GitHub
npx skills add fiveid/sid-skills --skill sid-review

# Install all skills globally
npx skills add fiveid/sid-skills -g

# Install from a local clone
npx skills add /path/to/sid-skills --skill sid-test
```

See the [Skills Guide](skills/README.md) for full usage, directory conventions, and security scanning instructions.
