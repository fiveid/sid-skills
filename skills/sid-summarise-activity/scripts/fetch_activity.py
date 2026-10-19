#!/usr/bin/env python3
"""
fetch_activity.py — Fetch git commit activity for sprint summarisation.

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

import argparse
import json
import re
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone

# Working hours (GMT). 10am–5pm on weekdays.
WORK_START = 10  # 10am GMT
WORK_END = 17    # 5pm GMT

# Matches conventional commit format:  type(ticket-id): message
TICKET_RE = re.compile(r"^[a-z]+\(([^)]+)\):", re.IGNORECASE)

# Sprint reference: a known sprint-start Monday. Adjust if the project's
# cadence doesn't align with this date.
SPRINT_REFERENCE = date(2025, 1, 6)


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
        capture_output=True, text=True, check=True,
    )
    name = result.stdout.strip()
    if not name:
        sys.exit("Error: could not determine git user name. Pass --author explicitly.")
    return name


def extract_ticket_id(message: str) -> str | None:
    m = TICKET_RE.match(message.strip())
    return m.group(1) if m else None


def fetch_commits(since: date, author: str) -> list[dict]:
    """Fetch commits since the given date by the given author with diff stats."""
    sep = "\x1e"  # ASCII Record Separator — safe delimiter for git output
    fmt = f"{sep}%H|%aI|%s"

    result = subprocess.run(
        [
            "git", "log",
            "--all",
            f"--author={author}",
            f"--after={since.isoformat()}T00:00:00+00:00",
            f"--format={fmt}",
            "--numstat",
            "--no-merges",
        ],
        capture_output=True, text=True, check=True,
    )

    commits = []
    for block in result.stdout.split(sep):
        block = block.strip()
        if not block:
            continue

        lines = block.splitlines()
        parts = lines[0].split("|", 2)
        if len(parts) != 3:
            continue

        sha, ts, msg = (p.strip() for p in parts)
        insertions = deletions = files_changed = 0

        for stat_line in lines[1:]:
            stat_line = stat_line.strip()
            if not stat_line:
                continue
            cols = stat_line.split("\t", 2)
            if len(cols) == 3:
                ins_str, del_str = cols[0], cols[1]
                if ins_str.isdigit():
                    insertions += int(ins_str)
                if del_str.isdigit():
                    deletions += int(del_str)
                files_changed += 1

        commits.append({
            "hash": sha,
            "timestamp": ts,
            "message": msg,
            "ticket_id": extract_ticket_id(msg),
            "insertions": insertions,
            "deletions": deletions,
            "files_changed": files_changed,
        })

    commits.sort(key=lambda c: c["timestamp"])
    return commits


def clamp_to_working_hours(ts: datetime) -> datetime:
    """
    Clamp a datetime to the nearest working boundary (10am–5pm GMT).
    Before 10am → 10am. After 5pm → 5pm.
    """
    day_start = ts.replace(hour=WORK_START, minute=0, second=0, microsecond=0)
    day_end   = ts.replace(hour=WORK_END,   minute=0, second=0, microsecond=0)
    return max(day_start, min(ts, day_end))


def working_minutes_for_commit(commit_ts: datetime, prev_ts: datetime | None) -> int:
    """
    Working minutes attributed to this commit (10am–5pm GMT, weekdays only).

    The commit time is clamped to 10am–5pm: commits before 10am count as 10am,
    commits after 5pm count as 5pm.

    Work on this commit is assumed to have started at 10am, unless the previous
    commit was on the same calendar day, in which case it started immediately
    after that commit (also clamped).

    Commits on Saturdays and Sundays contribute 0 minutes.
    """
    utc = timezone.utc
    ts = commit_ts.astimezone(utc)

    if ts.weekday() >= 5:  # Saturday=5, Sunday=6
        return 0

    end = clamp_to_working_hours(ts)

    if prev_ts is not None:
        prev_utc = prev_ts.astimezone(utc)
        if prev_utc.date() == ts.date():
            start = clamp_to_working_hours(prev_utc)
        else:
            start = ts.replace(hour=WORK_START, minute=0, second=0, microsecond=0)
    else:
        start = ts.replace(hour=WORK_START, minute=0, second=0, microsecond=0)

    if end <= start:
        return 0

    return int((end - start).total_seconds() / 60)


def add_timeframe_intervals(commits: list[dict]) -> list[dict]:
    """Add timeframe_minutes to each commit."""
    for i, commit in enumerate(commits):
        prev_ts = datetime.fromisoformat(commits[i - 1]["timestamp"]) if i > 0 else None
        curr_ts = datetime.fromisoformat(commit["timestamp"])
        commit["timeframe_minutes"] = working_minutes_for_commit(curr_ts, prev_ts)
    return commits


def group_by_ticket(commits: list[dict]) -> dict:
    groups: dict[str, list[dict]] = {}
    for c in commits:
        key = c["ticket_id"] or "Other"
        groups.setdefault(key, []).append(c)

    return {
        key: {
            "commits": group_commits,
            "total_insertions": sum(c["insertions"] for c in group_commits),
            "total_deletions": sum(c["deletions"] for c in group_commits),
            "total_timeframe_minutes": sum(
                c["timeframe_minutes"]
                for c in group_commits
                if c["timeframe_minutes"] is not None
            ),
        }
        for key, group_commits in groups.items()
    }


def main():
    parser = argparse.ArgumentParser(
        description="Fetch git activity for sprint summarisation."
    )
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

    today = date.today()
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
