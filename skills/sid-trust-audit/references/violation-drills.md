# Violation drills

Pick 6 to 12 that fit the project. Apply each alone in a throwaway worktree, run the gates the project relies on, record the result, reset. Format changed files first. Never commit or push.

## Procedure

```bash
git worktree add ../audit-scratch HEAD
# install if needed, apply one violation, format, run the gates (all inside ../audit-scratch)
git -C ../audit-scratch checkout -- . && git -C ../audit-scratch clean -fd   # reset between violations
git worktree remove ../audit-scratch --force
git status --porcelain               # must be empty
```

Run every reset with `git -C ../audit-scratch`, never from the current directory. A bare `git clean -fd` in the real checkout deletes the owner's untracked work.

Record for each: the violation, the rule it breaks, what was expected to catch it, the result, and the exact error or the fact that nothing caught it. Results fall into:

- **Caught:** the routine local check fails.
- **Caught, in CI only:** the local routine passes; only CI fails.
- **Caught by a command nobody routinely runs:** say which.
- **Caught by chance:** e.g. a test happens to cover this particular page. Say so; it isn't a safeguard.
- **Passes every gate.**

## Kinds that have proved revealing

**Top-risk violations** (always include one per risk):

- Saving or deleting: write outside the project directory, delete files not listed as changed, a non-atomic save.
- Processes: a new `sh -c`, `Command::new`, `child_process.exec`, or a recursive delete in a new module.
- Data leaving the device or crossing users: a personal field sent to a backend, a cache header on a credentialed response.
- Injection: unescaped content written into HTML or a script tag.
- Content correctness: change a puzzle or calculation's answer without changing its explanation.

**Boundaries and the obvious fix:**

- Import a forbidden package (e.g. React in a pure logic package). If caught, try the obvious fix: declare the dependency. Then try a relative path into another package's `src`.
- Add an export to a public API surface.
- A cyclic import.

**Contracts and generated code:**

- Rename a field on one side of a generated contract (e.g. Rust IPC type, OpenAPI schema) without regenerating. Check whether the local routine regenerates before type checking.
- Change a schema description or field without regenerating derived files.
- Malformed runtime data that the types say can't happen (wrong type, missing field). Does it fail one item or take down the whole page or screen?

**Stored data:**

- Add a required field to the stored format without bumping the version.
- Make the loader treat a newer save as invalid, so it would be overwritten.

**Rules from agent instructions:**

- A hard-coded string where content should come from data.
- A colour, class or token outside the design system.
- Whatever the project calls its "golden rules".

**Language-level mistakes in the half the owner reads:**

- Break React's rules of hooks (an early return before a hook).
- An explicit `any`.
- A floating promise.

**Tests and coverage:**

- Delete a large test file. Then delete a small one. Floors often catch the first and not the second.

**Secrets:**

- Commit a fake token in a separate throwaway repository (`git init` in a temporary directory, not the audit worktree) and scan it with the project's own config.

**Claims:**

- Pick the strongest behavioural claim in the README or docs and try to break it with the smallest change. If nothing fails, the claim isn't vouched for.
