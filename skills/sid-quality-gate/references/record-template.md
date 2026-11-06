# Record template

Setup writes two things. A human-readable record is for people. `quality-baseline.json` is for the audit script and must agree with it. The record's place follows the project's rules: a standalone `QUALITY.md` at the repo root by default, or a section of an existing doc where the project doesn't want separate decision records. `record_doc` says where it is. The template below is for the standalone file; as a section, keep the same headings one level down.

## `QUALITY.md`

```markdown
# Code quality gate

The gate is one command and one required CI check. Any change to a tool, threshold or exclusion goes through a dated entry in the decisions log below, so later audits can tell deliberate changes from drift.

- **Run locally:** `<command>` (one category: `<command> <category>`)
- **CI check:** `Code quality` in `<workflow path>`
- **Required before merge:** <yes, via <ruleset or branch protection> | no, see note | unavailable on <plan>>. Verified <YYYY-MM-DD>.
- **Run time:** about <n> s locally, about <n> min in CI (measured <YYYY-MM-DD>). Scheduled rather than blocking: <categories moved off the PR path, or "none">.
- **Local hooks:** <for example: "pre-commit secret scan of staged changes via Lefthook, about 0.3 s per commit; enable with `<command>`" | "none">. A convenience, not enforcement: hooks are per-clone and can be skipped.

## Categories

| Category | Tool (version) | Config | Threshold | Why this choice |
| :--- | :--- | :--- | :--- | :--- |
| Types | | | | |
| Lint | | | | |
| Complexity | | | | |
| Duplication | | | | |
| Dead code | | | | |
| Security: code | | | | |
| Security: dependencies | | | | |
| Security: secrets | | | | |
| Tests and coverage | | | | |
| Formatting | | | | |

## Deliberate exclusions

Anything a category doesn't cover, and why. A category with no tool is listed here or not at all.

| Category | What's excluded | Reason | Date | Decided by |
| :--- | :--- | :--- | :--- | :--- |

## Policies

- **Vulnerable dependencies:** <for example: fail on high and critical; allow-list entries in `<file>` need a reason and an expiry date>.
- **Suppressions:** <the owner's policy, if they have one. The gate doesn't set one; the audit only counts them.>

## Baseline

Measured <YYYY-MM-DD> by `quality_snapshot.py`. Full figures are in `quality-baseline.json`.

| | Total | Unexplained |
| :--- | ---: | ---: |
| Inline suppressions | | |
| <category rows> | | |

| Baseline or ignore file | Entries |
| :--- | ---: |

## Decisions log

Newest first. Each entry: what changed, from what to what, why, and who asked.

### <YYYY-MM-DD>: Gate set up
- <one line per category: tool and threshold>
- <what was baselined and how many entries>
- Requested by <owner>.
```

## `quality-baseline.json`

Hand-write everything except `measured`, which `quality_snapshot.py write` fills in and replaces. Keep it in sync with `QUALITY.md`.

```json
{
  "schema_version": 1,
  "record_doc": "QUALITY.md",
  "gate": {
    "command": "npm run quality",
    "check_name": "Code quality",
    "ci_workflow": ".github/workflows/quality.yml",
    "files": ["scripts/quality.sh", ".github/workflows/quality.yml", "package.json"],
    "enforcement": {
      "status": "required | not-required | unavailable | unverified",
      "verified": "2026-11-06",
      "how": "ruleset 'Protect main' requires 'Code quality'"
    },
    "timing": { "local_seconds": 40, "ci_minutes_estimate": 4, "measured": "2026-11-06", "scheduled_categories": [] },
    "local_hooks": [
      { "hook": "pre-commit", "category": "security_secrets", "manager": "lefthook", "config_file": "lefthook.yml", "seconds_per_commit": 0.3 }
    ]
  },
  "categories": {
    "types": {
      "tool": "typescript",
      "version": "x.y.z",
      "config_files": ["tsconfig.json"],
      "settings": { "strict": true, "noUncheckedIndexedAccess": true },
      "thresholds": {},
      "baseline_file": null,
      "exclusions": [],
      "runs_in": null
    },
    "lint": { "...": "same shape" },
    "complexity": { "...": "same shape; thresholds e.g. { \"cyclomatic\": 10, \"cognitive\": 15, \"function_lines\": 50, \"depth\": 3, \"params\": 4 }; \"runs_in\": \"lint\" if the linter checks it in the same run" },
    "duplication": { "...": "thresholds e.g. { \"min_tokens\": 50, \"max_percent\": 2 }" },
    "dead_code": { "...": "same shape" },
    "security_code": { "...": "same shape" },
    "security_dependencies": { "...": "thresholds e.g. { \"fail_on\": \"high\" }; baseline_file is the allow-list" },
    "security_secrets": { "...": "same shape" },
    "tests": { "...": "thresholds e.g. { \"lines\": 80, \"branches\": 70 }" },
    "formatting": { "...": "same shape" }
  },
  "excluded_categories": [
    { "category": "duplication", "scope": "all", "reason": "…", "date": "2026-11-06", "decided_by": "owner" }
  ],
  "watched_files": ["tsconfig.json", "eslint.config.js", "knip.json", ".jscpd.json", "vitest.config.ts"],
  "scan_exclude": [".agents/**", ".claude/**", "**/node_modules/**", "vendor/**", "**/*.min.js"],
  "extra_baseline_files": {
    ".oxlintrc.json": { "method": "json-path", "path": "overrides.*.files" },
    "knip.json": [
      { "method": "json-path", "path": "ignoreIssues", "label": "files" },
      { "method": "json-path", "path": "ignoreIssues.*", "label": "issue types" }
    ],
    ".semgrep.yml": { "method": "regex", "pattern": "^\\s+- " }
  },
  "extra_markers": [
    { "pattern": "mytool-allow\\(", "category": "lint", "scope": "line" }
  ],
  "measured": {}
}
```

Notes:

- `watched_files` lists every file that can change the gate's behaviour: tool configs, any config section inside `package.json`/`pyproject.toml`/`Cargo.toml`/`composer.json`, nested configs in sub-directories, ignore files, and allow-lists. Anything left off can drift without the audit seeing it.
- `gate.local_hooks` lists hooks set up at setup time. Put each hook's config file in `gate.files` too, so the audit sees it if it changes or disappears.
- `gate.files` lists the entry point and CI files. The script scans these for bypass patterns as well as the CI directory.
- `runs_in` names the category whose run also checks this one, when a tool can't check it on its own. The drill still has to show this category failing.
- `quality_snapshot.py write` writes plain two-space JSON. Run the project's formatter on the file afterwards; the script reads values, not layout.
- `scan_exclude` controls where the suppression scan looks. Changing it changes the counts, so the audit reports any change to it.
- `extra_baseline_files` maps a path to a counting method for baseline or allow-list files the script doesn't already know about. For a dedicated file, give a method name: `lines`, `eslint`, `phpstan`, `psalm`, `basedpyright`, `jscpd`, `complexipy`, `xml-id`, `xml-issue`, `detect-secrets` or `osv`.
- Where a tool keeps its pre-gate list inside its config, give a counter instead, or a list of counters with a `label` each. `json-path` counts the entries at a dotted path in a JSON, JSONC or TOML file, with `*` stepping into every item. `regex` counts matching lines, for YAML, or for a config written in code such as `knip.ts`. Run `quality_snapshot.py scan` and check each count by hand once. A count the script can't parse shows as `unreadable`.
- `extra_markers` adds suppression markers for tools the script doesn't know. Each one is a Python regex, a category and a scope (`line`, `block` or `file`). They are matched before the built-in markers. Removing one lowers the counts, so the audit treats it like a change to `scan_exclude`.
- Use the category keys above so audits stay comparable across projects.
