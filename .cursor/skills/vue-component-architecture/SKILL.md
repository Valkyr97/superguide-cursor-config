---
name: vue-component-architecture
description: Guide creation, extraction, and composition of Vue 3 components within the three-tier system (ui primitives, shared domain, views) for msg-guest and msg-guide. Use when creating, refactoring, or extracting components, designing props/emits, or splitting god components.
---

# Frontend Component Architecture

## Purpose

Guide the creation, extraction, and composition of Vue 3 components within this repository's three-tier component system: UI primitives (`src/components/ui/`), shared domain components (`src/components/shared/`), and page-level views (`src/views/`).

## When to Use

- Creating a new component
- Extracting a sub-component from a large file
- Refactoring component boundaries or responsibilities
- Deciding where a component belongs (ui vs shared vs views)
- Designing props, emits, or slot interfaces
- Breaking down a god component

## When NOT to Use

- Pure styling changes with no structural impact — use `frontend-styling-tailwind-and-design-system`
- Route or layout changes — use `frontend-routing-pages-and-layouts`
- State management or API integration logic — use `frontend-state-and-data-fetching`

## Source Priority Reminder

1. Existing component patterns in `src/components/` and `src/views/`
2. Project rules (especially `keep-files-short.mdc`: aim for < 200 lines)
3. This skill's checklist
4. `VUE3_DEVELOPMENT_STANDARDS.md` (VC1.x, VC2.x, VC9.x, VC13.x standards)
5. Official docs: [Vue 3](https://vuejs.org/guide/components/registration), [Radix Vue](https://www.radix-vue.com/), [shadcn-vue](https://www.shadcn-vue.com/)

## Repository Context

### Component tiers

| Tier | Location | Purpose | Naming |
|---|---|---|---|
| UI primitives | `src/components/ui/{name}/` | Generic, reusable, headless-style components (shadcn-vue + Radix Vue). Each has `index.ts` barrel export. | PascalCase directory, PascalCase `.vue` |
| Shared domain | `src/components/shared/` | Business-specific reusable components (cards, carousels, modals, filters). May have sub-folders for complex features (e.g., `tour-details/`). | PascalCase `.vue` |
| Views (pages) | `src/views/` | Route-level page components. Compose shared and UI components. | kebab-case `.vue` |

### Key libraries and patterns

- **Composition API**: all components use `<script setup lang="ts">`
- **Props**: `defineProps<T>()` with TypeScript interfaces
- **Emits**: `defineEmits<T>()`
- **Variants**: `class-variance-authority` (CVA) for UI component variants — see `src/components/ui/button/` for reference
- **Class merging**: `cn()` from `src/lib/utils.ts` (clsx + tailwind-merge)
- **Slots**: typed, documented, used for composition in UI primitives
- **Global components**: `gb-flag` (FlagIcon) registered globally in `main.ts`

### Existing shared components (reference)

- `Card.vue`, `CardSkeleton.vue` — card rendering with skeleton loading
- `Carousel.vue`, `DynamicCarousel.vue`, `ImageCarousel.vue` — swiper-based carousels
- `BottomSheet.vue`, `SearchSheet.vue`, `TourDetailSheet.vue` — drawer/sheet patterns
- `ErrorState.vue`, `LoadingState.vue`, `EmptyState.vue` — standard feedback states
- `LazyImage.vue` — image lazy loading
- `VirtualScroll.vue` — virtual scrolling for long lists
- `ExperienceDialog.vue`, `ExperienceOverlayCard.vue` — experience display patterns
- `tour-details/` — `CheckAvailability.vue`, `DatePicker.vue`, `Payment.vue`, `PeopleCounter.vue`, etc.

## Implementation Checklist

1. **Identify the tier.** Determine if the component is a UI primitive, shared domain component, or view. Place it accordingly.
2. **Check for existing components.** Search `src/components/` and `src/views/` before creating anything new. Reuse or extend existing components when possible.
3. **Single responsibility.** Each component MUST have one clear responsibility. If the template or script exceeds ~200 lines, extract sub-components or composables.
4. **Use `<script setup lang="ts">`.** No Options API. All reactive state typed with `ref<T>()` or `computed<T>()`.
5. **Define typed props and emits.** Use `defineProps<T>()` and `defineEmits<T>()` with explicit TypeScript interfaces. Avoid overly broad prop types.
6. **Prefer composition over inheritance.** Use slots, composables, and render composition rather than deep component hierarchies.
7. **UI primitives MUST be headless-compatible.** Follow the existing shadcn-vue pattern: Radix Vue for behavior, Tailwind + CVA for styling, `cn()` for class merging.
8. **Shared components SHOULD handle their own loading/error/empty states** using `LoadingState.vue`, `ErrorState.vue`, `EmptyState.vue` from `src/components/shared/`.
9. **Barrel exports for UI components.** Every `src/components/ui/{name}/` directory MUST have an `index.ts` that re-exports the component(s).
10. **Props flow down, events flow up.** Do not mutate props. Use `defineEmits` for parent communication. For deep state sharing, use Pinia stores (global domain state) or composables/provide-inject (local subtree state) — see `frontend-state-and-data-fetching` skill.
11. **Keep templates readable.** Extract complex conditional logic into computed properties. Avoid inline functions in `v-for` loops.
12. **Mobile-first always.** Every component MUST render correctly on mobile viewports as the primary target.

## Common Pitfalls

- **God components**: views in `src/views/` accumulating business logic, API calls, and complex templates. Extract composables and sub-components early.
- **Prop drilling**: passing data through 3+ component levels. Use Pinia stores for global state or provide/inject for local subtree state instead.
- **Duplicating UI primitives**: creating a new button/card/dialog variant instead of extending the existing shadcn-vue component with CVA variants.
- **Missing barrel exports**: adding a UI component without updating its `index.ts`, causing inconsistent import paths.
- **Inline anonymous functions in templates**: creating new function instances on every render inside `v-for`. Extract to named methods or computed properties.
- **Ignoring existing feedback components**: building custom loading/error states instead of using the shared `LoadingState.vue`/`ErrorState.vue`/`EmptyState.vue`.

## Output Expectations

- New components MUST follow the tier placement and naming conventions.
- Component files SHOULD stay under 200 lines.
- Props and emits MUST be typed with explicit TypeScript interfaces.
- CVA MUST be used for UI primitive variants, not conditional class strings.
- `cn()` MUST be used for merging Tailwind classes.
- No placeholder or stub implementations.
