# Test setup

Read this only when the project has no shared render helper or network mocking pattern. These pieces are written once and then used by every test, so get them right before writing any feature tests.

The examples assume Vitest, React Testing Library, MSW, and TanStack Query. Adapt names to the project's actual stack, router, and store.

## 1. Network mocks at the edge

Fake only the edges: network, time, browser APIs, third-party SDKs. Never fake our own code.

- Use MSW so requests go through the real fetch/client code.
- If the backend publishes an OpenAPI schema, generate typed handlers and response types from it (for example orval or openapi-msw). Generated handlers stop the response shape drifting from the real API.
- Generated defaults are happy-path. Tests override per case for error, empty, and slow responses.
- Wrap third-party SDKs (analytics, payments, maps) in a thin adapter module we own, and fake the SDK at that adapter or at the network beneath it.

```ts
// test/server.ts
import { setupServer } from 'msw/node'
import { handlers } from './handlers'

export const server = setupServer(...handlers)
```

```ts
// test/setup.ts (vitest setupFiles)
import { server } from './server'

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

`onUnhandledRequest: 'error'` makes a request with no handler fail the test instead of passing quietly.

## 2. Shared render helper

One function wraps components in the real providers. Tests then use real hooks with only the network faked underneath.

```tsx
// test/render.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'

type Options = { route?: string }

export function renderWithProviders(ui: React.ReactElement, { route = '/' }: Options = {}) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })

  return {
    user: userEvent.setup(),
    ...render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
      </QueryClientProvider>,
    ),
  }
}
```

- Create a new `QueryClient` per render so no cached data leaks between tests.
- `retry: false` stops error-state tests waiting through retries and timing out.
- Add the project's store, theme, and i18n providers here, using real implementations.
- Return a `user` from `userEvent.setup()` so tests do not each set it up.

## 3. Test data factories

If responses are generated from the schema, add small factories for common entities so tests can say `buildProduct({ name: 'A'.repeat(200) })` instead of copying fixtures. Keep defaults realistic and override only what the test is about.

## 4. Time

- Enable fake timers per test, not globally; global fake timers can stall promises and MSW.
- When combining fake timers with `userEvent`, set it up with `userEvent.setup({ advanceTimers: vi.advanceTimersByTime })`.
- If `findBy*` or `waitFor` hangs under fake timers, use `vi.useFakeTimers({ shouldAdvanceTime: true })`.
- Use `vi.setSystemTime(...)` for anything that depends on today's date.

## 5. Mutation testing

Mutation testing changes the code (flips conditions, removes branches) and checks whether any test fails. If the code can be broken while the tests stay green, those tests are not testing anything.

Set up StrykerJS with the Vitest runner:

```json
{
  "testRunner": "vitest",
  "vitest": { "related": true },
  "incremental": true
}
```

Run it on the changed components only, because a full run is slow:

```bash
npx stryker run --mutate "src/components/ProductCard/ProductCard.tsx"
```

Use it as a periodic audit or before merging risky changes, not on every commit.
