# **Secrets in the agent's environment**

*The principle behind this guide is in [HUMANS.md](../../HUMANS.md#secrets-and-sandboxing). For isolating the agent itself, see the [sandboxing proposal](../proposals/sandboxing.md).*

A secret in the agent's context can end up in logs or memory files by accident. Prompt injection and slopsquatting give attackers new ways to get at any secret the agent can see. And even without an attacker, broad instructions, hallucinations or a looping agent can make changes you didn't expect, or run up charges.

There's no single fix. Ask three questions of every secret a project uses, and combine the answers.

## **1. Does the agent need a real secret at all?**

Often it doesn't. Use mocks and test keys locally, and keep real credentials in CI, where the agent can't reach them. Production credentials never belong on a development machine.

## **2. If it leaks, how bad is it?**

Where a real key is needed, make a leak cheap:

* **Narrow scope.** Only the permissions and resources the task needs.
* **Not your own account.** Use a service account, so the key isn't tied to everything you can access.
* **Short expiry.** A key that expires next week is worth less to anyone who finds it.
* **Budget limits.** Always set them on anything that bills by usage, so a looping agent or a stolen key can't run up a large bill.

## **3. Can the agent see it?**

From most to least exposed:

* **In plain sight.** A `.env` file in the project, an environment variable in the agent's shell, a token in a config file. The agent can read it whenever it likes.
* **Masked.** A secrets manager (see [Tools](#tools)) keeps the value out of plain-text files and injects it when needed. The value can still be read at runtime and may be logged.
* **Never visible.** The agent gets a placeholder, and a proxy outside its reach swaps in the real value on outgoing requests. [Docker Sandboxes](docker-sandboxes.md#keep-secrets-out-of-the-sandbox) does this.

Rules in the agent's own settings help, but they're not a wall. Claude Code doesn't read `.claudeignore` at all. `permissions.deny` in `.claude/settings.json` stops Claude's own file tools reading secrets (e.g. `Read(./.env*)`), but it's a rule the tool applies, not the operating system, and can be worked around (a script that reads the file, for example).

## **Treat anything in context as exposed**

If a secret appeared in a prompt, a tool's output or a file the agent read, it has been sent to the model provider and saved in local session logs (for Claude Code, under `~/.claude/projects`). Rotate it. Deleting the line from the file doesn't undo that.

The same applies to secrets the agent writes: hardcoded into code or tests, printed in log statements or error messages, or saved to a memory file. Check for these in review, and run a secret scanner in pre-commit and CI (see [Risks and mitigations](risks-and-mitigations.md#secrets-exposure)).

## **Where secrets hide**

An agent running as you can reach more than the project. Worth checking:

* `.env` files, in this project and in others
* CLI logins: `~/.aws`, `~/.config/gh`, `~/.docker`, `~/.npmrc`, `~/.kube`
* SSH keys in `~/.ssh`
* MCP config files with tokens in them (`.mcp.json`, `~/.claude.json`)
* Shell history (`~/.zsh_history`, `~/.bash_history`), where tokens typed on the command line stay
* Git remotes with a token in the URL (`git remote -v`)

Don't hardcode tokens in MCP config files the agent can read. A CLI tool (or Claude connector) may be safer than an MCP if it hides the auth token, though the agent can still do whatever that token allows, so keep its scope narrow.

## **Tools**

A secrets manager is the main tool for question 3: it keeps values out of plain-text files and hands them over only when they're needed. For the never-visible level, see [Docker Sandboxes](docker-sandboxes.md#keep-secrets-out-of-the-sandbox). For catching leaks, see the secret scanners in [Risks and mitigations](risks-and-mitigations.md#secrets-exposure).

### **1Password**

* **Secret references.** Put `op://vault/item/field` in your `.env` file instead of the value. The file then holds only pointers, so it's safe for the agent to read.
* **CLI (`op run`).** `op run --env-file=.env -- npm start` swaps the references for the real values and passes them to that one command. Secrets printed to stdout or stderr are masked by default, but the command itself has the real values.
* **Environments.** Keep a project's variables together and share them with the team. An Environment can be mounted as a local `.env` file, served through a named pipe rather than written to disk. Once you approve it, any process can read that file until 1Password locks.
* **SSH agent.** Private keys stay in 1Password, and using one needs your approval. By default, an approval covers the app and everything it starts, so approving your terminal also approves an agent running in it. The *per key, per request* setting asks every time.
* **Service accounts.** Tokens limited to the vaults you choose, for CI and automation, so a pipeline doesn't run on your personal account.

### **1Password MCP**

1Password has a local MCP server that lets an agent work with your [1Password Environments](https://www.1password.dev/environments/): list them, list the variable names in each, add variables, and mount an Environment as a local `.env` file. It's an experiment for now: turn it on in the desktop app under *Settings → 1Password Labs → MCP Server*, and point your MCP client at the `1password-mcp` command.

**Why use it?** 1Password's developer tools are useful, but if you're not used to them they add some overhead, and it's easier to skip them. The agent doesn't mind the overhead. You keep the secrets in 1Password, and the agent does the legwork of finding the right Environment and wiring it up where it's needed.

**Isn't that risky?** Less than it sounds, but it's not airtight:

* **Names, not values.** Listing variables returns names only.
* **You approve access.** Each new connection, and the first access to each Environment, needs your approval in the 1Password app.
* **Values the agent adds pass through it.** If the agent adds a secret for you, the value is in its context. Add secrets in the 1Password app yourself.
* **The mounted `.env` file isn't agent-proof.** As above, once you approve it, the agent can read it too.
* **At runtime, it's like any other environment variable.** Once your app has loaded it, anything that can read the app's environment can read it too.

To keep secrets out of the agent's reach altogether, see [Docker Sandboxes](docker-sandboxes.md#keep-secrets-out-of-the-sandbox).
