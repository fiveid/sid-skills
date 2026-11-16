# **Building without a coding background**

*The principles behind this guide are in [HUMANS.md](../../HUMANS.md). That document assumes some software engineering experience; this one doesn't.*

You don't need to know how to write code to build software with AI. You do need to know how software breaks, where the traps are, and how to put automatic checks in place before things get messy.

Treat this as a map of the pitfalls. You don't need to memorise how each guardrail works, only to recognise the moment to ask the agent to set one up. Once the basics are in place, move on to the [Human Guidelines for AI Development](../../HUMANS.md).

A few terms come up throughout:

* **Agent:** the AI tool that reads and edits your project (Claude Code, Cursor, Codex and so on).
* **AGENTS.md:** a file of project instructions the agent reads at the start of every session. Some tools use their own name for it (Claude Code reads `CLAUDE.md`). Each session starts from scratch, so anything you want followed every time belongs in this file, not in the chat.
* **Guardrail:** a check that runs automatically and fails loudly. Agents don't always follow instructions; a script that blocks a bad change does its job whether or not the agent remembered the rule.

## **1. Save points (version control)**

* **What it is:** Git keeps a history of your project. Each *commit* is a save point you can go back to.
* **The AI trap:** The agent breaks a working feature while fixing an unrelated bug, and you don't notice until three changes later. Without save points there's no clean way back, only asking the agent to remember how the code used to work.
* **Your rule:** Every time something works, commit it before asking for the next feature. Put the habit in AGENTS.md so every new session follows it. If the agent hasn't fixed something after two attempts, stop prompting, throw away the changes and go back to the last working commit. Push your commits to a private repository (on GitHub, for example) so your save points survive a lost laptop.
* **What to ask the AI:**
  * "Initialise Git, commit our current working state, and add version control rules to AGENTS.md: commit small working changes often with clear messages, never commit broken code, and check `git status` before starting a new task."
  * "Throw away all uncommitted changes and take us back to the last working commit."
* **Level up:** Work on *branches*: separate copies of the code where a feature is built and checked before it joins the main version. Branches let agents work on several tasks at once without tripping over each other, and give you a point to review a change and run the automated checks (section 3) before it reaches the main version. Ask the agent to propose a branching workflow, and to ask you questions about your priorities before it picks one. [Parallel development](parallel-development.md) describes one setup.

## **2. Keep the code organised (architecture)**

* **What it is:** Splitting code into small files that each do one job, in a folder structure that makes it obvious where things live.
* **The AI trap:** Agents add to whatever file they're already in. Left alone, one file grows to thousands of lines. The agent loses track of what's inside, duplicates logic it can't see, and deletes code that was still in use.
* **Your rule:** Set the structure at the start, before the first feature, and back it with automatic limits. A *linter* (a tool that checks code against a set of rules) can fail when a file grows too large or a function too complicated. A rule the linter enforces holds; a rule in AGENTS.md is a suggestion.
* **What to ask the AI:**
  * "Before we write feature code, propose a simple folder structure for this project and explain it in AGENTS.md. Set up linter rules that fail if a file or function grows too large or complex."
  * "This file is too large and doing too much. Before changing anything, write tests that pin down how it behaves now. Then split it into smaller, single-purpose files without changing that behaviour, and show me the tests still pass."
* **Level up:** Once the app does several distinct jobs (accounts, billing, notifications), separate them by responsibility: each in its own folder or package, with its own short AGENTS.md and tests that run on their own. Then ask for lint rules that stop one area reaching into another's internals, so the boundaries hold without anyone having to remember them. For larger projects, ask the agent whether a *monorepo* (one repository holding several packages) would help.

## **3. Automated checks (linting, formatting and tests)**

* **What it is:** Scripts that check for mistakes, messy formatting and broken behaviour, so you don't have to click every button after every change.
* **The AI trap:** The agent says "everything is fixed" when half the app has just broken. Or it writes tests that pass whatever the code does, because they check the agent's own fake data instead of the real app.
* **Your rule:** Set up the checks early, run them on every change, and don't accept "it works" from the agent unless passing checks back it up.
* **What to ask the AI:**
  * "Set up a linter, a code formatter and a test runner so one command checks everything. Add that command to AGENTS.md as the thing to run before saying a task is done."
  * "Write a test for this new behaviour. Run it first to prove it fails, then write the code to make it pass."
* **Level up:**
  * **Decide what to test yourself.** Write the behaviours that matter as plain sentences ("a user who enters the wrong password sees an error and stays logged out") and give them to the agent before it writes any code.
  * **Check the tests can fail.** Ask a separate agent session to break the code on purpose and see whether the tests notice. This is *mutation testing*, and there are tools that automate it.
  * **Run the checks on every push.** CI (continuous integration, such as GitHub Actions) runs the checks on every change and can block a failing one from being merged, however confident the agent sounds.
  * **Ask for a manual checklist.** With each feature, ask the agent to list what tests can't prove (layout, wording, how it feels to use) for you to check before release.

  [Testing with confidence](testing-with-confidence.md) goes further. The [`sid-quality-gate`](../../skills/sid-quality-gate/SKILL.md) and [`sid-test-review`](../../skills/sid-test-review/SKILL.md) skills automate parts of this.

## **4. Reviewing when you can't read code**

* **What it is:** Judging whether a change is safe from what it does and what it touched, without reading every line.
* **The AI trap:** Accepting a large change because the code looks neat and the explanation sounds confident, or getting stuck on syntax instead of behaviour. Agents write fluent, technical-sounding explanations whether they're right or wrong. The warning signs are simpler: the change took longer than you expected, or touched more files than the task needed.
* **Your rule:** You don't need to read every line, but you do need to know the boundaries of a change. If changing a button colour touched the database, reject it. If the explanation doesn't make sense to you, ask for a simpler one. If it still doesn't, the change is probably more complicated than it should be.
* **What to ask the AI:**
  * "Summarise what you just changed in plain English: what goes in, what comes out, which parts of the app it touched, and how it could fail."
  * "This solution feels over-engineered. Is there a simpler, more standard way to do this with fewer moving parts?"
* **Level up:**
  * **Predict before you prompt.** Before the agent starts, note which parts of the app you expect it to touch. Compare that with its summary afterwards; a mismatch is your cue to ask why. Over time this builds your own map of the codebase.
  * **Get a second opinion.** Start a fresh session, or use a different model, and ask it to review the change against your original request without showing it the first agent's explanation. An agent reviewing its own work tends to agree with itself.
  * **Keep changes small.** A change you can check in five minutes gets checked. One that takes an hour gets skimmed.

  The [`sid-pr-prep`](../../skills/sid-pr-prep/SKILL.md) skill writes this kind of summary, with a manual checklist. [Hierarchy of verification](../proposals/hierarchy-of-verification.md) covers where to spend review time.

## **5. Debugging without guessing**

* **What it is:** Finding out why something broke from evidence, rather than asking the AI to guess.
* **The AI trap:** Telling the agent "it doesn't work, fix it". It has to guess, and guesses usually introduce new bugs.
* **Your rule:** Always bring evidence. For a web app, open your browser's developer tools (right-click the page, choose Inspect, then the Console tab), or look in the terminal where the app is running. Copy the exact error message and paste it to the agent. If it's still stuck, make it trace the problem before it rewrites anything.
* **What to ask the AI:**
  * "Here is the exact error from the console: [paste error]. Don't write any code yet. Explain why this is happening and what the root cause is."
  * "Add temporary logging at each step of this process so we can run it and see exactly where the data stops or goes wrong."
* **Level up:**
  * **Turn every bug into a test.** Before the fix, ask for a test that reproduces the bug and fails. Once the fix is in, it passes, and the bug can't quietly come back.
  * **Find when it broke.** If something used to work, your save points can find the change that broke it. Ask the agent to use `git bisect`, which steps through your commits between a working and a broken version until it finds the one responsible.
  * **Let the agent see for itself.** Many agent tools can now open your app in a browser and read the errors directly. The agent can then check its own fix instead of asking you to.

## **6. "Works on my machine" vs real users (the production gap)**

* **What it is:** The gap between an app running on your laptop and one on the public internet, used by real people.
* **The AI trap:** The agent builds something that works for one user (you), with fake data, fast local loading and no security. It feels 95% done. For real users it can be nowhere near.
* **Your rule:** Before sharing the app with anyone, run a production-readiness audit tailored to what it actually does: logins, payments, storing data, calling other services, limits on use.
* **What to ask the AI:**
  * "Review our codebase and architecture, then write a production-readiness checklist for this project. Cover data isolation between users, what happens when an external service fails, whether data survives a restart, limits on cost and abuse, and anything specific to our stack. Then audit the code against it."
* **Level up:**
  * **Don't let the agent mark its own homework.** Run the audit in a fresh session, or with a dedicated skill such as [`sid-trust-audit`](../../skills/sid-trust-audit/SKILL.md), and ask it to try to break the app: log in as one user and try to see another's data, put nonsense into every form, cut the connection halfway through a payment.
  * **Keep a separate test copy.** A *staging* environment is a copy of the app with its own database and test keys, where you try changes before real users see them. Keep the agent away from the real (*production*) data and keys (see section 7).
  * **Plan for things going wrong.** Automatic database backups (and try restoring one at least once), error tracking so you hear about crashes before your users tell you, and spending limits on every paid service.
  * **Bring in a human.** If the app takes payments, or stores health data or other people's personal information, pay an experienced engineer to review it before launch. Some of this also carries legal obligations (data protection law such as GDPR, for example) that an agent won't raise unless you ask.

  [Project lifecycle](../proposals/project-lifecycle.md) has an example checklist for the production phase.

## **7. Passwords, keys and secrets**

* **What it is:** API keys, database passwords and tokens that let your app talk to other services, often paid ones (OpenAI, Stripe, your database host).
* **The AI trap:** The agent writes a key straight into the code. Once that code is pushed to a public repository or deployed, anyone can read the key. Bots scan public repositories for leaked keys around the clock, and can be using yours within minutes and running up a large bill.
* **Your rule:** Secrets never go into code files or chat prompts (anything pasted into a chat is sent to the AI provider and saved in logs). Don't rely on memory or the agent's discipline: scan every commit for secrets automatically, so a leaked key is blocked before it leaves your machine. If a key was ever committed or pasted into a chat, treat it as exposed: create a new one and delete the old. Removing it from the code doesn't remove it from the save-point history.
* **What to ask the AI:**
  * "Check the whole codebase for hardcoded secrets and move them to a `.env` file listed in `.gitignore`. Then set up a Git pre-commit hook with Betterleaks (or another secret scanner) so any commit containing a secret is blocked. Tell me which keys were ever committed, so I can replace them."
* **Level up:**
  * **Scan in CI too.** A pre-commit hook can be skipped. Run the same scanner in CI, and turn on push protection if your Git host offers it (GitHub does).
  * **Keep keys out of plain-text files.** A password manager can hold your keys and supply them only while the app runs, instead of leaving them in a `.env` file the agent can read. 1Password, for example, can ask you to approve each use.
  * **Make a leak cheap.** Use keys with the narrowest permissions and shortest expiry the job allows, and set spending limits on anything that bills by usage.

  [Secrets in the agent's environment](secrets.md) covers this in more depth.

## **8. Using other people's code (dependencies)**

* **What it is:** Packages written by other developers, so you don't have to build things like login screens or calendars from scratch.
* **The AI trap:** Agents install large packages for small problems, pick brand-new (possibly compromised) or abandoned ones, or invent package names that don't exist. Attackers publish malicious packages under those invented names (*slopsquatting*), so an install the agent got wrong can still succeed. These packages are usually only days or weeks old, with almost no downloads.
* **Your rule:** Wait a week before using a new release, prefer a few lines of code over an obscure single-maintainer package, and commit before updating anything. Most compromised releases are caught and pulled within hours; a week's wait means someone else finds them first. If a new release fixes a security problem you're exposed to, make an exception for that one package.
* **What to ask the AI:**
  * "Configure our package manager (or add rules to AGENTS.md) to block installing package versions published less than 7 days ago. Before adding any new dependency, check it exists under exactly that name, and tell me if the package itself is less than a month old, is outdated, has low download numbers or has a single maintainer, and whether we can solve the problem without it."
* **Level up:**
  * **Commit the lockfile.** A *lockfile* (such as `package-lock.json`) records the exact version of every package, so every install gets the same code. Make sure it's committed and CI installs from it.
  * **Update little and often.** Tools such as Renovate or Dependabot open one small update at a time, each run through your checks (section 3), instead of one big, risky update every few months. Set them to the same waiting period.
  * **Check for known vulnerabilities.** Ask the agent to add a vulnerability scan (such as `npm audit` or osv-scanner) to CI.

  For npm projects, the [`sid-dep-audit`](../../skills/sid-dep-audit/SKILL.md) skill audits dependencies for these risks.
