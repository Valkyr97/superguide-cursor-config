---
name: vue-performance
description: Guide render efficiency, lazy loading, code splitting, bundle size, and Vite-specific performance for msg-guest and msg-guide Vue apps. Use when investigating slow renders, optimizing bundles, adding lazy loading, or applying v-memo.
---

# Frontend Performance, Bundle, and Rendering

## Purpose

Guide render efficiency, bundle size management, lazy loading, code splitting, and Vite-specific performance decisions for this Vue 3 mobile-first application.

## When to Use

- Investigating slow renders or unnecessary rerenders
- Adding or optimizing lazy loading (routes, components, images)
- Reducing bundle size
- Deciding whether to memoize or use `v-memo`
- Optimizing list rendering or virtual scrolling
- Improving initial load or navigation performance

## When NOT to Use

- API response caching (data-level) — use `frontend-state-and-data-fetching`
- Styling performance (CSS size) — use `frontend-styling-tailwind-and-design-system`
- Build config changes — use `frontend-config-env-and-tooling`

## Source Priority Reminder

1. Existing performance patterns in `src/composables/usePerformanceMonitoring.ts`, `src/composables/usePerformanceOptimized.ts`, and existing lazy-loading implementations
2. Project rules
3. This skill's checklist
4. `VUE3_DEVELOPMENT_STANDARDS.md` (VC5.x, VC13.21–VC13.28)
5. Official docs: [Vue 3 Performance](https://vuejs.org/guide/best-practices/performance), [Vite Build](https://vite.dev/guide/build)

## Repository Context

### Route-level code splitting

All routes use lazy imports — this is already the standard:
```typescript
component: () => import("@/views/experience-detail.vue")
```

Critical routes are prefetched on idle via `requestIdleCallback` in `src/router/index.ts`:
- `Home`, `ExperienceDetail`, `SubcategoryView`

### Image lazy loading

- `LazyImage.vue` (`src/components/shared/LazyImage.vue`) — custom lazy image component
- `useLazyLoading` composable (`src/composables/useLazyLoading.ts`) — intersection observer-based lazy loading

### Virtual scrolling

- `VirtualScroll.vue` (`src/components/shared/VirtualScroll.vue`) — virtual list rendering for long lists

### Performance monitoring

- `usePerformanceMonitoring` (`src/composables/usePerformanceMonitoring.ts`) — collects performance metrics, generates reports, sends them every 30s from `App.vue`
- `measureCustomMetric()` — measures route change performance
- `generateReport()` / `sendReport()` — periodic performance reporting

### Performance optimization composables

- `usePerformanceOptimized` (`src/composables/usePerformanceOptimized.ts`) — optimized data processing utilities
- `useDebouncedSearch` — debounced search with configurable delay

### Existing optimizations

- `router-view` keyed by `route.path` (not `fullPath`) to prevent remounts on query changes
- `v-memo` used on expensive list items
- Computed properties for derived state
- `onUnmounted` cleanup for event listeners and intervals
- Swiper for carousels (hardware-accelerated)
- `@vueuse/motion` for GPU-accelerated animations
- `OptimizedHome.vue` as a performance-tuned variant of the home page

### Vite build optimization

```typescript
// vite.config.ts
optimizeDeps: {
  include: ['vue']  // Pre-bundle Vue for faster dev startup
}
```

## Implementation Checklist

1. **Use lazy imports for all route components.** Every route in `src/router/index.ts` MUST use `() => import()`. This is already the pattern — do not break it.
2. **Use `v-memo` for expensive list rendering.** When rendering lists where each item involves complex computation or nested components, use `v-memo` with a dependency array of values that actually change.
3. **Use `VirtualScroll.vue` for long lists.** Lists exceeding ~50 items SHOULD use the existing virtual scroll component to avoid rendering off-screen DOM nodes.
4. **Use `LazyImage.vue` for images below the fold.** Images not in the initial viewport SHOULD use the lazy loading component to defer network requests.
5. **Use computed properties over methods in templates.** Template expressions are re-evaluated on every render. Computed properties are cached and only recompute when dependencies change.
6. **Debounce search and filter inputs.** Use `useDebouncedSearch` from `src/composables/usePerformanceOptimized.ts` for search-driven data fetching. Typical debounce: 300ms.
7. **Clean up event listeners and intervals.** Any `addEventListener`, `setInterval`, or `setTimeout` set in `onMounted` MUST be cleaned up in `onUnmounted`.
8. **Avoid unnecessary watchers.** Prefer `computed` over `watch` when the output is a derived value. Use `watch` only when side effects (API calls, DOM manipulation) are needed.
9. **Do not over-memoize.** `v-memo` has a comparison cost. Only apply it when the list item is genuinely expensive to render. For simple text/badge rendering, `v-memo` adds overhead without benefit.
10. **Profile before optimizing.** Use the browser DevTools Performance tab and `usePerformanceMonitoring` to identify actual bottlenecks. Do not optimize speculatively.
11. **Consider prefetching for high-traffic navigation paths.** If adding a new route that users frequently navigate to, add it to the `criticalRoutes` array in `src/router/index.ts` prefetch logic.
12. **Minimize reactive overhead.** Use `shallowRef` for large objects or arrays that are replaced wholesale rather than mutated in place. Use `markRaw` for non-reactive data (e.g., library instances, DOM references).

## Common Pitfalls

- **Inline anonymous functions in `v-for`**: `@click="() => handleClick(item.id)"` creates a new function per render. Extract to a method that receives the item or use a component with props.
- **Watching deeply nested objects without `{ deep: true }`**: missing reactive changes. Conversely, using `{ deep: true }` on large objects when a specific property watcher would suffice — this triggers on any nested change.
- **Forgetting cleanup**: leaving `setInterval` running after component unmount, causing memory leaks and ghost API calls.
- **Eagerly importing heavy components**: using `import HeavyChart from '...'` at the top of a file instead of `defineAsyncComponent(() => import('...'))` for components shown conditionally.
- **Reactive wrapping of static data**: wrapping constant config objects or lookup maps in `ref()` or `reactive()` when they never change. Use `markRaw` or plain objects.
- **Bundle-bloating imports**: importing the entire date-fns or lodash library instead of specific functions (e.g., `import { format } from 'date-fns'` not `import * as dateFns from 'date-fns'`).
- **Re-computing in templates**: repeating the same expression in multiple template locations instead of extracting to a `computed` that evaluates once.

## Output Expectations

- All route components MUST use lazy imports.
- `v-memo` MUST only be applied when profiling shows a measurable benefit.
- Event listeners and timers MUST be cleaned up in `onUnmounted`.
- Images below the fold SHOULD use `LazyImage.vue`.
- Long lists SHOULD use `VirtualScroll.vue`.
- Debouncing MUST be applied to search/filter inputs that trigger API calls.
- Performance claims MUST be backed by profiling evidence, not speculation.
