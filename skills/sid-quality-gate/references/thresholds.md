# Thresholds

These are the strict defaults for a new project and the rules for setting a baseline on existing code. The owner can tune any of them. Record the value chosen and the reason in the record.

## Strict defaults (greenfield)

| Category | Default | Why |
| :--- | :--- | :--- |
| Types | The checker's strictest practical mode, plus the extra flags it offers beyond that. For TypeScript: `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitOverride`, `noImplicitReturns`, `noFallthroughCasesInSwitch`, `noPropertyAccessFromIndexSignature`. For mypy: `--strict` + `--warn-unused-ignores`. No implicit `any`/`Any` | Type errors are the cheapest bugs to catch, and loosening later is easier than tightening |
| Lint | The tool's recommended set plus its type-aware or "strict" set, every rule at error, zero warnings allowed (`--max-warnings 0` or equivalent). Unused disable directives are errors | Warnings don't block anything, so they pile up unread |
| Cyclomatic complexity | 10 per function | McCabe's original limit, and the usual default in most tools |
| Cognitive complexity | 15 per function | SonarSource's default; it tracks how hard code is to read better than cyclomatic does |
| Function length | 50 lines, not counting blank lines or comments | Long enough for real work, short enough to read at once |
| Nesting depth | 3 | Deeper nesting is where agents hide edge cases |
| Parameters | 4 | Beyond that, pass an options object or a type |
| Duplication | Blocks of 50+ tokens; the gate fails above 2% duplicated lines | Below 50 tokens the noise outweighs the signal |
| Dead code | Zero unused files, exports and dependencies, with entry points configured explicitly | Agents leave old versions behind; dead code is how you notice |
| SAST | Fail on findings at error/high severity from the default free ruleset | Low-severity rules are noisy enough that people learn to ignore the whole check |
| Dependencies | Fail on high and critical advisories; allow-list entries need a reason and an expiry date | See "Dependency advisories" below |
| Secrets | Fail on any finding; allow-list entries are fingerprints with a reason | Anything committed has to be treated as leaked |
| Coverage | 80% lines, 70% branches, measured over source files only | See "Coverage" below |
| Formatting | Check mode, no exceptions beyond generated files | It's free once it's set up, and it removes a whole class of review noise |

Test files usually get relaxed function-length and parameter limits (long `describe` blocks and table-driven cases are normal). Record that as an exclusion. Keep complexity and type rules in tests: tangled tests are how fake coverage gets in.

## Existing code: getting to green on day one

Measure first, with the strict default, in report mode. Then choose by kind of rule.

### Per-function and per-line rules: strict limit plus a baseline file

Types, lint and complexity rules judge each function or line on its own. Keep the strict limit and record the existing violations in the tool's baseline file, so only new code has to meet it:

- New and changed code meets the strict bar from day one.
- The baseline file is a single, countable list. The audit reports when it grows. When it shrinks, the tool usually reports the stale entries (ESLint `--prune-suppressions`, PHPStan `reportUnmatchedIgnoredErrors`).

Where a tool has no baseline mechanism, choose in this order:

1. Run that rule through a tool that has one (complexity via an ESLint rule rather than a standalone counter, for example).
2. List the offending files as a recorded exclusion in config, with the reason "legacy, baselined on <date>". The audit tracks the list's length. Scope each exclusion to the specific rules that fire, never to a whole file. Say in round 2 that new code in those files is exempt from those rules too.
3. As a last resort, set the limit just above the worst existing value **and** write down a target in the record. Say plainly in round 2 that this lets through almost anything up to that value.

Never get to green by adding inline suppressions. They can't be told apart from new ones, and the audit would count them as debt the owner chose to take on.

### Project-wide numbers: just beyond the current value

| Measure | Day-one setting |
| :--- | :--- |
| Coverage | Current value rounded down to a whole percent, per metric (lines, branches, functions if measured) |
| Duplication % | Current value rounded up to one decimal place |
| Dead-code count | Prefer fixing or ignoring by name in the tool's config. If there are too many, baseline the list where the tool supports it, or record the current count as the limit |
| Advisory count | Allow-list each existing advisory with a reason and an expiry date (default 90 days) |

### Ratcheting

The gate doesn't tighten itself. When the owner asks to tighten, raise project-wide numbers to the new current value (rounded the same way) and prune baseline files. It's a rebaseline, so it gets a decisions-log entry. Some tools offer automatic ratcheting (Vitest `coverage.thresholds.autoUpdate`, for example). It rewrites config during a test run, so offer it as an option rather than a default. Leave it out if the owner wants every threshold change to appear in a PR on purpose.

## Coverage

A coverage floor stops coverage dropping. It says nothing about whether the tests check anything. Chasing the number is how test theatre starts: assertion-free tests, snapshot dumps, mocks of the thing being tested. Treat the floor as a ratchet, not a target. Pair it with test review (for example `sid-test-review`). Optional extras:

- **Coverage on changed lines** (`diff-cover` or the coverage tool's own diff mode) holds new code to a higher bar without touching the project-wide floor.
- **Mutation testing** (StrykerJS, mutmut, cargo-mutants, Infection, PIT) is the honest measure of whether tests catch breakage. It's slow, so suggest it as a scheduled job rather than part of the gate.

If the project has no tests and needs them, the floor starts at 0 with a written target, and the category isn't excluded. If the project really doesn't need tests (a config-only repo, a throwaway spike), record that as an exclusion with the reason.

## Dependency advisories

A new advisory can turn the gate red on a PR that touched nothing. The default policy:

- Fail on high and critical.
- Existing advisories, and any the owner decides to live with, go in the scanner's allow-list with a reason and an expiry date. Prefer scanners that support expiry natively (OSV-Scanner's `ignoreUntil`, for example). Otherwise put the date in a comment next to the entry.
- An expired entry fails the gate again. That's intentional: someone has to look at it again.

Alternatives the owner may prefer, to record if chosen: report advisories but don't block (record it as a deliberate exclusion of "vulnerable dependencies" from blocking), or block only on advisories introduced by the PR's own lockfile changes.
