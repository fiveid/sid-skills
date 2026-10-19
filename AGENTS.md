# Agent Instructions (AGENTS.md)

You are collaborating with the maintainer on a personal repository of practical knowledge and reusable skills for AI-assisted software development.

Read this document before writing or modifying any guidelines, documentation, or skills in this repository.

---

## 1. Repository Layout

- **[`HUMANS.md`](./HUMANS.md)**: Real-world reflections, risks, and practical workflows for developers working with AI agents.
- **[`skills/`](./skills/README.md)**: Modular agent instruction sets conforming to the [Agent Skills spec](https://agentskills.io/).

---

## 2. Tone of Voice

- **Non-prescriptive & non-authoritative**: Do not speak as an absolute authority or declare "industry best practices". Use language like *"in my experience"*, *"a pattern that has worked well"*, *"friction I have observed"*, *"rules of thumb"*.
- **Pragmatic & honest**: Be candid about trade-offs, limitations, and failure modes. Acknowledge when something is tedious, brittle, or requires a human gut check.
- **Evolving & iterative**: The content shifts as models and developer tooling change. Avoid over-formalizing ideas before they are tested in real workflows.
- **Terse and direct**: Favour short, high-signal paragraphs over corporate fluff or long-winded essays.

---

## 3. Working Invariants

- **Humans own the *what* and the *why***; agents help with the *how* of a single, bounded task.
- **Keep plans disposable, keep invariants permanent**: Task plans are discarded once merged; short, permanent READMEs and rulefiles capture the rules that matter.
- **Ask for evidence, not explanations**: When proposing code or changes, verify them with tests or script output rather than theoretical commentary.
- **Watch out for test theatre**: Tests must be behaviour-driven, test edge cases, mock only at system boundaries (network/clock), and be able to fail when code breaks.
- **Own what you merge**: If a diff passes CI but feels convoluted or fragile, call it out.

---

## 4. Working with Guidelines (`HUMANS.md`)

When expanding or refining guidelines:
- Maintain the existing visual structure and headings where possible.
- Provide concrete, realistic examples (test anti-patterns, review signals, worktree lane setups).
- Keep content focused on developer experience, attention management, and human review strategies.

---

## 5. Working with Skills (`skills/`)

### Structure
```text
skills/
  sid-<name>/
    SKILL.md          # Required: Frontmatter (name, description) + instructions
    scripts/          # Optional: Python or shell helper scripts
    references/       # Optional: Markdown references or API contracts
    templates/        # Optional: Code templates
```

### Standards
- **Frontmatter**: Must include `name` (matching directory name) and a concise `description`.
- **Single responsibility**: Each skill should have a focused persona and scope.
- **Behaviour over syntax**: Instruct the agent on how to think, what red flags to watch for, and what process to follow.

### Mandatory Security Check
Whenever creating or modifying a skill:
1. Run a scan using `skill-scanner` (`/skill-scanner scan skills/<skill-name>`).
2. Verify the scan results in a **Clean** or **Low** risk rating.
3. Ensure no hardcoded tokens, secret paths, prompt injections, or unrestricted file modifications exist.

---

## 6. Change Hygiene

- **Small, single-purpose commits**: Keep changes bounded and reviewable.
- **Keep catalogues in sync**: Whenever adding or renaming a skill, update the catalogues in both `skills/README.md` and `README.md`.
