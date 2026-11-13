#!/usr/bin/env bash
# Code quality gate: the single entry point for local runs and CI.
# Written for bash 3.2, the version macOS ships.
#
#   scripts/install-tools.sh             install the pinned tools (once, and after a pin changes)
#   scripts/quality.sh                   run every category
#   scripts/quality.sh lint types        run only the named categories
#
# Every selected category runs even if an earlier one fails, so one run
# reports everything. Exits non-zero if any category failed.
# Thresholds and the reasons behind them live in QUALITY.md.

set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

ROOT=$PWD
export PATH="$ROOT/.venv/bin:$ROOT/.tools/bin:$PATH"
APM="$ROOT/.tools/apm/apm"

ALL=(types lint complexity deadcode security-code security-secrets formatting shell workflows skills unicode links)
# Not run, by recorded decision (see QUALITY.md): duplication, security-deps, tests.

# Ruff rules that make up the complexity category (limits are in pyproject.toml)
COMPLEXITY_RULES=C901,PLR0911,PLR0912,PLR0913,PLR0915,PLR0917,PLR1702

types()         { mypy; }
lint()          { ruff check; }
complexity()    { ruff check --select "$COMPLEXITY_RULES"; }
deadcode()      { vulture; }
# Overriding the rule selection drops the config's ignore list, so pass it back from pyproject.toml
security-code() {
  local ignored
  ignored=$(python3 -c "import tomllib; print(','.join(tomllib.load(open('pyproject.toml', 'rb'))['tool']['ruff']['lint']['ignore']))") || return 1
  ruff check --select S --ignore "$ignored"
}
formatting()    { ruff format --check; }

shell() {
  local files=() file
  while IFS= read -r file; do files+=("$file"); done < <(git ls-files '*.sh' .githooks)
  shellcheck --severity=style "${files[@]}"
}

workflows() { zizmor --offline .github/workflows; }

# CI passes the commit range to scan in QUALITY_SECRETS_RANGE. Locally, and when the range has
# no usable start (an all-zero SHA on a new branch's first push, or none on a manual run), the
# whole history is scanned.
security-secrets() {
  local range=${QUALITY_SECRETS_RANGE:-}
  if [ -n "$range" ] && [[ "$range" != 0000000000000000000000000000000000000000..* ]] &&
    [[ "$range" != ..* ]]; then
    betterleaks git --no-banner --redact --verbose --log-opts="$range" .
  else
    betterleaks git --no-banner --redact --verbose .
  fi
}

skills() { python3 scripts/check_skills.py; }

# Hidden Unicode (zero-width, bidi and tag characters) in anything a skill ships.
# APM blocks installs on critical findings, so a skill that fails here can't be installed.
unicode() {
  local file failed=0
  while IFS= read -r file; do
    if ! "$APM" audit --file "$file" >/dev/null 2>&1; then
      echo "Hidden Unicode found in $file:"
      "$APM" audit --file "$file"
      failed=1
    fi
  done < <(git ls-files skills)
  [ "$failed" -eq 0 ] && echo "No hidden Unicode in $(git ls-files skills | wc -l | tr -d ' ') skill files."
  return "$failed"
}

# Relative links and #section anchors in Markdown. External URLs are not fetched.
links() {
  local files=() file
  while IFS= read -r file; do files+=("$file"); done < <(git ls-files '*.md')
  lychee --offline --include-fragments --no-progress "${files[@]}"
}

missing=()
for tool in mypy ruff vulture shellcheck zizmor betterleaks lychee; do
  command -v "$tool" >/dev/null || missing+=("$tool")
done
[ -x "$APM" ] || missing+=(apm)
if [ ${#missing[@]} -gt 0 ]; then
  echo "Missing tools: ${missing[*]}. Run scripts/install-tools.sh first." >&2
  exit 2
fi

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
