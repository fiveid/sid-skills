---
name: sid-test
description: Write behaviour-focused React + TypeScript tests that use the project's shared render helper and edge-only mocks, list cases before code, and prove each test can fail.
---

## Skill Behaviour

You are a sceptical test author. Your job is to increase confidence that the code works, not to increase the test count. A test that cannot fail when the code is broken is worse than no test, because it looks like coverage.

Every test must answer yes to: **would a user notice if this broke?** Do not write tests that only prove React works ("onClick triggers state", "props.title renders the title"). Spend effort on edge cases, errors, validation, and empty or disabled states.

## Process

1. **Find the shared test setup**
   - Locate the shared render helper (for example `renderWithProviders`, `test-utils`, `test/render.tsx`) and the shared network mocks (for example MSW handlers, `mocks/handlers`, generated API mocks).
   - Locate test data factories, if any.
   - If either the render helper or the network mocking pattern is missing, stop. Report what is missing and point to `references/setup.md`. Do not invent a one-off setup inside the test file.

2. **List the test cases first**
   - Write one-line names that read like small user stories: "shows…", "user can…", "when X, Y happens".
   - Check the list against the states that apply:
     - Anything that fetches data: loading, empty, error, success
     - Anything interactive: keyboard use, disabled state
     - Anything that accepts input: validation, special characters, very long values
     - Anything time-based: timeouts, debounce, expiry
   - Include at least one failure case, even if the prompt did not ask for one.
   - If the caller asked to approve cases first, return the list and stop here.

3. **Write the tests**
   - Render through the shared helper so real providers (router, store, query client) and real hooks run. Fake only the network underneath.
   - Never mock our own hooks, components, or context. Fake only at the edges: network, time, browser APIs, third-party SDKs (via their adapter module where one exists).
   - Override network responses per test for error, empty, and slow states (for example `server.use(...)`). Do not edit the shared default handlers for one test.
   - Query by role and accessible name (`getByRole('button', { name: 'Save' })`), then label or text. Use test IDs only when the element has no accessible role, such as a chart canvas.
   - Drive interactions with `userEvent` (not `fireEvent`) and `await` every interaction.
   - Prefer `findBy*` over `waitFor` + `getBy*` for things that appear asynchronously.
   - Use fake timers only in tests that need them, and pass `advanceTimers` to `userEvent.setup()` when both are used. Use `setSystemTime` for date-dependent behaviour.
   - Assert on what the user sees or what leaves the component (rendered text, roles, a request sent, a callback called after a user action). Do not assert on internal state.
   - Assert on a mock only as the result of a user action ("typing a name calls onChange with the new value"), never on its own.
   - No snapshot tests of components or DOM.
   - Pure functions (formatters, parsers, utils) may be unit tested directly, ideally as table-driven cases. Our own hooks may be tested directly with `renderHook`; the rule is not to mock them elsewhere.

4. **See it fail**
   - Bug fix: run the new test against the unfixed code and show it failing.
   - New behaviour: temporarily break the implementation (invert a condition, remove a branch, return early) and show the relevant test failing, then restore it and confirm with `git diff` that only intended changes remain.
   - The failure must be the expected assertion failing. A crash, import error, or missing provider does not count. Fix the test and repeat.

5. **Collect manual checks**
   - Anything that cannot sensibly be tested goes into a manual checks list for the MR: visual layout, long text overflowing, animation, cross-browser quirks.

## Output Format

Return, in order:

### Test cases
- The one-line case names, grouped by file

### Tests
- The test files

### Fail-first evidence
- For each case or group: what was broken (or that the old code was used), and the assertion failure message seen

### Manual checks
- One line per check, phrased as something a reviewer can do ("Open the panel with a 200-character name and confirm it wraps")

## Constraints

- Do not change assertions to make a failing test pass unless the behaviour change is intended, and say so explicitly in the output.
- Do not leave `.only`, `.skip`, or `.todo` in committed tests.
- Do not use `expect.anything()`, `toBeTruthy()`, or `toBeDefined()` where a specific value can be asserted.
- Do not add a "renders without crashing" test; any other test that renders the component already covers it.
