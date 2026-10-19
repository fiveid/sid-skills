# **Human Guidelines for AI Development**

*This document is a write-up of what I have learned so far from using AI agents for development. Do not treat the recommendations within as authoritative. These are purely based on my own subjective experience.* 

AI makes writing code cheap. It doesn't make reviewing, understanding or owning that code any cheaper. Almost everything in this guide follows from that.

The key assumption here is that human involvement is necessary, but human attention is finite.

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
  * **Don't let agents write the strategy.** They're great at challenging a plan, but the roadmap and priorities stay with us.  
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
  * **Sandboxed by default**. Something we need to decide as a team: whether to enforce it, and which tier (see Sandboxing).  
  * **No real secrets in the agent’s environment.**

## **Parallel development**

Sitting and waiting for an agent to finish its task, just to click approve and then wait for the next job to finish, leads to developer fatigue. It can kill motivation and productivity, while still introducing the same risks detailed above.

I've found working with AI more rewarding and engaging when running agents in parallel. However, as tempting as it is to open a session for each ticket in the sprint and just let them go at it, this will lead to a review bottleneck up ahead, and difficult context switching as your attention hops between potentially dozens of agents asking questions.

I've found that running parallel worktrees works, up to a point. Personally, the balance I have found is a maximum of 4 streams on a main project, with an optional fifth side-stream:

| Lane | What runs there |
| :---- | :---- |
| 1\. Feature A | One bounded, single-purpose task working from an approved checklist |
| 2\. Feature B | An independent task in a different domain, with its own branch, ports and test database |
| 3\. Background audit | Low-priority analysis (dead code, dependency pruning, lint fixes, missing types) to review later |
| 4\. Main tree | Hands-on human work: architecture decisions, spikes and local verification |
| 5\.  Side Project | Side projects or tooling experiments, in separate directories and repos |

In my case, I had to spend a bit of time working with the agent to create instructions and scripts that allowed agents to work in parallel without friction. For example, headless frontend lanes can point at a shared read-only dev API, or a mock server, without touching the local database. This was worth it.

## **Secrets and sandboxing**

Assume anything the agent can read, it will eventually read — and that anything it reads could leave the machine. **The surest way is to include no real secrets inside the agent's environment**. Real credentials live in CI/CD. 

1Password SSH agent can keep SSH keys hidden and ensure biometric approval is required before they are accessed. 1Password also allows environment variable management. However, while this is useful in a lot of ways, the tokens would still be ultimately accessible to a determined agent.

Don't hardcode tokens in MCP config files the agent can read. A CLI tool (or Claude connector) may be safer than an MCP if it hides the auth token, though the agent can still do whatever that token allows, so keep its scope narrow.

Note that prompt-level settings are steering, not security. Claude Code doesn't read .claudeignore at all. Use permissions.deny in .claude/settings.json to stop Claude's own file tools reading secrets (e.g. Read(./.env\*)). But even that is a rule applied by the tool, not the operating system, and can be worked around. 

### **Sandboxing**

Sandboxing a project ensures an agent cannot reach outside the scope of the project to reach system settings and trawl keys from other directories. An egress allowlist can limit what external hosts an agent would be able to connect to. It can also isolate SSH keys and CLI tokens. We may want to adopt a sandboxing approach as standard. There are options:

| Tier | Setup | What it covers | Watch out for |
| :---- | :---- | :---- | :---- |
| 1\. Built-in sandbox | Claude Code's /sandbox, which uses Seatbelt on macOS and bubblewrap on Linux | Shell commands and anything they start; network via a domain allowlist | Doesn't cover Claude's file tools, MCP servers or hooks. Reads most of the machine (including \~/.ssh) unless you deny it. Docker doesn't run inside it, so containerised test databases need an exception |
| 2\. Whole-process isolation | Run the agent itself inside a dev container, rootless container, micro-VM or Nix/bubblewrap shell | Everything the agent does; only the repo is mounted, shared packages read-only | More setup; you build the network allowlist yourself |
| 3\. Ephemeral cloud sandbox | A fresh remote environment per branch | Local credentials never exist there | Cost and slower feedback |

## **Project lifecycle**

Projects are not all alike, and in my experience, the problems faced by a greenfield codebase are different from those of a mature codebase. We can talk about "small PRs only, limited to specific domains", but, realistically, new projects will kick off with large PRs and changes that cross multiple domains.

Strict rules kill speed early on, and loose rules create a mess later. The aim is not to force one way or another, but to transition securely and with confidence from a fast-moving, emerging codebase, to a mature, stable one. 

We change mode deliberately, at two checkpoints, rather than drifting into a codebase that looks finished but that nobody really understands. From "feature complete" to "production ready".

Even with hobby projects, I’ve found that getting to 80-90% feature-complete with AI is easy. Getting to 100% starts to feel a lot more like old-fashioned software engineering. Reaching production ready on top of that is another big step that requires genuine domain knowledge and experience. 

![project lifecycle · 3 phases, 2 checkpoints](./assets/project-lifecycle.png)

### **Phase 1: Discovery**

The spec is defined but the solutions are theoretical. We might want to move fast to stress test the assumptions. We might not understand 100% of the code the agent has generated, but we are able to validate the output and pin down the stable data models, types, structures, patterns and so on. All the things that will become our baseline for acceptance of future work. 

At the end of this phase we want to clean up and streamline all generated docs to represent the stable state of the project.

### **Checkpoint 1: domain and contract freeze (example)**

* ☐ Core data models, schemas and types are stable  
* ☐ Code is organised into bounded domain folders (e.g. src/modules/billing)  
* ☐ Workspace package boundaries and the shared UI package are locked  
* ☐ An agent pass has removed duplicate helpers, unused packages and dead scaffolding from discovery  
* ☐ Agent instructions (CLAUDE.md) are in the repo root: architecture rules, preferred libraries, things not to do  
* ☐ Each domain has its short README of rules and contracts

### **Phase 2: Buildout**

At the end of this phase, the product should be "feature complete", but should not be assumed to be "production ready". This is where we need to dig deeper, challenge prior assumptions and ensure we are not releasing something no developer on the team fully understands.

### **Checkpoint 2: production-readiness audit (example)**

* ☐ Every external boundary (APIs, webhooks, user input) is validated at runtime  
* ☐ Every critical flow has integration tests with human-verified assertions  
* ☐ Critical queries and state changes checked for N+1s, missing transactions and race conditions  
* ☐ Security pass: no credentials in the repo or agent logs, no hardcoded keys, no overly broad permissions, secret scanning in CI  
* ☐ Lint rules for domain boundaries and duplicate detection are enforced in CI  
* ☐ Shared configs, migrations and libraries are frozen with CODEOWNERS, Git hooks and read-only mounts

### **Phase 3: Production**

The product is "mature", in production, and undergoing ongoing feature additions, bug fixes, and maintenance. Our strictest rules are in place and the expectation for agent output is predictable and manageable. 

## **Hierarchy of verification**

"Written by AI, approved by humans" is the mantra, but is it the reality? In this document, I've referred to various checks, reviews, and approvals. The difficulty is where to focus our time and attention when we are not able to review every line generated.

This hierarchy of verification attempts to delineate responsibilities at different levels.

![hierarchy of verification · 5 levels](./assets/hierarchy-of-verification.png)

* **1 · Code quality.** Formatting, types, unused imports. CI catches it, the agent fixes it, nobody discusses it in review.  
* **2 · Architectural drift.** If you keep catching the same kind of drift by hand (wrong imports, edits to shared code, duplicate helpers), turn it into a lint rule or CI check so you don’t have to.  
* **3 · Does it actually work?** Decide what the tests should check before the agent writes the code. Then check for the things tests rarely catch: queries in loops, missing transactions, race conditions, auth gaps.  
* **4 · Plan and scope.** Read the agent’s plan properly before it starts, and know roughly what the diff should look like before opening it. This is where review time is best spent.  
* **5 · What we build and why.** That stays with us.

## **Rules of thumb**

A few rules I keep coming back to.

1. **Trust your gut.** If a diff passes everything but feels convoluted or over-engineered, I reject it. If you feel like the AI is wrong, call it out. AI is very good at making bad architecture look tidy and is sometimes confidently wrong.  
2. **Know when to stop prompting.** If an agent hasn't cracked a bounded problem after a couple of corrections, the task usually isn't well defined or needs a human to spike it. Bin the branch and start again.  
3. **Own what you merge.** I don't need to know every specific line, any more than I do for a dependency. But I should be able to explain what a change does, what goes in and out, and how it fails. I should be able to predict where a bugfix or feature addition lands in the code and what it touches. If I can't, it's not ready.

## **Testing with confidence**

The aim is to increase confidence that tests are actually testing something. Agents will happily write lots of tests; the problem is that many of them only test React, or test their own mocks.

### **Initial project setup**

* **A shared mocking pattern for the backend.** Fake things only at the edges (network, time, browser APIs, third-party SDKs), never in the middle of the code you’re testing. If the handlers and types can be generated from the backend’s API schema, the fake responses can’t drift from what the backend really returns. Set the mock server to fail the test on any unhandled network request, so background fetches can't fail silently. This is the pattern the agent will use for every test, rather than rolling its own each time, so it deserves high attention.  
* **A shared render helper.** One function that wraps components in the real providers (router, store, query client). Tests then use the real `useUser` hook with only the network faked underneath. If the agent mocks each hook instead, the tests end up only testing React internals. Mock only what you don’t own.  
* **Mutation testing.** Set up something like Stryker to run on changed components, either as a regular audit or as a precaution. It’s slow, but it shows whether tests actually catch anything when the code is broken.

### **Writing agent skills**

A testing skill (or a section in the agent instructions) should cover:

* **Use the shared helper and mocking pattern.** Never mock our own hooks, components or context.  
* **Ask “would a user notice if this broke?”** We don’t want “`onClick` triggers state” or “`props.title` renders the title”; those are obvious at a glance and just test React. We want edge cases, errors, validation, and empty or disabled states.  
* **Cover the states where they apply.** Loading, empty, error and success for anything that fetches data. Keyboard use and disabled states for anything interactive.  
* **Use `userEvent`, never `fireEvent`.** Simulate real user actions (`await user.click()`, `await user.type()`). `fireEvent` dispatches synthetic events directly and will happily pass on elements that are hidden, disabled or unfocusable.  
* **Query by role and label** (`getByRole('button', { name: 'Save' })`) rather than test IDs or class names. No snapshot tests.  
* **Be careful asserting absence.** Never assert that something is *not* on the screen (`queryBy...`) until you have awaited the surrounding view to finish loading, and proven in another test that the selector actually matches when the element *is* shown.  
* **Pull complex logic into plain functions.** Don’t mount a full component tree twenty times to test twenty edge cases of a price calculation or date parser. Extract pure business logic and unit test it directly with table-driven tests (`it.each`), then use a few component tests to check the UI wires into it properly.  
* **List the test cases first**, as one-line names that read like small user stories: “shows…”, “user can…”, “when X, Y happens”.  
* **Anything that can’t sensibly be tested goes into the MR’s manual checks list**, e.g. visual layout, or long text overflowing.  
* **Reset the data cache in every test, and scope fake timers.** Only enable fake timers inside the specific tests that need them (wired to `userEvent`), so they don't deadlock async queries elsewhere.  
* **Treat existing tests as read-only by default.** If a change breaks an existing test, stop and explain why before touching the test. Never edit an assertion just to make the test suite green.  
* **See it fail first.** For a bug fix, the agent writes the test, runs it against the old code and shows it failing. It’s cheap, it’s mutation testing for one case, and it catches most fake tests before Stryker is needed.

### **When prompting**

* **Include a few one-line behaviour examples** of what the user should see and be able to do, including at least one failure case.  
* **Prompt for edge cases specifically.** What happens if the text is twice as long? If a user enters a special character rather than a number? If the request times out?  
* **Ask for the test list before the implementation**, so you can check the cases before any code exists.

### **When reviewing MRs**

* **Skim the test names, not the test code.** Red flags are anything that mirrors the code rather than the behaviour:  
  * one test per prop or branch  
  * “renders without crashing” or “component initialises” repeated as if they test something  
  * internal state (“sets `isOpen`”)  
  * assertions on a mock with no user action (“calls `onChange`” rather than “typing a name calls `onChange` with the new value”)  
  * asserting something isn't there (`expect(queryBy...).toBeNull()`) before asserting the page has actually loaded  
  * existing test assertions weakened or changed in the same MR as the code without a change in requirements.  
* **Check what’s missing.** Are loading, empty, error and keyboard states covered where they should be?  
* **Check the manual checks list** covers what the tests can’t.  
* **If in doubt, run mutation testing on the changed components.** If you can break the code and the tests stay green, they’re not testing anything.
