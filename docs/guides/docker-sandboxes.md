# **Docker Sandboxes**

*The principle behind this guide is in [HUMANS.md](../../HUMANS.md#secrets-and-sandboxing). This is one way to set up level 2 or 3 (whole agent) from the [sandboxing proposal](../proposals/sandboxing.md).*

[Docker Sandboxes](https://docs.docker.com/ai/sandboxes/) (`sbx`) runs the agent inside its own isolated micro-VM. These are pointers for using it with Claude Code, not a full walkthrough. `sbx` is changing quickly and some of the commands below are marked experimental, so check `sbx <command> --help` if something doesn't match.

## **Start a sandbox**

From your project directory:

```bash
sbx run --name my-project claude
```

This opens Claude Code in the terminal, running inside the sandbox.

* **Your project folder is shared, not copied.** The sandbox reads and writes the same directory on your machine, so changes on either side show up on the other. That's level 2 in the proposal.
* **Or share nothing with `--clone`.** Add `--clone` when you first create the sandbox and the agent works on a private copy of the repo instead. Its changes stay there until you fetch or push them. That's level 3.
* **Pick a network policy on first start.** You choose from a few defaults (e.g. *balanced*). Allow extra hosts per sandbox as you need them:

  ```bash
  sbx policy allow network --sandbox my-project my-hostname.com
  ```

## **Run it in the background and connect over SSH**

Set up SSH once (it needs an active Docker login, `sbx login`):

```bash
sbx setup ssh
```

Then start the sandbox detached, connect to it, and run `claude` from inside:

```bash
sbx run -d --name my-project
```

```bash
ssh my-project.sbx
```

Stop it when you're done (it keeps its state and can be started again with `sbx run`):

```bash
sbx stop my-project
```

## **Using Claude Code desktop**

Once `ssh my-project.sbx` works, start a new project in Claude Code desktop and use `my-project.sbx` as the SSH host. No other config is needed.

The desktop app asks for a starting directory. The agent can find your project from anywhere, but it's tidier to start in the right folder. The project sits at the same path inside the sandbox as on your machine, e.g. `/Users/<username>/projects/<project-name>`.

## **Editing in VS Code**

Because the folder is shared, you can keep editing in VS Code on your machine and the agent sees the changes. The catch: the VS Code terminal runs on your machine, **not** in the sandbox. Commands you run there aren't sandboxed.

With `--clone`, the files only exist inside the sandbox, so you see and edit them over SSH instead.

## **GitHub**

The GitHub CLI is already installed in the sandbox. To give one sandbox your GitHub token, run this on your machine:

```bash
sbx secret set github --sandbox my-project -t "$(gh auth token)"
```

The token is held by the sandbox's proxy, not passed into the sandbox. `--sandbox` limits it to one sandbox, but `gh auth token` is still your full personal token. If the agent only needs a few repos or permissions, create a fine-grained token for it instead.

## **Keep secrets out of the sandbox**

`sbx` can hold a secret on your machine and hand the sandbox a placeholder instead. When the sandbox makes a request to an allowed host, the proxy swaps the placeholder for the real value in the request headers. The agent only ever sees the placeholder. See Docker's [credentials docs](https://docs.docker.com/ai/sandboxes/configuration/credentials/).

All four ways below set `SECRET_API_TOKEN` to `MY_PLACEHOLDER` inside `my-project`, and swap in the real value on requests to `localhost`. They differ in where the real value comes from.

1. **Plain value.** The simplest, but the secret ends up in your shell history.

   ```bash
   sbx secret set-custom --sandbox my-project --host localhost --env SECRET_API_TOKEN --placeholder "MY_PLACEHOLDER" --value "xxx-xxx-xxx"
   ```

2. **Read the value from 1Password once.** Keeps the secret out of your shell history. `sbx` stores the value when you run the command, so if the secret changes, run it again.

   ```bash
   sbx secret set-custom --sandbox my-project --host localhost --env SECRET_API_TOKEN --placeholder "MY_PLACEHOLDER" --value "$(op read 'op://Vault/Project/Token')"
   ```

3. **1Password reference.** `sbx` stores the `op://` reference and fetches the value itself when it's needed, so changes in 1Password are picked up. It also accepts AWS Secrets Manager ARNs. Needs the `op` CLI installed and signed in.

   ```bash
   sbx secret set-custom --sandbox my-project --host localhost --env SECRET_API_TOKEN --placeholder "MY_PLACEHOLDER" --ref "op://Vault/Project/Token"
   ```

4. **Command.** `sbx` stores a command, runs it on your machine when the value is needed, and uses whatever it prints. Use this for anything else that can print a secret (Keychain, Vault, another CLI). It runs from a temporary folder, so give the tool's full path, and keep the tool and its config outside the shared project folder, where the agent could change them.

   ```bash
   sbx secret set-custom --sandbox my-project --host localhost --env SECRET_API_TOKEN --placeholder "MY_PLACEHOLDER" --command "/opt/homebrew/bin/op read 'op://Vault/Project/Token'"
   ```

For 3 and 4, `--refresh` controls how often the value is fetched again (on demand by default). Drop `--sandbox` to apply a secret to every sandbox.

The swap only happens in outbound request headers. A secret the app sends in a request body, or reads for local use, stays as the placeholder.

For why this matters and other ways to limit exposure, see [Secrets in the agent's environment](secrets.md).

## **Notes**

* **Dependencies.** On a Mac, packages installed on your machine are built for macOS, while the sandbox runs Linux. Packages with native binaries in `node_modules` won't work on both sides. pnpm can install for several platforms with the `supportedArchitectures` setting, but the simpler fix is to delete the local `node_modules` and reinstall inside the sandbox when switching over.
* **MCP servers.** The sandbox gives the agent a single MCP gateway. You register servers on your machine with `sbx mcp add`, then attach them to a sandbox with `--static-mcp` when creating it, or `sbx mcp load` on a running one. Local servers run on your machine, not in the sandbox, with your full permissions, and their OAuth credentials stay on your machine. Docker's [MCP docs](https://docs.docker.com/ai/sandboxes/mcp-gateway/) don't say whether Claude Code's own MCP config (`.mcp.json`, `~/.claude.json`) is picked up, so run `/mcp` inside the sandbox to see what's actually loaded.
