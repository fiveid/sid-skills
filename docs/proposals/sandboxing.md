# **Sandboxing**

**Status:** Proposal. My leaning is sandboxed by default. Needs a team decision on which level to use and whether to enforce it.  
**Responds to:** [secrets exposure](../guides/risks-and-mitigations.md#secrets-exposure) and [new attack vectors](../guides/risks-and-mitigations.md#new-attack-vectors).

Why sandbox the agent:

* **Contain mistakes.** An agent with your permissions can delete or overwrite files outside the project, install things globally, or change system settings. A sandbox limits it to the project.
* **Keep other credentials out of reach.** SSH keys, cloud CLI logins, browser sessions and `.env` files in other projects all sit on the same machine. Anything the agent can read can end up in its context or logs, or be sent elsewhere by a prompt injection.
* **Control where data can go.** A network allowlist stops the agent sending data to, or downloading from, hosts you haven't approved. Allowed hosts can still be misused, so keep the list short.
* **Approve less.** With hard limits in place, the agent can run without you approving every command. That cuts the approval fatigue that leads to clicking yes without reading.

The question is where to draw the line. Each level below puts more of the agent's work inside the sandbox.

| Level | What's inside the sandbox |
| :---- | :---- |
| 1\. Commands only | The shell commands the agent runs. The agent itself, its file tools and MCP servers stay on your machine. |
| 2\. Whole agent, shared folder | Everything the agent does. Your project folder is shared with your machine, so changes on either side show up on the other. |
| 3\. Whole agent, own copy | Everything the agent does, on its own copy of the repo. Nothing is shared with your machine. |

The more friction a level adds, the more likely people are to switch it off, so the default needs to be one people will keep using.

## **1. Commands only**

Claude Code's built-in `/sandbox` wraps the shell commands the agent runs, and anything they start, using Seatbelt on macOS and bubblewrap on Linux. Network access goes through a domain allowlist.

There's nothing to install and your workflow doesn't change. The gaps:

* Claude's own file tools, MCP servers and hooks run outside it. File tools are limited by permission rules instead, which the tool enforces, not the operating system (see [Secrets in the agent's environment](../guides/secrets.md)).
* Commands can read most of the machine, including `~/.ssh`, unless you deny it.
* Docker doesn't run inside it, so containerised test databases need an exception.

## **2. Whole agent, shared folder**

The agent runs inside a container or micro-VM, with only the project folder mounted from your machine. It can't see the rest of the machine, network access goes through an allowlist, and some tools keep secrets out of the sandbox altogether by swapping them in at a proxy.

Day to day, little changes: you edit in your usual editor, run your own tools against the same files, and see the agent's changes as they happen.

The shared folder is the remaining way back to your machine. A git hook, package script, editor task or `.envrc` the agent writes there runs with your full permissions the next time you run it outside the sandbox. Packages with native binaries can also clash between the two sides.

*Examples:* [Docker Sandboxes](#docker-sandboxes) (its default mode), dev containers.

## **3. Whole agent, own copy**

As level 2, but the project lives inside the sandbox. The agent works on its own clone of the repo and nothing is shared with your machine. You see and edit its files over SSH, or with an editor that connects remotely (e.g. VS Code Remote-SSH), and changes reach your machine through git.

This closes the shared-folder path from level 2. What changes is where you work: tools on your machine don't see the agent's files until you fetch them, so you either work inside the sandbox or go through git.

It can run locally or in the cloud. Cloud sandboxes work the same way, hosted remotely and usually paid for.

*Examples:* [Docker Sandboxes](#docker-sandboxes) with `--clone`, [nixenv](#nixenv), cloud sandboxes.

## **Tools**

### **Docker Sandboxes**

[Docker Sandboxes](https://docs.docker.com/ai/sandboxes/) (`sbx`) offers a low-config way to start sandboxing. It's quick to set up and get into, and nothing needs to be added to the project.

* **One command to start.** Install the `sbx` CLI and run `sbx run claude` from the project folder. It also supports Codex, Gemini CLI, OpenCode and other agents.
* **Micro-VM per sandbox.** Each sandbox has its own Docker daemon, so the agent can build images, run containers and use Compose. An existing Docker Compose setup runs inside the sandbox, separate from the containers on your machine.
* **Level 2 or 3.** The project folder is shared by default. `--clone` gives the agent its own copy instead, and `--cloud` runs the sandbox remotely.
* **Network policy.** Pick a default policy on first start, then allow extra hosts per sandbox.
* **Secrets swapped in at the proxy.** Secrets stay on your machine; the sandbox sees a placeholder that's replaced with the real value on outgoing requests.
* **SSH access.** Connect over SSH from a terminal, or from Claude Code desktop.

→ **Guide:** [Docker Sandboxes](../guides/docker-sandboxes.md): setup, SSH, editors, GitHub and secrets.

### **nixenv**

[nixenv](https://rande.github.io/nixenv/) is a single bash script that runs a small, disposable container per project on your own machine, using Docker or Podman. Its tagline: *"One Nix store. A room for every project."*

* **Shared toolchain.** Every project mounts one shared Nix store read-only, so projects run the same pinned tools. Nix doesn't need to be installed on your machine. Per-project flakes add runtimes and services on top.
* **Projects kept apart.** Each project has its own volume and can't see the others' files or reach their URLs unless the other project opts in.
* **Network allowlist.** Restricted projects have no direct route out. Outbound traffic goes through an allowlist proxy, and `nixenv capture` records HTTP(S) traffic without loosening it.
* **Secrets.** Each project gets its own SSH key, generated on your machine and mounted read-only. By its own account, every project can read the shared Claude login, and traffic captures contain tokens and cookies.
* **Claude Code built in.** One Claude login is shared across projects, while each project keeps its own settings, hooks and MCP servers.
* **Getting in.** `nixenv init myapp <git-url>`, `nixenv start myapp`, then `ssh myapp`. It also supports VS Code Remote-SSH, HTTPS for every port at `https://<project>-<port>.nixenv.localhost`, and ready-made templates.
