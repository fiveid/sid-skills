# **Testing with confidence**

*The principle behind this guide is in [HUMANS.md](../../HUMANS.md#testing-with-confidence).*

## **Initial project setup**

* **A shared mocking pattern for the backend.** Fake things only at the edges (network, time, browser APIs, third-party SDKs), never in the middle of the code you’re testing. If the handlers and types can be generated from the backend’s API schema, the fake responses can’t drift from what the backend really returns. Set the mock server to fail the test on any unhandled network request, so background fetches can't fail silently. This is the pattern the agent will use for every test, rather than rolling its own each time, so it deserves high attention.  
* **A shared render helper.** One function that wraps components in the real providers (router, store, query client). Tests then use the real `useUser` hook with only the network faked underneath. If the agent mocks each hook instead, the tests end up only testing React internals. Mock only what you don’t own.  
* **Mutation testing.** Set up something like Stryker to run on changed components, either as a regular audit or as a precaution. It’s slow, but it shows whether tests actually catch anything when the code is broken.

## **Writing agent skills**

A testing skill (or a section in the agent instructions) should cover:

* **Use the shared helper and mocking pattern.** Never mock our own hooks, components or context.  
* **Ask “would a user notice if this broke?”** We don’t want “`onClick` triggers state” or “`props.title` renders the title”; those are obvious at a glance and just test React. We want edge cases, errors, validation, and empty or disabled states.  
* **Cover the states where they apply.** Loading, empty, error and success for anything that fetches data. Keyboard use and disabled states for anything interactive.  
* **Use `userEvent`, never `fireEvent`.** Simulate real user actions (`await user.click()`, `await user.type()`). `fireEvent` dispatches synthetic events directly and will happily pass on elements that are hidden, disabled or unfocusable.  
* **Query by role and label** (`getByRole('button', { name: 'Save' })`) rather than test IDs or class names. No snapshot tests.  
* **Be careful asserting absence.** Never assert that something is *not* on the screen (`queryBy...`) until you have awaited the surrounding view to finish loading, and proven in another test that the selector actually matches when the element *is* shown.  
* **Pull complex logic into plain functions.** Don’t mount a full component tree twenty times to test twenty edge cases of a price calculation or date parser. Extract pure business logic and unit test it directly with table-driven tests (`it.each`), then use a few component tests to check the UI wires into it properly.  
* **List the test cases first**, as one-line names that read like small user stories: “shows…”, “user can…”, “when X, Y happens”.  
* **Anything that can’t sensibly be tested goes into the MR’s manual checks list**, e.g. visual layout, or long text overflowing.  
* **Reset the data cache in every test, and scope fake timers.** Only enable fake timers inside the specific tests that need them (wired to `userEvent`), so they don't deadlock async queries elsewhere.  
* **Treat existing tests as read-only by default.** If a change breaks an existing test, stop and explain why before touching the test. Never edit an assertion just to make the test suite green.  
* **See it fail first.** For a bug fix, the agent writes the test, runs it against the old code and shows it failing. It’s cheap, it’s mutation testing for one case, and it catches most fake tests before Stryker is needed.

## **When prompting**

* **Include a few one-line behaviour examples** of what the user should see and be able to do, including at least one failure case.  
* **Prompt for edge cases specifically.** What happens if the text is twice as long? If a user enters a special character rather than a number? If the request times out?  
* **Ask for the test list before the implementation**, so you can check the cases before any code exists.

## **When reviewing MRs**

* **Skim the test names, not the test code.** Red flags are anything that mirrors the code rather than the behaviour:  
  * one test per prop or branch  
  * “renders without crashing” or “component initialises” repeated as if they test something  
  * internal state (“sets `isOpen`”)  
  * assertions on a mock with no user action (“calls `onChange`” rather than “typing a name calls `onChange` with the new value”)  
  * asserting something isn't there (`expect(queryBy...).toBeNull()`) before asserting the page has actually loaded  
  * existing test assertions weakened or changed in the same MR as the code without a change in requirements.  
* **Check what’s missing.** Are loading, empty, error and keyboard states covered where they should be?  
* **Check the manual checks list** covers what the tests can’t.  
* **If in doubt, run mutation testing on the changed components.** If you can break the code and the tests stay green, they’re not testing anything.
