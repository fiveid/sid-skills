# Tool selection

This file tells you how to choose a tool, not which one to choose. The candidate lists are a place to start, not the whole field. The traps at the end are dated, so check each one before relying on it. Consistency comes from the record: once the record names a tool, later audits and rebaselines use that tool rather than choosing again.

## How to choose

For each category, shortlist two or three tools: the owner's preference if they have one, the candidates below, and anything newer that a search for "<language> <category> tool" turns up. Keep only the tools that meet all of these:

1. **Free**, locally and in CI, for a solo developer. Hosted dashboards don't count towards the gate.
2. **Real:** it exists in the official registry (npm, PyPI, crates.io, Packagist, the Go module proxy, RubyGems, NuGet), and the source repo it links to is the right one. Never recommend a tool from memory alone, because hallucinated and lookalike packages exist.
3. **Maintained:** at least one release in the last 12 months, and open issues get answered.
4. **Stable:** not marked alpha, beta or preview, unless the owner asks for it. Say so if they do.
5. **Can fail a run:** it exits non-zero at a configurable level, with no warnings-only mode as the default.
6. **Can be pinned:** to an exact version, through the lockfile or a checksum.
7. **Can be baselined:** it can record existing violations, or you record the gap (see `thresholds.md`).

Where several tools pass, prefer in this order:

1. The tool the project already uses.
2. The ecosystem's dominant tool.
3. One tool that covers several categories, over several single-purpose ones.
4. The faster one.

Ask "would most teams in this ecosystem recognise this choice?" If the answer is no, give the reason in the record.

Check before pinning:

| Ecosystem | Versions and release dates |
| :--- | :--- |
| npm | `npm view <pkg> version time --json` |
| PyPI | `curl -s https://pypi.org/pypi/<pkg>/json` (`info.version`, `releases`) |
| Go | `go list -m -versions <module>`, or the module proxy |
| crates.io | `cargo search <crate>`, or `https://crates.io/api/v1/crates/<crate>` |
| Binaries | `gh api repos/<owner>/<repo>/releases --jq '.[0:5][] \| [.tag_name, .published_at, .prerelease]'` |

Pick a release at least two weeks old (see SKILL.md, step 6). Write the chosen version, its release date and the alternatives you rejected into the category row of the record. That evidence is what a later audit's drift check compares against.

## Vetting a tool before its first run

Measuring runs the tool, so vet any tool the project doesn't already use before it runs. That includes one-off helpers you'd only run during setup, such as a workflow linter fetched with `uvx` or `npx`. Use `sid-dep-audit` if it's installed. Otherwise look at these signals:

| Signal | Reassuring | Warning sign |
| :--- | :--- | :--- |
| **Use** | Widely used: for npm or PyPI, roughly 100k+ weekly downloads, or many dependents | Little use in absolute terms: under roughly 10k weekly downloads, or a few thousand release downloads in all. A newer tool with fewer users than the one it replaces isn't a warning sign on that alone |
| **Age** | Releasing for six months or more | First release under six months ago |
| **Maintenance** | A release in the last 12 months, issues answered | Nothing for over a year, or a sudden change of owner |
| **Maintainers** | An organisation, or several people with publish rights | One person, **and** another warning sign |
| **Source** | The registry links to the repo you expect, and its release matches the published version | A mismatch: treat this as failing on its own |

Anything between the two columns is neutral. Weigh the signals together. Many of the dominant tools have one main maintainer (Knip and jscpd, for example), and that alone isn't a reason to stop. Ask for approval when:

- the source doesn't match, or
- two or more warning signs appear together, such as young and little used, or
- one maintainer comes with any other warning sign.

The question says which signs you found.

If the host's safety checks refuse to run a tool, that's an answer: offer the alternative, never another way to run it. If a registry page is behind a bot check, use its API or another official source, or say you couldn't check. Never retry with a different user agent.

If a host the setup needs is blocked (a registry, an advisory API, a rule source), put it to the owner in round 1: grant access, or a named alternative and what it loses. Don't swap tools quietly to avoid asking. An alternative that covers less, or that needs a hand-written script to make up the difference, isn't an equal swap.

## Candidates

Names only, with no versions: check those yourself. Where a language has no candidate for a category, look for one, then fall back to a cross-language tool or a recorded exclusion.

| Category | Cross-language | JS/TS | Python | Go | Rust | PHP | JVM | Ruby | .NET |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Types | | TypeScript (strict + extra flags) | basedpyright, mypy, pyright, Pyrefly | compiler + `go vet` | compiler | PHPStan, Psalm | javac `-Werror` + Error Prone, NullAway | Sorbet | Nullable + warnings as errors |
| Lint | Semgrep (custom rules) | ESLint + typescript-eslint, Oxlint, Biome | Ruff | golangci-lint | clippy | PHPStan rules, PHP_CodeSniffer | PMD, Checkstyle, detekt | RuboCop | Roslyn analysers |
| Complexity | lizard | the linter's rules, sonarjs (cognitive) | Ruff (C901, PLR09xx), complexipy (cognitive) | golangci-lint (gocyclo, gocognit, funlen, nestif) | clippy | PHPMD | PMD, detekt | RuboCop Metrics | CA1502 |
| Duplication | jscpd, PMD CPD | | | golangci-lint `dupl` | | | CPD | flay | |
| Dead code | | Knip | vulture, deptry | `deadcode`, `unused` | rustc, cargo-shear, cargo-machete | shipmonk dead-code-detector, composer-unused | PMD | | IDE0051/0052 |
| Security: code | Semgrep CE, Opengrep | | Ruff `S` | gosec | | | SpotBugs + FindSecBugs | Brakeman | |
| Security: deps | OSV-Scanner | `npm`/`pnpm` audit | pip-audit | govulncheck | cargo-deny, cargo-audit | `composer audit` | OWASP Dependency-Check | bundler-audit | `dotnet list package --vulnerable` |
| Security: secrets | Betterleaks, gitleaks, trufflehog | | | | | | | | |
| Coverage | diff-cover (changed lines) | Vitest, Jest | pytest-cov / coverage.py | `go test -cover` + a threshold script | cargo-llvm-cov | PHPUnit | JaCoCo | SimpleCov | coverlet |
| Formatting | | Prettier, Biome, Oxfmt | `ruff format` | gofmt | rustfmt | PHP-CS-Fixer | Spotless, ktlint | RuboCop | `dotnet format` |

Known baseline mechanisms (check each one still works this way): ESLint bulk suppressions (`eslint-suppressions.json`), PHPStan and Psalm baselines, basedpyright `--writebaseline`, jscpd `--baseline`, complexipy snapshots, detekt and Android lint baseline XML, `.rubocop_todo.yml`, `brakeman.ignore`, golangci-lint `new-from-merge-base` (moving, no file), vulture whitelist. If your chosen tool has no baseline, record that in the category row.

## Known traps

Each trap has the date it was observed and how to re-check it. Check it, then act on what you find. If a trap no longer applies, say so in the confirmation. If you find a new one, tell the owner, so it can be added here.

| Observed | Trap | How to re-check |
| :--- | :--- | :--- |
| 2026-03 | Trivy's GitHub Actions were compromised (CVE-2026-33634): tags were force-pushed and a malicious binary published. The general lesson: pin actions to a SHA, images to a digest, and binaries to a checksum | Search for current advisories on any scanner action you plan to use |
| 2026-05 | `gitleaks-action` needs a licence key for organisation repos. Run the scanner binary directly instead | The action's README |
| 2026-03 | gitleaks has stalled since its original author left. Betterleaks is his drop-in successor | Release dates on both repos |
| 2026-07 | TypeScript 7 (Go-native) is stable, but typescript-eslint supports TS below 6.1, so a gate with typed ESLint pins TS 6.0.x. Oxlint's type-aware mode needs TS 7 | typescript-eslint's `typescript` peer dependency; Oxlint's type-aware docs |
| 2026-11 | Ruff has no baseline file, and `RUF100` (unused `noqa`) is off by default | Ruff's docs on error suppression |
| 2026-11 | Semgrep's own dependencies carry advisories, so install it in isolation (pinned `uvx`, pipx or a container), not in the project lockfile. Registry rule packs (`p/default`) change over time and need semgrep.dev. Default to rules pinned by commit from the `semgrep/semgrep-rules` repo (or a committed copy): repeatable, auditable, and they work offline once fetched. `semgrep ci` needs a login; `semgrep scan` doesn't | Run `pip-audit` on a fresh Semgrep install; the rules repo's licence and latest commit |
| 2026-11 | Semgrep CE analyses within a single function and file only. Data passed between functions is missed, so record the gap or consider Opengrep | Semgrep CE vs Pro docs |
| 2026-11 | CodeQL is free on public repos only | GitHub's Code Security pricing page |
| 2026-11 | OSV-Scanner had no confirmed severity-threshold flag. To block on high and critical, filter its JSON output | `osv-scanner scan --help` |
| 2026-02 | Since Vitest 4, files no test imports are only counted if `coverage.include` is set, so coverage looks higher than it is without it | Vitest's coverage docs |
| 2026-02 | ESLint 10 dropped eslintrc and looks up config from each file's directory, so nested configs change the gate | ESLint's configuration docs |
| 2026-11 | golangci-lint v2 changed its config format (`version: "2"`) | golangci-lint's migration docs |
| 2026-11 | govulncheck's GitHub releases are stale; take its version from the Go module proxy | `go list -m -versions golang.org/x/vuln` |
| 2026-11 | detect-secrets has had no release since 2024 | PyPI release dates |
| 2026-11 | `ty` (Astral's Python type checker) and Oxfmt (a JS/TS formatter) were still beta | Their release notes |

## Suppression markers

`quality_snapshot.py` counts inline suppressions using a built-in list of markers for the tools above. If you pick a tool whose suppression comment it doesn't recognise, add the marker to `extra_markers` in `quality-baseline.json` (see `record-template.md`), so the audit counts it too. Check this by putting one suppression in a scratch file and running `quality_snapshot.py scan --locations`.

Where the chosen tool can require a reason on each suppression, turn it on. It makes "unexplained" mean something. Examples:

- ESLint: `@eslint-community/eslint-comments/require-description`
- golangci-lint: `nolintlint.require-explanation`
- clippy: `allow_attributes_without_reason`
- mypy: the `ignore-without-code` error code
- TypeScript: typescript-eslint `ban-ts-comment` with `allow-with-description`
