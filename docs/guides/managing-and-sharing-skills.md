# **Managing and sharing skills**

*The principle behind this guide is in [HUMANS.md](../../HUMANS.md#managing-skills). Which skills belong in a project, and which stay personal, is in the [project and personal skills proposal](../proposals/project-and-personal-skills.md).*

How to install, update and share [Agent Skills](https://agentskills.io/) with the two package managers I've used: [skills.sh](https://skills.sh/) (`npx skills`) and Microsoft's [APM](https://github.com/microsoft/apm) (Agent Package Manager). Both are changing quickly. Commands were checked in November 2026, so run `--help` if something doesn't match.

## **Where skills live**

Agents look for skills in a folder per project and a folder per user. Most have now converged on one shared folder; Claude Code still uses its own.

| Agent | Project | User (global) |
| :--- | :--- | :--- |
| Claude Code | `.claude/skills/<name>/` | `~/.claude/skills/<name>/` |
| Copilot, Cursor, Codex, Gemini, OpenCode, Windsurf | `.agents/skills/<name>/` | `~/.agents/skills/<name>/` |

If you commit skills to a repo by hand, put them in `.agents/skills/` and symlink `.claude/skills` to it. One copy, every agent.

## **Before you install anything**

A skill is instructions your agent will follow, and often scripts it will run, with your permissions. Treat it like a new dependency, not like a snippet.

* **Read it first.** The `SKILL.md` and anything in `scripts/`. If it's too long to read, that's a signal too.
* **Pin it.** Install from a tag or commit, not a moving branch. Both tools record the resolved commit in a lockfile.
* **Scan it.** [`skill-scanner`](https://skills.sh/getsentry/skills/skill-scanner) checks for prompt injection and unsafe commands. `apm audit --file <path>/SKILL.md` checks for hidden Unicode.
* **Review lockfile changes like code.** An update can change what the agent does without touching a line of your code.
* **Decide whose skill it is.** If only you want it, install it globally (`-g`) rather than into the project. See the [proposal](../proposals/project-and-personal-skills.md).

## **skills.sh (`npx skills`)**

[skills.sh](https://skills.sh/) is a searchable directory of skills; [`npx skills`](https://github.com/vercel-labs/skills) is the CLI that installs them. It needs Node.js 22.20 or later and only handles skills.

```bash
# Install one skill into the project, for Claude Code only
npx skills add fiveid/sid-skills --skill sid-review -a claude-code

# Install globally instead
npx skills add fiveid/sid-skills --skill sid-scout -g

# Pin a tag
npx skills add owner/repo@v1.2.3 --skill my-skill

# Search, list, check, update, remove
npx skills find review
npx skills list
npx skills check
npx skills update
npx skills remove sid-review
```

* **One copy, symlinked.** By default it installs a single copy to `.agents/skills/` and symlinks it into each agent's folder. Pass `--copy` if symlinks cause trouble.
* **Lockfile.** Project installs are recorded in `skills-lock.json` with the source commit and a content hash. `npx skills list` marks a skill as `modified` when its files no longer match.
* **CI check.** `npx skills check` exits with code 1 when a skill has an update or local changes.
* **Restoring from the lockfile is experimental** (`npx skills experimental_install`). Until that settles, committing the installed folders is the reliable way to give a fresh clone the same skills.
* **Telemetry.** The CLI sends anonymous usage data, plus security-audit requests for public GitHub repos. `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1` turns both off.
* **Try before installing.** `npx skills use <source>@<skill> --agent claude-code` runs a skill once without installing it.

## **APM (Agent Package Manager)**

[APM](https://github.com/microsoft/apm) is Microsoft's open-source package manager for agent configuration. It handles skills, and also instructions, prompts, agents, hooks and MCP servers. It's pre-1.0 (v0.35 at the time of writing).

```bash
brew install apm                                   # or: curl -sSL https://aka.ms/apm-unix | sh

# Install one skill from a repo of skills
apm install fiveid/sid-skills --skill sid-review --target claude

# Restore everything in apm.yml (e.g. after cloning)
apm install

# See what's installed, update, remove
apm deps list
apm view fiveid/sid-skills
apm update
apm uninstall fiveid/sid-skills
```

* **Manifest and lockfile.** `apm install <package>` adds the package to `apm.yml` and pins it in `apm.lock.yaml` by commit and content hash. Commit both, plus the deployed files; gitignore `apm_modules/`.
* **One install, several agents.** It copies each skill into every agent it detects: `.claude/skills/` for Claude Code, `.agents/skills/` for most others.
* **Security checks.** Every install scans for hidden Unicode (zero-width and bidi characters) and blocks on critical findings. `apm audit --ci` fails CI when deployed files drift from the lockfile. Organisations can add an allow-list with `apm-policy.yml`.
* **User scope.** `-g` installs to your user folders instead of the project.

### **Gotchas**

* **It won't guess the agent.** APM picks targets from signals in the project: a `.claude/` folder or `CLAUDE.md` for Claude Code. In a folder with neither, install stops with a target error. Pass `--target claude`, or add `targets: [claude]` to `apm.yml` so you don't need the flag again. The reverse also applies: a `CLAUDE.md` that is only documentation will switch the Claude target on. Global installs (`-g`) didn't need a target in my testing.
* **`apm list` doesn't list packages.** It lists the `scripts:` in `apm.yml`, like `npm run` with no arguments. Use `apm deps list`, `apm deps tree` or `apm view <package>`.
* **`--skill` is remembered and additive.** The selection is saved in `apm.yml`, and a later `--skill` adds to it rather than replacing it. `--skill '*'` resets to all skills.
* **It won't overwrite your own skill.** If a different skill with the same name is already in the destination folder, the whole install stops. Rename one of them.
* **Don't mix tools for the same skills.** skills.sh symlinks skills into each agent's folder by default, and APM refuses to deploy over a symlink: the whole install fails with "contains a symlink -- refusing to deploy". To switch a skill from skills.sh to APM, remove it first (`npx skills remove <name>`, with `-g` for global skills).

## **Choosing between them**

| | skills.sh | APM |
| :--- | :--- | :--- |
| **Handles** | Skills | Skills, instructions, prompts, agents, hooks, MCP servers |
| **Needs** | Node.js 22.20+ | Standalone binary (Homebrew, installer) or Python |
| **Project record** | `skills-lock.json` | `apm.yml` and `apm.lock.yaml` |
| **Installs as** | One copy, symlinked into each agent | A copy per agent folder |
| **Checks** | Content hash; `check` can gate CI; security-audit lookups | Hidden-Unicode scan on install; `audit --ci`; org policy |

For personal skills installed globally, either works, and skills.sh has less to set up. APM earns its extra weight when a team wants one pinned set of agent configuration across several agents, or an organisation wants to control what gets installed. Most projects don't need that; the [proposal](../proposals/project-and-personal-skills.md) covers why.

## **Sharing your own skills**

* **Use the `skills/<name>/SKILL.md` layout.** Both tools install from it without a manifest. This repo is an example.
* **Keep the frontmatter simple.** `name` must match the folder name. APM requires frontmatter values to be ASCII only. Keep `description` under 1024 characters and lead with when to use the skill, so agents pick the right one.
* **Tag releases** so people can pin a version instead of tracking `main`.
* **Scan before you publish.** Run `skill-scanner` and `apm audit --file` on each skill you change.
* **Private repos work too.** Both tools use your normal git credentials, so a private repo is a reasonable home for skills you don't want to publish.
