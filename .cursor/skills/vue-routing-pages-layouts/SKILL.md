---
name: vue-routing-pages-layouts
description: Guide route definition, page creation, layout composition, and navigation patterns with Vue Router 4 for msg-guest and msg-guide. Use when adding routes, creating pages, modifying auth guards, or handling route-level loading/error states.
---

# Frontend Routing, Pages, and Layouts

## Purpose

Guide route definition, page component creation, layout composition, navigation patterns, and route-level code organization within the Vue Router 4 setup in this repository.

## When to Use

- Adding a new route or page
- Modifying route structure, params, or guards
- Creating or adjusting layouts
- Handling loading, error, or empty states at the page level
- Implementing navigation flows (redirects, auth-gated pages, deep links)
- Adding route-level code splitting or prefetching

## When NOT to Use

- Component extraction within a page — use `frontend-component-architecture`
- API call logic inside a page — use `frontend-state-and-data-fetching`
- Styling-only page changes — use `frontend-styling-tailwind-and-design-system`

## Source Priority Reminder

1. Existing routes in `src/router/index.ts` and page components in `src/views/`
2. Project rules
3. This skill's checklist
4. `VUE3_DEVELOPMENT_STANDARDS.md` (VC1.6, VC1.12, VC1.16)
5. Official docs: [Vue Router 4](https://router.vuejs.org/), [Vue 3](https://vuejs.org/)

## Repository Context

### Router setup

- **File**: `src/router/index.ts`
- **Router**: `createRouter` with `createWebHistory()` (no hash mode)
- **Route-view key**: `App.vue` uses `<router-view :key="route.path" />` to prevent remounting on query param changes while still remounting on path changes

### Route patterns

| Pattern | Example |
|---|---|
| Lazy-loaded views | `component: () => import("@/views/experience-detail.vue")` |
| Props from params | `props: true` on route definition |
| Auth guard | `meta: { requiresAuth: true }` checked in `beforeEach` against Supabase session |
| Prefetch hint | `meta: { prefetch: true }` — used by idle-time prefetching logic |
| 404 catch-all | `path: "/:pathMatch(.*)*"` as the last route |

### Auth guard behavior

- Routes with `meta.requiresAuth` redirect unauthenticated users:
  - `Guides` route redirects to `GuidesPublic`
  - Other protected routes redirect to `Home`
- Auth check uses `supabase.auth.getSession()` (or the Pinia auth store when migrated)

### Route prefetching

- Critical routes (`Home`, `ExperienceDetail`, `SubcategoryView`) are prefetched on idle via `requestIdleCallback`
- After navigating to `Home`/`Catalogue`, the `Guides` route is prefetched after 2s delay

### Page file conventions

- Location: `src/views/`
- Naming: **kebab-case** `.vue` files (e.g., `experience-detail.vue`, `getting-around.vue`)
- Route names: **PascalCase** (e.g., `ExperienceDetail`, `GettingAround`)

### Current route groups

- **Share routes**: `/share/:id`, `/share/:id/subcategory/:subcategoryId`, `/share/:shareId/experience/:experienceId`
- **Preview routes**: `/preview/list/:listid`, `/preview/goto/:gotoListId`, `/preview/template/:templateid`
- **Main routes**: `/`, `/subcategory/:subcategoryId`, `/experience/:id`, `/catalogue`
- **Auth-protected**: `/guides`, `/journey`, `/profile`
- **City routes**: `/getting-around/:city_id`, `/city/:city_id`, `/moving-around/:city_id`, `/discover-more/:city_id`
- **Booking flow**: `/bookings`, `/checkout`, `/success`, `/mbway-timer`

## Implementation Checklist

1. **Add the route definition to `src/router/index.ts`.** Use lazy import: `component: () => import("@/views/new-page.vue")`. Set `props: true` if the route has params.
2. **Create the page component in `src/views/`.** Use kebab-case filename. Use `<script setup lang="ts">`.
3. **Set route name in PascalCase.** The `name` field MUST be unique and PascalCase (e.g., `NewFeature`).
4. **Add auth guard if needed.** Set `meta: { requiresAuth: true }` and verify the `beforeEach` guard handles the redirect path for this route.
5. **Add prefetch hint if the route is high-traffic.** Set `meta: { prefetch: true }` and add the route name to the `criticalRoutes` array in the prefetch logic if warranted.
6. **Handle loading, error, and empty states in the page.** Use `LoadingState`, `ErrorState`, `EmptyState` from `src/components/shared/`. Pages SHOULD show a loading skeleton or state while async data resolves.
7. **Compose the page from shared components.** Pages SHOULD be thin orchestrators that compose shared components and composables. Keep page files under 200 lines.
8. **Place the route in the correct group.** More specific routes MUST come before less specific ones (e.g., `/share/:id/subcategory/:subcategoryId` before `/share/:id`).
9. **Preserve the 404 catch-all as the last route.** `/:pathMatch(.*)*` MUST remain at the end of the routes array.
10. **Test navigation manually.** Confirm the route resolves, params pass correctly, auth redirects work, and back navigation behaves as expected.

## Common Pitfalls

- **Route ordering**: placing a catch-all or less-specific route before a more-specific one, causing the wrong component to render.
- **Missing `props: true`**: forgetting to set `props: true` when the page component expects route params as props, forcing manual `useRoute()` param extraction.
- **Duplicating auth logic**: adding inline session checks in page components instead of relying on the centralized `beforeEach` guard.
- **Heavy page components**: putting all business logic, API calls, and template markup directly in the view instead of extracting to composables and shared components.
- **Forgetting prefetch**: adding a high-traffic route without considering idle-time prefetching.
- **Breaking the `route.path` key**: using `route.fullPath` in `App.vue` would cause remounts on query param changes, breaking frontend-only filtering.

## Output Expectations

- Route definitions MUST use lazy imports.
- Page files MUST be in `src/views/` with kebab-case naming.
- Route names MUST be PascalCase and unique.
- Auth-protected routes MUST use `meta.requiresAuth`.
- The 404 catch-all MUST remain the last route entry.
- Page components SHOULD stay under 200 lines.
