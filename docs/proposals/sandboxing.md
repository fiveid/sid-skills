# **Sandboxing**

**Status:** Proposal. My leaning is sandboxed by default. Needs a team decision on enforcement and tier.  
**Responds to:** [secrets exposure and new attack vectors](../../HUMANS.md#risks).

Sandboxing a project ensures an agent cannot reach outside the scope of the project to reach system settings and trawl keys from other directories. An egress allowlist can limit what external hosts an agent would be able to connect to. It can also isolate SSH keys and CLI tokens. We may want to adopt a sandboxing approach as standard. There are options:

| Tier | Setup | What it covers | Watch out for |
| :---- | :---- | :---- | :---- |
| 1\. Built-in sandbox | Claude Code's /sandbox, which uses Seatbelt on macOS and bubblewrap on Linux | Shell commands and anything they start; network via a domain allowlist | Doesn't cover Claude's file tools, MCP servers or hooks. Reads most of the machine (including \~/.ssh) unless you deny it. Docker doesn't run inside it, so containerised test databases need an exception |
| 2\. Whole-process isolation | Run the agent itself inside a dev container, rootless container, micro-VM or Nix/bubblewrap shell | Everything the agent does; only the repo is mounted, shared packages read-only | More setup; you build the network allowlist yourself |
| 3\. Ephemeral cloud sandbox | A fresh remote environment per branch | Local credentials never exist there | Cost and slower feedback |
