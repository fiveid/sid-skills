# Skills Collection

Reusable agent skills conforming to the [Agent Skills specification](https://agentskills.io/) and installable via the [skills CLI](https://github.com/vercel-labs/skills) (`npx skills`), [skills.sh](https://skills.sh/) or [APM](https://github.com/microsoft/apm). [Managing and sharing skills](../docs/guides/managing-and-sharing-skills.md) compares the two tools and covers what to check before installing.

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

Project installs are recorded in a `skills-lock.json` in the project you install into.

### With APM

Install a specific skill by name:

```bash
apm install fiveid/sid-skills --skill sid-review
```

APM installs for the agents it detects in the project, such as a `.claude/` folder or `CLAUDE.md` for Claude Code. If there are none, name the agent:

```bash
apm install fiveid/sid-skills --skill sid-review --target claude
```

Pass `-g` to install for your user rather than the project:

```bash
apm install -g fiveid/sid-skills --skill sid-scout
```

Manage installed skills:

```bash
# List installed packages (`apm list` shows scripts, not packages)
apm deps list

# Update to the latest version
apm update
```

Project installs are recorded in `apm.yml` and `apm.lock.yaml` in the project you install into. Your `--skill` choices are saved there too, and a later `--skill` adds to them rather than replacing them.

---

## Versioning

Releases are tagged `vMAJOR.MINOR.PATCH`, and the whole collection shares one version. Pin a tag rather than tracking `main`, so a skill only changes when you choose to update it:

```bash
npx skills add fiveid/sid-skills@v1.0.0 --skill sid-review
apm install fiveid/sid-skills#v1.0.0 --skill sid-review
```

| Bump | When | Examples |
| :--- | :--- | :--- |
| **Major** | A skill is renamed or removed, or changes in a way that breaks how people use it | Renaming `sid-review`; changing the JSON a skill's script outputs |
| **Minor** | A new skill, or a new capability in an existing one | Adding a skill; a new check in `sid-trust-audit` |
| **Patch** | Fixes and tighter wording that don't change what a skill is for | Clarifying a step; fixing a script bug |

Skills are instructions, so "breaks how people use it" is a judgement call: a reworded instruction can change what an agent does. When in doubt, bump minor and say what changed in the release notes. Each release on GitHub lists what changed.

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
| [`sid-quality-gate`](./sid-quality-gate/SKILL.md) | Set up a language-agnostic CI quality gate with a recorded baseline, then audit it later for loosened thresholds, new suppressions and CI bypasses. |
| [`sid-review`](./sid-review/SKILL.md) | Opinionated frontend review focusing on layout, composition, and common anti-patterns. |
| [`sid-scout`](./sid-scout/SKILL.md) | Read-only codebase explorer that outputs minimal context snapshots. |
| [`sid-summarise-activity`](./sid-summarise-activity/SKILL.md) | Summarises sprint commits and PRs for timesheets and standups. |
| [`sid-test`](./sid-test/SKILL.md) | Behaviour-driven test authoring using shared helpers and edge mocks. |
| [`sid-test-review`](./sid-test-review/SKILL.md) | Sceptical review of test suites to catch fake coverage and weakened assertions. |
| [`sid-trust-audit`](./sid-trust-audit/SKILL.md) | Audit an agent-built project's safeguards by breaking them on purpose, labelling each as enforced, unenforced, convention or owner-checked. |

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

### Hidden Unicode Check with `apm audit`

`apm audit --file` adds a mechanical check for invisible characters (zero-width spaces, bidi controls, Unicode tag characters) that can hide instructions from a human reviewer. APM runs the same check on every install and blocks the install on critical findings, so a skill that fails here can't be installed with APM.

Check every file in a skill before merging:

```bash
find skills/sid-review -type f -exec apm audit --file {} \; -print
```

Each file is printed after a clean scan; a file with findings is reported and not printed. Fix or remove anything flagged as critical or warning.
