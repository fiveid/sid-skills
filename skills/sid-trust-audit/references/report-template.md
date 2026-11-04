# Report template

Use this structure. Keep sections short; put detail in tables.

```markdown
# Trust audit: <project>

An audit against the rule "you can ship code you haven't read, but not behaviour you can't vouch for". Drafted by the agent that wrote most of the code, so every claim points to a file, a config entry or a command run for this audit. Anything without evidence is under Gaps.

**Date:** <YYYY-MM-DD>. **Commit:** `<sha>` on `<branch>` (<n> commits ahead of `main`).

Labels used throughout:
- **Enforced:** a tool fails a run, and the failure blocks something.
- **Exists, not enforced:** the check exists, but someone has to run it, or its failure blocks nothing.
- **Convention:** a written rule nothing checks.

## 1. Overview
What it is · stack (table) · size (table) · how it was built (commits, agent trailers, PRs, reviews) · what the owner reads and doesn't · what the owner does by hand (owner's own description) · how code reaches users and what gates it.

## 2. Risk profile
Table: # · failure · where it would happen · who notices, and when. One line on where the risky code sits relative to what the owner reads.

## 3. Where trust comes from today
### Checks run for this audit
Table: command · result · time.
### Deliberate violations
Table: # · violation · rule it breaks · expected catch · result. Then one line: "<n> of <m> caught; <k> of the misses map to the top risks."
### Layer 1: always-on checks
Table: check · where · label.
**What runs, and when:** CI triggers, what gates release or deploy, whether `main` is protected, whether the agent's verify routine is complete.
### Layer 2: checkpoints
Table: trigger · what exists · label. Whether anything triggers checkpoints mechanically, and whether they leave a record.
### Layer 3: milestones
Feature complete: where defined, open items, "not in this version" list. Production ready: table of item · state · evidence.
### Claims
Table: claim · where it's made · what backs it (test / prose / nothing).

## 4. Human checkpoints
Table: what · where · size · can the owner realistically check it? Note which ones flag their own changes.

## 5. Gaps
Ordered by risk. Bold one-line summary, then evidence. "It seems to work when used" and "unproven, not absent" are acceptable verdicts.

## 6. Recommendations
Table: # · change · closes · cost · proof it works (usually: re-run V<n>, it now fails). Then "Left out on purpose" with reasons.
```

For a delta audit, add a section after the Overview:

```markdown
## Changes since the last audit (<date>, `<sha>`)
Table: gap · then · now · evidence. Then re-run every earlier violation with the same number and show then vs now.
```
