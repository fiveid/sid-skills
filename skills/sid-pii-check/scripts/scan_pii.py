#!/usr/bin/env python3
"""
scan_pii.py — Scan code and git diffs for personal information, machine paths, and credentials.

Usage:
    python scan_pii.py [--staged] [--all] [--path PATH] [--names NAME [NAME ...]]

Options:
    --staged        Scan staged git files (default if in a git repo with staged changes)
    --all           Scan all tracked files in the git repository
    --path PATH     Scan a specific file or directory
    --names NAMES   Additional personal or client names to flag
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# Built-in detection patterns
PATTERNS = {
    "Absolute Paths": re.compile(r"(/Users/[a-zA-Z0-9_-]+(?:/|\\|\b)|/home/[a-zA-Z0-9_-]+(?:/|\\|\b)|[A-Za-z]:\\Users\\[a-zA-Z0-9_-]+)"),
    "Emails": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "Private IPs": re.compile(r"\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"),
    "Credentials / Secrets": re.compile(
        r"(ghp_[a-zA-Z0-9]{36,}|glpat-[a-zA-Z0-9_-]{20,}|sk-[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN (?:RSA|OPENSSH|DSA|EC|PGP) PRIVATE KEY|(?:bearer|api[_-]?key|secret|password)\s*[:=]\s*['\"][^'\"]{8,}['\"])",
        re.IGNORECASE,
    ),
}

# Domains commonly used as examples or standards that shouldn't trigger PII alarms
IGNORED_EMAIL_DOMAINS = {
    "example.com", "example.org", "example.net",
    "test.com", "localhost", "schema.org", "w3.org"
}

IGNORED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp",
    ".svg", ".woff", ".woff2", ".ttf", ".eot", ".pdf",
    ".lock", ".lockb"
}


def get_git_user_names() -> list[str]:
    """Retrieve git user name and author if available to check for accidental leaks."""
    names = []
    try:
        res = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True, check=False)
        if res.returncode == 0 and res.stdout.strip():
            name = res.stdout.strip()
            # Split full name into parts if > 2 chars to check individually
            names.append(name)
            for part in name.split():
                if len(part) > 2:
                    names.append(part)
    except Exception:
        pass
    return list(set(names))


def get_files_to_scan(args: argparse.Namespace) -> list[str]:
    """Determine the list of files to scan based on CLI arguments."""
    if args.path:
        target = Path(args.path)
        if target.is_file():
            return [str(target)]
        elif target.is_dir():
            return [
                str(p)
                for p in target.rglob("*")
                if p.is_file() and p.suffix.lower() not in IGNORED_EXTENSIONS and not any(part.startswith(".") for part in p.parts)
            ]
        return []

    if args.all:
        try:
            res = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True)
            files = [f for f in res.stdout.splitlines() if Path(f).suffix.lower() not in IGNORED_EXTENSIONS]
            if files:
                return files
        except Exception:
            pass

    # Check git status for staged, modified, or untracked files
    try:
        res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
        staged = []
        other = []
        for line in res.stdout.splitlines():
            if len(line) < 4:
                continue
            index_status = line[0]
            work_status = line[1]
            fname = line[3:].strip()
            path = Path(fname)
            candidates = [fname] if path.is_file() else [str(p) for p in path.rglob("*") if p.is_file()] if path.is_dir() else []
            for c in candidates:
                p = Path(c)
                if p.suffix.lower() in IGNORED_EXTENSIONS or any(part.startswith(".") for part in p.parts):
                    continue
                if index_status in ("M", "A", "R", "C"):
                    staged.append(c)
                else:
                    other.append(c)
        if staged:
            return staged
        if other and not args.staged:
            return other
    except Exception:
        pass

    return []


def scan_file(filepath: str, name_patterns: list[re.Pattern]) -> list[dict]:
    findings = []
    path = Path(filepath)
    if not path.is_file() or path.suffix.lower() in IGNORED_EXTENSIONS:
        return findings

    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return findings

    lines = content.splitlines()

    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped:
            continue

        # Check built-in patterns
        for cat, pattern in PATTERNS.items():
            for match in pattern.findall(line):
                # If tuple from group matching, grab non-empty
                val = match if isinstance(match, str) else [m for m in match if m][0]

                # Filter ignored email domains
                if cat == "Emails":
                    domain = val.split("@")[-1].lower()
                    if domain in IGNORED_EMAIL_DOMAINS:
                        continue

                findings.append({
                    "file": filepath,
                    "line": idx,
                    "category": cat,
                    "match": val,
                    "snippet": stripped[:120],
                })

        # Check custom names / git authors
        for n_pat in name_patterns:
            for match in n_pat.findall(line):
                findings.append({
                    "file": filepath,
                    "line": idx,
                    "category": "Personal / Configured Names",
                    "match": match,
                    "snippet": stripped[:120],
                })

    return findings


def main():
    parser = argparse.ArgumentParser(description="Scan code and git changes for PII, paths, and secrets.")
    parser.add_argument("--staged", action="store_true", help="Scan staged git files.")
    parser.add_argument("--all", action="store_true", help="Scan all tracked git files.")
    parser.add_argument("--path", type=str, help="Scan a specific file or directory.")
    parser.add_argument("--names", nargs="*", default=[], help="Specific names or identifiers to check.")

    args = parser.parse_args()

    # Compile names to check
    names_to_check = set(args.names)
    if not args.names:
        names_to_check.update(get_git_user_names())

    name_patterns = [
        re.compile(rf"\b{re.escape(name)}\b", re.IGNORECASE)
        for name in names_to_check
        if len(name) > 2
    ]

    files = get_files_to_scan(args)
    all_findings = []

    for f in files:
        file_findings = scan_file(f, name_patterns)
        all_findings.extend(file_findings)

    # Git committer info for review summary
    git_identity = {}
    try:
        user_name = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True, check=False).stdout.strip()
        user_email = subprocess.run(["git", "config", "user.email"], capture_output=True, text=True, check=False).stdout.strip()
        if user_name or user_email:
            git_identity = {"name": user_name, "email": user_email}
    except Exception:
        pass

    output = {
        "files_scanned": len(files),
        "total_findings": len(all_findings),
        "git_identity": git_identity,
        "findings": all_findings,
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
