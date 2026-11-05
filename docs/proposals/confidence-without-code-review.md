# **Confidence without code review**

**Status:** Proposal. Drawn from three solo side projects built almost entirely by agents. Not tried on a team or at work.  
**Responds to:** [review fatigue and automation bias](../guides/risks-and-mitigations.md#review-fatigue-and-automation-bias) and [the human bottleneck](../guides/risks-and-mitigations.md#the-human-bottleneck).

## Why code review breaks down

At work I use AI in small steps, and changes still go through code review. On my side projects I've pushed much further: agents write nearly all the code, and I'm the only human involved. There, code review stops working:

- Some of the code is in a language I can't read.
- The changes are too big to read properly.
- They arrive faster than I can read them.

Asking "what replaces code review?" got me jargon and tools that didn't hold up. The better question is: how do I trust code an agent wrote? We already ship plenty of code we've never read (frameworks, database drivers, the operating system), and we trust it because of what it does.

## The instruction

**Check the behaviour, not the code.** Decide what "done" looks like before the agent starts, check it yourself by using the thing, and let CI catch what you can't see by using it.

## Decide what "done" looks like

An agent can turn a thin spec into something that looks finished in minutes. Getting it to feature complete, and then production ready, takes real thought: what's in this version, what isn't, and what "ready" means for this project. Agents remove the friction that used to force those decisions, so they're the ones that get skipped. The [project lifecycle](project-lifecycle.md) proposal covers the two milestones.

On RendrGO I work in rounds: the agent asks its open questions, I answer, it writes a plan, I approve it, then it builds. I rarely read its code, and it's the most disciplined of my three projects.

## Check it yourself

I play every KS2 Detective case before it goes in. I use Llym every day. I check RendrGO's playground after each round. Most of my confidence comes from this.

Nothing in the repository records it, though. When I ran [trust audits](../../skills/sid-trust-audit/SKILL.md) on these projects, they couldn't see any of it. An audit has to ask what you do by hand.

## Let CI catch the rest

Using the product won't show you everything. RendrGO's copy promises that pages loaded with a visitor's cookies stay out of shared caches, but the code only does that when the cookies are read one particular way. I'd never spot that by clicking around, and it could leak one user's data to another. In Llym, a new recursive delete in the Rust I can't read would have passed every check I had.

Those are the gaps that types, lint rules and tests are for. Run them on CI so nobody has to remember to, and gate the release on the result. The [hierarchy of verification](hierarchy-of-verification.md) and the [testing guide](../guides/testing-with-confidence.md) cover what goes in them. An occasional audit that breaks the checks on purpose finds the gaps you didn't know to cover. Both examples above came from one.

## What it costs

Review doesn't disappear. It moves into defining done, using the product and choosing the checks: [the bill comes due](../../HUMANS.md#the-bill-comes-due-always). It's also harder to explain than "do a code review", because it happens at two points instead of one: before the agent starts, and after it finishes.

## Open questions

- **Does this carry over to a team?** At work I still use code review, on a mature project with small, focused changes. Dropping it there would need a trial, with the measures agreed up front.
- **When is a second agent enough?** On KS2 a second agent solves each new case. It catches unfair clues but not wrong answers. It makes a case better before I play it; it doesn't replace me playing it.
- **What does "use it yourself" look like when there's nothing to click?** A game and an editor are easy to use. A library or an API is harder.

## The projects

- **Llym:** a macOS code editor for reading code and sending line-level notes to AI command-line tools. TypeScript front end, Rust back end.
- **KS2 Detective:** a browser game of mystery cases for Year 5 children, where each clue is a short curriculum puzzle.
- **RendrGO:** a server-first React framework for sites built from a headless CMS's page-builder JSON.
