# **Confidence without code review**

(links to sid-trust-audit)

Traditional code review simply does not scale to the demands of agentic development. Humans cannot (and will not) manually review agent-written PRs with the same attention they would give to human-written PRs.

And would we want to? A slow, human-scale manual review would kill any productivity benefits brought by the AI.

So what do we do? Vibe freely and hope for the best? Here, I outline my thoughts and experience working across three vibecoded projects, to try and conceptualise a world beyond code review.

## What was code review for?

Code review was never the goal. Code confidence was. The question isn't "what replaces code review?" but "what gives me that confidence now?"

Peer code review is strong at catching architectural drift, refining the approach and spotting gaps in business logic. It has also been an important part of engineering culture for humans: training and sharing knowledge. But, in reality, code review is weak at enforcing conventions, finding bugs, and reliably catching critical errors, such as security flaws.

Code review assumed a human author who understood what they'd written. With agents, there may be nobody who understands every line. But we already ship plenty of code we've never read: React, database drivers, compilers, the OS. We trust them through clear interfaces, observed behaviour, tests and a limited blast radius (but we also trust that these tools have also undergone code reviews themselves!).

You can ship code you haven't read, but not behaviour you can't vouch for.

## The problem with all this

Code review is a really simple concept. Write code, review code, approve code. Regardless of whatever flaws it may have, it's an immediately understandable idea and easy to implement in some way.

The alternatives I've researched and in cases tried to put into practice (some of which are outlined below) are, in contrast, not yet simple to me. They are scattered across different touchpoints, a combination of various tools, discipline, and seemingly trial and error. The problem is I try to bring my (relatively limited) experience alongside what the LLM recommends when ask for best practice and solutions. It's just a mess of different things to try and incorporate and keep in mind.

One thing I've also found is that the AI agent has no idea what you the user are doing. I ran some trust audits on some projects and found the agents reporting things like "this is released without human approval" when that's not the case. I don't record every thing I do for the benefit of the AI. And some historical states and processes of the project get cleaned up or removed. Does this matter? I made a conscious decision NOT to bloat the project with a markdown file of every decision, every idea, with ongoing refinement to ensure only relevant docs are kept. This is my preference. But this is a reminder that the true "memory" of the project has to come from the human not the AI, which only sees a snapshot in time.

What follows are AI generated text based on my notes and conversations, with my new comments in square brackets (e.g. [SD: these are my notes])

## Guidelines?

Any piece of AI-generated code should either be understood by a human, or sit behind an interface a human understands and be checked by tests a human owns. Two caveats:
- The tests can't be written and judged only by the agent that wrote the code. A second agent helps, but it isn't independence. [SD: maybe we need to soften this so it doesn't read as if humans should write the actual test code]
- Code nobody understands should be regenerated rather than patched. That pushes towards small, well-bounded pieces. [SD: I don't really know what this means]

## Safeguard audits

Three labels for every safeguard

- Enforced: a tool fails a run without anyone having to remember it.
- Exists, not enforced: the check is there, but someone has to choose to run it, or its failure blocks nothing.
- Convention: a written rule the agent has been asked to follow. Nothing checks it.
Every rule in CLAUDE.md or AGENTS.md is a convention until a tool enforces it. Labelling each safeguard honestly is the quickest audit there is.

[SD: this is a nice way of working through the audit, and is applied in sid-audit-trust. But let's face it, this is merely agent doing code review...]

## Layer 1: always-on checks

The things code review was weak at get handed to tooling: types, linting, formatting, static analysis, unit tests, project rules written as lint rules (package boundaries, banned calls), and contracts at the edges (generated types, shared schemas, runtime validation). I define the boundaries and expectations; the tools enforce them.

Review kept standards in reviewers' heads, applied inconsistently. Tooling makes them explicit and applies them every time.

[SD: I think this repeats some of what I said in testing-with-confidence.md]

What the audits added:
- Encode the intent, not the friction. In KS2, pnpm blocks the engine importing React. But the obvious fix for that error, declaring the dependency, passes everything. An agent will take the easiest route around friction. The rule has to say "the engine never uses React".
- Know what each check proves. KS2's validator says "all valid and solvable", but "solvable" only means the suspect logic adds up, not that the answers are right. RendrGO's documented verify step quietly skipped the package-boundary and API tests. An agent's "all green" is only as good as the list it ran, so I check the list.
- Ask how the work was checked. When the agent hands work back, I want to know what it tested, how it confirmed the tests are valid, what it could check itself and what's untested.
- Run violation drills. Breaking things on purpose, in a throwaway worktree, revealed more in every audit than any description of the safeguards. It's worth repeating every so often.

[SD: I've been working through these audits to get a sense of them. It makes sense, but I feel I'm pulled in two directions. Adding elaborate tooling workarounds to try and formalise spec and rules and make it more testable (in more complex ways that are hard to validate if they're working properly), plus more pressure to validate and review and approve things. I'd go so far as to say an AI is unhelpful with this matter. The main outcome of this is finding gaps / bugs, which is important, but more of an ongoing review thing, which sometimes gets caught by an audit, and sometimes not]

Gate the release, not the commit

I'm not a fan of git hooks. I've been burned by "I committed late on Friday... oh, the hook failed". A failure that's loud and shared on CI is one I can see, pick up and get help debugging. A failure stuck on someone's machine isn't.
So CI on main is my loud, shared signal, and the hard stop goes where code leaves my hands: the deploy (as in KS2, where deploys need CI to pass) or the release script. Hooks are a fallback for when there's no CI or no release step.
One agent-specific wrinkle: a human sees CI go red, but an agent will happily keep building on a broken main. So the agent's routine should include waiting for CI and reading the result (gh run watch or similar) before it moves on.

[SD: I'm definitely not a fan of git hooks, but I've now started using it to enforce rules like "don't push on main" (if that can't be enforced by Github - free, private repo for example). I still think tests should live in the CI, but I do appreciate hooks as restrictions]

Layer 2: checkpoints

My main advice is "slow down". It sounds odd when the point is productivity, but speed is where the risk builds up. The agent makes an assumption, builds on it, then builds on that. A checkpoint is where I stop that pile-up and spend some time deep-diving: interrogating the agent, reading the code, or both. Not on every commit, and not every line.
"Checkpoint" has a useful double meaning: a point where you stop and inspect, and a known-good save point you can return to.

[SD: AI not letting any subtext go through unstated...]

When to do one

- Before something becomes hard to undo: a schema change, a migration, a public API, a release.
- When the work touches a risk area: auth, payments, user data, caching, external boundaries.
- When the agent surprises me: an approach I didn't expect, or a change I can't explain.
- Before building on something new: a new dependency, an unfamiliar pattern, a language I can't read.
- After a long uninterrupted run.
- When an experiment becomes something I'm keeping. Nothing marks this moment, which is why it gets missed. It's exactly when the always-on checks should go in.
The triggers shouldn't all live in my head. Tooling can flag them: Clippy's disallowed-methods makes every new remove_dir_all or sh -c stand out, and CODEOWNERS can flag any change to the files that matter. The tool doesn't judge the change; it just makes sure I look.

[SD: In general, checkpoints, I think, remain a good idea. As a term I think it does what "code review" does: blunt, but easy to grasp. But is it really all that insightful or useful?]

Ask for evidence, not assurance

[SD: this comes up time and time again when I have these discussions with the AI. I really need to drill into this as it's kind of meaningless if the assurance is from the claims of evidence. Essentially, the only real assurance is testing it again yourself. That's fine, but it's micro-managing]

Interrogating the agent is often more useful than reading the code: "How do we stop server code being imported into the frontend?", "How do we prevent future changes exposing auth-protected routes?" But an agent is a fluent witness, not a reliable one. Every question should end in something I can check: show me the rule, then prove a deliberate violation fails.

The best human checkpoint is a small table of behaviour

[SD: maybe. this means more docs, more specs to review and approve. And viewing a table in raw markdown isn't ideal. In my tests, the AI has incorporated specs in md into tests (so it tests against specifically stated values in the table of behaviour). I'm not sure how I feel about that]

Across all three projects, the most useful thing for a human to check was a short table: commands by effect (read, write files, run Git, start a process), page data and headers to Cache-Control, a case summarised as suspects and clues. Each is readable without knowing the code, and each can be backed by a test.
This also answers "what do I skim?". I don't decide per PR. I decide once which few files are the human-checkable interface, and make changes to them flag themselves. Then I read a handful of files per PR instead of 3,600 lines.

[SD: that's good in principle]

Checkpoints need to leave a record

The record is lopsided. Everything the agent does leaves a trail: commits, co-author trailers, PR descriptions. What I do (playing through a case, rewriting a line, deciding something) leaves nothing unless I record it. So any audit of the repository understates the human role, and a sceptical colleague sees the same record the agent does. The record should cost almost nothing: a PR checkbox, a line in the description, a Checked-by: trailer.

[SD: this came from an outcome of discussions and the flaw that the agents did not know what I was doing. However, the drawback is it adds noise to the codebase, which is something I've said elsewhere I want to avoid. In my pro work, I have a PR with "manual checks" checklist, generated by the AI and curated / marked by me, but in that project I am more likely to code review. It's also a mature project, so changes tend to be small and focused]

Layer 3: milestones

Alongside the small checkpoints I keep two big ones: feature complete and production ready. Each is really a pair: define it early, confirm it later. The defining is the hard part, and that's the point.
This matters most for vibecoding. Agents remove the friction that used to limit scope. When a feature cost an evening, you prioritised. When it costs one prompt, it's easy (and more fun) to keep adding cool stuff to a vague spec. These milestones force the boring slog of working out what "done" means.
Feature complete is specific to the project, and only I can define it. It needs a "not in this version" list: writing down what I'm not building is what turns a vague spec into a finish line. Once it's written, "what's missing against this?" is a far better question to ask the agent than "is it done?"
Production ready is mostly generic, and it's where the agent's idea of "done" differs most from mine. Agents build the happy path. Production readiness is everything else, so it can be a reusable template adjusted per project:
- Error handling, empty and loading states, error reporting
- Input validation and security, including an adversarial pass on the top risks
- Secrets management and dependency monitoring
- Logging and backups
- Performance on real data, with a threshold, not just a measurement
- Accessibility, checked with a tool or a screen reader
- Behaviour on a bad network
RendrGO taught me one more: claims are part of what I vouch for. Its marketing copy promised safer caching than the code delivers. Docs, copy and READMEs make behaviour claims, and each claim should point to a test, not to prose.

[SD: I think this is a mindset thing, which has certainly helped me. It's based on the idea that AI can generate a good looking "functional" product in a few minutes based on a flimsy spec, but taking it to "feature complete" and "production ready" requires real input from the user, real thought.]

Data: vibecode it, but make changes surface

I used to say "you can vibecode the interface to the data, but you can't vibecode the data structure". 

[SD: I'm not sure I used to say that. I did have one experience where I went badly down the wrong path vibecoding with an agent that had got the basics of the schema wrong. It's clearly an important touchpoint for some things, but as I later backtracked on this, in some cases (depending on who you are and your skill level) the AI may indeed be better at the data structure than you]

In reality people will vibecode the data structure, and it'll probably be fine. Models are good at boring, conventional schemas.
But "probably fine" is a risk judgement, and data is where the downside is worst. Code is disposable; data isn't. A bad function gets regenerated. A bad schema with six months of real data in it needs migrations, backfills and maybe an apology.
So: vibecode the data structure, but look at it. A schema is short, mostly language-agnostic, and changes rarely, at clear moments. Glancing at every migration is a bar people will actually meet.
The audits showed that this rule needs a mechanism, or there's nothing to glance at:
- Llym's stored notes and layout have no version at all. A format change would never show up as a migration.
- KS2 has proper save versioning, but changing the shape without bumping the version passed every check. A child would silently lose their progress.
The fix is cheap: commit a real current save (or record) as a frozen fixture and test that it still loads. Then any change to the format forces a migration, and the migration is what I look at.

[SD: in my defence, those two examples from my projects are not exactly the same as the problem I'm highlighting. That's more of a data migration issue and would more than likely have been picked up HAD I need to migrate the version. Also, in KS2 project, we DID change the save structure, but because it's still pre-release there's no need to add a full migration - I'd rather we kept only the target structure until release than keep a record of outdated shapes]

What the audits found

Each agent audited its own project, backed every claim with a file or a command, and broke the safeguards on purpose to see what held.
Project
Deliberate violations caught
The most telling miss
Llym
3 of 6
A new recursive delete or sh -c in Rust passed every check
KS2 Detective
6 of 13
A save-format change that would wipe a child's progress passed every check
RendrGO
7 of 9
A package-boundary breach passed the agent's own verify routine; only a test it doesn't run caught it
The patterns that held across all three:
- I did ask, but ad hoc. Every project had a moment where I stopped and asked what safeguards it needed: a security pass in Llym, a health check in KS2, spikes with kill criteria in RendrGO. The answers mostly became fixes and roadmap items rather than checks that run on their own.
- Experiments become products without a marker. All three grew from experiments into something I'm keeping, and nothing prompted the switch.
- Risk collects where my attention isn't. In Llym it's the Rust I can't read. In KS2 it's the case content, not the UI I worked on. In RendrGO it's the cache semantics behind the features I specified.
- Almost everything is "exists, not enforced" or a convention. None of the three has a hard gate on main (free private repos don't get branch protection). The real gates are my own build (Llym), the deploy step (KS2), or nothing yet (RendrGO).
- Claims run ahead of code. RendrGO's copy promised more than its cache logic delivers. I confirmed the intent; the agent built a narrower version.
- An agent's "all green" depends on the list it ran. It wasn't lying; its list was incomplete.
- My own work is invisible. I play every KS2 case before a PR, but the audit couldn't see it.

[SD: here's perhaps the tension here: I'm the one managing those projects as they fully form, not the agent. Yet some of these "findings" seem predicated on the sense that anything that's under my control is a risk. Don't get me wrong, the audit was useful in highlighting some areas of risk that had not been flagged in previous health checks, or some big gaps I didn't think to spec, or hadn't got around to planning yet.]

Case study: Llym

Llym is a native macOS code editor for reading code and sending line-level notes to AI command-line tools, with everyday Git built in. It's for me only. The UI is TypeScript and React, which I read. The logic is Rust (Tauri 2), which I don't.
It took six days: 109 commits, 104 of them co-authored by Claude, and about 24,000 lines of code. That speed is exactly why "slow down" matters.
How I work on it. There's no release plan yet. I build it on my own machine and use it, because that's the only meaningful way to test a desktop editor. There's a CI, but it exists out of habit. My release doesn't depend on it.
The honest verdict. The TypeScript half meets the framework. The Rust half, which holds every risk (writing files, running Git, starting processes), only partly does. The IPC types are generated from Rust, so I can read the shape of all 57 commands. But a type tells me the shape, not the effect: nothing tells me which commands write to disk or start a process without reading Rust.
What it taught me.
- Risk collects in the code I can't read, and that's probably no accident: the systems layer is where the dangerous operations live.
- A type contract isn't an effect contract. The fix is a table of commands by effect, kept honest by a test and written as Markdown I can review.
- Automation can trigger a checkpoint rather than replace it. Clippy's disallowed-methods won't judge a new remove_dir_all, but it makes sure I look.
- Stored data with no version means format changes never surface for review.
What I'd fix first: disallowed-methods for risky calls, the command-by-effect table, settling how Git behaves in untrusted folders, and ESLint for React hooks.

Case study: KS2 Detective

KS2 Detective is a browser game for Year 5 children (age 9 to 10). Each case is a mystery, and each clue is a short curriculum puzzle. Solving clues rules suspects out until one is left. It's a static site, played by family for now, with optional cloud save planned.
It's four weeks old: 84 commits, 18 of 42 planned cases, 250 tests, and a proper release pipeline where deploys only happen if CI passes.
How I work on it. I spent my time on the puzzle and case UI/UX. I haven't gone into how a case's JSON is structured. But I play through every new case and every puzzle before a PR is created.
The honest verdict. This is the most mature of the three, and the audit shows exactly which safeguards hold. Content is checked by Zod schemas and a solvability check, saves are versioned and validated, and secrets are scanned. But a wrong answer, a clue that depends on another clue, and a save-format change without a version bump all passed every check.
What it taught me.
- My biggest risk, wrong content reaching a child, is covered by a human check: me playing every case. The audit couldn't see it because nothing records it. A one-line checkbox on the PR would fix that.
- The stakes are real in a way the code doesn't show. As the audit put it, a child told they're wrong when they're right will probably blame themselves rather than report it.
- Agent checks agent isn't independence. The case-creation skill has a second agent solve each case, which catches unfair clues but not wrong answers.
- A check's message can overstate what it proves. "Solvable" meant the logic adds up, not that the puzzles are right.
- Gate the release, not the merge. Without branch protection, the deploy gate still keeps broken builds away from players.
- Write the checkpoint before the code. Before cloud save exists, write the two tests that must fail: one account reading another's data, and a write containing a child's name.
What I'd fix first: a frozen real save as a test fixture, the PR checkbox for playing every case, boundary lint rules, and upgrading zod, which has an advisory in a shipped dependency.

Case study: RendrGO

RendrGO is a server-first React framework for sites built from a headless CMS's page-builder JSON. The page data sets the HTTP status, redirects and Cache-Control, and interactive parts hydrate as islands. It isn't published yet.
It started as an experiment, and I just ran with it. Since mid-October: 47 commits (46 co-authored by Claude), 21 PRs and 930 tests. I hadn't even thought about whether it had CI. It doesn't.
How I work on it. In "rounds". The agent asks the open questions, each with a recommended option. I answer, it writes a plan, I approve it, and it implements, tests and updates the docs. Big unknowns get a spike with written kill criteria first. I define the features, answer the questions and approve the plans. I don't routinely read the code, the tests or the diffs.
The honest verdict. The process is the most disciplined of the three, and the checks are good when they run: type-aware linting, enforced package boundaries, a snapshot of the public API. But nothing makes them run. Today the trust is "the agent ran the checks, said they passed, and the playground looked right".
What it taught me.
- Pre-alignment done properly carries a lot. The quality here came from the round process, while the infrastructure never caught up, because there was no moment when it stopped being an experiment.
- Claims run ahead of code. The marketing copy says pages loaded with a visitor's cookies are kept out of shared caches automatically. The code only does that when cookies go through api(). I confirmed the intent; the agent built a narrower version. Nobody did anything wrong, and the gap is a potential cross-user data leak at CDN scale.
- "The checks passed" depends on which checks. The verify step in CLAUDE.md skipped the boundary and API tests.
- Decide once what to look at. CODEOWNERS on the API snapshot, the package map, the page schema and a cache-behaviour test table means a handful of files to read per PR instead of thousands of lines.
What I'd fix first: one verify command that runs everything, on CI; pinning down the cache-safety boundary with a table of page data and headers to Cache-Control; and adding operations (CI, a security pass, accessibility, benchmark thresholds) to the launch checklist.

Where the "code review is dead" ideas fit

[SD: these five phrases were from my initial brainstorming session with AI, which recommended a bunch of ways to replace code review. They didn't quite hit the mark for me]

My original research boiled the alternatives down to five phrases. As one-for-one replacements for code review, none of them work. But that was the wrong test. They're how you gain confidence in code nobody has read, and my projects use most of them already.
Idea
Where it fits
In my projects
Pre-alignment
The "define" half of milestones; the human-owned spec and interface
RendrGO's rounds; KS2's roadmap and exit criteria
Mirroring
A specialist tool for migrations and big refactors
Not used
Smart testing
Keeps always-on checks fast enough not to slow the agent down
Turborepo in KS2 and RendrGO
Stress testing
Checking the behaviour of unread code and generated data
KS2's solvability check is a step towards it
Contract sync
Enforcing interfaces at the boundaries
Llym's generated IPC types; KS2's Zod schemas; RendrGO's API snapshot
The one I dismissed too quickly was pre-alignment. RendrGO shows how far it can carry a project on its own.

Open questions

- How much of this carries over to a team? At work I still use traditional code review. Would I propose dropping line-by-line review on a professional project? If so, as a trial on one project, with the safeguards written down and the measures agreed up front: escaped bugs, incidents, time to ship, and how often checkpoints find something.
- Is a second agent ever enough? KS2's second-agent solve catches unfair clues but not wrong answers. Where does agent-checks-agent stop being useful?
- How cheap can the human record be? A checkbox, a trailer, a line in the PR. What will I actually keep doing?
- How do I notice the experiment-to-product moment? All three projects crossed it without my noticing. Is there a signal, such as the first real user, the first deploy, or the first time I'd be upset to lose it?
- Can behaviour tables be generated rather than written? If the table of commands by effect, or of page data to headers, comes from the code and is checked by a test, it stays honest without anyone maintaining it.

[SD: I think agent-checks-agent is a part of what we'll do and, in the case of the KS2 project, it's a useful sanity check and means when it comes to me reviewing it, the clues are more refined than they would otherwise be. How chepa can the human record be? That is a question as I'm not convinced we need it, beyond the focus of the audit prompt. How do I notice the experiment-to-product moment? It's a strange assumption from the AI that I crossed this threshold without noticing. Can behaviour tables be generated rather than written? Surely this creates a weird loop, where the markdown informs the code that is used to generate the markdown. This goes against my code is the source of truth principle and I think I need to clamp down on this]
