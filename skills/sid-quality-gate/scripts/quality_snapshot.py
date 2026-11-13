#!/usr/bin/env python3
"""Measure and compare the configuration state of a quality gate.

Standard library only. Read-only except for `write`, which updates the
`measured` section of the record file and nothing else.

  quality_snapshot.py scan    [--root DIR] [--record FILE]   print measured state as JSON
  quality_snapshot.py compare --record FILE [--root DIR]     print a Markdown drift report
  quality_snapshot.py write   --record FILE [--root DIR]     store measured state in the record

The suppression scan is a heuristic. "Explained" means the marker is followed
by at least two plain words on the same line, or sits under a plain comment
line. Spot-check the locations before reporting them.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
import tomllib
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# (compiled pattern, pattern source, category, scope)
Marker = tuple[re.Pattern[str], str, str, str]

SCHEMA_VERSION = 1

DEFAULT_SCAN_EXCLUDE = [
    ".agents/**",
    ".claude/**",
    "**/node_modules/**",
    "vendor/**",
    "**/*.min.js",
]

DOC_SUFFIXES = {".md", ".mdx", ".rst", ".txt", ".adoc"}
# Tool configs mention marker names in comments and rule names; suppressions live in source.
CONFIG_SUFFIXES = {".toml", ".ini", ".cfg", ".json", ".jsonc", ".lock", ".neon"}
# A marker that starts with a letter must not be the tail of a longer name,
# such as the rule `unicorn/no-abusive-eslint-disable`.
NAME_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-/.")
MAX_FILE_BYTES = 1_000_000

# (pattern, category, scope). Order matters: longer, more specific markers come
# first, and a span already matched on a line is not matched again.
MARKERS: list[tuple[str, str, str]] = [
    # Types
    (r"@ts-nocheck", "types", "file"),
    (r"@ts-ignore", "types", "line"),
    (r"@ts-expect-error", "types", "line"),
    (r"#\s*mypy:\s*ignore-errors", "types", "file"),
    (r"type:\s*ignore", "types", "line"),
    (r"pyright:\s*ignore", "types", "line"),
    (r"@phpstan-ignore(?:-next-line|-line)?", "types", "line"),
    (r"@psalm-suppress", "types", "line"),
    (r"#\s*typed:\s*(?:false|ignore)", "types", "file"),
    # Lint (reclassified as complexity when the rule named is a complexity rule)
    (r"eslint-disable-next-line", "lint", "line"),
    (r"eslint-disable-line", "lint", "line"),
    (r"eslint-disable(?![-\w])", "lint", "block"),
    (r"oxlint-disable-next-line", "lint", "line"),
    (r"oxlint-disable-line", "lint", "line"),
    (r"oxlint-disable(?![-\w])", "lint", "block"),
    (r"biome-ignore-all", "lint", "file"),
    (r"biome-ignore-start", "lint", "block"),
    (r"biome-ignore(?![-\w])", "lint", "line"),
    (r"deno-lint-ignore-file", "lint", "file"),
    (r"deno-lint-ignore(?![-\w])", "lint", "line"),
    (r"#\s*(?:ruff|flake8):\s*noqa", "lint", "file"),
    (r"#\s*ruff:\s*file-ignore\[", "lint", "file"),
    (r"#\s*ruff:\s*disable\[", "lint", "block"),
    (r"#\s*ruff:\s*ignore\[", "lint", "line"),
    (r"\bnoqa\b", "lint", "line"),
    (r"pylint:\s*disable", "lint", "line"),
    (r"//\s*nolint\b", "lint", "line"),
    (r"#!\[(?:allow|expect)\(", "lint", "file"),
    (r"#\[(?:allow|expect)\(", "lint", "line"),
    (r"rubocop:disable", "lint", "line"),
    (r"standard:disable", "lint", "line"),
    (r"phpcs:(?:ignore|disable)", "lint", "line"),
    (r"@phpcsSuppress", "lint", "line"),
    (r"@SuppressWarnings", "lint", "line"),
    (r"@Suppress\(", "lint", "line"),
    (r"\[SuppressMessage", "lint", "line"),
    (r"#pragma\s+warning\s+disable", "lint", "block"),
    (r"\bNOSONAR\b", "lint", "line"),
    (r"noinspection\s", "lint", "line"),
    (r"#lizard\s+forgives", "complexity", "line"),
    # Coverage
    (r"istanbul\s+ignore", "coverage", "line"),
    (r"\bc8\s+ignore", "coverage", "line"),
    (r"\bv8\s+ignore", "coverage", "line"),
    (r"pragma:\s*no\s*cover", "coverage", "line"),
    (r"@codeCoverageIgnore", "coverage", "line"),
    (r"LCOV_EXCL", "coverage", "line"),
    (r"#\[coverage\(off\)\]", "coverage", "line"),
    (r":nocov:", "coverage", "block"),
    # Duplication
    (r"jscpd:ignore-start", "duplication", "block"),
    (r"CPD-OFF", "duplication", "block"),
    # Security
    (r"\bnosemgrep\b", "security", "line"),
    (r"\bnosec\b", "security", "line"),
    (r"gitleaks:allow", "security", "line"),
    (r"pragma:\s*allowlist\s+secret", "security", "line"),
    (r"trufflehog:ignore", "security", "line"),
    (r"checkov:skip", "security", "line"),
    (r"trivy:ignore", "security", "line"),
    # Formatting
    (r"prettier-ignore", "formatting", "line"),
    (r"dprint-ignore", "formatting", "line"),
    (r"fmt:\s*(?:off|skip)", "formatting", "block"),
    (r"rustfmt::skip", "formatting", "line"),
    (r"@formatter:off", "formatting", "block"),
    (r"clang-format\s+off", "formatting", "block"),
]
COMPILED: list[Marker] = [(re.compile(p), p, cat, scope) for p, cat, scope in MARKERS]


def compile_markers(extra: list[dict[str, Any]]) -> list[Marker]:
    """Project markers from the record's `extra_markers`, ahead of the built-in list."""
    compiled: list[Marker] = []
    for entry in extra:
        pattern = entry.get("pattern", "")
        try:
            regex = re.compile(pattern)
        except re.error as err:
            sys.exit(f"Invalid extra_markers pattern {pattern!r}: {err}")
        compiled.append((regex, pattern, entry.get("category", "lint"), entry.get("scope", "line")))
    return compiled + COMPILED


COMPLEXITY_RULES = re.compile(
    r"complexity|cognitive|max-depth|max-lines|max-params|max-statements|"
    r"max-nested|\bC901\b|PLR09\d\d|PLR1702|gocyclo|gocognit|funlen|nestif|"
    r"cyclop|too_many_(?:lines|arguments)|excessive",
    re.IGNORECASE,
)

DIRECTIVE_WORDS = {
    "next",
    "line",
    "file",
    "start",
    "end",
    "stop",
    "all",
    "if",
    "else",
    "format",
    "lint",
    "off",
    "on",
    "ignore",
    "disable",
    "enable",
    "error",
    "errors",
    "warning",
    "warnings",
    "rule",
    "rules",
}
PLAIN_WORD = re.compile(r"[A-Za-z]+(?:'[a-z]+)?")
COMMENT_LINE = re.compile(r"^\s*(?://|#|/\*|\*|--|;|<!--)")

# Files that hold accepted violations or ignore lists. Growth here loosens the gate.
BASELINE_FILES: dict[str, str] = {
    "eslint-suppressions.json": "eslint",
    "phpstan-baseline.neon": "phpstan",
    "phpstan-baseline.php": "phpstan",
    "psalm-baseline.xml": "psalm",
    ".basedpyright/baseline.json": "basedpyright",
    ".jscpd-baseline.json": "jscpd",
    "jscpd-baseline.json": "jscpd",
    "complexipy-snapshot.json": "complexipy",
    ".betterer.results": "lines",
    "detekt-baseline.xml": "xml-id",
    "lint-baseline.xml": "xml-issue",
    ".secrets.baseline": "detect-secrets",
    ".gitleaksignore": "lines",
    ".trivyignore": "lines",
    ".semgrepignore": "lines",
    ".jscpdignore": "lines",
    ".prettierignore": "lines",
    ".eslintignore": "lines",
    ".snyk": "lines",
    "osv-scanner.toml": "osv",
    ".osv-scanner.toml": "osv",
    "audit-ci.json": "lines",
    "audit-ci.jsonc": "lines",
    "vulture_whitelist.py": "lines",
}

CI_FILE_GLOBS = [
    ".github/workflows/*.yml",
    ".github/workflows/*.yaml",
    ".gitlab-ci.yml",
    "bitbucket-pipelines.yml",
    ".circleci/config.yml",
    "azure-pipelines.yml",
    "Jenkinsfile",
]

CI_FLAGS: list[tuple[str, str]] = [
    (r"continue-on-error:\s*(?:true|\$\{\{)", "continue-on-error"),
    (r"allow_failure:\s*true", "allow_failure"),
    (r"\|\|\s*(?:true|:|exit 0)\b", "|| true"),
    (r"\|\|\s*echo\b", "|| echo"),
    (r"\bset \+e\b", "set +e"),
    (r"^\s*if:\s*(?:false|\$\{\{\s*false\s*\}\})", "if: false"),
    (r"^\s*if:\s", "conditional step or job"),
    (r"^\s*paths(?:-ignore)?:", "path filter"),
    (r"^\s*branches(?:-ignore)?:", "branch filter"),
    (r"--exit-zero\b", "--exit-zero"),
    (r"--no-fail\b|--soft-fail\b|--exit-code[= ]0\b", "non-failing flag"),
    (r"--max-warnings[= ]?(?:-\d|[1-9])", "--max-warnings above 0"),
    (r"--passWithNoTests\b|--pass-with-no-tests\b", "pass with no tests"),
    (r"skip-?ci|\[skip", "skip marker"),
]
CI_COMPILED = [(re.compile(p), label) for p, label in CI_FLAGS]


TEXT_LIMIT = 200
BINARY_SNIFF_BYTES = 8192
# A marker is explained by this many plain words after it, or a comment line above it with
# at least COMMENT_EXPLAINS_WORDS plain words.
EXPLAINS_WORDS = 2
COMMENT_EXPLAINS_WORDS = 3


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def list_files(root: Path, exclude: list[str]) -> list[str]:
    out = git(root, "ls-files", "--cached", "--others", "--exclude-standard")
    if out:
        files = out.splitlines()
    else:
        files = [str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()]
    return sorted(f for f in files if not any(fnmatch.fnmatch(f, g) for g in exclude))


def read_text(path: Path) -> str | None:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return None
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data[:BINARY_SNIFF_BYTES]:
        return None
    return data.decode("utf-8", errors="replace")


def is_explained(
    after: str, previous_line: str, whole_line_comment: bool, markers: list[Marker]
) -> bool:
    text = re.sub(r"(\*/|-->)\s*$", "", after)
    if re.search(r"(?:^|\s)--\s+\w", text):
        return True
    words = [t.strip("\"'(),;*/#[]{}") for t in text.split()]
    plain = [w for w in words if PLAIN_WORD.fullmatch(w) and w.lower() not in DIRECTIVE_WORDS]
    if len(plain) >= EXPLAINS_WORDS:
        return True
    # A comment above only explains a marker that sits on its own line.
    if (
        whole_line_comment
        and COMMENT_LINE.match(previous_line)
        and not any(c.search(previous_line) for c, *_ in markers)
    ):
        prev_words = [w for w in re.split(r"\W+", previous_line) if PLAIN_WORD.fullmatch(w)]
        return len(prev_words) >= COMMENT_EXPLAINS_WORDS
    return False


def is_name_tail(pattern: str, line: str, start: int) -> bool:
    """A letter-led marker preceded by a name character is part of a longer name."""
    return pattern[0].isalpha() and start > 0 and line[start - 1] in NAME_CHARS


def line_suppressions(line: str, previous: str, markers: list[Marker]) -> list[dict[str, Any]]:
    """Suppression markers on one line. A span already matched is not matched again."""
    found: list[dict[str, Any]] = []
    taken: list[tuple[int, int]] = []
    for regex, pattern, category, scope in markers:
        for match in regex.finditer(line):
            overlaps = any(match.start() < e and match.end() > s for s, e in taken)
            if overlaps or is_name_tail(pattern, line, match.start()):
                continue
            taken.append((match.start(), match.end()))
            after = line[match.end() :]
            is_complexity = category == "lint" and COMPLEXITY_RULES.search(after)
            found.append(
                {
                    "marker": pattern,
                    "category": "complexity" if is_complexity else category,
                    "scope": scope,
                    "explained": is_explained(
                        after, previous, bool(COMMENT_LINE.match(line)), markers
                    ),
                    "text": line.strip()[:TEXT_LIMIT],
                }
            )
    return found


def scan_suppressions(
    root: Path, files: list[str], baseline_names: set[str], markers: list[Marker]
) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for rel in files:
        suffix = Path(rel).suffix.lower()
        if suffix in DOC_SUFFIXES or suffix in CONFIG_SUFFIXES or rel in baseline_names:
            continue
        text = read_text(root / rel)
        if text is None:
            continue
        previous = ""
        for number, line in enumerate(text.splitlines(), start=1):
            found.extend(
                {"file": rel, "line": number, **loc}
                for loc in line_suppressions(line, previous, markers)
            )
            previous = line
    return found


def count_eslint(data: Any) -> int:
    total: int = sum(
        rule.get("count", 1) if isinstance(rule, dict) else 1
        for rules in data.values()
        if isinstance(rules, dict)
        for rule in rules.values()
    )
    return total


def count_complexipy(data: Any) -> int:
    return sum(len(entry.get("functions", [])) for entry in data if isinstance(entry, dict))


def count_jscpd(data: Any) -> int:
    total: int = sum(data.get("fingerprints", {}).values())
    return total


def count_phpstan(text: str) -> int:
    counts = re.findall(r"count:\s*(\d+)|'count'\s*=>\s*(\d+)", text)
    return sum(int(a or b) for a, b in counts) or len(re.findall(r"message:", text))


def count_lines(text: str) -> int:
    return sum(
        1 for raw in text.splitlines() if raw.strip() and not raw.strip().startswith(("#", "//"))
    )


# Baseline files stored as JSON, counted from the parsed data
JSON_COUNTERS: dict[str, Callable[[Any], int]] = {
    "eslint": count_eslint,
    "basedpyright": lambda data: sum(len(v) for v in data.get("files", {}).values()),
    "detect-secrets": lambda data: sum(len(v) for v in data.get("results", {}).values()),
    "jscpd": count_jscpd,
    "complexipy": count_complexipy,
}

# Baseline files counted from their text
TEXT_COUNTERS: dict[str, Callable[[str], int]] = {
    "phpstan": count_phpstan,
    "psalm": lambda text: len(re.findall(r"<code>", text)),
    "xml-id": lambda text: len(re.findall(r"<ID>", text)),
    "xml-issue": lambda text: len(re.findall(r"<issue\b", text)),
    "osv": lambda text: len(re.findall(r"^\s*\[\[IgnoredVulns\]\]", text, re.MULTILINE)),
}


def count_baseline_entries(path: Path, kind: str) -> int | None:
    text = read_text(path)
    if text is None:
        return None
    if kind in JSON_COUNTERS:
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return None
        return JSON_COUNTERS[kind](data)
    return TEXT_COUNTERS.get(kind, count_lines)(text)


def strip_json_comments(text: str) -> str:
    """Drop // and /* */ comments and trailing commas (JSONC), leaving strings alone."""
    out, i, n = [], 0, len(text)
    while i < n:
        if text[i] == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            out.append(text[i : j + 1])
            i = j + 1
        elif text.startswith("//", i):
            end = text.find("\n", i)
            i = n if end == -1 else end
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = n if end == -1 else end + 2
        else:
            out.append(text[i])
            i += 1
    return re.sub(r",(\s*[}\]])", r"\1", "".join(out))


def load_structured(path: Path, text: str) -> Any:
    """Parse a JSON, JSONC or TOML config file, or return None."""
    try:
        if path.suffix == ".toml":
            return tomllib.loads(text)
        return json.loads(strip_json_comments(text))
    except ValueError:
        return None


def count_at_path(data: Any, keys: list[str]) -> int:
    """Count entries at a dotted path. `*` steps into every item of a list or object."""
    if not keys:
        if isinstance(data, (list, dict)):
            return len(data)
        return 0 if data is None else 1
    key, rest = keys[0], keys[1:]
    if key == "*":
        items = data.values() if isinstance(data, dict) else data if isinstance(data, list) else []
        return sum(count_at_path(item, rest) for item in items)
    if isinstance(data, dict):
        return count_at_path(data[key], rest) if key in data else 0
    if isinstance(data, list) and key.isdigit() and int(key) < len(data):
        return count_at_path(data[int(key)], rest)
    return 0


def count_with_counter(path: Path, counter: dict[str, Any]) -> int | None:
    """Count a list held inside a config file, for tools with no baseline file of their own."""
    text = read_text(path)
    if text is None:
        return None
    if counter["method"] == "json-path":
        data = load_structured(path, text)
        return None if data is None else count_at_path(data, counter["path"].split("."))
    return len(re.findall(counter["pattern"], text, re.MULTILINE))


def counter_label(rel: str, counter: dict[str, Any]) -> str:
    """The label for one counter spec, exiting with a message if the spec is invalid."""
    method = counter.get("method")
    if method == "json-path" and counter.get("path"):
        return str(counter.get("label") or counter["path"])
    if method == "regex" and counter.get("pattern"):
        try:
            re.compile(counter["pattern"], re.MULTILINE)
        except re.error as err:
            sys.exit(f"Invalid extra_baseline_files pattern for {rel}: {err}")
        return str(counter.get("label") or counter["pattern"])
    sys.exit(
        f"extra_baseline_files[{rel!r}] needs method json-path with a path, or regex with a pattern"
    )


def config_counters(rel: str, spec: Any) -> list[tuple[str, dict[str, Any]]]:
    """Expand an `extra_baseline_files` value into (result key, counter) pairs."""
    specs = spec if isinstance(spec, list) else [spec]
    pairs = []
    for counter in specs:
        label = counter_label(rel, counter)
        key = rel if len(specs) == 1 and not counter.get("label") else f"{rel} [{label}]"
        pairs.append((key, counter))
    return pairs


def counter_results(root: Path, rel: str, spec: Any) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for key, counter in config_counters(rel, spec):
        entries = count_with_counter(root / rel, counter)
        result[key] = {"kind": counter["method"], "entries": entries}
        if entries is None:
            result[key]["unreadable"] = True
    return result


def scan_baseline_files(
    root: Path, files: list[str], extra: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    known = {**BASELINE_FILES, **{k: v for k, v in extra.items() if isinstance(v, str)}}
    result: dict[str, dict[str, Any]] = {}
    for rel in files:
        spec = extra.get(rel)
        if spec is not None and not isinstance(spec, str):
            result.update(counter_results(root, rel, spec))
            continue
        kind = known.get(rel) or known.get(Path(rel).name)
        if kind is None:
            continue
        result[rel] = {"kind": kind, "entries": count_baseline_entries(root / rel, kind)}
    return result


def ci_flag(line: str) -> str | None:
    """The first CI flag a line matches, if any."""
    return next((label for regex, label in CI_COMPILED if regex.search(line)), None)


def scan_ci(root: Path, files: list[str], extra_files: list[str]) -> list[dict[str, Any]]:
    targets = sorted(
        {f for f in files if any(fnmatch.fnmatch(f, g) for g in CI_FILE_GLOBS) or f in extra_files}
    )
    flags = []
    for rel in targets:
        text = read_text(root / rel) or ""
        for number, line in enumerate(text.splitlines(), start=1):
            label = ci_flag(line)
            if label:
                flags.append(
                    {"file": rel, "line": number, "flag": label, "text": line.strip()[:TEXT_LIMIT]}
                )
    return flags


def summarise(locations: list[dict[str, Any]]) -> dict[str, Any]:
    by_category: dict[str, dict[str, int]] = {}
    by_file: dict[str, dict[str, dict[str, int]]] = {}
    for loc in locations:
        cat = by_category.setdefault(
            loc["category"], {"total": 0, "explained": 0, "unexplained": 0}
        )
        cat["total"] += 1
        cat["explained" if loc["explained"] else "unexplained"] += 1
        key = f"{loc['category']}:{loc['marker']}"
        entry = by_file.setdefault(loc["file"], {}).setdefault(key, {"total": 0, "explained": 0})
        entry["total"] += 1
        entry["explained"] += int(loc["explained"])
    explained = sum(1 for loc in locations if loc["explained"])
    return {
        "total": len(locations),
        "explained": explained,
        "unexplained": len(locations) - explained,
        "file_or_block_scope": sum(1 for loc in locations if loc["scope"] != "line"),
        "by_category": dict(sorted(by_category.items())),
        "by_file": dict(sorted(by_file.items())),
    }


def load_record(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    record: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return record


def measure(root: Path, record: dict[str, Any], record_path: Path | None) -> dict[str, Any]:
    exclude = record.get("scan_exclude", DEFAULT_SCAN_EXCLUDE)
    files = list_files(root, exclude)
    if record_path is not None:
        files = [f for f in files if (root / f).resolve() != record_path]
    extra_baselines = record.get("extra_baseline_files", {})
    baseline_names = set(BASELINE_FILES) | set(extra_baselines)
    markers = compile_markers(record.get("extra_markers", []))
    locations = scan_suppressions(root, files, baseline_names, markers)
    gate_files = record.get("gate", {}).get("files", [])
    return {
        # Today in the local timezone, as `date.today()` would give
        "date": datetime.now(UTC).astimezone().date().isoformat(),
        "commit": git(root, "rev-parse", "HEAD"),
        "scan_exclude": exclude,
        "suppressions": summarise(locations),
        "baseline_files": scan_baseline_files(root, files, extra_baselines),
        "ci_flags": scan_ci(root, files, gate_files),
        "_locations": locations,
    }


def delta(old: int | None, new: int | None) -> str:
    if old is None and new is not None:
        return "new"
    if new is None and old is not None:
        return "removed"
    if old is None or new is None:
        return "n/a"
    diff = new - old
    return f"{diff:+d}" if diff else "0"


def fenced(title: str, body: str) -> str:
    return f"{title}\n```\n{body}\n```"


def anchor_line(root: Path, anchor: str) -> str:
    if not anchor:
        return (
            "- The record has not been committed (or this is not a git checkout, or the clone is "
            "shallow). Git-based checks below are skipped."
        )
    commits_since = git(root, "rev-list", "--count", f"{anchor}..HEAD")
    return (
        f"- Anchor (last commit touching the record): `{anchor[:12]}`, "
        f"{commits_since} commit(s) ago"
    )


def watched_section(root: Path, record: dict[str, Any], anchor: str) -> list[str]:
    watched = sorted(
        set(record.get("watched_files", [])) | set(record.get("gate", {}).get("files", []))
    )
    out = ["\n## Watched config files"]
    missing = [f for f in watched if not (root / f).exists()]
    if missing:
        out.append("Missing now: " + ", ".join(f"`{f}`" for f in missing))
    if not watched:
        out.append("The record lists no watched files.")
    elif anchor:
        stat = git(root, "diff", "--stat", anchor, "--", *watched)
        out.append(
            fenced("Changed since the anchor (including uncommitted):", stat)
            if stat
            else "No changes since the anchor."
        )
        out.append(f"Inspect with: `git diff {anchor[:12]} -- <file>`")
    untracked = git(root, "ls-files", "--others", "--exclude-standard", "--", *watched)
    if untracked:
        out.append("Untracked: " + ", ".join(f"`{f}`" for f in untracked.splitlines()))
    return out


def history_section(root: Path, record_files: list[str]) -> list[str]:
    log = git(root, "log", "-20", "--format=%h %ad %an: %s", "--date=short", "--", *record_files)
    dirty = git(root, "status", "--porcelain", "--", *record_files)
    out = [
        "\n## History of the record",
        fenced("Last 20 commits touching the record:", log)
        if log
        else "No commits touch the record.",
    ]
    if dirty:
        out.append(fenced("Uncommitted changes to the record:", dirty))
    out.append("Match each change to a dated entry in the decisions log.")
    return out


def suppression_totals(old_s: dict[str, Any], new_s: dict[str, Any]) -> list[str]:
    out = [
        "\n## Inline suppressions",
        "| | Recorded | Now | Change |\n| :--- | ---: | ---: | ---: |",
    ]
    for key in ("total", "explained", "unexplained", "file_or_block_scope"):
        change = delta(old_s.get(key), new_s[key])
        out.append(
            f"| {key.replace('_', ' ')} | {old_s.get(key, 'n/a')} | {new_s[key]} | {change} |"
        )
    out.append(
        "\n| Category | Recorded (unexplained) | Now (unexplained) |\n| :--- | ---: | ---: |"
    )
    empty = {"total": 0, "unexplained": 0}
    old_cats, new_cats = old_s.get("by_category", {}), new_s["by_category"]
    for cat in sorted(set(old_cats) | set(new_cats)):
        o, n = old_cats.get(cat, empty), new_cats.get(cat, empty)
        out.append(
            f"| {cat} | {o['total']} ({o['unexplained']}) | {n['total']} ({n['unexplained']}) |"
        )
    return out


def suppression_changes(
    old_files: dict[str, Any], new_files: dict[str, Any]
) -> tuple[list[tuple[str, str]], list[str]]:
    """(file, category:marker) pairs whose count grew, and descriptions of those that shrank."""
    grown, shrunk = [], []
    for rel in sorted(set(old_files) | set(new_files)):
        old_rel, new_rel = old_files.get(rel, {}), new_files.get(rel, {})
        for key in sorted(set(old_rel) | set(new_rel)):
            o = old_rel.get(key, {"total": 0})["total"]
            n = new_rel.get(key, {"total": 0})["total"]
            if n > o:
                grown.append((rel, key))
            elif n < o:
                shrunk.append(f"`{rel}` {key}: {o} → {n}")
    return grown, shrunk


def suppression_section(
    old_s: dict[str, Any], new_s: dict[str, Any], locations: list[dict[str, Any]]
) -> list[str]:
    out = suppression_totals(old_s, new_s)
    grown, shrunk = suppression_changes(old_s.get("by_file", {}), new_s["by_file"])
    if grown:
        out.append("\nNew suppressions (current locations in files where the count grew):")
        out.append("| Location | Category | Explained | Text |\n| :--- | :--- | :--- | :--- |")
        for loc in locations:
            if (loc["file"], f"{loc['category']}:{loc['marker']}") in grown:
                text = loc["text"].replace("|", "\\|")
                explained = "yes" if loc["explained"] else "no"
                out.append(
                    f"| `{loc['file']}:{loc['line']}` | {loc['category']} | {explained} "
                    f"| `{text}` |"
                )
    if shrunk:
        out.append("\nRemoved: " + "; ".join(shrunk))
    return out


def baseline_section(old_b: dict[str, Any], now_b: dict[str, Any]) -> list[str]:
    out = ["\n## Baseline and ignore files"]
    rows = sorted(set(old_b) | set(now_b))
    if not rows:
        out.append("None found.")
        return out
    out.append("| File | Recorded entries | Now | Change |\n| :--- | ---: | ---: | ---: |")
    for rel in rows:
        o = old_b.get(rel, {}).get("entries")
        n_entry = now_b.get(rel, {})
        n = n_entry.get("entries")
        unreadable = n_entry.get("unreadable")
        shown = n if n is not None else "unreadable" if unreadable else "absent"
        recorded = o if o is not None else "absent"
        change = "n/a" if unreadable else delta(o, n)
        out.append(f"| `{rel}` | {recorded} | {shown} | {change} |")
    return out


def ci_section(old_flags: list[dict[str, Any]], now_flags: list[dict[str, Any]]) -> list[str]:
    out = ["\n## CI lines worth checking"]
    old_keys = {(f["file"], f["text"]) for f in old_flags}
    if now_flags:
        out.append("| Location | Flag | New since record | Text |\n| :--- | :--- | :--- | :--- |")
        for flag in now_flags:
            new = "yes" if (flag["file"], flag["text"]) not in old_keys else "no"
            text = flag["text"].replace("|", "\\|")
            out.append(f"| `{flag['file']}:{flag['line']}` | {flag['flag']} | {new} | `{text}` |")
    else:
        out.append("None found.")
    gone = old_keys - {(f["file"], f["text"]) for f in now_flags}
    if gone:
        out.append(f"\n{len(gone)} recorded CI line(s) no longer present.")
    return out


def compare(root: Path, record_path: Path, record: dict[str, Any]) -> str:
    if not record:
        return f"No record found at {record_path}. There is no baseline to audit against."
    old = record.get("measured", {})
    now = measure(root, record, record_path)
    shown = (
        str(record_path.relative_to(root)) if record_path.is_relative_to(root) else str(record_path)
    )
    record_files = [shown] + ([record["record_doc"]] if record.get("record_doc") else [])
    # The anchor is the last commit that touched the record: config changes after
    # it were made without the record being updated.
    anchor = git(root, "log", "-1", "--format=%H", "--", shown)
    out = [
        "## Record",
        f"- Record: `{shown}` (schema {record.get('schema_version', '?')})",
        f"- Last measured: {old.get('date', '?')}",
        f"- Now: {now['date']} at `{now['commit'][:12]}`",
        anchor_line(root, anchor),
        *watched_section(root, record, anchor),
        *history_section(root, record_files),
        *suppression_section(old.get("suppressions", {}), now["suppressions"], now["_locations"]),
        *baseline_section(old.get("baseline_files", {}), now["baseline_files"]),
        *ci_section(old.get("ci_flags", []), now["ci_flags"]),
    ]
    if old.get("scan_exclude") and old["scan_exclude"] != now["scan_exclude"]:
        out.append(f"\nScan exclusions changed: {old['scan_exclude']} → {now['scan_exclude']}")
    return "\n".join(out)


def require_record(parser: argparse.ArgumentParser, command: str, path: Path | None) -> Path:
    if path is None:
        parser.error(f"{command} needs --record")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("command", choices=["scan", "compare", "write"])
    parser.add_argument("--root", default=".", help="repository root (default: current directory)")
    parser.add_argument("--record", help="path to quality-baseline.json")
    parser.add_argument(
        "--locations", action="store_true", help="scan: include every suppression location"
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    record_path = Path(args.record).resolve() if args.record else None

    if args.command == "scan":
        measured = measure(root, load_record(record_path), record_path)
        locations = measured.pop("_locations")
        if args.locations:
            measured["locations"] = locations
        print(json.dumps(measured, indent=2))
        return 0

    target = require_record(parser, args.command, record_path)
    record = load_record(target)
    if args.command == "compare":
        print(compare(root, target, record))
        return 0

    measured = measure(root, record, target)
    measured.pop("_locations")
    record.setdefault("schema_version", SCHEMA_VERSION)
    record["measured"] = measured
    target.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(
        f"Updated measured state in {target}: {measured['suppressions']['total']} suppressions, "
        f"{len(measured['baseline_files'])} baseline files, "
        f"{len(measured['ci_flags'])} CI lines flagged."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
