#!/usr/bin/env bash
# Code quality gate: the single entry point for local runs and CI.
#
#   scripts/quality.sh               run every category
#   scripts/quality.sh lint types    run only the named categories
#
# Every selected category runs even if an earlier one fails, so one run
# reports everything. Exits non-zero if any category failed.
# Thresholds and the reasons behind them live in the quality record (QUALITY.md by default).

set -uo pipefail
cd "$(dirname "$0")/.."

ALL=(types lint complexity duplication deadcode security-code security-deps security-secrets tests formatting)

# Replace each body with the project's commands. Keep one category per function
# so CI jobs can call them by name. If a tool checks a category only inside
# another category's run, drop that function from ALL and record `runs_in`. Do not add `|| true` or exit-zero flags here:
# the audit reports them as bypasses.
types()            { echo "TODO: type checker"; return 1; }
lint()             { echo "TODO: linter at error level, zero warnings"; return 1; }
complexity()       { echo "TODO: complexity rules (often part of the linter run)"; return 1; }
duplication()      { echo "TODO: duplicate detector"; return 1; }
deadcode()         { echo "TODO: unused files, exports and dependencies"; return 1; }
security-code()    { echo "TODO: SAST"; return 1; }
security-deps()    { echo "TODO: dependency advisories"; return 1; }
security-secrets() { echo "TODO: secret scan (CI passes the commit range in QUALITY_SECRETS_RANGE)"; return 1; }
tests()            { echo "TODO: tests with coverage floor"; return 1; }
formatting()       { echo "TODO: formatter in check mode"; return 1; }

selected=("$@")
[ ${#selected[@]} -eq 0 ] && selected=("${ALL[@]}")

failed=()
for category in "${selected[@]}"; do
  if ! declare -F "$category" >/dev/null; then
    echo "Unknown category: $category (expected one of: ${ALL[*]})" >&2
    exit 2
  fi
  [ -n "${GITHUB_ACTIONS:-}" ] && echo "::group::$category"
  if "$category"; then
    echo "✓ $category"
  else
    echo "✗ $category"
    failed+=("$category")
  fi
  [ -n "${GITHUB_ACTIONS:-}" ] && echo "::endgroup::"
done

if [ ${#failed[@]} -gt 0 ]; then
  echo "Code quality failed: ${failed[*]}" >&2
  exit 1
fi
echo "Code quality passed: ${selected[*]}"
