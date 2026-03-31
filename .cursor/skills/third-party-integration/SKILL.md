---
name: third-party-integration
description: Documentation-driven workflow for integrating external APIs, SDKs, widgets, and provider-specific flows (Ventrata, Bokun, others). Use when integrating any third-party service, embedding widgets, or consuming external APIs from the frontend.
---

# Third-Party Integration

## Purpose

Handle frontend integrations with third-party providers using provided documentation links and repository-compatible patterns. This skill defines a documentation-driven workflow for integrating external APIs, SDKs, widgets, scripts, and provider-specific frontend flows.

## When to Use

- Integrating an external provider's widget, SDK, or API into the frontend
- Adding a checkout, booking, availability, or payment flow from a third-party
- Injecting external scripts or embedding iframes
- Consuming a third-party REST API from the browser
- Handling authentication handoffs, callback events, or webhook-adjacent frontend flows
- Adapting an existing integration to a new provider

## When NOT to Use

- Internal API consumption (`callApi`/`callPublicApi`) — use `frontend-state-and-data-fetching`
- General component architecture without a third-party concern — use `frontend-component-architecture`
- Styling provider UI — use `frontend-styling-tailwind-and-design-system`

## Source Priority Reminder

1. Existing integration patterns in the repository (see Reference Implementation below)
2. Project rules
3. This skill's workflow
4. Provider documentation (see Documentation Registry below)
5. Official library/framework docs (Vue, Vite)
6. General best-practice guidance — only when docs are silent

**Never guess undocumented third-party behavior.** If the provider docs do not confirm an API shape, config option, or initialization step, state the gap explicitly.

## Supported Providers (Examples)

- **Ventrata** — checkout widget, booking flow, availability
- **Bokun** — booking/availability integration

This skill applies to any external provider integration, not only the ones listed above.

## Third-Party Documentation Registry

<!-- EDITABLE: Add, update, or remove provider documentation links below. -->

| Provider | Documentation URLs |
|---|---|
| Ventrata | https://support.ventrata.com/en/ |
|  | https://support.ventrata.com/en/collections/9417674-web-checkout |
| Bokun | https://docs.bokun.io/en/ |
<!-- Add new providers here:
| ProviderName | https://docs.example.com/ |
|  | https://docs.example.com/api-reference |
-->

## Reference Implementation: Ventrata

The repository already contains a Ventrata integration in `src/views/experience-detail.vue`. This serves as the reference pattern for script-injected widget integrations:

**Pattern summary:**
- Supplier detection: `experience.value?.supplier?.name === "Boost Group"` triggers the Ventrata flow
- Config: `ventrataCheckoutConfig` computed property produces a JSON config with `productID` and `referrer`
- Script injection: a `watch` on `isBoost` dynamically creates a `<script>` element pointing to `https://cdn.checkout.ventrata.com/v3/production/ventrata-checkout.min.js`
- Widget binding: a `<button ventrata-checkout :data-config="ventrataCheckoutConfig">` element renders the checkout widget
- API key: passed via `script.dataset.config` with an `apiKey` field

**What to reuse from this pattern:**
- Conditional script loading based on a data flag
- Dynamic `data-config` binding for widget configuration
- Guard against duplicate script injection (`document.getElementById(scriptId)`)

**What to improve in new integrations:**
- Extract integration logic into a dedicated composable (e.g., `useVentrataCheckout`) rather than inlining in the view
- Move the API key to a `VITE_*` environment variable if it is browser-safe/public
- Isolate provider-specific UI into a dedicated component in `src/components/shared/`

## Required Workflow

When implementing a third-party integration, follow these steps in order:

### Step 1: Identify the integration scope

Determine the provider and the desired frontend integration outcome:
- Widget embed
- SDK initialization
- REST API consumption from the browser
- Checkout / booking / availability flow
- Script injection
- Iframe / embed adaptation
- Authentication handoff
- Callback / event handling
- Webhook-adjacent frontend callback

### Step 2: Read the provider documentation

Before proposing any implementation details, read the relevant documentation URLs from the registry above. If the URLs are not in the registry, request them from the user.

### Step 3: Extract integration facts from the docs

Summarize the following from the provider documentation:

- **Installation method**: script tag, npm package, CDN, or API-only
- **Required script or package**: exact URL or package name
- **Auth model**: API key, OAuth, bearer token, or none
- **Public vs secret keys**: which keys are browser-safe and which MUST stay server-side
- **Environment variable needs**: new `VITE_*` variables required
- **Request/response shapes**: for REST API integrations
- **Required headers**: API key headers, content-type, CORS
- **CORS constraints**: whether the provider allows direct browser requests
- **Widget/embed initialization**: script loading order, config attributes, DOM requirements
- **Callback/event model**: custom events, postMessage, callbacks
- **Localization/currency/date**: any locale, currency, or date format requirements
- **Sandbox/test mode**: how to use a test environment during development
- **Error and retry behavior**: how the provider reports errors
- **Frontend-visible limitations**: rate limits, browser support, feature restrictions

If any of these are not documented, explicitly state what is unknown and what assumptions are being made.

### Step 4: Inspect current repository patterns

Before implementing, check:
- `src/components/shared/` for existing provider components
- `src/composables/` for existing provider composables
- `src/lib/` for existing API adapters or service modules
- `src/views/` for existing pages that integrate with providers
- `.env` and `.env.dev` for existing `VITE_*` variables related to the provider
- `src/types/index.ts` for existing provider-related types

### Step 5: Design the integration boundary

Design the integration to fit the repository architecture:

| Concern | Where to place |
|---|---|
| Provider service/adapter | `src/lib/{provider-name}.ts` — initialization, config, API client |
| Composable | `src/composables/use{ProviderFeature}.ts` — reactive state, loading, error |
| Component | `src/components/shared/{ProviderWidget}.vue` — UI wrapper |
| Page integration | `src/views/{page}.vue` — compose the above |
| Types | `src/types/index.ts` or `src/types/{provider}.ts` |
| Env variables | `.env`, `.env.dev`, `src/vite-env.d.ts` |

### Step 6: Implement with isolation

- **Isolate provider-specific logic** in dedicated files. Provider code MUST NOT leak across unrelated components or composables.
- **Use an adapter pattern** when the provider's API shape differs from the app's internal data model. Transform provider data at the boundary.
- **Script injection MUST be guarded** against duplicates (check by element ID before inserting).
- **Dynamic imports for heavy SDKs** — if the provider package is large, use `defineAsyncComponent` or dynamic `import()` to avoid bloating the initial bundle.

### Step 7: Handle secrets correctly

- **VITE_* variables are public.** Only browser-safe values (public API keys, widget IDs, public endpoints) may use the `VITE_` prefix.
- **Secret/private keys MUST NOT appear in frontend code or `VITE_*` variables.** If the integration requires a secret key, it MUST be handled by the backend API, and the frontend should call the backend endpoint.
- **Explicitly warn** if a provider's docs show a "secret key" or "private key" — confirm whether the integration can work with only the public key before proceeding.

### Step 8: Handle incomplete documentation

If the provider docs are incomplete or ambiguous:
- State what is confirmed from the docs
- State what is missing
- State what assumptions are being made, clearly labeled as `[ASSUMPTION]`
- Do not fabricate SDK methods, API endpoints, or config options

### Step 9: Keep changes minimal and reversible

- PREFER isolated files that can be removed without affecting unrelated features
- PREFER feature flags or supplier-based conditionals (like the existing `isBoost` pattern) to enable/disable integrations
- Do not modify shared utilities or base components to accommodate a single provider

### Step 10: Verify the integration

- Confirm the widget/SDK loads without console errors
- Confirm the auth/config values are picked up from env variables
- Confirm the integration renders correctly on mobile (mobile-first rule)
- Confirm cleanup on component unmount (remove injected scripts, event listeners)
- Confirm the integration degrades gracefully when the provider is unavailable

## Common Pitfalls

- **Exposing secret keys in `VITE_*` variables**: treating all provider keys as public. Always check the provider docs to distinguish public vs secret keys.
- **Inlining integration logic in views**: putting script injection, config computation, event handling, and UI all in a single view file. Extract to composable + component.
- **Not guarding duplicate script injection**: loading the same external script multiple times on navigation, causing duplicate widget instances or errors.
- **Assuming CORS is allowed**: making direct browser requests to a provider API that requires server-side calls. Check CORS headers before implementing client-side fetching.
- **Fabricating SDK methods**: inventing method names or config options not found in the provider docs. If unsure, state the gap.
- **Tight coupling**: importing provider-specific types or logic in generic components, making it impossible to swap or remove the provider later.
- **Missing mobile testing**: provider widgets may not be mobile-responsive by default. Test on mobile viewports.
- **Forgetting cleanup**: not removing injected `<script>` elements or event listeners when the component unmounts, causing memory leaks or ghost interactions.

## Output Expectations

- **Direct references to provider docs used** — cite the specific page or section that informed the implementation
- **Explicit listing of new `VITE_*` variables** — name, purpose, and whether the value is browser-safe
- **Exact files to create or modify** — with paths
- **Concise explanation of the integration boundary** — which file does what
- **No invented SDK methods** — every method, config option, or endpoint must trace to documentation
- **No speculative endpoints** — unless clearly labeled as `[ASSUMPTION]` with justification
- **Provider logic isolated** in dedicated files, not spread across the codebase
- **Cleanup on unmount** for any injected scripts, DOM elements, or event listeners
