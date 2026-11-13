# **Project and personal skills**

**Status:** Proposal. I'm using the three-way split below in my own projects. The middle kind has no good tooling yet, and what a team commits needs a team decision.  
**Responds to:** [new attack vectors](../guides/risks-and-mitigations.md#new-attack-vectors) and [review fatigue and automation bias](../guides/risks-and-mitigations.md#review-fatigue-and-automation-bias).

Skills are cheap to write and cheap to install. Committing one to a shared repo isn't free, and the cost lands on the whole team:

* **Context and triggering.** Every skill's description competes for the agent's attention. The more there are, the more often the wrong one fires, or none does.
* **Review and upkeep.** Someone has to read each skill, and keep it current as the codebase changes. A stale skill is confidently wrong.
* **Supply chain.** A third-party skill is instructions, and often scripts, that run with each teammate's permissions.
* **Behaviour you didn't choose.** A teammate's agent starts following someone else's preferences without them deciding to.

So the question for each skill is not "is it useful?" but "does this project need it, or do I want it?"

## **Three kinds of skill**

| Kind | Who needs it | Where it lives |
| :--- | :--- | :--- |
| 1\. Project skill | Anyone working on the project | Committed to the repo |
| 2\. Personal skill for one project | Me, on this project | In the project folder, but not committed |
| 3\. Personal skill for any project | Me, everywhere | Installed globally |

## **1. Project skill**

The skill only makes sense in this repo, and the project depends on it.

*Example:* `shopfront-add-migration` walks the agent through adding a database migration the way this project does it: run the project's generator script, follow its naming scheme, update the seed data, then run the rollback check in `scripts/`. Anyone changing the schema needs it, and none of it applies to another repo.

Commit it, and review changes to it like code. If teammates use different agents, keep one copy in `.agents/skills/` and symlink the other agents' folders to it (see [Where skills live](../guides/managing-and-sharing-skills.md#where-skills-live)).

## **2. Personal skill for one project**

The skill is specific to this project, and specific to me: my queue, my knowledge, my accounts, my admin. The next person in my role would have to rewrite it before it was any use to them.

*Example:* `shopfront-next` answers "what should I work on next?" It reads the project board, filters to tickets assigned to me, and ranks them by the project's priority labels and my open PRs. The board is shared, but the filters are about me.

*Example:* `shopfront-explain-backend` is for when I, as a front-end developer, have to read this project's PHP. It explains the back-end code in terms of what I already know ("this controller is like a route handler"). Another developer's gaps would be different, and a back-end developer would find it patronising. It's about me, not the code.

**The problem:** the skill has to sit in the project folder for the agent to find it, but it shouldn't be committed. Git can ignore it without a shared `.gitignore` change (list it in `.git/info/exclude`), but then nothing versions it or backs it up. Delete the folder and the skill is gone.

Neither skills.sh nor APM has a layer for this. Both assume what you install into a project is recorded in a file you commit. What's missing is something like a `settings.local.json` for skills: project-scoped, personal and uncommitted. In the meantime, I keep one private repo for all my project-specific skills, a folder per project, and copy them in by hand.

## **3. Personal skill for any project**

The skill reflects how I work, wherever I am: how I audit a plan, how I write a PR description. It's my choice, and teammates' agents behaving a little differently from mine is fine.

Install them globally (`npx skills add ... -g` or `apm install -g ...`).

## **Deciding which kind**

A skill is a project skill if any of these is true:

* It references files, services or instructions that exist only in this repo.
* CI, a documented workflow or a teammate's work depends on it.
* A reviewer would need it to understand or reproduce an output.

If none is true, it's personal, however useful it is. To tell the two personal kinds apart, ask whether it would work in another repo. If you're not sure, start personal. Promoting a skill later is easy; removing one people have come to rely on isn't.

A personal skill that's specific to one project can still be a project skill in disguise. Ask: **would the next person in my role want it as it is?** If yes, commit it, or at least offer it to the team.

### **Examples**

| Skill | What it does | Where | Why |
| :--- | :--- | :--- | :--- |
| `shopfront-add-migration` | Adds a database migration using the project's generator, naming scheme, seed data and rollback check | Commit | Anyone changing the schema needs it, and it depends on the repo's scripts |
| `shopfront-debug` | Narrows a bug down to front end or back end using the project's logs and API endpoints | Commit | Every developer on the project asks this question. It started as one person's routine and was promoted |
| `shopfront-new-component` | Scaffolds a component with the project's design tokens, Storybook story and test helpers | Commit | The next front-end developer would want it as it is, even if only one person uses it today |
| `shopfront-release` | Runs the release steps: changelog, version bump, smoke tests | Commit | A documented workflow depends on it, whoever does the release |
| `shopfront-image-prompts` | Writes prompts for an image-generation service, then reviews and processes the results | Commit | It references files that exist only in this repo, and the output is only used here |
| `shopfront-add-copy` | Adds new UI text to the locale files in the project's format and flags missing translations | Commit | Anyone adding UI text needs it |
| `shopfront-next` | Ranks my assigned tickets by the project's priorities and my open PRs | Project folder, not committed | The board is shared, but the filters are about me |
| `shopfront-explain-backend` | Explains the project's back-end code in terms a front-end developer already knows | Project folder, not committed | It's built around my knowledge gaps, not the code |
| `shopfront-reset-test-customer` | Resets my staging test customer: basket, orders, the vouchers I test with | Project folder, not committed | Each developer has their own test customer |
| `shopfront-where-was-i` | Reads my gitignored notes, current branch and open PRs, then summarises where I left off | Project folder, not committed | It reads files only I have |
| `shopfront-timesheet` | Drafts my timesheet entries from my commits and tickets, using my billing codes for this project | Project folder, not committed | Billing codes and reporting lines are personal |
| `shopfront-weekly-update` | Turns my week's work into the format my project manager asks for | Project folder, not committed | It's an arrangement between me and one person |
| [`sid-plan-audit`](../../skills/sid-plan-audit/SKILL.md) | Questions an implementation plan for hidden decisions and missing guardrails | Global | It's how I review plans, in any repo |
| [`sid-pr-prep`](../../skills/sid-pr-prep/SKILL.md) | Drafts PR descriptions the way I like them | Global | My style travels with me. A project's PR rules belong in its instructions |
| [`sid-summarise-activity`](../../skills/sid-summarise-activity/SKILL.md) | Summarises my commits and PRs for a sprint review or timesheet | Global | The general version of `shopfront-timesheet`, with no project details |
| [`sid-scout`](../../skills/sid-scout/SKILL.md) | Explores an unfamiliar codebase read-only and writes a short context snapshot | Global | Useful at the start of any task, in any repo |
| [`sid-review`](../../skills/sid-review/SKILL.md) | Reviews front-end code against my own list of layout bugbears and anti-patterns | Global | It's openly opinionated: my taste, not a team standard |
| [`sid-pii-check`](../../skills/sid-pii-check/SKILL.md) | Scans my changes for personal info, local paths, client names and secrets before I commit | Global | A habit I want in every repo, whatever the project's own checks are |

**Every committed skill needs an owner:** someone who keeps it current and removes it when it stops earning its place.

## **Skill or project instructions?**

Some things written as skills are really project rules. Take a `create-pr` skill that says: include evidence the change works, and add a manual review checklist for a human to approve. That's a rule for every PR, not a procedure the agent should reach for sometimes. It belongs in the project instructions (`AGENTS.md`, `CLAUDE.md`).

The difference is when the agent reads it. Project instructions load at the start of every session. A skill loads only when the agent decides its description matches the task, so a rule kept in a skill can be skipped without anyone noticing.

| What it is | Where it goes |
| :--- | :--- |
| A rule that must hold every time | A CI check, because [instructions are suggestions](../../HUMANS.md#instructions-are-suggestions) |
| A rule every session should follow | Project instructions, kept short because they're always in context |
| A procedure used for some tasks, often with scripts or reference files | A skill |

## **Naming skills so they don't clash**

Skills are found by folder name, so two skills with the same name can't sit side by side. APM stops the whole install when a different skill with the same name is already in the destination folder (see the [gotchas](../guides/managing-and-sharing-skills.md#gotchas)). Generic names are the ones most likely to collide: a project skill called `release-notes` will clash with the `release-notes` skill your organisation later rolls out to every repo.

Prefix every skill with where it comes from:

* **Skills for one project, committed or personal:** the project name, e.g. `shopfront-add-migration` or `shopfront-next`.
* **Personal skills for any project:** your own prefix. Mine use `sid-`, e.g. `sid-plan-audit`.

A prefix also tells a teammate, or you in six months, where a skill came from and who to ask about it.

## **Shared third-party skill sets**

There's an understandable attraction towards "everyone should install this set" when someone finds a popular collection. A package manager with a team manifest, like APM, makes that a one-line change. The cost of that line falls on everyone else.

A team-wide third-party skill should clear the same bar as a new dependency:

* **A reason it's shared.** What goes wrong for the team without it? "It's good" makes it a personal skill.
* **A named owner.** Who reads it before it's added and reviews each update?
* **Pinned, not tracked.** A tag or commit in the lockfile, not `main`.
* **Removed when unused.** If nobody can say when it last helped, take it out.

## **Open questions**

* **Tooling for personal skills tied to one project.** Is there a cleaner pattern than excluding files and keeping a private repo? A user-level manifest keyed by project would cover it, but I haven't found a tool that offers one.
* **Promotion.** When a personal skill turns out to be useful to others, what's the path to committing it? Probably the same as any proposal to the team: show what it does, name an owner, agree to try it.
