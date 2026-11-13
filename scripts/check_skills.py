#!/usr/bin/env python3
"""Check every skill's frontmatter and that the skill catalogues list exactly the skills present.

Usage: python3 scripts/check_skills.py [--root DIR]

Frontmatter rules (from the Agent Skills spec, plus APM's ASCII requirement):
  - SKILL.md starts with a `---` frontmatter block
  - `name` is 1-64 lowercase letters, digits and single hyphens, and matches the folder name
  - `description` is present and at most 1024 characters
  - every frontmatter value is ASCII

Catalogue rule (AGENTS.md, "Keep catalogues in sync"): README.md and skills/README.md each list
every skill folder once, and list nothing that isn't a skill folder.

Only the small YAML subset skills use is parsed: `key: value` lines, quoted values, and folded
(`>`, `>-`) or literal (`|`, `|-`) blocks. Anything else is reported as unsupported rather than
guessed at. Exits 1 if any check fails.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
KEY_RE = re.compile(r"^([A-Za-z][\w-]*):\s*(.*)$")
BLOCK_INDICATORS = {">", ">-", ">+", "|", "|-", "|+"}
# A catalogue row links a skill like [`sid-name`](...)
CATALOGUE_RE = re.compile(r"^\|\s*\[`([^`]+)`\]\(", re.MULTILINE)
CATALOGUES = ("README.md", "skills/README.md")


class FrontmatterError(Exception):
    pass


def frontmatter_lines(text: str) -> list[str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        msg = "does not start with a --- frontmatter block"
        raise FrontmatterError(msg)
    for end, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines[1:end]
    msg = "frontmatter block is not closed with ---"
    raise FrontmatterError(msg)


def unquote(value: str) -> str:
    if len(value) > 1 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def block_value(indicator: str, body: list[str]) -> str:
    stripped = [line.strip() for line in body]
    joined = " ".join(stripped) if indicator.startswith(">") else "\n".join(stripped)
    return joined.strip() if indicator.endswith("-") else joined


def parse_frontmatter(lines: list[str]) -> dict[str, str]:
    fields: dict[str, str] = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = KEY_RE.match(line)
        if not match:
            msg = f"unsupported frontmatter line: {line!r}"
            raise FrontmatterError(msg)
        key, value = match.group(1), match.group(2).strip()
        if value in BLOCK_INDICATORS:
            body = []
            while i < len(lines) and (lines[i].startswith((" ", "\t")) or not lines[i].strip()):
                body.append(lines[i])
                i += 1
            fields[key] = block_value(value, body)
        else:
            fields[key] = unquote(value)
    return fields


def check_fields(folder: str, fields: dict[str, str]) -> list[str]:
    problems = []
    name = fields.get("name", "")
    if not NAME_RE.fullmatch(name) or len(name) > MAX_NAME_LENGTH:
        problems.append(f"name {name!r} must be 1-64 lowercase letters, digits and single hyphens")
    if name != folder:
        problems.append(f"name {name!r} does not match the folder name {folder!r}")
    description = fields.get("description", "")
    if not description:
        problems.append("description is missing")
    elif len(description) > MAX_DESCRIPTION_LENGTH:
        problems.append(f"description is {len(description)} characters (max 1024)")
    problems.extend(
        f"{key} contains non-ASCII characters"
        for key, value in fields.items()
        if not value.isascii()
    )
    return problems


def check_skill(skill_md: Path) -> list[str]:
    try:
        fields = parse_frontmatter(frontmatter_lines(skill_md.read_text(encoding="utf-8")))
    except FrontmatterError as err:
        return [str(err)]
    return check_fields(skill_md.parent.name, fields)


def check_catalogue(root: Path, catalogue: str, skills: set[str]) -> list[str]:
    path = root / catalogue
    if not path.is_file():
        return [f"{catalogue}: missing"]
    listed = CATALOGUE_RE.findall(path.read_text(encoding="utf-8"))
    problems = [
        f"{catalogue}: {name} is listed more than once"
        for name in sorted({n for n in listed if listed.count(n) > 1})
    ]
    problems += [f"{catalogue}: {name} is not listed" for name in sorted(skills - set(listed))]
    problems += [
        f"{catalogue}: {name} is listed but has no skill folder"
        for name in sorted(set(listed) - skills)
    ]
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".", help="repository root (default: current directory)")
    root = Path(parser.parse_args().root)

    folders = sorted(p for p in (root / "skills").iterdir() if p.is_dir())
    problems: list[str] = []
    for folder in folders:
        skill_md = folder / "SKILL.md"
        if not skill_md.is_file():
            problems.append(f"skills/{folder.name}: no SKILL.md")
            continue
        problems.extend(f"skills/{folder.name}/SKILL.md: {p}" for p in check_skill(skill_md))

    skills = {f.name for f in folders}
    for catalogue in CATALOGUES:
        problems.extend(check_catalogue(root, catalogue, skills))

    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        return 1
    print(f"{len(folders)} skills checked: frontmatter valid, catalogues in sync.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
