---
name: vue-styling-tailwind
description: Guide Tailwind CSS usage, CVA variants, design tokens, and visual consistency for msg-guest and msg-guide Vue apps. Use when styling components, creating variants, working with design tokens, or resolving class conflicts.
---

# Frontend Styling, Tailwind, and Design System

## Purpose

Guide styling decisions, Tailwind usage, design-system alignment, and visual consistency across the Vue 3 guest application using the established shadcn-vue + CVA + Tailwind CSS stack.

## When to Use

- Styling a new component or modifying existing styles
- Creating or extending component variants
- Working with design tokens (colors, spacing, typography, border radius)
- Ensuring visual consistency across views
- Adding animations or transitions
- Resolving Tailwind class conflicts or overrides

## When NOT to Use

- Component structure decisions — use `frontend-component-architecture`
- Performance concerns about CSS/rendering — use `frontend-performance-bundle-and-rendering`
- Tailwind config file changes — use `frontend-config-env-and-tooling`

## Source Priority Reminder

1. Existing styling patterns in `src/components/ui/`, `src/components/shared/`, `src/assets/index.css`
2. Project rules (especially `mobile-first.mdc`: always mobile-first)
3. This skill's checklist
4. `VUE3_DEVELOPMENT_STANDARDS.md` (VC2.13–VC2.18, VC13.13–VC13.20)
5. Official docs: [Tailwind CSS](https://tailwindcss.com/docs), [Radix Vue](https://www.radix-vue.com/), [CVA](https://cva.style/docs), [Tailwind Merge](https://github.com/dcastil/tailwind-merge)

## Repository Context

### Styling stack

| Library | Version | Purpose |
|---|---|---|
| `tailwindcss` | 3.4.17 | Utility-first CSS framework |
| `tailwindcss-animate` | 1.0.7 | Animation utilities (accordion, collapsible transitions) |
| `class-variance-authority` (CVA) | 0.7.1 | Type-safe component variant definitions |
| `clsx` | 2.1.1 | Conditional class joining |
| `tailwind-merge` | 2.5.5 | Intelligent Tailwind class deduplication |

### Class merging utility

```typescript
// src/lib/utils.ts
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

`cn()` MUST be used whenever merging dynamic or conditional classes to prevent Tailwind conflicts.

### Design tokens (from `tailwind.config.js`)

**Colors** — CSS variable-based (shadcn-vue pattern):
- Semantic: `background`, `foreground`, `card`, `popover`, `primary`, `secondary`, `muted`, `accent`, `destructive`
- Utility: `border`, `input`, `ring`
- All defined as `hsl(var(--token-name))` for theme support

**Typography** — Custom font families:
- `font-wix` — Wix Madefor Text (primary body font)
- `font-handwritten` — Reenie Beanie (decorative/cursive)

**Border radius** — CSS variable-based:
- `rounded-lg`, `rounded-md`, `rounded-sm` mapped to `--radius` variable

**Animations** — Keyframes defined for:
- `accordion-down` / `accordion-up`
- `collapsible-down` / `collapsible-up`

**Container** — Centered with 2rem padding, max-width 1400px at 2xl, min 320px at xsm

### Dark mode

- Configured as `darkMode: ["class"]` in Tailwind config
- Toggled via `dark` class on root element

### shadcn-vue component configuration

```json
// components.json
{
  "style": "default",
  "typescript": true,
  "tailwind": {
    "config": "tailwind.config.js",
    "css": "src/assets/index.css",
    "baseColor": "slate",
    "cssVariables": true
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils"
  }
}
```

### CVA pattern (used in UI primitives)

```typescript
import { cva, type VariantProps } from "class-variance-authority"

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  }
)
```

### Global styles

- Base CSS: `src/assets/index.css` — imports Tailwind layers, defines CSS custom properties for the color system
- Scoped styles: `<style scoped>` in individual components when needed

## Implementation Checklist

1. **Use Tailwind utility classes as the primary styling method.** Avoid writing custom CSS unless a utility does not exist.
2. **Mobile-first always.** Write base styles for mobile, then layer responsive overrides with `sm:`, `md:`, `lg:` prefixes. This is a hard project rule.
3. **Use `cn()` for all dynamic class merging.** Never manually concatenate Tailwind class strings. Always import from `@/lib/utils`.
4. **Use CVA for component variants.** Any UI primitive in `src/components/ui/` with multiple visual states MUST define variants using CVA. Export the `VariantProps` type for consumers.
5. **Use semantic color tokens.** Refer to `bg-primary`, `text-foreground`, `border-border`, etc. — not raw hex or HSL values. These tokens respect theming and dark mode.
6. **Use design-system spacing and sizing.** Use Tailwind's scale (`p-4`, `gap-2`, `h-10`) instead of arbitrary values (`p-[17px]`). Arbitrary values are acceptable only when no Tailwind token matches and the value is design-intentional.
7. **Keep class lists readable.** For components with many classes, group by concern: layout/positioning first, then sizing, then colors, then typography, then interactions. Use line breaks in templates for long class strings.
8. **Use `tailwindcss-animate` for standard animations.** Leverage existing keyframes (`accordion-down`, `collapsible-down`) rather than defining new ones. Add new keyframes to `tailwind.config.js` only when existing ones are insufficient.
9. **Scoped styles for edge cases only.** Use `<style scoped>` when Tailwind utilities cannot achieve the desired effect (e.g., complex pseudo-element styling, third-party widget overrides).
10. **Prefer `font-wix` for body text.** Use `font-handwritten` sparingly for decorative elements only.

## Common Pitfalls

- **String concatenation instead of `cn()`**: writing `` `${baseClass} ${condition ? 'px-4' : 'px-2'}` `` instead of `cn(baseClass, condition ? 'px-4' : 'px-2')`. The string approach breaks when Tailwind classes conflict.
- **Desktop-first responsive styles**: writing `lg:hidden` + base visible instead of base hidden + `lg:block`. Mobile-first means the base (no prefix) targets the smallest screen.
- **Arbitrary values everywhere**: using `p-[13px]` when `p-3` (12px) or `p-3.5` (14px) would work. Arbitrary values make the design inconsistent.
- **Hardcoded colors**: using `bg-blue-500` instead of `bg-primary` or `text-gray-900` instead of `text-foreground`. Hardcoded colors break theming.
- **Duplicate variant logic**: recreating button/card/badge variants inline instead of extending the existing CVA definitions in `src/components/ui/`.
- **Missing dark mode consideration**: styling only the light appearance when `darkMode: ["class"]` is configured. Semantic tokens handle this automatically — avoid overriding them with raw colors.
- **Forgetting `tailwind-merge`**: stacking conflicting utilities like `p-4 p-2` without `cn()`, which leaves both in the output.

## Output Expectations

- All styling MUST use Tailwind utilities as the default approach.
- `cn()` MUST be used for any dynamic or conditional class merging.
- CVA MUST be used for UI primitive variants.
- Semantic color tokens MUST be used over raw color values.
- All layouts MUST be mobile-first.
- Arbitrary values SHOULD be avoided unless no token matches and the value is intentional.
- Custom CSS (`<style scoped>`) SHOULD be used only when Tailwind cannot achieve the desired result.
