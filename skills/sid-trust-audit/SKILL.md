---
name: sid-trust-audit
description: Audit a codebase that was largely written by an AI agent and find out what actually stands behind it, under the rule "you can ship code you haven't read, but not behaviour you can't vouch for". Runs the checks, breaks the safeguards on purpose to see which ones bite, labels every safeguard as enforced, exists-not-enforced or convention, and ends with the smallest set of fixes, each with proof it works. Use this whenever the user asks whether they can trust their vibecoded or agent-built project, wants a safeguards, quality or confidence review of a repository, asks "what are the gaps?", "is this legit?", "is this ready to release?", or "what would a sceptical engineer say about this?", wants a case study of how a project was built with AI, or wants to re-run a previous trust audit to see what has changed. Not for dependency vulnerabilities on their own (use sid-dep-audit) or for reviewing a plan before work starts (use sid-plan-audit).
---

# Trust audit

You are auditing a project that you, or another agent, probably wrote most of. That makes you a fluent witness, not a reliable one: you will lean towards describing safeguards as if they exist and making "it seems to work" sound like a strategy. The whole method below exists to stop that. Every claim needs evidence you can point to, and anything you can't point to goes under Gaps.

The rule being tested: **you can ship code you haven't read, but not behaviour you can't vouch for.** Each piece of code should either be understood by a human, or sit behind an interface a human understands and be checked by tests a human owns.

Read `references/framework.md` before starting. It explains the three layers you audit against and the patterns earlier audits found, which tell you where to look hardest.

## The three labels

Label every safeguard with exactly one of these, and be strict about it:

- **Enforced:** a tool fails a run without anyone having to remember it, and that failure blocks something (a deploy, a release, a merge).
- **Exists, not enforced:** the check is there, but someone has to choose to run it, or its failure blocks nothing.
- **Convention:** a written rule (in `CLAUDE.md`, `AGENTS.md`, a skill, a doc) that the agent has been asked to follow. Nothing checks it.

A rule in agent instructions is a convention until you have shown a tool enforces it.

## Workflow

### 1. Ask before gathering

You can see what the repository records. You cannot see what the owner does, and the record is lopsided: agent work leaves commits and trailers, human work usually leaves nothing. An audit that skips this step will understate the human's role and misplace the risks.

Before running anything, give the user a short list of the evidence you plan to gather, then ask (in one message, briefly):

- Which parts of the code they read or understand, and which they don't (languages, packages, data files).
- What they do by hand that the repository doesn't record: playing through features, manual testing, reading particular files, release steps on their own machine.
- How code actually reaches users: is there a release or deploy step, and what gates it? (Don't assume CI is the gate. For a desktop app built locally, the owner's own build may be the real gate.)
- What "feature complete" and "production ready" mean for this project, if not written down.
- Whether this is still an experiment or something they intend to keep. That changes how strict the bar should be.

If a previous audit exists (look for `docs/trust-audit*.md` or similar), say so and offer a delta audit (see step 8).

Treat the answers as evidence and say where they came from ("owner's own description").

### 2. Overview and how it was built

Pin the audit to a date and commit (`git rev-parse --short HEAD`, branch, distance from `main`). Then gather:

- What the project is, its stack, and size per package or layer (lines of source and tests).
- How it was built: commit count and date range, how many commits carry an agent co-author trailer (a lower bound, not an exact figure), PR count and whether any have reviews or comments.
- Which parts the owner reads and which they don't, from step 1.

### 3. Risk profile

Name the two or three failures that would actually hurt, for this specific project, and where in the code they would happen. Think about who notices and when: a failure a user blames on themselves, or that leaks data silently, is worse than one that crashes loudly.

Then check where the risky code sits relative to what the owner reads. In every earlier audit, the highest risk sat in the part the owner didn't read. Say so plainly if that's the case here.

### 4. Run everything, then break it on purpose

**Run the checks** from a clean, uncached state (`--force` or equivalent): install, build, types, lint, format, tests, coverage, any project-specific verify scripts, and `npm audit` / `pnpm audit` / `cargo audit` where available. Record the command, the result and the time. Report failures exactly as they happened.

**Find out what actually runs, and when.** Read the CI config, the release or deploy script, and the verify routine in the agent instructions. Compare the agent's own verify list with everything that exists: earlier audits found verify routines that quietly skipped whole test suites. Check whether anything gates `main` (branch protection is often unavailable on free private repos: `gh api repos/{owner}/{repo}/branches/main/protection` returns 403) and whether deploys or releases depend on checks passing.

**Run violation drills.** This is the most valuable part of the audit. Use a throwaway git worktree (`git worktree add ../audit-scratch HEAD`), apply one violation at a time, run the same gates the project relies on, record what happened, then reset with `git -C ../audit-scratch` so the reset can never touch the real checkout. Format a changed file first so a formatting failure can't count as a catch. Remove the worktree at the end and confirm the real checkout is untouched (`git status --porcelain` empty). Never commit or push.

Aim for 6 to 12 violations chosen for this project. `references/violation-drills.md` lists the kinds that have proved most revealing. Always include at least:

- One violation per top risk from step 3.
- One rule from the agent instructions (a "golden rule").
- The **obvious fix** for a violation that gets caught. If a boundary error is caught, try the fix an agent would reach for next (declaring the dependency, a relative import, a cast). Rules enforced by friction get routed around.
- A change to stored data or a public interface made without the accompanying version bump or migration.

For each: the violation, what was expected to catch it, and what actually happened (caught, caught only in CI, caught only by a command nobody routinely runs, or passed every gate).

### 5. Audit the three layers

Work through `references/framework.md` layer by layer and build a table for each, with a location and a label for every row.

- **Layer 1, always-on checks:** what exists, what the violations proved, and what gates the release.
- **Layer 2, checkpoints:** what triggers a human to stop and look, whether anything triggers it mechanically, whether checkpoints leave a record, and whether interrogation has ended in evidence (tests, rules) or only in prose.
- **Layer 3, milestones:** whether "feature complete" is defined with a "not in this version" list, and how the project stands against the production-ready list.

Also check **what each check claims**. A green message can overstate what it proves ("valid and solvable" when only structure was checked). And check **what the project claims**: README, docs, marketing copy. For each behavioural claim, find the code and test behind it. Claims running ahead of code was one of the most serious findings in earlier audits.

### 6. Human checkpoints

List the interfaces and data a human needs to understand to vouch for behaviour without reading the implementation: public APIs, IPC or API contracts, schemas and stored formats, the effects of commands, the content users see. For each, judge whether the owner can realistically check it today, and why.

The strongest human checkpoint is usually a **small table of behaviour**: commands by effect, inputs to outputs, page data to headers, a feature summarised as cases. If one doesn't exist for a top risk, recommending it is often the highest-value fix. Also note whether changes to these files flag themselves (e.g. `CODEOWNERS`, snapshot tests), so the owner knows what to look at without reading every diff.

### 7. Gaps and recommendations

**Gaps**, ordered by the risk they leave open. Be specific and blunt. "It seems to work when used" is a legitimate answer; name it as such. Something that may happen but leaves no trace is "unproven, not absent". Don't soften.

**Recommendations**: the smallest set of changes that closes the most important gaps, in priority order. For each give the change, the gap it closes, a rough cost, and **proof it works**: usually re-running a named violation and showing it now fails. Also say what you deliberately left out and why.

When recommending gates, follow the owner's workflow rather than imposing one. Prefer a loud, shared CI signal plus a gate at the release or deploy step. Suggest git hooks only when there is no CI or no release step, and say why. If CI exists but the agent could keep building on a red `main`, recommend the agent's routine waits for CI and reads the result.

If the project has crossed from experiment to something being kept, say so: that's the moment the always-on checks should go in.

### 8. Delta audits

If a previous audit exists, re-run its violations first and report, per gap: closed (with evidence), partly closed, unchanged, or new. Keep the same violation numbers so the two audits can be compared. Finish with what changed and what to do next.

## Writing the report

Write it to `docs/trust-audit.md` (or a dated file if one exists) using the structure in `references/report-template.md`. Write for a sceptical senior engineer:

- Plain, direct British English. Short sentences. No marketing language or filler.
- Tables wherever things are compared. Every row has a file path, config entry or command.
- Distinguish clearly between what's enforced, what exists, and what's a convention.
- Never claim to have run, seen or verified something you didn't. If you couldn't run a check, say why.
- Credit the owner's unrecorded work only from what they told you in step 1, and attribute it.

End your reply to the user with three or four sentences: the honest verdict, the most important gap, and the single most valuable fix. Don't repeat the report.
