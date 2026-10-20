# Skills Collection

Reusable agent skills conforming to the [Agent Skills specification](https://agentskills.io/) and installable via the [skills CLI](https://github.com/vercel-labs/skills) (`npx skills`) or [skills.sh](https://skills.sh/).

---

## Installation

### From GitHub

Install all skills from this repository:

```bash
npx skills add fiveid/sid-skills
```

Install a specific skill by name:

```bash
npx skills add fiveid/sid-skills --skill sid-review
```

### From a Local Path

If you have this repository cloned locally, you can install into another project using a relative or absolute path:

```bash
# Relative path (from within your target project)
npx skills add ../sid-skills --skill sid-review

# Absolute path
npx skills add /path/to/sid-skills --skill sid-test
```

### Global Installation

Pass `-g` to make the skill available across all your local projects:

```bash
npx skills add fiveid/sid-skills --skill sid-scout -g
```

### Managing Skills

```bash
# List installed skills in the current project
npx skills list

# Update installed skills to the latest version
npx skills update
```

A `skills-lock.json` file is committed to track third-party skill dependencies.

---

## Available Skills

| Skill | Description |
| :--- | :--- |
| [`sid-a11y-review`](./sid-a11y-review/SKILL.md) | WCAG 2.2 AA audit for semantic HTML, ARIA, focus, and contrast. |
| [`sid-dep-audit`](./sid-dep-audit/SKILL.md) | Audit dependencies for supply-chain risk, age gating (< 30 days), and trivial utilities. |
| [`sid-draft`](./sid-draft/SKILL.md) | Fast first-pass React/TypeScript component drafter prioritizing layout fidelity. |
| [`sid-health-check`](./sid-health-check/SKILL.md) | Maintainability audit for React/TS/Tailwind v4 catching structural debt. |
| [`sid-pii-check`](./sid-pii-check/SKILL.md) | Scan git changes and code for personal info, local paths, client names, and secrets. |
| [`sid-plan-audit`](./sid-plan-audit/SKILL.md) | Sceptically distill implementation plans to expose implicit decisions, scope, and missing guardrails. |
| [`sid-pr-prep`](./sid-pr-prep/SKILL.md) | Prepare concise, evidence-first pull request descriptions with manual review checklists. |
| [`sid-review`](./sid-review/SKILL.md) | Opinionated frontend review focusing on layout, composition, and common anti-patterns. |
| [`sid-scout`](./sid-scout/SKILL.md) | Read-only codebase explorer that outputs minimal context snapshots. |
| [`sid-summarise-activity`](./sid-summarise-activity/SKILL.md) | Summarises sprint commits and PRs for timesheets and standups. |
| [`sid-test`](./sid-test/SKILL.md) | Behaviour-driven test authoring using shared helpers and edge mocks. |
| [`sid-test-review`](./sid-test-review/SKILL.md) | Sceptical review of test suites to catch fake coverage and weakened assertions. |

---

## Authoring & Contributing Skills

### Skill Structure

Each skill lives in its own directory within `skills/`:

```text
skills/
  sid-example/
    SKILL.md        # Required: YAML frontmatter + prompt instructions
    scripts/        # Optional: helper scripts executed by the skill
    references/     # Optional: documentation or schemas loaded by the skill
    templates/      # Optional: template files
```

The `SKILL.md` must include YAML frontmatter:

```yaml
---
name: sid-example
description: Brief description explaining what the skill does and when an agent should use it.
---
```

### Security Scanning with `skill-scanner`

Before submitting new or modified skills, run a security scan using [skill-scanner](https://skills.sh/getsentry/skills/skill-scanner) to check for prompt injection, secret exposure, or unsafe commands.

**Setup (one-time):**

```bash
npx skills add https://github.com/getsentry/skills --skill skill-scanner
```

**Run a scan in your agent:**

```text
/skill-scanner scan skills/sid-review
```

Or scan all skills:

```text
/skill-scanner scan all skills in the skills directory
```

All skills must pass with a **Clean** or **Low** risk rating before being merged.
