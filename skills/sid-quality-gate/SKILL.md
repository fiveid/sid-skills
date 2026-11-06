---
name: sid-quality-gate
description: Set up an essential code-quality gate in any project, in any language, as one required "Code quality" CI check backed by a single local command. It covers types, lint, complexity, duplication, dead code, security (code, dependencies, secrets), test coverage and formatting, and writes a decisions record and baseline. Re-run it later to audit whether the gate has been weakened (changed thresholds, disabled rules, grown ignore lists, new inline suppressions, CI bypasses, drift). Use this whenever the user wants to add or harden linting, static analysis, type checking, coverage thresholds or CI quality checks, set up a "quality gate" or required check, ratchet a legacy codebase, or asks "has our quality gate been weakened?", "audit our lint config", "how many eslint-disables have crept in?" or "is CI still enforcing anything?". Not for judging the code itself (use sid-health-check or sid-review), a whole-project trust review (use sid-trust-audit) or vetting a new dependency (use sid-dep-audit).
---

# Quality gate

You set up a gate once, then audit it as often as the owner likes. The gate is a fixed set of categories, enforced by tools the owner is happy with, written down with the reasons, and measured so that any later loosening shows up.

What belongs to whom:

- **The skill owns the categories.** Every category below ends up either enforced by a tool or recorded as a deliberate exclusion with a reason. Nothing gets dropped quietly.
- **The owner owns tools, thresholds and policy.** Honour their tool preferences even when they're chosen out of curiosity (Oxlint over ESLint, `ty` over mypy). Say plainly where a preferred tool leaves a gap in a category, and propose how to fill it.
- **Audits report and never act.** Changing the baseline only happens when the owner asks for it.

**Outcomes are fixed; methods are defaults.** Each step says what it must achieve. Where it gives a method, that's the usual way, not the only one. If the method doesn't fit this repo, use another that reaches the same outcome and say so in one line. If every way forward needs a compromise, stop and ask before doing it. Compromises include a blocked host, an extra config file, a looser check, a tool that failed vetting, or a conflict with the project's own rules. A blocked command, a permission prompt, a safety refusal, a bot check or a rate limit is a question for the owner. Never route around one: no changed user agent, no proxy or mirror, no other tool to fetch the same thing.

## Pick the mode

| Situation | Mode |
| :--- | :--- |
| No `quality-baseline.json` in the repo | **Setup** |
| A record exists and the user wants to check, audit or "see what's changed" | **Audit** |
| A record exists and the user wants to change a tool or threshold, accept a new baseline, or add a language or package | **Rebaseline** |
| A record exists and the user asks for setup again | **Rebaseline**, scoped to what's new |

If the user asks for an audit and no record exists, say there's no baseline to compare against and offer setup. Don't make one up from the current config.

## The categories

| Category | What it must catch |
| :--- | :--- |
| Types | The strictest practical checker for the language, with strict options on |
| Lint | Bugs and code smells, at **error** level. Warnings are invisible in CI, so a gate allows none |
| Complexity | Cyclomatic or cognitive complexity, function length, nesting depth, parameter count |
| Duplication | Copy-pasted blocks above a token threshold |
| Dead code | Unused files, exports and dependencies |
| Security | Code vulnerabilities (SAST), vulnerable dependencies, committed secrets |
| Tests | The suite passes with a coverage floor, where the project has tests or needs them |
| Formatting | A check-only formatter run, where it's cheap to enforce |

`references/tool-selection.md` has the criteria for choosing a tool, a starting list of candidates per language, and dated traps to check. `references/thresholds.md` has the strict defaults and the ratchet rules.

## Setup

The owner makes the real decisions in up to two short rounds of questions: one before you run anything, one after you've measured. A confirmation follows. One big proposal invites a "yes" without reading, so keep each decision visible on its own.

If the owner has said to take your recommendations without checking back, skip round 2 and list what you chose in the confirmation. Round 1 still applies to anything that needs their permission: granting access, running a tool that failed vetting, or going against a project rule. Where the recommended option needs none of those, take it and say so.

### 1. Read the project before asking anything

Work out as much as you can yourself:

- Languages and their share of the code, package managers and lockfiles, monorepo layout.
- Existing configs: type checker, linters, formatter, coverage, security scanners. Note what's already strict.
- The test runner, whether tests exist, and current coverage if it's cheap to measure.
- The CI platform and existing workflows, and the repo host and visibility. On GitHub, `gh repo view --json visibility,owner` and the account plan decide whether a check can be made required (see `references/ci-github-actions.md`).
- Size and maturity: lines of code, commit count, age.
- **The project's own rules:** agent instructions (`AGENTS.md`, `CLAUDE.md`, rule files), `CONTRIBUTING`, and docs conventions. Look for rules on decision records, where docs live, generated files and new dependencies. The human-readable record follows those rules. Only `quality-baseline.json` is fixed, because the script reads it. Note any conflict for round 1.
- **Access:** list every host setup will need (package registries, the advisory database's API, rule sources, the repo host's API) and check each one with a cheap request. Note anything blocked.

If there's no project yet, ask what's being built (language, kind of app, where it runs) and wait for the answer before going further.

### 2. Choose and vet the tools

Follow `references/tool-selection.md`. For each category, shortlist the owner's preference, the listed candidates and anything newer a search turns up. Keep the tools that meet the criteria, choose by the tie-breaks, and check the known traps that apply. Confirm every tool in its official registry and get its current version from there (`ctx7`, the registry or a web search), never from memory. This space changes every few months: tools get forked, renamed, compromised, or quietly start needing a licence key. Record the version, its release date and the alternatives you rejected. If you can't search or reach a registry, say so in round 1 rather than choosing from memory.

Everything must run free for a solo developer, locally and in CI. Hosted dashboards can be mentioned as optional extras, never as part of the gate.

**Vet before you run.** Measuring a tool means running it, so vet every tool the project doesn't already use first, including one-off helpers you only run during setup. Check it as `references/tool-selection.md` describes. If `sid-dep-audit` is installed, use it. Most established tools pass, even with a single maintainer. A tool with several warning signs together, or whose source doesn't match its registry entry, needs the owner's explicit approval in round 1. Don't run it before then.

**Check each kind of tool can run here.** Once the tools have passed vetting, and before you change anything in the repo, run one harmless command (such as `--version`) for each way the plan runs tools: a downloaded release binary, `uvx` or `pipx`, `npx`, a container. Sandboxes and safety checks often refuse some of these, and a refusal found now becomes a round-1 question instead of a half-built repo.

### 3. Round 1: anything that blocks the plan

Before measuring or changing anything, ask about what would change the plan:

- Blocked hosts: grant access, or use a named alternative. Ask even when you have an alternative, unless it's just as good, and say what the alternative loses. It isn't just as good if it covers less, or if you'd have to build something by hand to make up for it (an allow-list with expiry dates, say). A host the plan doesn't need at all goes in the confirmation instead.
- Tools that need approval after vetting, with the warning signs you found.
- Kinds of tool this environment refused to run, with the alternative and what it loses.
- Conflicts with the project's own rules, such as where the record goes.
- Tool preferences that leave a gap in a category, and how you'd fill it.

Use the question format in `references/handover-format.md`. If there's nothing to ask, skip the round.

### 4. Measure, then set thresholds

**Existing code:** run each chosen tool at the strict default in report mode and count the violations. The gate has to pass on day one and be easy to tighten later. How to get there depends on the kind of rule (detail in `references/thresholds.md`):

- **Per-function or per-line rules** (types, lint, complexity): keep the strict threshold and record existing violations in the tool's baseline file (ESLint bulk suppressions, PHPStan baseline, basedpyright baseline and so on). New code is held to the strict bar. Don't raise a per-function limit to the worst existing function, because a limit of 87 lets nearly everything through. Where a tool has no baseline mechanism, list the existing offenders as a recorded exclusion instead.
- **Project-wide numbers** (coverage %, duplication %, dead-code count): set them just beyond the current value. The gate then fails only if things get worse.

Never add inline suppressions to get to green. A baseline file is counted and can be audited. Scattered `// eslint-disable` comments can't be told apart from new ones.

**Greenfield:** use the strict defaults.

**Try every setting you plan to propose.** A strict rule gets a report-mode run. A minimum-release-age setting gets a dry-run install against the current lockfile, because existing pins younger than the window break the first install. If you can't try something, mark it "not tried" in round 2.

**Time every category** while you measure: the local run time, and an estimate of the CI time including tool installs. The owner is agreeing to a cost, so show it. The default budget is **5 minutes wall-clock for the CI gate**, with jobs running in parallel. If the estimate is over budget, name the slow categories (whole-history scans and Semgrep are the usual ones). Propose moving them to a scheduled job, which runs on a timer and doesn't block merges. Moving one is a recorded decision, not a quiet exclusion.

### 5. Round 2: the trade-offs, then confirm

Ask about what measuring turned up, with the real numbers:

- CI time over budget: which categories move to a scheduled job.
- Existing code where a tool has no baseline file: which files are exempt from which rules, and that new code in those files is exempt too.
- Any threshold looser than the strict default, with its value.
- **Secrets before they're committed:** recommend a pre-commit hook that scans staged changes with the secret scanner, with its time per commit measured on a real staged change. This is the one category where CI is too late: by the time CI fails, the secret is in history and probably pushed, so it has to be treated as leaked. Agents commit often and pull secrets into context, which makes it matter more. Offer this hook only. Lint, format and test hooks slow every commit down, and CI catches those in time.
- Anything marked "not tried".

Then send a short confirmation: the table, the owner's answers, and the defaults you applied without asking, so they can still object to one. Defaults:

- **Record location:** wherever the project's rules put decisions. With no rule, `QUALITY.md` and `quality-baseline.json` at the repo root.
- **New CVEs in existing dependencies:** fail on high and critical, with an allow-list where every entry has a reason and an expiry date. This stops the gate failing unrelated PRs without hiding anything.
- **Agent instructions:** no change. Offer a line in `AGENTS.md`/`CLAUDE.md` telling agents to run the gate command before finishing, and add it only if the owner says yes.

### 6. Build it

If something still stops the build partway, say exactly what's now in the repo and what isn't. Don't leave a command pointing at a file you haven't written.

- **One local entry point** runs every category, carries on past failures so all of them are reported, and exits non-zero if any failed. Use the project's own convention (a package script, `make quality`, a Composer script, a `justfile` recipe). CI calls the same command, so a local run and CI can't drift apart. There's a shell skeleton in `templates/quality.sh`.
- **Each category fails the gate on its own violations,** but it doesn't need its own command. If a tool can only check one category in another category's run (with Oxlint, enabling a rule from the command line resets its options), run it there and record `runs_in` in the baseline. Don't add a second config just to split them.
- **Pin every tool:** dev dependencies in the lockfile, exact versions for standalone binaries. CI actions are pinned to a full commit SHA. Without pins the gate changes under you and the audit can't compare versions. Pick releases that are at least two weeks old, unless a newer one fixes a security problem you're pinning around. If the project already has an age policy, such as the 30 days in `sid-dep-audit`, use that instead. Hijacked releases are usually caught within days, and security tools themselves have been the target (see the known traps in `references/tool-selection.md`). Where the package manager has a minimum-release-age setting, add it only if step 4's dry run passed or the owner chose how to handle the young pins.
- **CI:** use `references/ci-github-actions.md`. Run the jobs in parallel, then one aggregator job named **Code quality** that fails unless every job succeeded. That gives one required check name. No path filters on the gate workflow: a required check whose workflow was skipped never reports, and the PR waits forever. For other CI platforms, carry the same rules over.
- **Secrets:** scan the full history once during setup and give the owner what it finds. Don't rewrite history or rotate anything yourself. In CI, scan the commits in the PR.
- **Secrets hook (if accepted):** add it through the project's existing hook manager (Husky, Lefthook, the pre-commit framework) so you don't fight existing tooling. If there isn't one, commit the hook script and tell the owner the one command that turns it on in each clone. Use the same pinned scanner and config as CI. CI stays the guard: hooks are per-clone and can be skipped with `--no-verify`, so record the hook as a local convenience, not enforcement.

### 7. Prove it bites

Run the gate locally and show it passing. Then make one deliberate violation per category and show the gate failing on each: a type error, an unused export, a function over the complexity limit, a copied block, a fake secret, an untested branch that drops coverage, and so on. A check that has never failed hasn't been shown to work.

The drill must run the **new** gate, and leave the owner's working tree exactly as it was. The setup isn't committed yet, so a worktree from `HEAD` has the old checks. By default, copy the working changes into a scratch worktree:

```bash
git worktree add --detach <scratch> HEAD
{ git diff --name-only -z --diff-filter=d HEAD; git ls-files -o -z --exclude-standard; } \
  | rsync -a --from0 --files-from=- ./ <scratch>/
git diff --name-only -z --diff-filter=D HEAD | (cd <scratch> && xargs -0 rm -f --)
```

Check that `git -C <scratch> status` matches the owner's tree, and install dependencies there from the lockfile. Undo each violation by restoring the one file you changed. Never run `git reset --hard`, `git checkout .` or `git clean`, in either tree: in the scratch tree they drop the copied setup, and in the owner's tree they destroy work. Remove the worktree when you're done.

Save each run's output to a log, and describe each violation only as far as its log shows. If a log shows a different failure from the one you intended, the drill hasn't proved anything yet, so fix it and run it again.

### 8. Write the record

Write the human-readable record from `references/record-template.md`, in the place the project's rules allow, and set `record_doc` to it. It holds the gate command, each category with its tool, version, config files, thresholds and reason, the deliberate exclusions, the CVE policy, and a decisions log whose first entry is the setup. If the project keeps decisions somewhere else (an ADR folder, or commit messages only), put the log there and say where in `record_doc`. Fill in the hand-written parts of `quality-baseline.json` (schema in the same file), then measure the rest:

```bash
python3 <skill-dir>/scripts/quality_snapshot.py write --record quality-baseline.json
```

This counts inline suppressions (explained and unexplained), entries in baseline and ignore files, and CI lines that could bypass the gate. Where a tool keeps its pre-gate list inside its config (Oxlint overrides, Knip `ignoreIssues`, a Semgrep allow-list), add a counter for it to `extra_baseline_files`, so the audit sees it grow. Copy the totals into the Baseline section of the record. If the project has a formatter, run it on `quality-baseline.json` after each `write`. The script reads values, not layout, so this is safe, and it beats adding the file to the formatter's ignore list.

The scan is a heuristic. If it misreads something, note the false positive in the record. Never reword comments or restructure scripts just to dodge it: that's gaming the measure the audit relies on.

Config, gate and record belong in the same commit, because the audit anchors on the last commit that touched the record. Commit only if the owner asks you to.

### 9. Check enforcement and hand over

A gate that blocks nothing is a report. Check whether **Code quality** is already required on the default branch, using the API calls in `references/ci-github-actions.md`. If it isn't, give the owner the exact steps to require it. If the plan doesn't allow it (private repos on GitHub Free, for instance), say so and record the status as `unavailable`. The check still runs and still shows red, but nothing stops a merge.

Finish with the hand-over format in `references/handover-format.md`: the table with measured times, what changed in their code and dependencies, what now blocks a merge, any workaround you used, and the one thing they need to do. Everything else (reasons, the drill logs, the baseline counts) is in the record and the logs, and the hand-over points there.

## Audit

The audit looks at configuration, not at what the tools say about the code. It's read-only: don't edit configs, the record or code, and don't run anything that writes (`--fix`, formatters in write mode, `snapshot write`). It reports facts. It doesn't recommend fixes or say whether a change was justified; that's the owner's call.

1. Load `quality-baseline.json` and the record it names in `record_doc`. If they're missing, report that and stop.
2. Run `python3 <skill-dir>/scripts/quality_snapshot.py compare --record quality-baseline.json`. It reports changes to watched files since the anchor commit, the history of the record, suppression counts against the baseline with the new locations, growth in baseline and ignore files, and CI lines to check.
3. Work through `references/audit-checklist.md`. It covers what the script can't see: reading each config diff for changed thresholds and downgraded rules, config files that aren't watched yet, gate coverage per category, CI triggers and the aggregator, enforcement, and tool versions.
4. Spot-check the suppression scan. It's a heuristic: "explained" means there's a reason on the same line, or in a comment line above a marker that sits on its own line. Correct any misreads before reporting.
5. Match every change to the record against a dated decisions-log entry, and mark each finding as **logged** or **unlogged**.
6. Report in chat using the format in `references/audit-checklist.md`. Write it to a file only if asked, and never commit it. End by saying that changes to the baseline happen only at the owner's request.

## Rebaseline

Only when the owner asks, and only for what they asked. Make the change, run the gate, update the hand-written fields in `quality-baseline.json`, re-measure with `quality_snapshot.py write`, and add a dated decisions-log entry: what changed, from what to what, why (in the owner's words), and who asked. Loosening is allowed; it's the owner's call. It just has to be on the record. To add a language or package, run setup steps 1 to 8 for that part only, with question rounds scoped to it. Keep the recorded tools for everything else. Choosing tools again on every run is how the same project ends up inconsistent.

## Red flags in your own work

- Raising a threshold or adding a suppression during setup to make something pass, without asking in round 2.
- Claiming a tool covers a category because of its name, without having watched it fail.
- Recommending a tool from memory without confirming it in its registry and checking its current version and licence.
- Turning an audit finding into a recommendation, or "fixing" drift while you audit.
- Routing around a blocked host, a permission prompt, a safety refusal or a bot check, or running a tool (gate tool or helper) that failed vetting, instead of asking.
- Stopping to ask about an established tool because it has one maintainer. That's a question the owner can't usefully answer.
- Proposing a setting you haven't tried on this repo, without saying so.
- A workaround the owner didn't approve, reported as if the step had gone to plan.
