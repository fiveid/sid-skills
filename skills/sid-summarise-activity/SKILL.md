---
name: sid-summarise-activity
description: >-
  Summarise recent activity in the repository, including commits and pull requests. Provide concise overviews of key changes and updates and time estimates.
---

You are the Summarise Activity skill.

Your task is to help me fill in my timesheet at the end of the sprint.

## Step 1 — Determine the date range

- By default ("since the beginning of the sprint"), do **not** pass `--since`; the script calculates the sprint start automatically.
- If I ask for a different period, calculate the appropriate start date and pass it via `--since`:
  - "since last week" → today minus 7 days
  - "since the start of this week" → the most recent Monday

## Step 2 — Run the script

Run from the repository root:

```
python .agents/skills/sid-summarise-activity/scripts/fetch_activity.py [--since YYYY-MM-DD]
```

The script outputs JSON containing:
- `period` — `start`, `end` dates and `author`
- `commits` — all commits (sorted ascending) with `hash`, `timestamp`, `message`, `ticket_id`, `insertions`, `deletions`, `files_changed`, and `timeframe_minutes` (working minutes from 10am GMT on the commit's day, or from the previous commit if it was on the same day; commit times are clamped to 10am–5pm GMT; weekends = 0)
- `groups` — commits keyed by ticket ID (ungrouped commits appear under `"Other"`), each with aggregate diff totals and `total_timeframe_minutes`

## Step 3 — Produce the summary

Using the script output, produce a summary **grouped by ticket ID** (or `"Other"`). For each group include:
- **Ticket ID / group name** and the commit messages it contains
- **Pure dev estimate** — your judgment based on `insertions`, `deletions`, and `files_changed`
- **Timeframe estimate** — convert `total_timeframe_minutes` to hours/minutes

Include the `period.start` and `period.end` dates from the script output at the top of the summary for context.
