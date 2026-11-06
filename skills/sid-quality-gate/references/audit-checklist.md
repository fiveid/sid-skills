# Audit checklist

The snapshot script handles counting. This list covers what it can't see. Work through it after running `quality_snapshot.py compare`. Every finding needs a location (file and line, a config key, or a command and its output).

## 1. Thresholds and rules

For each watched file the script reports as changed, read `git diff <anchor> -- <file>` and classify every hunk:

| Finding | Examples |
| :--- | :--- |
| Threshold changed | `complexity: 10 → 15`, coverage `lines: 80 → 72`, jscpd `threshold: 2 → 5`, PHPStan `level: 8 → 6`, `fail_under` lowered |
| Rule disabled or downgraded | `"error" → "warn"`, `→ "off"`, removed from an `extends` list, a strict preset swapped for a recommended one, `strict: true` removed, a mypy module override with `ignore_errors = true` |
| Exclusion or ignore pattern added or grown | lint `ignores`/`exclude`, coverage `exclude`/`omit`, jscpd `ignore`, Knip `ignore`/`ignoreDependencies`, Semgrep `exclude`, Gitleaks allow-list paths, `tsconfig` `exclude` |
| Tool removed or replaced | A dev dependency removed, a step deleted from the gate script, a config file deleted |
| Tightened | Report these too. They're changes from the record, and the record should be updated at the owner's request |

Compare each one with the values in `quality-baseline.json` → `categories`, and look for a decisions-log entry that matches it.

## 2. Config the record doesn't watch

Look for files that affect the gate but aren't in `watched_files`:

- Nested or override configs: `.eslintrc*` or `eslint.config.*` in sub-directories, `overrides`/`files` blocks, per-package `tsconfig.json` that don't extend the strict base, `pyproject.toml` per-module overrides, `[lints]` tables in workspace member `Cargo.toml` files, `phpstan.neon` includes.
- New ignore or baseline files anywhere in the tree.
- Tool config sections that turned up in `package.json`, `pyproject.toml`, `setup.cfg`, `composer.json`.

Report each one as "affects the gate, not in the record".

## 3. The gate still covers every category

Read the entry point (`gate.command` and the script it runs):

- Every category in the record still runs, with the recorded config file (look for `--config` pointing somewhere else, or `--no-config`). A category with `runs_in` is checked inside that category's run: confirm its rules are still in that tool's config at the recorded level.
- No step swallows failures: `|| true`, `set +e` with no check of exit codes later, `--exit-zero`, `--no-fail`, warnings that no longer fail (`--max-warnings` above 0), `passWithNoTests` on a suite that should have tests.
- The tools run over the recorded paths (no narrowed globs, no `--changed-only` unless that was recorded).

## 4. CI

Read the gate workflow (or the equivalent on other platforms):

- **Triggers:** runs on every pull request to the default branch, with no `paths`, `paths-ignore` or `branches` filter that skips some PRs. Also runs on pushes to the default branch and on `merge_group` if a merge queue is used.
- **Bypasses:** `continue-on-error`, `if:` conditions that can skip a job (actor, label, title, branch name), `allow_failure`, skip markers.
- **Aggregator:** the job named in `gate.check_name` still exists, still lists every quality job in `needs`, runs with `if: always()`, and fails on any result other than `success` (a skipped job must fail it).
- **Pinning:** actions pinned to a full SHA. Tool versions pinned rather than `latest`.
- **Check name** unchanged. Renaming the job silently breaks a required check.
- **Every trigger scans something.** Work out what each range or filter evaluates to on each event. For example, `origin/main..HEAD` is empty on a push to `main`, so a secret scan using it only ever covers PRs.

## 4a. Local hooks and scheduled jobs

- For each entry in `gate.local_hooks`, check the hook config still exists and still runs the recorded scanner. You can't see whether any particular clone has the hook installed, so say that rather than implying it's active.
- For categories recorded as scheduled rather than blocking, check the scheduled workflow still exists and its schedule hasn't been removed. Also check that no further categories have moved off the PR path without a log entry.

## 5. Enforcement

Where you can check it (see `ci-github-actions.md` for the commands), confirm the check named in `gate.check_name` is still required on the default branch, and whether admins can bypass it. Compare with `gate.enforcement` in the record. If you can't check (no access, another host), say "not verifiable" and why. Don't guess.

Also check that the gate could pass at all. If the config makes green impossible, a merged PR means the check isn't really blocking anything. Examples: a test category with no test files, a lint preset that bans a directive the code now contains, dead-code checks that would flag files added since the record. Without running the tools, report this as "the recorded enforcement is doubtful", with the evidence.

## 6. Drift

- **Versions:** compare the installed or pinned version of each tool with the recorded version, and with the latest release. Report a tool one or more major versions behind, or with no release in 18 months (possibly abandoned). Note deprecations or replacements you find while checking.
- **Missing tools:** a tool the record lists that's no longer installed, pinned or invoked.
- **Record mismatch:** a value in the record (`record_doc`) that doesn't match `quality-baseline.json`, or either one that doesn't match the config.

## 7. Suppressions

Use the script's tables. If `scan_exclude` or `extra_markers` changed since the anchor (check the record's history), the counts aren't comparable, so report that first. For new locations, spot-check that each one really is a suppression and that its explained/unexplained label is right; adjust the counts if not. List file-scope and block-scope suppressions (`@ts-nocheck`, file-level `eslint-disable`, `# ruff: noqa`, `#![allow(...)]`) separately, because each one hides a whole file or block.

## Report format

Write in plain, direct British English. Give findings, not advice.

```markdown
## Quality gate audit: <repo> at <short sha>, <date>

Compared with the baseline recorded on <date> (anchor <sha>, <n> commits ago).

**Summary:** <n> unlogged changes, <n> logged changes, suppressions <old> → <new> (<+n unexplained>), enforcement <status>.

### Thresholds and rules
| Location | Category | Change | Recorded | Now | Logged? |

### Exclusions and ignore lists
| Location | Category | Change | Logged? |

### Inline suppressions
| | Recorded | Now | Change |
(totals, then by category)

New locations:
| Location | Category | Explained | Text |

### Baseline and allow-list files
| File | Recorded | Now | Change |

### CI and gate script
| Location | Finding |

### Enforcement
<status, how verified, or why not verifiable>

### Drift
| Tool | Recorded | Installed | Latest | Note |

### Not checked
<anything you couldn't verify, and why>
```

Leave out empty sections. Close with a single line saying that baseline changes happen only at the owner's request, via a rebaseline.
