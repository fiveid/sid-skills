#!/usr/bin/env python3
"""
audit_deps.py — Audit proposed or new dependencies for age-gating, slopsquatting, and trivial utilities.

Usage:
    python audit_deps.py [package-names ...]
    python audit_deps.py --file package.json
    python audit_deps.py --diff [package.json]
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Packages less than this many days old trigger an age warning
AGE_THRESHOLD_DAYS = 30

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


def get_npm_view(pkg: str) -> dict | None:
    """Fetch package metadata using `npm view --json`."""
    try:
        res = subprocess.run(["npm", "view", pkg, "--json"], capture_output=True, text=True, check=False)
        if res.returncode == 0 and res.stdout.strip():
            return json.loads(res.stdout)
    except Exception:
        pass
    return None


def get_added_deps_from_diff(file_path: str = "package.json") -> list[str]:
    """Find newly added dependencies from git diff of package.json."""
    added = []
    try:
        res = subprocess.run(["git", "diff", "HEAD", "--", file_path], capture_output=True, text=True, check=False)
        if not res.stdout:
            # Fall back to diff --cached or plain diff
            res = subprocess.run(["git", "diff", "--cached", "--", file_path], capture_output=True, text=True, check=False)
        
        # Regex to match added dependency lines: + "package-name": "version"
        dep_re = re.compile(r'^\+\s*"([@a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+|[a-zA-Z0-9_-]+)"\s*:', re.MULTILINE)
        for match in dep_re.findall(res.stdout):
            if match not in ("dependencies", "devDependencies", "peerDependencies"):
                added.append(match)
    except Exception:
        pass
    return list(set(added))


def get_deps_from_file(file_path: str) -> list[str]:
    """Extract all dependency names from a package.json file."""
    path = Path(file_path)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        deps = list(data.get("dependencies", {}).keys()) + list(data.get("devDependencies", {}).keys())
        return deps
    except Exception:
        return []


def audit_package(pkg: str) -> dict:
    meta = get_npm_view(pkg)
    if not meta:
        return {
            "name": pkg,
            "status": "UNRESOLVED_OR_OFFLINE",
            "warning": "Could not resolve package on npm registry. Check for spelling/hallucination.",
            "is_trivial": pkg.lower() in TRIVIAL_PACKAGES,
            "trivial_alternative": TRIVIAL_PACKAGES.get(pkg.lower()),
        }

    # Extract creation date and latest publish date
    time_data = meta.get("time", {})
    created_str = time_data.get("created")
    latest_version = meta.get("version", "")
    latest_release_str = time_data.get(latest_version) or time_data.get("modified")

    now = datetime.now(timezone.utc)
    pkg_age_days = None
    latest_release_days = None

    if created_str:
        try:
            created_dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            pkg_age_days = (now - created_dt).days
        except Exception:
            pass

    if latest_release_str:
        try:
            rel_dt = datetime.fromisoformat(latest_release_str.replace("Z", "+00:00"))
            latest_release_days = (now - rel_dt).days
        except Exception:
            pass

    # Evaluate age warnings
    warnings = []
    if pkg_age_days is not None and pkg_age_days < AGE_THRESHOLD_DAYS:
        warnings.append(f"Package created only {pkg_age_days} days ago (Age gate threshold: {AGE_THRESHOLD_DAYS} days). High supply-chain risk.")
    elif latest_release_days is not None and latest_release_days < 7:
        warnings.append(f"Latest version ({latest_version}) was published {latest_release_days} days ago. Consider pinning to previous stable.")

    # Triviality check
    is_trivial = pkg.lower() in TRIVIAL_PACKAGES
    alternative = TRIVIAL_PACKAGES.get(pkg.lower())

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


def main():
    parser = argparse.ArgumentParser(description="Audit packages for age-gating, triviality, and supply-chain risk.")
    parser.add_argument("packages", nargs="*", help="Package names to audit.")
    parser.add_argument("--file", type=str, help="Path to package.json to audit.")
    parser.add_argument("--diff", nargs="?", const="package.json", help="Scan newly added packages from git diff.")

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
        print(json.dumps({"audited": 0, "message": "No dependencies specified or found in diff."}, indent=2))
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
