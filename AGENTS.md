# Agent Instructions (AGENTS.md)

You are collaborating with the maintainer on a personal repository of practical knowledge and reusable skills for AI-assisted software development.

Read this document before writing or modifying any guidelines, documentation, or skills in this repository.

---

## 1. Repository Layout

- **[`HUMANS.md`](./HUMANS.md)**: The guiding principles. Real-world reflections, risks and rules of thumb for developers working with AI agents.
- **[`docs/guides/`](./docs/guides/README.md)**: Concrete practices that put those principles to work and have held up in use.
- **[`docs/proposals/`](./docs/proposals/README.md)**: Frameworks and team decisions that are still being tested.
- **[`skills/`](./skills/README.md)**: Modular agent instruction sets conforming to the [Agent Skills spec](https://agentskills.io/).

---

## 2. Tone of Voice

- **Direct, not authoritative**: This is a public repo for anyone building software with AI. State principles plainly and with conviction; drop hedges like *"it might be worth considering"*. Direct is not the same as authoritative: do not declare "industry best practice" or claim more certainty than the evidence supports.
- **Grounded in experience**: The content comes from real projects. Where a claim rests on personal experience rather than wider evidence, say so once (*"in my projects"*), not in every sentence. Proposals carry a **Status** line for this.
- **Not judgemental**: Describe what an approach costs and who pays, rather than calling it wrong. Do not assume the reader already works this way; many are starting from more basic problems.
- **Pragmatic & honest**: Be candid about trade-offs, limitations, and failure modes. Acknowledge when something is tedious, brittle, or requires a human gut check.
- **Accurate before memorable**: A catchy name, analogy or "law" is welcome only if the claim behind it holds. Stick to one metaphor per idea.
- **Evolving & iterative**: The content shifts as models and developer tooling change. Avoid over-formalizing ideas before they are tested in real workflows.
- **Terse**: Favour short, high-signal paragraphs over corporate fluff or long-winded essays.

---

## 3. Working Invariants

- **Humans own the *what* and the *why***; agents help with the *how* of a single, bounded task.
- **Keep plans disposable, keep invariants permanent**: Task plans are discarded once merged; short, permanent READMEs and rulefiles capture the rules that matter.
- **Ask for evidence, not explanations**: When proposing code or changes, verify them with tests or script output rather than theoretical commentary.
- **Watch out for test theatre**: Tests must be behaviour-driven, test edge cases, mock only at system boundaries (network/clock), and be able to fail when code breaks.
- **Own what you merge**: If a diff passes CI but feels convoluted or fragile, call it out.

---

## 4. Working with Guidelines (`HUMANS.md` and `docs/`)

Where content goes:
- **`HUMANS.md`** holds the *why*: principles, observed risks and rules of thumb. Each principle gets a short summary there and links to the guide or proposal that makes it concrete.
- **`docs/guides/`** holds the *how* for practices that have been tried and kept.
- **`docs/proposals/`** holds the *how* for ideas that are still untested or need a team decision. Each proposal opens with a **Status** line and a **Responds to** line naming the risk it addresses. When a proposal proves itself, move it into a guide.
- Say each thing once. A summary in `HUMANS.md` states the principle; the steps live only in the linked doc.

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
