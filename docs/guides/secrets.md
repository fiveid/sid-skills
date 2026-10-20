# **Secrets in the agent's environment**

*The principle behind this guide is in [HUMANS.md](../../HUMANS.md#secrets-and-sandboxing). For isolating the agent itself, see the [sandboxing proposal](../proposals/sandboxing.md).*

1Password SSH agent can keep SSH keys hidden and ensure biometric approval is required before they are accessed. 1Password also allows environment variable management. However, while this is useful in a lot of ways, the tokens would still be ultimately accessible to a determined agent.

Don't hardcode tokens in MCP config files the agent can read. A CLI tool (or Claude connector) may be safer than an MCP if it hides the auth token, though the agent can still do whatever that token allows, so keep its scope narrow.

Claude Code doesn't read .claudeignore at all. Use permissions.deny in .claude/settings.json to stop Claude's own file tools reading secrets (e.g. Read(./.env\*)). But even that is a rule applied by the tool, not the operating system, and can be worked around. 
