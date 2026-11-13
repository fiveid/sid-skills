#!/usr/bin/env python3
"""
audit_deps.py - Audit proposed or new dependencies for age-gating, slopsquatting, and trivial
utilities.

Usage:
    python audit_deps.py [package-names ...]
    python audit_deps.py --file package.json
    python audit_deps.py --diff [package.json]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Packages less than this many days old trigger an age warning
AGE_THRESHOLD_DAYS = 30

# A latest release younger than this many days suggests pinning the previous version
RECENT_RELEASE_DAYS = 7

DEPENDENCY_SECTIONS = ("dependencies", "devDependencies", "peerDependencies")

# Matches added dependency lines in a diff: + "package-name": "version"
ADDED_DEP_RE = re.compile(
    r'^\+\s*"([@a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+|[a-zA-Z0-9_-]+)"\s*:', re.MULTILINE
)

# Common trivial micro-packages that should generally be written natively
TRIVIAL_PACKAGES = {
    "is-number": "Use `typeof x === 'number' && !Number.isNaN(x)`",
    "is-odd": "Use `n % 2 !== 0`",
    "is-even": "Use `n % 2 === 0`",
    "is-plain-object": "Use `Object.prototype.toString.call(x) === '[object Object]'`",
    "is-array": "Use native `Array.isArray()`",
    "left-pad": "Use native `String.prototype.padStart()`",
    "pad-left": "Use native `String.prototype.padStart()`",
    "array-flatten": "Use native `Array.prototype.flat()`",
    "arr-flatten": "Use native `Array.prototype.flat()`",
    "object-assign": "Use native `Object.assign()` or object spread `{ ...obj }`",
    "clone-deep": "Use native `structuredClone()`",
    "deep-clone": "Use native `structuredClone()`",
    "has-own-prop": "Use native `Object.hasOwn()`",
}


def get_npm_view(pkg: str) -> Any:
    """Fetch package metadata using `npm view --json`. Returns None if it can't be resolved."""
    try:
        res = subprocess.run(
            ["npm", "view", pkg, "--json"], capture_output=True, text=True, check=False
        )
        if res.returncode != 0 or not res.stdout.strip():
            return None
        return json.loads(res.stdout)
    except (OSError, ValueError):
        return None


def get_added_deps_from_diff(file_path: str = "package.json") -> list[str]:
    """Find newly added dependencies from git diff of package.json."""
    try:
        res = subprocess.run(
            ["git", "diff", "HEAD", "--", file_path], capture_output=True, text=True, check=False
        )
        if not res.stdout:
            # Fall back to the staged diff
            res = subprocess.run(
                ["git", "diff", "--cached", "--", file_path],
                capture_output=True,
                text=True,
                check=False,
            )
    except OSError:
        return []
    added = {m for m in ADDED_DEP_RE.findall(res.stdout) if m not in DEPENDENCY_SECTIONS}
    return list(added)


def get_deps_from_file(file_path: str) -> list[str]:
    """Extract all dependency names from a package.json file."""
    path = Path(file_path)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(data, dict):
        return []
    sections = [data.get("dependencies", {}), data.get("devDependencies", {})]
    if not all(isinstance(section, dict) for section in sections):
        return []
    return [name for section in sections for name in section]


def days_since(timestamp: Any, now: datetime) -> int | None:
    """Whole days between an ISO 8601 timestamp from npm and now, or None if it won't parse."""
    if not timestamp:
        return None
    try:
        then = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return (now - then).days
    except (AttributeError, TypeError, ValueError):
        return None


def age_warnings(
    latest_version: str, pkg_age_days: int | None, latest_release_days: int | None
) -> list[str]:
    if pkg_age_days is not None and pkg_age_days < AGE_THRESHOLD_DAYS:
        return [
            f"Package created only {pkg_age_days} days ago "
            f"(Age gate threshold: {AGE_THRESHOLD_DAYS} days). High supply-chain risk."
        ]
    if latest_release_days is not None and latest_release_days < RECENT_RELEASE_DAYS:
        return [
            f"Latest version ({latest_version}) was published {latest_release_days} days ago. "
            "Consider pinning to previous stable."
        ]
    return []


def audit_package(pkg: str) -> dict[str, Any]:
    if pkg.startswith("-"):
        # npm names can't start with "-", and npm would read one as an option (--registry=...)
        return {
            "name": pkg,
            "status": "INVALID_NAME",
            "warning": "Not a valid npm package name. Not passed to npm.",
        }
    is_trivial = pkg.lower() in TRIVIAL_PACKAGES
    alternative = TRIVIAL_PACKAGES.get(pkg.lower())
    meta = get_npm_view(pkg)
    if not meta:
        return {
            "name": pkg,
            "status": "UNRESOLVED_OR_OFFLINE",
            "warning": (
                "Could not resolve package on npm registry. Check for spelling/hallucination."
            ),
            "is_trivial": is_trivial,
            "trivial_alternative": alternative,
        }

    # Creation date and latest publish date
    time_data = meta.get("time", {})
    latest_version = meta.get("version", "")
    now = datetime.now(UTC)
    pkg_age_days = days_since(time_data.get("created"), now)
    latest_release_days = days_since(
        time_data.get(latest_version) or time_data.get("modified"), now
    )
    warnings = age_warnings(latest_version, pkg_age_days, latest_release_days)

    return {
        "name": pkg,
        "latest_version": latest_version,
        "license": meta.get("license", "Unknown"),
        "created_days_ago": pkg_age_days,
        "latest_release_days_ago": latest_release_days,
        "is_trivial": is_trivial,
        "trivial_alternative": alternative,
        "warnings": warnings,
        "status": "FLAGGED" if (warnings or is_trivial) else "PASS",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit packages for age-gating, triviality, and supply-chain risk."
    )
    parser.add_argument("packages", nargs="*", help="Package names to audit.")
    parser.add_argument("--file", type=str, help="Path to package.json to audit.")
    parser.add_argument(
        "--diff", nargs="?", const="package.json", help="Scan newly added packages from git diff."
    )

    args = parser.parse_args()

    pkgs_to_check = set(args.packages)

    if args.diff:
        pkgs_to_check.update(get_added_deps_from_diff(args.diff))
    elif args.file:
        pkgs_to_check.update(get_deps_from_file(args.file))
    elif not pkgs_to_check:
        # Default: check git diff of package.json if it exists
        pkgs_to_check.update(get_added_deps_from_diff("package.json"))

    if not pkgs_to_check:
        message = {"audited": 0, "message": "No dependencies specified or found in diff."}
        print(json.dumps(message, indent=2))
        return

    results = [audit_package(p) for p in sorted(pkgs_to_check)]

    output = {
        "audited_count": len(results),
        "flagged_count": sum(1 for r in results if r.get("status") != "PASS"),
        "results": results,
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
