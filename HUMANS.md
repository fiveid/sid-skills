# **Human Guidelines for AI Development**

AI makes writing code cheap. It doesn't make reviewing, understanding or owning that code any cheaper.

This guide is for humans who are building software with AI. It is based on the following assumptions:

- When used effectively, AI can increase productivity without sacrificing quality.
- Human involvement is necessary; human attention is finite.

## **A collaborative culture**

If you have ever worked as part of a team, you know the importance of a _working culture_. In brief, we can define it as a shared understanding that encourages collaboration and ensures everyone is pulling in the same direction.

Working with agents requires a similar culture. When working with AI, you may be the only human in the team. This means it's up to you to make sure you and your agents work effectively within the culture you've established.

> [!NOTE]
> Remember, each agent session is effectively a new worker. Enabling new agents to seamlessly onboard is part of the process.

A culture is not a detailed 200-file spec. It's not a plugin that can be installed in a harness. It's not a prompt engineering trick.

We can't simply map software engineering culture onto AI development either (although we can learn from software engineering best practices). The culture I'm proposing emerges from a set of basic principles from which all else follows:

- **YOU own the product**
- **The bill comes due. Always**
- **You don't need to know every line of code written, but you need to know _how_ to know**
- **Code is the source of truth**
- **What _should_ be read _will_ be skimmed**
- **Instructions are suggestions**
- **Don’t leave your thinking in the chat**

### YOU own the product

Ask an AI to plan a wedding and it'll write the most detailed and confident-sounding plan you've ever seen. But the AI has never planned a wedding before. An AI has never even been to a wedding.

As impressive as LLMs are, they have limits that you do not. YOU are the strategy, the taste, the continuity. You set the quality floor. The repo holds the state. The AI holds the immediate, disposable context window.

### The bill comes due. Always

Human review is the inevitable bottleneck, whether you factor that in up front or wait to test on your unfortunate users. You can do one of three things with review cost: move it, shrink it, or write it off. What you cannot do is ignore it and keep the code.

Plan capacity around human review bandwidth, not machine generation capacity.

### You don't need to know every line of code written, but you need to know _how_ to know

Your codebase is a dark house. If you were dropped into a random room with a weak flashlight, could you find your way around? An encyclopedic knowledge of every nail used in construction isn't needed, but a familiarity with the layout and furnishings (and lightswitches) would avoid some bruises. If you keep walking into furniture, the layout is wrong, not your memory.

Aim for code that is skimmable, predictable, human-readable. Prefer convention over specification, predictable patterns over clever abstractions, familiarity over novelty. Define boundaries through architecture, not instructions.

Whether your primary interface is code, text, or diagrams, possess a mental model of the product and know how to spot red flags.

### Code is the source of truth

The behaviour is the behaviour. Regardless of what is written in the spec, or what sits in your mind, ultimately the code is the source of truth. Docs grow stale. Memories erode. When all else fades, the code remains.

### What _should_ be read _will_ be skimmed

**Nobody** reads every word of generated AI output. Any strategy or workflow that assumes otherwise will fail. Assume what is written will, at most, be skim-read. Plan around human attention, not AI verbosity.

### Instructions are suggestions

Prompts are advisory. Context is guidance. Adherence is not guaranteed. Only mechanically enforced constraints can be trusted.

### Don’t leave your thinking in the chat

AI chats are a poor substitute for proper organisation. Used carelessly, chats scatter your thinking across a dozen brains that forget it the moment you close the tab. Any concrete progress will as good as lost.

Start any chat with an end goal in mind. Agent sessions are ephemeral and should be considered fragile. Every chat or agent session should conclude with something left behind. Something that can be moved or exists outside the session chat, e.g. something to copy and paste into your notes, a report, a commit, a merge request, etc.

## **Risks**

* **The planning doom spiral.** Over-planning adds a docs burden and risks anchoring AI to outdated or unwanted specs.  
* **Plan drift.** AI can write flawless-sounding plans with no real-world experience. Tiny, plausible assumptions slip in, reviewers skim and approve, those mistakes become gospel.  
* **Architectural drift.** Minor, individually harmless aberrations in PRs pass CI and manual review, but risk adding up to architectural fragmentation.  
* **Review fatigue and automation bias.** Reviewers inevitably default to skim-reading high-volume AI code.   
* **Issue abundance.** AI code reviews produce long lists of bugs and improvements, some of which are overstated or incorrect. Triaging the list can cost as much as reviewing the code, and adds further noise.  
* **The human** **bottleneck.** Babysitting a single agent is tedious and limiting. But juggling multiple agents brings its own problems when human review is the real bottleneck.  
* **Secrets exposure.** Agents pull secrets (ssh keys, MCP tokens, environment variables) into context. Prompt injection can exfiltrate secrets.  
* **New** **attack vectors.** Prompt injection and slopsquatting (malicious packages using commonly hallucinated package names) are just two of the ways bad actors are exploiting agent behaviour. 

## **Mitigation**

* **Planning and context**  
  * Humans own the *what* and the *why*. Agents can help with the *how* of a single, bounded task.  
  * **Keep plans disposable, keep invariants permanent.** Bin the task plan once it's merged; keep a short README per domain with the rules that actually matter.  
  * **Architectural boundaries.** Giving an agent one bounded domain limits hallucination and keeps dependencies contained.   
  * **Don't let agents write the strategy.** They're great at challenging a plan, but the roadmap and priorities stay with the human.  
  * **Audit any plan an agent proposes.** Look specifically for unstated dependencies, speculative abstractions and quiet scope creep. Maybe even get a second, *human* opinion.  
  * **Set up shared foundations early.** Set up workspace packages with hard boundaries early (e.g. Turborepo monorepo with a shared packages/ui).   
* **Reviewing AI code**  
  * **Predict the diff first.** Know roughly what the change should look like before opening it, then look for what doesn't fit.  
  * **Keep PRs small and single purpose.**  
  * **Ask for evidence, not explanations.** Test output or a curl command beats an AI-written essay.  
  * **Add "manual review tasks" to PR checklist.**  
  * **Use AI review for targeted questions, not open-ended trawls.** "Find every query inside a loop" gets a better answer than "review this PR".  
  * **Watch out for test theatre.** Left alone, agents mock everything and assert the mock was called. All green, proving nothing.  
  * **Gate dependencies and commits.** New dependencies need a human sign-off. Run gitleaks or trufflehog in pre-commit hooks and CI to catch leaked tokens.  
* **Throughput**  
  * Generation is nearly free; review isn't. **Plan capacity around how much a person can properly review**, not how much an agent can produce.  
  * **Slow down to speed up.** Stop. Take a breath. Wait.  
  * **Optimise codebase for parallel development**. See below.
* **Security**
  * **Instructions are suggestions**. For reliability we need hard enforcement: sandboxes, permissions and CI checks that fail loudly  
  * **Sandboxed by default** see [Sandboxing](docs/proposals/sandboxing.md).  
  * **No real secrets in the agent’s environment.**

## **Rules of thumb**

A few rules I keep coming back to.

1. **Trust your gut.** If a diff passes everything but feels convoluted or over-engineered, I reject it. If you feel like the AI is wrong, call it out. AI is very good at making bad architecture look tidy and is sometimes confidently wrong.  
2. **Know when to stop prompting.** If an agent hasn't cracked a bounded problem after a couple of corrections, the task usually isn't well defined or needs a human to spike it. Bin the branch and start again.  
3. **Own what you merge.** I don't need to know every specific line, any more than I do for a dependency. But I should be able to explain what a change does, what goes in and out, and how it fails. I should be able to predict where a bugfix or feature addition lands in the code and what it touches. If I can't, it's not ready.

These are the areas I'm focusing on to improve developer experience and confidence in outcomes:

## **Parallel development**

In my experience, running agents on several jobs in parallel has been more productive, but it brings greater risks of developer fatigue and review bottlenecks. Depending on the project setup, it might also introduce technical complexities. My experience tackling these problems is described in the parallel development guide.

→ **Guide:** [Parallel development](docs/guides/parallel-development.md): the lane setup I use, and what it took to make it work.

## **Secrets and sandboxing**

The key takeaway for secrets is to **assume anything the agent can read, it will eventually read** — and that anything it reads could leave the machine. **The surest way is to include no real secrets inside the agent's environment**. Real credentials live in CI/CD. Prompt-level settings are steering, not security. Hard boundaries are what count. Balancing friction with security is essential (or else developers will default to the smoother option).

Sandboxed by default seems the best option. In the Sandboxing proposal I explore and compare options.

→ **Guide:** [Secrets in the agent's environment](docs/guides/secrets.md): practical notes on SSH keys, MCP tokens and permission rules.  
→ **Proposal:** [Sandboxing](docs/proposals/sandboxing.md): three tiers of isolation, and the trade-offs a team would need to decide between.

## **Project lifecycle**

Projects are not all alike, and in my experience, the problems faced by a greenfield codebase are different from those of a mature codebase. We can talk about "small PRs only, limited to specific domains", but, realistically, new projects will kick off with large PRs and changes that cross multiple domains.

Strict rules kill speed early on, and loose rules create a mess later. **We can move the human-review bottleneck but we cannot avoid it.** The aim is not to force one way or another, but to transition securely and with confidence from a fast-moving, emerging codebase, to a mature, stable one.

Even with hobby projects, I’ve found that getting to a (seemingly) "feature-complete" state with AI is easy. Getting it "production ready" starts to feel a lot more like old-fashioned software engineering, requiring human-led planning, genuine domain knowledge and experience.

The Project Lifecycle proposal sets out one approach to managing AI development projects.

→ **Proposal:** [Project lifecycle](docs/proposals/project-lifecycle.md): three phases (discovery, buildout, production) with example checkpoint lists.

## **Hierarchy of verification**

"Written by AI, approved by humans" is the mantra, but is it the reality? In this document, I've referred to various checks, reviews, and approvals. The difficulty is where to focus our time and attention when we are not able to review every line generated.

So far, my answer is to push the mechanical checks into tooling and spend review time on the plan and scope.

→ **Proposal:** [Hierarchy of verification](docs/proposals/hierarchy-of-verification.md): five levels of review responsibility, from CI up to intent.

## **Testing with confidence**

The aim is to increase confidence that tests are actually testing something. Agents will happily write lots of tests; the problem is that many of them only test React, or test their own mocks.

The testing guide recommends setting up shared foundations early so the agent doesn't roll its own mocks, deciding the behaviours under test before any code exists, and making the agent prove a test can fail.

→ **Guide:** [Testing with confidence](docs/guides/testing-with-confidence.md): project setup, what a testing skill should cover, prompting, and red flags when reviewing.
