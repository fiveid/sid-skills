# **Parallel development**

*The principle behind this guide is in [HUMANS.md](../../HUMANS.md#parallel-development).*

Sitting and waiting for an agent to finish its task, just to click approve and then wait for the next job to finish, leads to developer fatigue. It can kill motivation and productivity, while still introducing the same risks detailed in [HUMANS.md](../../HUMANS.md#risks).

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

