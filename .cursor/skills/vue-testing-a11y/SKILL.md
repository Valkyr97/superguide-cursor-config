---
name: vue-testing-a11y
description: Guide frontend testing with Vitest and Vue Testing Library, accessibility practices, and error reporting for msg-guest and msg-guide. Use when writing tests, adding a11y attributes, or working with error boundaries and diagnostics.
---

# Frontend Testing, Accessibility, and Observability

## Purpose

Guide frontend test implementation, accessibility practices, error reporting, and diagnostic tooling using this repository's Vitest + Vue Testing Library setup.

## When to Use

- Writing or updating tests for components, composables, or views
- Adding accessibility attributes or improving keyboard/screen-reader support
- Working with error boundaries or error reporting
- Adding diagnostic hooks or observability for UI failures
- Reviewing test coverage or test quality

## When NOT to Use

- API-level error handling (response shape, retries) — use `frontend-state-and-data-fetching`
- Component extraction purely for testability — use `frontend-component-architecture`
- Backend test writing — out of scope

## Source Priority Reminder

1. Existing tests in `src/test/`, `src/composables/__tests__/`, `src/components/shared/__tests__/`, `src/views/__tests__/`
2. Project `TESTING.md` document
3. This skill's checklist
4. `VUE3_DEVELOPMENT_STANDARDS.md` (VC7.x, VC13.37–VC13.44)
5. Official docs: [Vitest](https://vitest.dev/guide/), [Vue Testing Library](https://testing-library.com/docs/vue-testing-library/intro), [Testing Library queries](https://testing-library.com/docs/queries/about)

## Repository Context

### Test stack

| Tool | Version | Purpose |
|---|---|---|
| `vitest` | 0.34.6 | Test runner and assertion library |
| `@testing-library/vue` | 6.6.1 | Component rendering with user-centric queries |
| `@testing-library/jest-dom` | 5.17.0 | Custom DOM matchers (`toBeVisible`, `toHaveTextContent`, etc.) |
| `@testing-library/user-event` | 13.5.0 | Realistic user interaction simulation |
| `@vue/test-utils` | 2.4.6 | Vue-specific mount/wrapper utilities |
| `jsdom` | 22.1.0 | DOM environment for tests |
| `@vitest/coverage-v8` | — | Code coverage via V8 |

### Test configuration

- **Config file**: `vitest.config.ts`
- **Setup file**: `src/test/setup.ts` — registers jest-dom matchers, mocks router and VueUse
- **Test commands**:
  - `npm test` — run tests in watch mode
  - `npm run test:run` — single run
  - `npm run test:watch` — explicit watch mode
  - `npm run test:coverage` — run with coverage report

### Test file conventions

| Test type | Location | Naming |
|---|---|---|
| Component tests | `src/components/shared/__tests__/` | `component-name.test.ts` |
| Composable tests | `src/composables/__tests__/` | `useComposableName.test.ts` |
| View/integration tests | `src/views/__tests__/` | `view-name.test.ts` |
| Test utilities | `src/test/utils/test-utils.ts` | — |
| API mocks | `src/test/mocks/api.ts` | — |
| Integration tests | `src/test/__tests__/` | `integration.test.ts` |

### Test utilities

- `mountWithRouter(component, options)` — mounts a component with a configured Vue Router instance (`src/test/utils/test-utils.ts`)
- `createMockCard(overrides)` — creates mock card/experience data for tests

### Error reporting and observability

| Module | Location | Purpose |
|---|---|---|
| `useErrorReporting` | `src/composables/useErrorReporting.ts` | Error capture and reporting composable |
| `setupErrorReporting(app)` | `src/composables/useErrorReporting.ts` | Global Vue error handler setup (called in `main.ts`) |
| `errorReporter` | `src/composables/useErrorReporting.ts` | Singleton error reporter instance |
| `usePerformanceMonitoring` | `src/composables/usePerformanceMonitoring.ts` | Performance metric collection and reporting |

### Feedback state components

| Component | Location | Purpose |
|---|---|---|
| `ErrorState.vue` | `src/components/shared/ErrorState.vue` | Standard error display with optional retry |
| `LoadingState.vue` | `src/components/shared/LoadingState.vue` | Standard loading spinner/skeleton |
| `EmptyState.vue` | `src/components/shared/EmptyState.vue` | Standard empty data display |

### Coverage targets (from `TESTING.md`)

| Metric | Target |
|---|---|
| Statements | > 80% |
| Branches | > 75% |
| Functions | > 80% |
| Lines | > 80% |

## Implementation Checklist

### Testing

1. **Place tests next to the code they test.** Use `__tests__/` directories adjacent to the source: `src/composables/__tests__/`, `src/components/shared/__tests__/`, `src/views/__tests__/`.
2. **Name test files consistently.** Use `{source-name}.test.ts` matching the source file name (kebab-case for views, camelCase for composables).
3. **Use Vue Testing Library for component tests.** Prefer `render()` from `@testing-library/vue` and query by accessible roles/labels (`getByRole`, `getByLabelText`, `getByText`) over implementation-detail queries (`querySelector`, wrapper internals).
4. **Use `mountWithRouter` for routed components.** Views and components that use `useRoute` or `useRouter` MUST be mounted via the test utility in `src/test/utils/test-utils.ts`.
5. **Use `@testing-library/user-event` for interactions.** Simulate clicks, typing, and keyboard events through `userEvent` for realistic behavior (focus, blur, input events).
6. **Mock API calls and stores.** Use `vi.mock()` to mock `@/lib/api` and `@/lib/api-public`. Return typed mock responses. See `src/test/mocks/api.ts` for existing mock patterns. For Pinia stores, use `createTestingPinia()` from `@pinia/testing` to provide mock stores — see [Pinia Testing](https://pinia.vuejs.org/cookbook/testing).
7. **Test the three states.** For data-dependent components, test: loading state renders `LoadingState`, error state renders `ErrorState`, empty data renders `EmptyState`, populated data renders correctly.
8. **Test user flows, not implementation.** Assert on visible output (text, elements, navigation) rather than internal state. Tests SHOULD survive internal refactors.
9. **Add regression tests for bugs.** When fixing a bug, add a test that reproduces the failure before applying the fix.
10. **Run tests after changes.** Execute `npm run test:run` to verify all tests pass. Check coverage with `npm run test:coverage` for files you modified.

### Accessibility

11. **Use semantic HTML.** Prefer `<button>`, `<nav>`, `<main>`, `<section>`, `<article>`, `<header>` over generic `<div>` elements.
12. **Add `aria-label` to icon-only buttons.** Any button or link with no visible text MUST have an `aria-label`.
13. **Use `aria-invalid` and `aria-describedby` on form fields.** Connect error messages to their fields for screen reader support.
14. **Ensure keyboard navigability.** All interactive elements MUST be reachable and operable via keyboard. Use `tabindex` only when necessary; prefer native focusable elements.
15. **Use `role="alert"` for dynamic error/success messages.** This ensures screen readers announce state changes.

### Observability

16. **Use `ErrorState.vue` for recoverable errors.** Do not build custom error UIs — use the existing shared component that supports retry actions.
17. **Use `setupErrorReporting`/`useErrorReporting` for unhandled errors.** The global error handler is already configured in `main.ts`. For component-specific error reporting, use the `useErrorReporting` composable.
18. **Log meaningful context in error reports.** When catching errors in composables, include the operation name and relevant identifiers (route, entity ID) so errors are diagnosable.

## Common Pitfalls

- **Testing implementation details**: asserting on internal ref values, computed cache, or component instance methods instead of user-visible behavior.
- **Forgetting to mock the router**: components using `useRoute()` or `useRouter()` will fail without `mountWithRouter`. Raw `mount()` from Vue Test Utils does not provide router context.
- **Not awaiting async operations**: forgetting `await nextTick()` or `await flushPromises()` after triggering async actions, leading to assertions running before the DOM updates.
- **Snapshot over-reliance**: using snapshot tests as the primary assertion for complex components. Snapshots break on any markup change and provide low signal. Use them selectively for stable UI primitives.
- **Skipping error state tests**: testing only the happy path. Every component consuming async data SHOULD have tests for loading, error, and empty states.
- **Inaccessible custom elements**: building custom dropdowns, modals, or toggles without proper ARIA roles, breaking screen reader and keyboard support. Use Radix Vue primitives which handle this by default.
- **Missing cleanup in tests**: not cleaning up after tests that add global event listeners or modify global state, causing test pollution.

## Output Expectations

- Tests MUST be placed in `__tests__/` directories adjacent to the source.
- Component tests MUST use Vue Testing Library with accessible queries.
- Routed components MUST use `mountWithRouter`.
- API calls MUST be mocked — tests MUST NOT make real HTTP requests.
- All three data states (loading, error, populated) SHOULD be tested for async components.
- Accessibility attributes MUST be present on interactive and form elements.
- `ErrorState.vue` / `LoadingState.vue` / `EmptyState.vue` MUST be used for feedback states.
