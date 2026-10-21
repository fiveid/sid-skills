# **Risks and mitigations**

*The principles behind this guide are in [HUMANS.md](../../HUMANS.md#a-collaborative-culture).*

These are the risks I think matter most when building software with agents, each followed by practical mitigations. Most come from my own projects; new attack vectors are well documented, but not something I've hit myself. The principles explain why they matter; this page is the practical side.

Where a skill in this repo helps with a mitigation, it's linked as an example. Treat it as a first pass: it surfaces questions, and the decision stays with you.

## **The planning doom spiral**

Over-planning adds a docs burden and risks anchoring AI to outdated or unwanted specs.

* **Keep plans disposable, keep invariants permanent.** Bin the task plan once it's merged; keep a short README per domain with the rules that actually matter.

## **Plan drift**

AI can write flawless-sounding plans with no real-world experience. Tiny, plausible assumptions slip in, reviewers skim and approve, those mistakes become gospel.

* Humans own the *what* and the *why*. Agents can help with the *how* of a single, bounded task.
* **Don't let agents write the strategy.** They're great at challenging a plan, but the roadmap and priorities stay with the human.
* **Audit any plan an agent proposes.** Look specifically for unstated dependencies, speculative abstractions and quiet scope creep. Maybe even get a second, *human* opinion. *Example skill:* [`sid-plan-audit`](../../skills/sid-plan-audit/SKILL.md).

→ **Proposal:** [Project lifecycle](../proposals/project-lifecycle.md)

## **Architectural drift**

Minor, individually harmless aberrations in PRs pass CI and manual review, but risk adding up to architectural fragmentation.

* **Architectural boundaries.** Giving an agent one bounded domain limits hallucination and keeps dependencies contained.
* **Set up shared foundations early.** Set up workspace packages with hard boundaries early (e.g. Turborepo monorepo with a shared packages/ui).
* **Keep PRs small and single purpose.**

→ **Proposal:** [Project lifecycle](../proposals/project-lifecycle.md)

## **Review fatigue and automation bias**

Reviewers inevitably default to skim-reading high-volume AI code.

* **Predict the diff first.** Know roughly what the change should look like before opening it, then look for what doesn't fit.
* **Ask for evidence, not explanations.** Test output or a curl command beats an AI-written essay.
* **Add "manual review tasks" to PR checklist.** *Example skill:* [`sid-pr-prep`](../../skills/sid-pr-prep/SKILL.md) drafts an evidence-first PR description with this checklist.
* **Watch out for test theatre.** Left alone, agents mock everything and assert the mock was called. All green, proving nothing. *Example skill (React/TypeScript):* [`sid-test-review`](../../skills/sid-test-review/SKILL.md).

→ **Guide:** [Testing with confidence](testing-with-confidence.md)  
→ **Proposal:** [Hierarchy of verification](../proposals/hierarchy-of-verification.md)

## **Issue abundance**

AI code reviews produce long lists of bugs and improvements, some of which are overstated or incorrect. Triaging the list can cost as much as reviewing the code, and adds further noise.

* **Use AI review for targeted questions, not open-ended trawls.** "Find every query inside a loop" gets a better answer than "review this PR".

## **The human bottleneck**

Babysitting a single agent is tedious and limiting. But juggling multiple agents brings its own problems when human review is the real bottleneck.

* Generation is nearly free; review isn't. **Plan capacity around how much a person can properly review**, not how much an agent can produce.
* **Slow down to speed up.** Stop. Take a breath. Wait.
* **Optimise codebase for parallel development.**

→ **Guide:** [Parallel development](parallel-development.md)

## **Secrets exposure**

Agents pull secrets (ssh keys, MCP tokens, environment variables) into context. Prompt injection can exfiltrate secrets.

* **No real secrets in the agent's environment.**
* **Instructions are suggestions.** For reliability we need hard enforcement: sandboxes, permissions and CI checks that fail loudly.
* **Scan commits for secrets.** Run gitleaks or trufflehog in pre-commit hooks and CI to catch leaked tokens.

→ **Guide:** [Secrets in the agent's environment](secrets.md)  
→ **Proposal:** [Sandboxing](../proposals/sandboxing.md)

## **New attack vectors**

Prompt injection and slopsquatting (malicious packages using commonly hallucinated package names) are just two of the ways bad actors are exploiting agent behaviour.

* **Gate dependencies.** New dependencies need a human sign-off. *Example skill (npm):* [`sid-dep-audit`](../../skills/sid-dep-audit/SKILL.md).
* **Sandboxed by default.** Which tier is a trade-off, explored in the proposal below.

→ **Proposal:** [Sandboxing](../proposals/sandboxing.md)
