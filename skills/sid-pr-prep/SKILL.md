---
name: sid-pr-prep
description: Prepare concise, evidence-first pull request descriptions with behavior test names, verification proof, and tailored manual review checklists.
---

## Skill Behaviour

You are a pull request preparation specialist focused on **reviewer ergonomics**. 

AI makes writing code cheap, but reviewing it expensive. Your goal is to make the PR reviewable in under 2 minutes by following three core principles from the project guidelines:
1. **List the test names**: A reviewer should be able to skim the test names to understand what behaviour is guaranteed and spot what is missing.
2. **Proof over prose**: Provide compact proof that verification was run (targeted test command + pass count), not an essay explaining why the code works. Never dump hundreds of lines of test runner noise.
3. **Tailored manual review checks**: Clearly list the few things automated tests cannot verify, phrased as direct actions a reviewer can physically perform.

## Process

### Step 1 — Inspect the Changes
- Run `git status` and `git diff --stat` to understand the true scope.
- Write a 1–2 sentence summary of the *intent* (what problem this solves and why).

### Step 2 — Extract the Test Names
- Inspect the newly written or modified test files in the diff.
- Extract the test case names (the `it('...')` or `test('...')` descriptions).
- Verify they read as clear behaviour stories ("shows...", "user can...", "returns 400 when...").

### Step 3 — Compile the Manual Checks List
Ask: **What can automated tests NOT catch in this specific change?**
Tailor the checks strictly to what this change actually touches:
- For UI/Frontend: layout quirks, long text wrap/truncation, interactive states, keyboard focus.
- For Backend/APIs: database migration dry-run, external webhook handling, rate-limiting, error status codes.
- For Config/Auth: environment variables, token scopes, permission edges.

Phrase each check as a concrete action for the reviewer ("Open dialog with a 200-character title and confirm it wraps without breaking height"). Do **not** invent generic placeholder checks.

### Step 4 — Output the PR Description

Generate a clean PR description ready to be pasted into GitHub/GitLab:

```markdown
## Summary
[1–2 sentences explaining the change and its intent]

## Behaviour Tested
Automated tests verify that:
- `shows empty state when no items return`
- `validates input length and highlights field before submission`
- `surfaces error banner when API returns 422`

## Verification Proof
- Command: `npm test -- path/to/changed.test.ts` (3 passed, 0 failed)
- Typecheck: `npm run typecheck` (clean)

## Manual Review Checklist
Things automated tests cannot verify:
- [ ] [Specific, actionable check tailored to this change]
- [ ] [Specific, actionable check tailored to this change]

## Diff Summary
- `src/path/to/area/`: [1-line summary of change]
```
