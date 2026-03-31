---
name: vue-config-env-tooling
description: Guide safe modifications to VITE_* env vars, Vite config, TypeScript config, Tailwind config, and related frontend tooling for msg-guest and msg-guide. Use when adding env variables, modifying build config, or changing tooling settings.
---

# Frontend Config, Environment, and Tooling

## Purpose

Guide safe modifications to Vite configuration, TypeScript configuration, Tailwind configuration, `VITE_*` environment variables, and related frontend tooling files.

## When to Use

- Adding, renaming, or removing a `VITE_*` environment variable
- Modifying `vite.config.ts` (plugins, aliases, build options)
- Modifying `tailwind.config.js` (content paths, theme, plugins)
- Modifying `tsconfig.json`, `tsconfig.app.json`, or `tsconfig.node.json`
- Updating `components.json` (shadcn-vue settings)
- Adding or updating PostCSS plugins
- Changing `vitest.config.ts` test configuration

## When NOT to Use

- Tailwind class usage in components — use `frontend-styling-tailwind-and-design-system`
- Performance-related build tuning — use `frontend-performance-bundle-and-rendering`
- Backend environment variables (non-`VITE_`) — out of scope for the frontend agent

## Source Priority Reminder

1. Existing config files in the repository root
2. Project rules
3. This skill's checklist
4. `VUE3_DEVELOPMENT_STANDARDS.md` (VC10.x)
5. Official docs: [Vite Config](https://vite.dev/config/), [TypeScript](https://www.typescriptlang.org/tsconfig/), [Tailwind Config](https://tailwindcss.com/docs/configuration)

## Repository Context

### Environment files

| File | Purpose |
|---|---|
| `.env` | Default/local development environment |
| `.env.dev` | Dev deployment environment |

Both files contain `VITE_*` prefixed variables (exposed to the browser) and non-`VITE_` variables (backend/server-only, out of scope).

### Current `VITE_*` variables

| Variable | Purpose |
|---|---|
| `VITE_SUPABASE_URL` | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase anonymous/public key (browser-safe) |
| `VITE_API_ENDPOINT` | Authenticated API base URL |
| `VITE_PUBLIC_API_ENDPOINT` | Public (guest) API base URL |
| `VITE_UPLOADS_CDN` | CDN URL for uploaded assets |
| `VITE_PUBLIC_URL` | Public-facing app URL |
| `VITE_MODE` | Application mode identifier |
| `VITE_GOOGLE_MAPS_API_KEY` | Google Maps API key (browser-safe public key) |

### Type declarations

- `src/vite-env.d.ts` — Vite client type reference
- `vue-shims.d.ts` — Vue SFC module declarations

New `VITE_*` variables SHOULD be typed in `src/vite-env.d.ts` via `ImportMetaEnv` interface augmentation.

### Vite config (`vite.config.ts`)

```typescript
export default defineConfig({
  css: {
    postcss: {
      plugins: [tailwind(), autoprefixer()],
    },
  },
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  define: {
    global: 'globalThis',  // Polyfill for libraries expecting Node global
  },
  optimizeDeps: {
    include: ['vue']
  }
})
```

PostCSS is inline in the Vite config — there is no separate `postcss.config.js`.

### TypeScript config

- `tsconfig.json` — project references file (references `tsconfig.app.json` + `tsconfig.node.json`)
- `tsconfig.app.json` — app source config, extends `@vue/tsconfig/tsconfig.dom.json`, strict mode, path alias `@/*` -> `./src/*`
- `tsconfig.node.json` — node/build tool config (covers `vite.config.ts`)

### Tailwind config (`tailwind.config.js`)

- Content paths: `./pages/**`, `./components/**`, `./app/**`, `./src/**` (`.ts`, `.tsx`, `.vue`)
- Dark mode: `class` strategy
- Plugin: `tailwindcss-animate`
- Custom theme: font families, CSS variable-based colors, border radius, animations

### shadcn-vue config (`components.json`)

```json
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

## Implementation Checklist

1. **Only `VITE_*` variables are in scope.** Do not add, modify, or reference non-`VITE_` environment variables. Those belong to the backend.
2. **Never put secrets in `VITE_*` variables.** All `VITE_*` values are embedded in the client bundle and visible in the browser. Only public/browser-safe values (anon keys, public API URLs, CDN URLs) belong here. Secret keys, service role keys, and API secrets MUST NOT be prefixed with `VITE_`.
3. **Add new `VITE_*` variables to both `.env` and `.env.dev`.** Provide a sensible default or placeholder in `.env` and the correct dev value in `.env.dev`.
4. **Type new env variables.** Augment the `ImportMetaEnv` interface in `src/vite-env.d.ts`:
   ```typescript
   interface ImportMetaEnv {
     readonly VITE_NEW_VARIABLE: string
   }
   ```
5. **Config changes MUST be minimal and justified.** Do not reorganize config files for style. Only change what the task requires. Explain why the change is needed.
6. **Preserve the `@` path alias.** The `@` -> `./src` alias is used throughout the codebase. Do not remove or rename it.
7. **Preserve inline PostCSS.** PostCSS plugins are configured inside `vite.config.ts`. Do not extract to a separate `postcss.config.js` unless there is a specific technical need.
8. **Do not change TypeScript strictness.** `strict: true` is set in `tsconfig.app.json`. Do not relax it. Additional strict options (`noUnusedLocals`, `noUnusedParameters`, `noFallthroughCasesInSwitch`) MUST also be preserved.
9. **Tailwind content paths MUST cover `src/`.** If adding components outside `src/`, add the corresponding content path to `tailwind.config.js`.
10. **Test after config changes.** Run `npm run dev` to verify the dev server starts. Run `npm run build` to verify the production build succeeds. Run `npm test` to verify tests pass.

## Common Pitfalls

- **Exposing secrets as `VITE_*`**: adding a Supabase service role key or OpenAI API key with the `VITE_` prefix. These are visible in the browser and must never be exposed.
- **Missing env in one file**: adding a variable to `.env` but not `.env.dev` (or vice versa), causing inconsistent behavior across environments.
- **Breaking the `@` alias**: modifying `resolve.alias` in Vite config or `paths` in `tsconfig.app.json` without updating the other, causing import resolution failures.
- **Adding unnecessary Vite plugins**: adding plugins that duplicate existing functionality (e.g., a separate PostCSS config file when inline PostCSS is already configured).
- **Relaxing TypeScript checks**: disabling `strict` mode or removing `noUnusedLocals` to suppress warnings instead of fixing the underlying code.
- **Modifying `tsconfig.json` directly**: this file only contains project references. Compiler options belong in `tsconfig.app.json` (for app code) or `tsconfig.node.json` (for build tools).

## Output Expectations

- Only `VITE_*` variables are created or modified.
- No secrets in `VITE_*` values.
- New env variables MUST appear in both `.env` and `.env.dev` and be typed in `src/vite-env.d.ts`.
- Config changes MUST be minimal, justified, and tested.
- The `@` path alias, TypeScript strict mode, and inline PostCSS setup MUST be preserved.
