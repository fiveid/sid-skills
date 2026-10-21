# **Parallel development**

*The principle behind this guide is in [HUMANS.md](../../HUMANS.md#parallel-development).*

Sitting and waiting for an agent to finish its task, just to click approve and then wait for the next job to finish, leads to developer fatigue. It can kill motivation and productivity, while still introducing the same risks detailed in [Risks and mitigations](risks-and-mitigations.md).

I've found working with AI more rewarding and engaging when running agents in parallel. However, as tempting as it is to open a session for each ticket in the sprint and just let them go at it, this will lead to a review bottleneck up ahead, and difficult context switching as your attention hops between potentially dozens of agents asking questions.

Running parallel worktrees has worked for me, up to a point: a handful of independent lanes, each bounded to its own domain, with one kept for hands-on human work. The limit is how much I can properly review, not how many agents I can start.

Personally, the balance I have found is a maximum of 4 streams on a main project, with an optional fifth side-stream:

| Lane | What runs there |
| :---- | :---- |
| 1\. Feature A | One bounded, single-purpose task working from an approved checklist |
| 2\. Feature B | An independent task in a different domain, with its own branch, ports and, if needed, test database |
| 3\. Background audit | Low-priority analysis (dead code, dependency pruning, lint fixes, missing types) to review later |
| 4\. Main tree | Hands-on human work: architecture decisions, spikes and local verification |
| 5\.  Side Project | Side projects or tooling experiments, in separate directories and repos |

In my case, I had to spend a bit of time working with the agent to create instructions and scripts that allowed agents to work in parallel without friction. This was worth it.

## **Running the app in parallel lanes**

The friction shows up as soon as more than one lane needs to run the app. Worktrees compete for the same ports, several dev servers running at once eat memory, and if each lane also runs its own local backend, the machine runs out of headroom quickly.

The details depend on the project, but these are the ideas I'd look to support from the start on a new one:

* **Share the backend, not the frontend.** Point the agent lanes at one upstream source rather than a local backend each: ideally a read-only API serving public data, or a mock server if there's no safe upstream. This saves the most memory, and lanes can't collide on migrations or test data. The limit: it only suits frontend-only tasks. A branch that needs a backend change that hasn't been deployed upstream can't be tested this way.  
* **Build to verify; keep dev mode for the human.** Agents don't need hot reloading, so agent lanes run a production build instead of a dev server. It uses less memory once running, sits closer to production, and a failed build is evidence in itself. Builds still spike memory briefly, so with more lanes it may be worth making them take turns. Dev mode stays in the main tree, where a person is iterating.  
* **Let a script own ports and processes.** A helper script picks a free port for each lane, starts the build, and knows how to stop it again. Leaving this to instructions works until the agent forgets, and then a stale server holds a port or memory for hours.  
* **Hand back a URL per lane.** The agent finishes by giving me the lane's URL to check. Note that cookies on `localhost` are shared across ports, so lanes can clobber each other's sessions. A hostname per lane (e.g. `feature-a.localhost:3001`) keeps them apart.  
* **Keep credentials boring.** If the upstream is read-only and public, the lanes need no real secrets at all. If a lane needs a write token to work, that's a sign it belongs in the main tree.

### **Example: a headless frontend**

On a large headless project (Next.js Pages Router with Storybook, plus a local CMS), running more than one `next dev` at a time quickly hit both port clashes and memory limits.

My current setup is a `wt-preview` rule in `.claude/rules`, plus helper scripts. Each worktree's frontend points at the upstream's public, read-only page API instead of the local CMS. The script picks the port, the agent builds for production and serves it, and then gives me the URL to test against. In practice that's two agent worktrees plus the main tree, with brief memory spikes during builds.


### **Prompt: setting this up on your own project**

This is roughly the brief I'd give an agent to build something similar for a different project. It's distilled from building my own setup and hasn't yet been run from scratch elsewhere, so expect to adjust it.

The important part is stage 2: the agent measures the options and stops, and you choose.

```text
I run several coding agents in parallel, each in its own git worktree. I want each worktree
to be able to build and run its own copy of the frontend, so an agent can check its changes
in a browser without disturbing my main local setup or the other worktrees.

Work in three stages. Stop after stages 1 and 2 for me to review.

1. Investigate (read-only)
   - How does the app run locally today: dev server, containers, ports, backend?
   - What stops a worktree running it now: port clashes, mounts pointing at the main
     checkout, a shared local backend?
   - How much memory is available, and how much does my main setup already use?
   - Is there a remote environment we could read data from instead of a local backend?
     Is it read-only, and does it serve only public data?

2. Measure and compare
   - Measure the time and peak memory of each realistic option, e.g. a dev server per
     worktree, a production build plus server, a static Storybook build vs its dev server.
   - Present a table: memory held while running, peak memory, feedback loop, what it can
     and can't check, and any repo changes needed.
   - Recommend one, then stop. I'll decide.

3. Build the chosen option as one helper script, aiming for:
   - The script owns ports: a stable port per worktree, refusing to start if it's taken.
   - One heavy job (install, build) at a time across all worktrees, using a lock.
   - A free-memory check before each heavy job, keeping a reserve for my main setup.
   - Each preview runs as one process group with an idle timeout, so stopping it leaves
     nothing behind.
   - Commands for up, down, status, logs, and prune (clean up previews whose worktree is gone).
   - With a remote upstream: proxy it on the server side, rewrite its absolute URLs to the
     preview's own, and block writes by default. Only allow POST endpoints you've checked
     are read-only.
   - A hostname per worktree if the app relies on cookies, because cookies on localhost
     are shared across ports.
   - Optionally, a headless page check (screenshot, console errors, failed requests), so
     you can verify a page without me.

Constraints:
- No real secrets. It must work without production or write credentials.
- Don't install anything on my machine outside the project. Prefer containers or the
  project's existing toolchain.
- Keep it opt-in and out of the shared repo unless I say otherwise (e.g. untracked and
  excluded via .git/info/exclude). No changes to CI or other developers' setups.

Watch for:
- Build-time config (e.g. NEXT_PUBLIC_* in Next.js) is baked in, so set per-worktree
  ports and upstream URLs before building.
- When memory runs out, the OS often kills the biggest process, which may be my main dev
  server rather than the worktree that caused it. Dev server caches can grow large enough
  to trigger this on their own.
- Headless browsers in containers can render no text at all without a font config.

Finish with a short README (commands, URLs, limits), an ADR recording the options,
measurements and decision, and the instructions you'll need in future sessions, added to my
local, untracked agent instructions (e.g. CLAUDE.local.md).
```

### **Stack-specific tips**

If your stack matches, paste the relevant tips under the prompt, as options to measure rather than conclusions. The numbers are single runs on one large project and one machine, so treat them as rough.

* **Next.js: serve a `standalone` build.** With `output: 'standalone'`, a production build runs as a small Node server. Mine sat at about 0.2–0.3 GB, against 2–2.5 GB for a warm dev server (peaking at about 3.7 GB). The build itself took about 60s and peaked at about 1.6 GB.  
* **Storybook: build statically and serve the files.** A plain file server over `storybook-static` held about 20 MB, against 1.3–2 GB for the Storybook dev server. Keep the dev server for when you're iterating on a component yourself.  
* **Storybook: use a test build for checks.** `storybook build --test` keeps every story but drops the docs pages, autodocs and other docs-only features. It roughly halved build time (21–25s against 47s) and cut peak memory (about 2.7 GB against 3.3 GB). The same story rendered pixel-identical from a full build, a test build and the dev server, so it's fine for visual checks. Run a full build when the docs pages are what you're checking.  
* **pnpm: share the store between worktrees.** Each worktree still gets its own `node_modules` and lockfile, but the default store is content-addressed, so sharing it is safe and installs in a new worktree are quick.
