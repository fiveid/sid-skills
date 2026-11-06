# Questions, confirmation and hand-over

The owner should see what they're agreeing to, one decision at a time. Reasons, logs and baseline counts belong in the record, so link to it rather than repeating them. Leave out any line that doesn't apply.

## Question rounds (setup steps 3 and 5)

Ask only about decisions the owner owns that cost something. Versions, routine defaults and anything you can work out yourself go in the confirmation's defaults list instead.

- **Each question states the consequence of each option,** for example "adds about 0.3 s to every commit" or "Semgrep moves off PRs, so a merged PR can contain a finding until the nightly run". The owner answers by choosing, not with a general "yes".
- **Recommendation first,** marked as such. Taking every recommendation stays quick.
- **At most about four per round.** More than that means some aren't key: move them to the defaults list.
- **Use the host's structured question tool** if it has one. Otherwise, number the questions so the owner can answer "1a, 2b".
- **No questions, no round.** Don't invent questions to fill one.

```markdown
Before I run anything, <n> decisions for <repo>:

1. **api.osv.dev is blocked from this sandbox.** Dependency advisories need it.
   a. (Recommended) Allow api.osv.dev, then I'll use OSV-Scanner.
   b. Use `pnpm audit` instead: covers npm advisories only, and reaches registry.npmjs.org, which is open.
2. **AGENTS.md says not to write separate decision records.** The gate needs a record of thresholds and why.
   a. (Recommended) A "Code quality" section in `docs/development.md`, with the decisions log in it.
   b. A standalone `QUALITY.md`, as an exception to the rule.
```

## Confirmation (end of setup step 5)

```markdown
Here's the gate I'll build for <repo>, with your answers in.

| Category | Tool | Threshold | Local time |
| :--- | :--- | :--- | ---: |
| Types | basedpyright | strict; 56 existing errors baselined | 4 s |
| … one row per category, or "excluded: <reason>" | | | |

- **CI:** about <n> min per PR, as <n> parallel jobs plus one required check, `Code quality`. <Scheduled instead: "Semgrep, nightly".>
- **Your answers:** <one line each>.
- **Defaults I applied:** <record location, CVE policy, no agent-instructions change>. Say if you want any changed.
- **Changes to your repo:** <n> dev dependencies, <n> new config files, CI workflow <added | replaced>. <Code changes: "formatting only" or "none".>
- **Inferred:** <one line of facts you worked out and they might want to correct>.
```

## Hand-over (setup step 9)

```markdown
The quality gate is set up. Run it locally with `<command>`; details and reasons are in `<record_doc>`.

| Category | Tool | Threshold | Local time |
| :--- | :--- | :--- | ---: |
| … same table, with measured times | | | |

- **Blocks a merge:** `Code quality`, about <n> min in CI, <n>/<n> categories shown to fail on a deliberate violation (logs: `<path>`).
- **Changed:** <files and dependencies added>, <code changes, if any>.
- **Baselined:** <counts per tool, or "nothing: greenfield">.
- **Differs from the plan:** <any method you swapped for another, and why, or "nothing">.
- **Not verified:** <for example "the workflow hasn't run on GitHub yet">.
- **You need to:** <the one action, usually "require `Code quality` in a ruleset on main (steps in the record)", or "nothing">.
```

## Length

Aim for about 20 lines for the confirmation and the hand-over. That's a target, not a limit. A monorepo with real trade-offs will go over, and that's fine: each trade-off gets its line, and any caveat that changes what blocks a merge stays in. Background still goes in the record.
