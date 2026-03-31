---
name: vue-state-and-data-fetching
description: Guide API consumption, client-side data flow, Pinia stores for global state, composables for local async state, and caching for msg-guest and msg-guide. Use when making API calls, creating stores or data composables, adding caching, or managing loading/error states.
---

# Frontend State and Data Fetching

## Purpose

Guide API consumption, client-side data flow, global state management with Pinia, local async state with composables, caching, and request handling.

## When to Use

- Making API calls from the frontend
- Creating or modifying a Pinia store for global state
- Creating or modifying a composable that manages async data
- Designing client-side data flow for a feature
- Deciding whether state belongs in a store or a composable
- Adding caching or request deduplication
- Handling loading, error, and success states for data operations

## When NOT to Use

- Form validation logic — use `frontend-forms-validation-and-user-input`
- Component structure decisions — use `frontend-component-architecture`
- Performance optimization unrelated to data fetching — use `frontend-performance-bundle-and-rendering`

## Source Priority Reminder

1. Existing stores in `src/stores/`, composables in `src/composables/`, and API modules in `src/lib/`
2. Project rules (especially `api-rules.mdc` for endpoint patterns)
3. This skill's checklist
4. `VUE3_DEVELOPMENT_STANDARDS.md` (VC3.x, VC8.x, VC13.29–VC13.36)
5. Official docs: [Vue 3 Reactivity](https://vuejs.org/guide/essentials/reactivity-fundamentals), [Pinia](https://pinia.vuejs.org/core-concepts/), [VueUse](https://vueuse.org/)

## Repository Context

### API layer

| Module | Import | Auth | Base URL env var |
|---|---|---|---|
| Authenticated API | `callApi` from `@/lib/api` or `useApi()` composable | Supabase bearer token (automatic) | `VITE_API_ENDPOINT` |
| Public API (guest) | `callPublicApi` from `@/lib/api-public` or `usePublicApi()` | None | `VITE_PUBLIC_API_ENDPOINT` |

Both return `ApiResponse<T>` with `{ data, status, statusText, headers }`. Errors from the server are returned in the same shape (not thrown) when the HTTP response exists. Network errors are thrown.

### API helpers

- `extractArrayFromResponse(response)` — extract array data from API response (`src/lib/api-utils.ts`)
- `extractItemFromResponse(response)` — extract single item from API response (`src/lib/api-utils.ts`)

### State architecture

This repository uses **two complementary patterns**:

| Pattern | When | Location |
|---|---|---|
| **Pinia stores** | Global state shared across 3+ components/views, domain entities, persistent state | `src/stores/` |
| **Composables** | Local/feature state, single-view data fetching, UI state, temporary data | `src/composables/` |

**Decision rule (KISS)**: if state is consumed and/or mutated by multiple unrelated components across different views, use a Pinia store. Otherwise, use a composable.

### Pinia store pattern (setup stores)

```typescript
// src/stores/city.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { callPublicApi } from '@/lib/api-public'
import type { City } from '@/types'

export const useCityStore = defineStore('city', () => {
  const currentCity = ref<City | null>(null)
  const cities = ref<City[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const cityName = computed(() => currentCity.value?.name ?? '')

  async function fetchCities() {
    loading.value = true
    error.value = null
    try {
      const response = await callPublicApi<City[]>('/cities', 'GET')
      cities.value = response.data
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
    } finally {
      loading.value = false
    }
  }

  function setCurrentCity(city: City) {
    currentCity.value = city
    localStorage.setItem('currentCityId', city.id)
  }

  return { currentCity, cities, loading, error, cityName, fetchCities, setCurrentCity }
})
```

### Composable pattern (local/feature state)

```typescript
// src/composables/useFeatureName.ts
export function useFeatureName() {
  const data = ref<T[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const fetchData = async () => {
    loading.value = true
    error.value = null
    try {
      const response = await callPublicApi<T[]>("/endpoint", "GET")
      data.value = response.data
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Unknown error"
    } finally {
      loading.value = false
    }
  }

  return { data: computed(() => data.value), loading, error, fetchData }
}
```

### Global state modules

| Module | Current location | Target location | Provides |
|---|---|---|---|
| Auth | `src/lib/auth-context.ts` | `src/stores/auth.ts` | user, loading, isAuthenticated, signIn, signUp, signOut, OTP |
| City | `src/lib/city-context.ts` | `src/stores/city.ts` | currentCity, cities, loading, setCurrentCity, fetchCities |
| List editing | `src/lib/list-edit-store.ts` | `src/stores/list-edit.ts` | List editing state with localStorage persistence |

> **Migration**: existing singleton modules in `src/lib/` should be migrated to Pinia stores when next modified. New global state MUST use Pinia from the start.

### Caching composables

| Composable | Location | Purpose |
|---|---|---|
| `useApiCache` | `src/composables/useEnhancedApiCache.ts` | Basic API response caching with TTL |
| `useEnhancedApiCache` | `src/composables/useEnhancedApiCache.ts` | Enhanced caching with configurable TTL via `CACHE_CONFIGS` |
| `useGlobalCache` | `src/composables/useGlobalCache.ts` | Global shared cache across composable instances |
| `useCacheWarming` | `src/composables/useEnhancedApiCache.ts` | Pre-warm cache for anticipated data needs |

### Key data composables (reference)

- `useExperiences` — experience list fetching and filtering
- `useCityData` — city information and related data
- `useFilters` / `useFiltersApi` — filter state and API-driven filter options
- `useReferenceData` — shared reference data (categories, tags, etc.)
- `useLatestSharedList` — latest shared list data
- `useHomeSubcategories` — home page subcategory data

## Implementation Checklist

1. **Decide: store or composable.** Apply the KISS decision rule. Global state shared across views → Pinia store in `src/stores/`. Local data or single-view fetching → composable in `src/composables/`.
2. **Choose the correct API function.** Use `callPublicApi` for guest/unauthenticated endpoints (`/api-public`). Use `callApi` or `useApi().callApi` for authenticated endpoints (`/api`). Check `api-rules.mdc` for endpoint conventions.
3. **Follow the correct pattern.** Pinia stores use `defineStore` with setup syntax. Composables use `useXxx` functions. Both MUST expose `loading`, `error`, and data.
4. **Type the API response.** Define or reuse types in `src/types/index.ts`. Use the generic `callPublicApi<T>()` or `callApi<T>()` for typed responses.
5. **Handle all three states.** Every store/composable that fetches data MUST expose `loading`, `error`, and the data ref. Components MUST render `LoadingState`, `ErrorState`, or `EmptyState` accordingly.
6. **Use try/catch/finally.** Set `loading = true` before the call, reset in `finally`. Catch errors and set the `error` ref. Do not let unhandled promise rejections propagate.
7. **Use caching when appropriate.** For frequently accessed, infrequently changing data, use `useApiCache` or `useEnhancedApiCache` with an appropriate TTL from `CACHE_CONFIGS`. Do not cache user-specific mutable data without invalidation.
8. **Avoid scattered fetch logic.** API calls MUST NOT appear directly in component templates or inline in `onMounted` without a composable/store. Centralize data fetching.
9. **Debounce search inputs.** Use `useDebouncedSearch` from `src/composables/usePerformanceOptimized.ts` or VueUse's `useDebounceFn` for search-driven API calls.
10. **Reuse existing stores and composables.** Check `src/stores/` and `src/composables/index.ts` for existing exports before creating new data-fetching logic. Extend rather than duplicate.
11. **Keep files focused.** One store per domain. One composable per data concern. If a file grows beyond ~150 lines, split into sub-modules.

## Common Pitfalls

- **Using `callApi` for guest endpoints**: guest/public routes use `callPublicApi` (no auth header). Using `callApi` will fail without a session.
- **Forgetting `finally` block**: leaving `loading` stuck at `true` when an error occurs.
- **Not typing the generic**: calling `callPublicApi("/endpoint")` without `<T>` returns `unknown`, losing type safety downstream.
- **Fetching in components directly**: scattering `axios.get()` or `callApi()` calls inside `<script setup>` instead of extracting to a store or composable.
- **Over-caching mutable data**: caching user-specific state (bookmarks, profile) without invalidation logic, leading to stale UI.
- **Ignoring error response shape**: `callApi`/`callPublicApi` return error responses in the same `ApiResponse` shape (not thrown). Check `response.status` — a 400/500 response is not an exception.
- **Duplicating existing modules**: creating `useCities` when `useCityStore`/`useCityData` already exists, or `useSearch` when `useDebouncedSearch` is available.
- **Overusing stores when a composable suffices**: creating a Pinia store for state only used by one component. Apply KISS — use a composable instead.
- **Using Options stores instead of Setup stores**: this codebase uses Composition API everywhere. Pinia stores MUST use setup syntax (`defineStore('name', () => { ... })`) for consistency.

## Output Expectations

- All API calls MUST go through `callApi` or `callPublicApi` — never raw `axios` or `fetch`.
- Global shared state MUST use Pinia stores in `src/stores/`.
- Local/feature state MUST use composables in `src/composables/`.
- Both stores and composables MUST expose `loading`, `error`, and data.
- Pinia stores MUST use setup syntax for Composition API consistency.
- Types MUST be defined in `src/types/index.ts` or a feature-specific type file in `src/types/`.
- Caching decisions MUST be justified (what is cached, TTL, invalidation strategy).
- No unhandled promise rejections.
