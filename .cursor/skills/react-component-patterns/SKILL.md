---
name: react-component-patterns
description: Guide React 19 component patterns, page structure, shared components, and UI conventions for msg-marketplace (Kloud). Use when creating pages, building components, or implementing UI patterns in the marketplace admin app.
---

# React Component Patterns (Marketplace / Kloud)

## Purpose

Guide component architecture, page structure, and UI conventions for the msg-marketplace React 19 + Vite + TypeScript + Tailwind CSS admin application.

## When to Use

- Creating a new page or view in msg-marketplace
- Building or extracting components
- Implementing UI patterns (forms, tables, dialogs)
- Deciding component structure and file organization

## When NOT to Use

- Backend API work -> use `backend-endpoint-crud` or related backend skills
- Vue frontend work (msg-guest/msg-guide) -> use `vue-component-architecture`

## Repository Context

### Tech Stack

- React 19 + React Router 7 + Vite 6 + TypeScript
- Tailwind CSS 4 with `@tailwindcss/vite`
- Radix UI React for accessible primitives
- shadcn components in `src/components/ui/`
- react-hook-form + Zod for forms
- axios via `callApi()` for API calls
- sonner for toast notifications

### File Organization

| Concern | Location |
|---|---|
| Pages/views | `src/pages/` |
| Shared components | `src/components/` |
| UI primitives (shadcn) | `src/components/ui/` |
| Auth components | `src/components/auth/` |
| Hooks | `src/lib/hooks/` |
| Utilities | `src/lib/` |
| Tests | `src/components/__tests__/`, `src/lib/__tests__/` |

### UI Patterns

- All UI components use shadcn (Radix UI + Tailwind).
- Buttons calling endpoints MUST show a loading state.
- Destructive operations MUST show a confirmation dialog.
- Backend interaction feedback via sonner toasts.

## Implementation Checklist

1. **Place files correctly.** Pages in `src/pages/`, components in `src/components/`, hooks in `src/lib/hooks/`.
2. **Create React Router mapping** when adding a new page.
3. **Check for existing components** in `src/components/ui/` and `src/components/` before creating new ones.
4. **Use TypeScript strictly.** Props typed with interfaces, no `any` types.
5. **Use react-hook-form + Zod** for all forms.
6. **Use shadcn UI primitives** for buttons, inputs, dialogs, etc.
7. **Add loading states** to all buttons that trigger API calls.
8. **Add confirmation dialogs** to all destructive operations.
9. **Use sonner toasts** for success/error notifications after API calls.
10. **Keep files under 300 lines.** Extract sub-components and hooks when approaching the limit.

## Common Pitfalls

- Missing loading states on API-calling buttons.
- Missing confirmation on delete/destructive actions.
- Not using shadcn primitives (building custom inputs/buttons).
- Putting all logic in a single page component instead of extracting hooks and sub-components.
- Using `fetch` or raw `axios` instead of `callApi()`.

## Output Expectations

- Pages MUST be in `src/pages/` with React Router mappings.
- Components MUST use shadcn UI primitives.
- Forms MUST use react-hook-form + Zod.
- API buttons MUST have loading states.
- Destructive actions MUST have confirmation dialogs.
- Toast notifications MUST use sonner.
