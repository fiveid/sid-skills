#!/usr/bin/env python3
"""
fetch_activity.py - Fetch git commit activity for sprint summarisation.

Usage:
    python fetch_activity.py [--since YYYY-MM-DD] [--author NAME]

Arguments:
    --since DATE    Start date (YYYY-MM-DD). Defaults to the start of the current 2-week sprint.
    --author NAME   Git author name filter. Defaults to `git config user.name`.

Output: JSON to stdout containing:
  - period:   start/end dates and author
  - commits:  list of commits (sorted ascending) with hash, timestamp, message,
              ticket_id, diff stats, and timeframe_minutes (working minutes from
              10am GMT on the commit day, or from the previous commit if it was
              on the same day; weekends contribute 0 minutes)
  - groups:   commits keyed by ticket_id (ungrouped commits appear under "Other"),
              each with aggregate diff stats and total_timeframe_minutes
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import UTC, date, datetime, timedelta
from typing import Any

# Working hours (GMT). 10am-5pm on weekdays.
WORK_START = 10  # 10am GMT
WORK_END = 17  # 5pm GMT
SATURDAY = 5  # date.weekday(): Monday is 0

# Matches conventional commit format:  type(ticket-id): message
TICKET_RE = re.compile(r"^[a-z]+\(([^)]+)\):", re.IGNORECASE)

# Sprint reference: a known sprint-start Monday. Adjust if the project's
# cadence doesn't align with this date.
SPRINT_REFERENCE = date(2025, 1, 6)

# ASCII Record Separator: a safe delimiter for git output
RECORD_SEP = "\x1e"

# `git log --numstat` lines are "insertions<TAB>deletions<TAB>path"
NUMSTAT_COLUMNS = 3
# The format line is "hash|timestamp|subject"
HEADER_FIELDS = 3


def get_sprint_start(today: date) -> date:
    """Return the Monday that started the current 2-week sprint."""
    days_since_monday = today.weekday()  # 0 = Monday
    this_monday = today - timedelta(days=days_since_monday)
    weeks_since_ref = (this_monday - SPRINT_REFERENCE).days // 7
    sprint_week_offset = weeks_since_ref % 2
    return this_monday - timedelta(weeks=sprint_week_offset)


def get_git_user() -> str:
    result = subprocess.run(
        ["git", "config", "user.name"],
        capture_output=True,
        text=True,
        check=True,
    )
    name = result.stdout.strip()
    if not name:
        sys.exit("Error: could not determine git user name. Pass --author explicitly.")
    return name


def extract_ticket_id(message: str) -> str | None:
    m = TICKET_RE.match(message.strip())
    return m.group(1) if m else None


def numstat_totals(stat_lines: list[str]) -> tuple[int, int, int]:
    """Sum insertions, deletions and files changed. Binary files count as changed, with no lines."""
    insertions = deletions = files_changed = 0
    for raw in stat_lines:
        cols = raw.strip().split("\t", 2)
        if len(cols) != NUMSTAT_COLUMNS:
            continue
        ins_str, del_str = cols[0], cols[1]
        if ins_str.isdigit():
            insertions += int(ins_str)
        if del_str.isdigit():
            deletions += int(del_str)
        files_changed += 1
    return insertions, deletions, files_changed


def parse_commit_block(block: str) -> dict[str, Any] | None:
    """One commit from `git log` output: a header line, then its numstat lines."""
    lines = block.strip().splitlines()
    if not lines:
        return None
    parts = lines[0].split("|", 2)
    if len(parts) != HEADER_FIELDS:
        return None
    sha, ts, msg = (p.strip() for p in parts)
    insertions, deletions, files_changed = numstat_totals(lines[1:])
    return {
        "hash": sha,
        "timestamp": ts,
        "message": msg,
        "ticket_id": extract_ticket_id(msg),
        "insertions": insertions,
        "deletions": deletions,
        "files_changed": files_changed,
    }


def fetch_commits(since: date, author: str) -> list[dict[str, Any]]:
    """Fetch commits since the given date by the given author with diff stats."""
    result = subprocess.run(
        [
            "git",
            "log",
            "--all",
            f"--author={author}",
            f"--after={since.isoformat()}T00:00:00+00:00",
            f"--format={RECORD_SEP}%H|%aI|%s",
            "--numstat",
            "--no-merges",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    commits = [c for c in map(parse_commit_block, result.stdout.split(RECORD_SEP)) if c]
    commits.sort(key=lambda c: c["timestamp"])
    return commits


def clamp_to_working_hours(ts: datetime) -> datetime:
    """
    Clamp a datetime to the nearest working boundary (10am-5pm GMT).
    Before 10am -> 10am. After 5pm -> 5pm.
    """
    day_start = ts.replace(hour=WORK_START, minute=0, second=0, microsecond=0)
    day_end = ts.replace(hour=WORK_END, minute=0, second=0, microsecond=0)
    return max(day_start, min(ts, day_end))


def working_minutes_for_commit(commit_ts: datetime, prev_ts: datetime | None) -> int:
    """
    Working minutes attributed to this commit (10am-5pm GMT, weekdays only).

    The commit time is clamped to 10am-5pm: commits before 10am count as 10am,
    commits after 5pm count as 5pm.

    Work on this commit is assumed to have started at 10am, unless the previous
    commit was on the same calendar day, in which case it started immediately
    after that commit (also clamped).

    Commits on Saturdays and Sundays contribute 0 minutes.
    """
    ts = commit_ts.astimezone(UTC)

    if ts.weekday() >= SATURDAY:
        return 0

    end = clamp_to_working_hours(ts)

    if prev_ts is not None and prev_ts.astimezone(UTC).date() == ts.date():
        start = clamp_to_working_hours(prev_ts.astimezone(UTC))
    else:
        start = ts.replace(hour=WORK_START, minute=0, second=0, microsecond=0)

    if end <= start:
        return 0

    return int((end - start).total_seconds() / 60)


def add_timeframe_intervals(commits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add timeframe_minutes to each commit."""
    for i, commit in enumerate(commits):
        prev_ts = datetime.fromisoformat(commits[i - 1]["timestamp"]) if i > 0 else None
        curr_ts = datetime.fromisoformat(commit["timestamp"])
        commit["timeframe_minutes"] = working_minutes_for_commit(curr_ts, prev_ts)
    return commits


def group_by_ticket(commits: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for c in commits:
        key = c["ticket_id"] or "Other"
        groups.setdefault(key, []).append(c)

    return {
        key: {
            "commits": group_commits,
            "total_insertions": sum(c["insertions"] for c in group_commits),
            "total_deletions": sum(c["deletions"] for c in group_commits),
            "total_timeframe_minutes": sum(
                c["timeframe_minutes"] for c in group_commits if c["timeframe_minutes"] is not None
            ),
        }
        for key, group_commits in groups.items()
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch git activity for sprint summarisation.")
    parser.add_argument(
        "--since",
        metavar="DATE",
        help="Start date (YYYY-MM-DD). Defaults to start of current 2-week sprint.",
    )
    parser.add_argument(
        "--author",
        metavar="NAME",
        help="Git author name filter. Defaults to git config user.name.",
    )
    args = parser.parse_args()

    # Today in the local timezone, as `date.today()` would give
    today = datetime.now(UTC).astimezone().date()
    since = date.fromisoformat(args.since) if args.since else get_sprint_start(today)
    author = args.author or get_git_user()

    commits = fetch_commits(since, author)
    commits = add_timeframe_intervals(commits)
    groups = group_by_ticket(commits)

    output = {
        "period": {
            "start": since.isoformat(),
            "end": today.isoformat(),
            "author": author,
        },
        "commits": commits,
        "groups": groups,
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
