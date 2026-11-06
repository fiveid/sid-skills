# CI: GitHub Actions

**Last reviewed: 2026-11-06.** A template for the gate workflow, the rules it follows, and how to check enforcement. For other CI platforms, carry the same rules over (see the end).

## Rules the template follows

- **One required check name.** Quality jobs run in parallel. A final job called `Code quality` depends on all of them and fails unless every one of them succeeded. Branch protection then needs only that one name, and you can add or split jobs without touching repo settings.
- **No workflow-level path or branch filters on `pull_request`.** A required check whose workflow was filtered out never reports, and the PR sits at "Pending" for good. Filter inside a job if you have to.
- **A skipped job fails the gate.** GitHub reports a job skipped by `if:` as success to branch protection, so the aggregator checks each `needs` result itself and accepts only `success`.
- **Everything goes through the local entry point.** Jobs call `<gate command> <category>`. They never call tools directly, so a local run and CI stay the same.
- **Pin everything.** Actions are pinned to a full commit SHA with the version in a comment. Downloaded binaries are pinned to a version and checked against a SHA-256. GitHub can also *require* SHA pinning in the repo or org Actions policy (`sha_pinning_required`). Suggest it to the owner, but changing settings is their call.
- **Least privilege.** `permissions: contents: read` at the top. No secrets are needed for any free tool here.
- **Stay inside the time budget** (default 5 minutes wall-clock per PR). Cache dependency installs and tool binaries. Split the slowest categories into their own parallel jobs. If a category still pushes the gate over budget, move it to a scheduled workflow (`on: schedule`) that reports instead of blocking, and record that as a decision.
- **Untrusted input stays out of `run:`.** Pass PR values (SHAs, refs) through `env:`, never with `${{ }}` inside a script.

## Resolving SHAs

Don't write SHAs from memory. Resolve each action's current release tag, then the commit it points to:

```bash
gh api repos/actions/checkout/releases/latest --jq .tag_name
gh api repos/actions/checkout/commits/<tag> --jq .sha
```

Tools such as `pinact` or Renovate can keep pins up to date. Mention them as an option.

## Template

Adapt the setup steps (language runtime, dependency install, caching) to the project. Keep the job split cheap: group categories that share an install.

```yaml
name: Quality

on:
  pull_request:
  push:
    branches: [main]        # the default branch
  merge_group:              # only if the repo uses a merge queue
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: quality-${{ github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}

jobs:
  static:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<sha> # vX.Y.Z
      - uses: actions/setup-node@<sha> # vX.Y.Z   (or setup-python, setup-go, …)
        with:
          node-version-file: .nvmrc
          cache: npm
      - run: npm ci
      - run: npm run quality -- types lint complexity formatting

  structure:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<sha> # vX.Y.Z
      - uses: actions/setup-node@<sha> # vX.Y.Z
        with:
          node-version-file: .nvmrc
          cache: npm
      - run: npm ci
      - run: npm run quality -- duplication deadcode

  tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<sha> # vX.Y.Z
      - uses: actions/setup-node@<sha> # vX.Y.Z
        with:
          node-version-file: .nvmrc
          cache: npm
      - run: npm ci
      - run: npm run quality -- tests

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<sha> # vX.Y.Z
        with:
          fetch-depth: 0          # the secret scan needs the PR's commits
      - uses: actions/setup-node@<sha> # vX.Y.Z
        with:
          node-version-file: .nvmrc
          cache: npm
      - run: npm ci
      - name: Install secret scanner (pinned, checksum verified)
        env:
          VERSION: "<x.y.z>"
          SHA256: "<sha256 of the linux x64 archive>"
        run: |
          curl -sSfL -o scanner.tar.gz "https://github.com/<org>/<scanner>/releases/download/v${VERSION}/<asset>.tar.gz"
          echo "${SHA256}  scanner.tar.gz" | sha256sum -c -
          tar -xzf scanner.tar.gz -C /usr/local/bin <binary>
      - run: npm run quality -- security-code security-deps security-secrets
        env:
          # PR: scan only the PR's commits. Push: scan what was pushed.
          QUALITY_SECRETS_RANGE: ${{ github.event_name == 'pull_request' && format('{0}..{1}', github.event.pull_request.base.sha, github.event.pull_request.head.sha) || format('{0}..{1}', github.event.before, github.sha) }}

  gate:
    name: Code quality
    if: always()
    needs: [static, structure, tests, security]
    runs-on: ubuntu-latest
    steps:
      - name: Fail unless every quality job succeeded
        env:
          RESULTS: ${{ join(needs.*.result, ' ') }}
        run: |
          for r in $RESULTS; do
            if [ "$r" != "success" ]; then
              echo "A quality job finished with: $r"
              exit 1
            fi
          done
```

Notes on the template:

- The `security-secrets` function in the entry point reads `QUALITY_SECRETS_RANGE` and passes it as `--log-opts` to the scanner (gitleaks and Betterleaks share `git --log-opts="<range>"`; check against the installed version). Locally it can default to the full history or to `HEAD`. On the first push of a new branch `github.event.before` is all zeros. Handle that in the script by falling back to the default branch's merge base.
- For a monorepo, give each package its own jobs, or a matrix over packages, and list them all in `needs`. If a job is skipped for packages a PR didn't touch, treat it as an exclusion, because the aggregator will fail it. Recording "runs all packages on every PR" is simpler and safer.
- Containerised scanners: pin images by digest (`image@sha256:…`), not by tag.

## Enforcement: checking and requiring the check

Branch protection and rulesets work on public repos on every plan, but on **private repos only with GitHub Pro, Team or Enterprise**. On GitHub Free a private repo can run the gate but can't require it.

Read the active rules for the default branch (works unauthenticated on public repos; a fine-grained token needs Metadata: read):

```bash
gh api repos/{owner}/{repo}/rules/branches/main \
  --jq '.[] | select(.type == "required_status_checks") | .parameters.required_status_checks[].context'
```

This shows only *active* rulesets (not those in "evaluate" mode) and doesn't show bypass actors. Classic branch protection is a separate API and needs Administration: read:

```bash
gh api repos/{owner}/{repo}/branches/main/protection/required_status_checks --jq '.contexts'
```

Check both. A 403 or 404 on the second can mean no protection, no permission, or a plan that doesn't support it, so say which you think it is and why. For bypass actors, read the ruleset itself (`gh api repos/{owner}/{repo}/rulesets/{id} --jq .bypass_actors`) if the token allows it.

Steps to give the owner (don't change repo settings yourself):

1. Merge the workflow and let it run once, so that `Code quality` appears in the check picker.
2. **Settings → Rules → Rulesets → New branch ruleset.** Target the default branch. Enable **Require status checks to pass**, add `Code quality`, and enable **Require branches to be up to date** if they want strictness over convenience.
3. Decide who can bypass. An empty bypass list means the gate applies to admins too.
4. Optionally, in **Settings → Actions → General**, require actions to be pinned to a full SHA.

Record the result in `quality-baseline.json` → `gate.enforcement`, with the date checked.

## Other platforms

The rules carry over. Platform features change, so check the names below before relying on them.

- **GitLab CI:** jobs with `rules: - if: $CI_PIPELINE_SOURCE == "merge_request_event"` plus the default branch. No `allow_failure: true` on quality jobs. Enforce with the project's merge-check setting that requires a successful pipeline. A single aggregator isn't needed because the pipeline status is the check, but keep the quality jobs in one stage group so they're easy to audit.
- **Bitbucket Pipelines, CircleCI, Azure Pipelines, Jenkins:** run every category through the same entry point on every PR, have no step that swallows failures, and make the PR status required in the host's merge settings. If the host can't require it on the owner's plan, record `enforcement.status: unavailable`.
- **No CI at all:** say plainly that nothing enforces the gate. Offer a pre-push hook that runs the entry point as a stopgap, and record it as `not-required`. Hooks can be skipped with `--no-verify`.
