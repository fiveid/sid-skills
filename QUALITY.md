# Code quality gate

The gate is one command and one required CI check. Any change to a tool, threshold or exclusion goes through a dated entry in the decisions log below, so later audits can tell deliberate changes from drift. It was set up with this repo's own [`sid-quality-gate`](skills/sid-quality-gate/SKILL.md) skill.

- **Install the tools:** `scripts/install-tools.sh` (once, and again after a pin changes). Python tools go into `.venv`, binaries into `.tools/`. Both are gitignored.
- **Run locally:** `scripts/quality.sh` (one category: `scripts/quality.sh <category>`)
- **CI check:** `Code quality` in `.github/workflows/quality.yml`
- **Required before merge:** not yet. Add a ruleset on `main` once the workflow has run there (steps below). Verified 2026-11-13.
- **Run time:** about 12 s locally, about 45 s in CI (measured 2026-11-13). The hidden Unicode scan is 11 s of the local run. Scheduled rather than blocking: none.
- **Local hooks:** a pre-commit secret scan of staged changes (`.githooks/pre-commit`), about 0.02 s per commit. Turn it on per clone with `git config core.hooksPath .githooks`. A convenience, not enforcement: hooks are per-clone and `--no-verify` skips them.

### Requiring the check

1. Merge the workflow and let it run on `main`, so `Code quality` appears in the check picker.
2. **Settings → Rules → Rulesets → New branch ruleset.** Target `main`, enable **Require status checks to pass**, and add `Code quality`.
3. Decide who can bypass. An empty bypass list applies the gate to admins too.
4. Optionally, in **Settings → Actions → General**, require actions to be pinned to a full SHA.

## Categories

| Category | Tool (version) | Config | Threshold | Why this choice |
| :--- | :--- | :--- | :--- | :--- |
| Types | mypy 2.4.1 | `pyproject.toml` | `--strict`, unused `type: ignore` is an error | The most widely used Python checker. With no existing errors left to baseline, basedpyright's baseline file wasn't needed. Rejected: basedpyright 1.40.2, pyright |
| Lint | Ruff 0.17.3 | `pyproject.toml` | Recommended rules plus bugbear, pyupgrade, simplify, pylint, bandit and others, all at error | The dominant Python linter, and one tool for lint, complexity, security and formatting |
| Complexity | Ruff 0.17.3 | `pyproject.toml` | Cyclomatic 10, 4 parameters, nesting depth 3, 50 statements | Strict defaults. Nesting depth (PLR1702) is a preview rule, enabled on its own with `explicit-preview-rules` |
| Dead code | vulture 2.16 | `pyproject.toml` | Confidence 60 | The usual Python dead-code finder |
| Security: code | Ruff 0.17.3 (`S` rules) | `pyproject.toml` | All `S` rules except S603 and S607 | S603/S607 flag calling `git`, `gh` and `npm` by name. The scripts do that on purpose, with fixed argument lists and no shell |
| Security: secrets | Betterleaks 1.9.0 | none | Any finding fails. CI scans the PR's commits; locally, the full history | The maintained successor to gitleaks. Rejected: gitleaks 8.30.1 (stalled), trufflehog |
| Formatting | `ruff format` 0.17.3 | `pyproject.toml` | Check mode, line length 100 | Same tool as lint |
| Shell | ShellCheck 0.11.0 (shellcheck-py 0.11.0.1) | none | Severity: style and above | The standard shell linter, installed from PyPI so it's hash-pinned with the Python tools |
| CI workflows | zizmor 1.31.1 | none | Default persona, offline | Catches unpinned actions, template injection and credential leaks in the workflow. Offline, so it needs no token |
| Skills | `scripts/check_skills.py` | the script | Frontmatter `name` matches the folder and fits the spec, `description` present and at most 1024 characters, ASCII only; both catalogues list every skill exactly once | Enforces the spec and AGENTS.md's "keep catalogues in sync". Rejected: `skills-ref` 0.1.1, which says it's for demonstration only and whose PyPI entry points to a repo that no longer exists |
| Hidden Unicode | APM 0.35.0 (`apm audit --file`) | none | Fail on critical and warning findings in any file under `skills/` | APM runs the same check on install and blocks critical findings, so a skill that fails here can't be installed with it |
| Links | lychee 0.24.2 | none | Every relative link and `#section` anchor in tracked Markdown resolves. External URLs are not fetched | Catches broken cross-links and renamed headings |

All tools are pinned: Python tools by hash in `requirements-quality.txt`, binaries by SHA-256 in `scripts/install-tools.sh`, and GitHub Actions by commit SHA. Every pinned release was at least two weeks old at setup, except where noted in the decisions log.

## Deliberate exclusions

| Category | What's excluded | Reason | Date | Decided by |
| :--- | :--- | :--- | :--- | :--- |
| Duplication | Everything | Each skill must be self-contained, so its scripts can't share code. The fix a duplication check pushes towards isn't available | 2026-11-13 | Owner |
| Security: dependencies | Everything | The skill scripts use the Python standard library only. The gate's own tools are pinned by hash or checksum and reviewed when a pin changes | 2026-11-13 | Owner |
| Tests and coverage | Everything, for now | No tests yet. **Target:** tests for `scan_pii.py` and `quality_snapshot.py` before v1.1.0, then a coverage floor at the measured value | 2026-11-13 | Owner |

## Policies

- **Vulnerable dependencies:** not applicable while the scripts have no third-party dependencies (see exclusions).
- **Suppressions:** none set. There are no inline suppressions in the repo; the audit counts any that appear.

## Baseline

Measured 2026-11-13 by `quality_snapshot.py`. Full figures are in `quality-baseline.json`.

| | Total | Unexplained |
| :--- | ---: | ---: |
| Inline suppressions | 35 | 31 |
| Lint | 17 | 17 |
| Types | 5 | 5 |
| Coverage | 3 | 2 |
| Formatting | 4 | 3 |
| Security | 4 | 4 |
| Duplication | 2 | 0 |

**All 35 are false positives:** they are the marker table in `skills/sid-quality-gate/scripts/quality_snapshot.py`, which lists every suppression comment the scanner looks for. The file is still scanned, so a real suppression added there shows up as growth.

| Baseline or ignore file | Entries |
| :--- | ---: |
| `pyproject.toml` Ruff ignored rules | 2 |

The two CI lines flagged are intended: `branches: [main]` limits push runs to `main` (pull requests run on every branch), and `if: always()` lets the `Code quality` job report when another job fails.

## Decisions log

Newest first. Each entry: what changed, from what to what, why, and who asked.

### 2026-11-13: Gate set up

- Types: mypy 2.4.1, strict. Lint, complexity, security (code) and formatting: Ruff 0.17.3. Dead code: vulture 2.16. Secrets: Betterleaks 1.9.0. Shell: ShellCheck 0.11.0. Workflows: zizmor 1.31.1. Skills: `scripts/check_skills.py`. Hidden Unicode: APM 0.35.0. Links: lychee 0.24.2.
- Existing code was fixed rather than baselined, at the owner's choice: 86 Ruff findings (21 of them complexity) and 40 mypy errors across the four skill scripts. Behaviour was checked unchanged by running every script mode against fixed fixtures before and after (33 cases, identical output).
- Nothing baselined.
- `mypy-extensions` held at 1.1.0: 1.2.0 was 10 days old.
- APM is installed from its release binary, not PyPI, to keep its 17 direct dependencies out of the gate's Python environment.
- Excluded: duplication, security (dependencies), tests. Reasons above.
- Pre-commit secret scan added at the owner's choice.
- Requested by the owner.
