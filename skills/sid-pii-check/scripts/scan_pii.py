#!/usr/bin/env python3
"""
scan_pii.py - Scan code and git diffs for personal information, machine paths, and credentials.

Usage:
    python scan_pii.py [--staged] [--all] [--path PATH] [--names NAME [NAME ...]]

Options:
    --staged        Scan staged git files (default if in a git repo with staged changes)
    --all           Scan all tracked files in the git repository
    --path PATH     Scan a specific file or directory
    --names NAMES   Additional personal or client names to flag
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

# Built-in detection patterns
PATTERNS = {
    "Absolute Paths": re.compile(
        r"(/Users/[a-zA-Z0-9_-]+(?:/|\\|\b)|/home/[a-zA-Z0-9_-]+(?:/|\\|\b)"
        r"|[A-Za-z]:\\Users\\[a-zA-Z0-9_-]+)"
    ),
    "Emails": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "Private IPs": re.compile(
        r"\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}"
        r"|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"
    ),
    "Credentials / Secrets": re.compile(
        r"(ghp_[a-zA-Z0-9]{36,}|glpat-[a-zA-Z0-9_-]{20,}|sk-[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16}"
        r"|BEGIN (?:RSA|OPENSSH|DSA|EC|PGP) PRIVATE KEY"
        r"|(?:bearer|api[_-]?key|secret|password)\s*[:=]\s*['\"][^'\"]{8,}['\"])",
        re.IGNORECASE,
    ),
}

# Domains commonly used as examples or standards that shouldn't trigger PII alarms
IGNORED_EMAIL_DOMAINS = {
    "example.com",
    "example.org",
    "example.net",
    "test.com",
    "localhost",
    "schema.org",
    "w3.org",
}

IGNORED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".webp",
    ".svg",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".pdf",
    ".lock",
    ".lockb",
}

# Names this short match too much ordinary text to be useful
MIN_NAME_LENGTH = 3

# `git status --porcelain` lines are "XY path": anything shorter has no path
MIN_STATUS_LINE_LENGTH = 4
STAGED_STATUSES = ("M", "A", "R", "C")

SNIPPET_LENGTH = 120


def git_output(*args: str) -> str | None:
    """Run a git command and return its stdout, or None if git fails or isn't available."""
    try:
        res = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    except OSError:
        return None
    return res.stdout if res.returncode == 0 else None


def get_git_user_names() -> list[str]:
    """Retrieve git user name and author if available to check for accidental leaks."""
    name = (git_output("config", "user.name") or "").strip()
    if not name:
        return []
    # Check the full name, and each part long enough to be meaningful on its own
    names = [name, *(part for part in name.split() if len(part) >= MIN_NAME_LENGTH)]
    return list(set(names))


def is_skipped(path: Path) -> bool:
    """Binary-ish extensions and anything under a hidden directory are skipped."""
    return path.suffix.lower() in IGNORED_EXTENSIONS or any(
        part.startswith(".") for part in path.parts
    )


def files_under_path(target: Path) -> list[str]:
    if target.is_file():
        return [str(target)]
    if target.is_dir():
        return [str(p) for p in target.rglob("*") if p.is_file() and not is_skipped(p)]
    return []


def tracked_files() -> list[str]:
    """All tracked files, or an empty list if git fails or isn't available."""
    out = git_output("ls-files")
    if out is None:
        return []
    return [f for f in out.splitlines() if Path(f).suffix.lower() not in IGNORED_EXTENSIONS]


def status_candidates(fname: str) -> list[str]:
    """Files behind one `git status` entry: the file itself, or every file in a new directory."""
    path = Path(fname)
    if path.is_file():
        return [fname]
    if path.is_dir():
        return [str(p) for p in path.rglob("*") if p.is_file()]
    return []


def changed_files(staged_only: bool) -> list[str]:
    """Staged files if there are any, otherwise modified or untracked files (unless staged_only)."""
    out = git_output("status", "--porcelain")
    if out is None:
        return []
    staged: list[str] = []
    other: list[str] = []
    for line in out.splitlines():
        if len(line) < MIN_STATUS_LINE_LENGTH:
            continue
        bucket = staged if line[0] in STAGED_STATUSES else other
        bucket.extend(c for c in status_candidates(line[3:].strip()) if not is_skipped(Path(c)))
    if staged:
        return staged
    if other and not staged_only:
        return other
    return []


def get_files_to_scan(args: argparse.Namespace) -> list[str]:
    """Determine the list of files to scan based on CLI arguments."""
    if args.path:
        return files_under_path(Path(args.path))
    if args.all:
        files = tracked_files()
        if files:
            return files
    return changed_files(args.staged)


def line_findings(
    filepath: str, idx: int, line: str, name_patterns: list[re.Pattern[str]]
) -> list[dict[str, Any]]:
    snippet = line.strip()[:SNIPPET_LENGTH]

    def finding(category: str, match: str) -> dict[str, Any]:
        return {
            "file": filepath,
            "line": idx,
            "category": category,
            "match": match,
            "snippet": snippet,
        }

    findings = []
    for cat, pattern in PATTERNS.items():
        for match in pattern.findall(line):
            # A tuple comes from group matching: take the first non-empty group
            val = match if isinstance(match, str) else next(m for m in match if m)
            if cat == "Emails" and val.split("@")[-1].lower() in IGNORED_EMAIL_DOMAINS:
                continue
            findings.append(finding(cat, val))

    # Custom names / git authors
    findings.extend(
        finding("Personal / Configured Names", match)
        for n_pat in name_patterns
        for match in n_pat.findall(line)
    )
    return findings


def scan_file(filepath: str, name_patterns: list[re.Pattern[str]]) -> list[dict[str, Any]]:
    path = Path(filepath)
    if not path.is_file() or path.suffix.lower() in IGNORED_EXTENSIONS:
        return []

    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    findings = []
    for idx, line in enumerate(content.splitlines(), 1):
        if line.strip():
            findings.extend(line_findings(filepath, idx, line, name_patterns))
    return findings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scan code and git changes for PII, paths, and secrets."
    )
    parser.add_argument("--staged", action="store_true", help="Scan staged git files.")
    parser.add_argument("--all", action="store_true", help="Scan all tracked git files.")
    parser.add_argument("--path", type=str, help="Scan a specific file or directory.")
    parser.add_argument(
        "--names", nargs="*", default=[], help="Specific names or identifiers to check."
    )

    args = parser.parse_args()

    # Compile names to check
    names_to_check = set(args.names)
    if not args.names:
        names_to_check.update(get_git_user_names())

    name_patterns = [
        re.compile(rf"\b{re.escape(name)}\b", re.IGNORECASE)
        for name in names_to_check
        if len(name) >= MIN_NAME_LENGTH
    ]

    files = get_files_to_scan(args)
    all_findings = []
    for f in files:
        all_findings.extend(scan_file(f, name_patterns))

    # Git committer info for review summary
    git_identity = {}
    user_name = (git_output("config", "user.name") or "").strip()
    user_email = (git_output("config", "user.email") or "").strip()
    if user_name or user_email:
        git_identity = {"name": user_name, "email": user_email}

    output = {
        "files_scanned": len(files),
        "total_findings": len(all_findings),
        "git_identity": git_identity,
        "findings": all_findings,
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
