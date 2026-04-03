# FareHarbor Lightframe integration

This document lives at **`docs/fareharbor-lightframe/README.md`** (SuperGuide **monorepo root**). The guest app implementation is under **`msg-guest/`**.

Single reference to **restore the correct setup** if the in-page overlay stops working or starts sending users to the top-level `fareharbor.com` site.

**Out of scope:** database schema, `booking_system_*` columns, supplier rows in Supabase.

---

## 1. Symptom

“Check availability” / embed actions open **FareHarbor in the top window** instead of the **Lightframe overlay** on the same page (often on touch devices or narrow viewports).

---

## 2. Root cause (what the embed script expects)

1. **DOM shell** with these ids (same structure FareHarbor’s script creates internally):
   - `#fareharbor-lightframe`
   - `#fareharbor-lightframe-shade`
   - `#fareharbor-lightframe-loading`  
   If the root `#fareharbor-lightframe` is missing, the script’s internal logic can fall back to **`window.top.location`** instead of the overlay.

2. **Script URL query params** so Lightframe is allowed when the script would otherwise prefer full navigation:
   - `autolightframe=yes`
   - `lightframe=always` (important on touch / small width)

Official doc: [FareHarbor Lightframe API](https://fareharbor.com/help/website/resources/lightframe-api/).

---

## 3. `msg-guest/index.html` — exact shape to replicate

Place **before** `#app` (current order: lightframe shell → `#app` → FareHarbor script → swiper → Vite app):

```html
<!-- Required for in-page Lightframe: embed.js falls back to window.top.location if #fareharbor-lightframe is missing (same shell ids as FareHarbor’s own markup). See docs/fareharbor-lightframe/README.md (repo root). -->
<div id="fareharbor-lightframe">
  <div id="fareharbor-lightframe-shade"></div>
  <div id="fareharbor-lightframe-loading" aria-busy="true"></div>
</div>
<div id="app"></div>
<!-- FareHarbor embeds API — keep one script tag; official: https://fareharbor.com/help/website/resources/lightframe-api/ -->
<!-- lightframe=always: allows iframe overlay on touch / narrow viewports; without it the script may navigate the top window. -->
<script src="https://fareharbor.com/embeds/api/v1/?autolightframe=yes&amp;lightframe=always"></script>
```

- Use `&amp;` in HTML for `&` inside the `src` URL.
- Load this script **once** per page.

### Query parameters

| Param | Role |
|--------|------|
| `autolightframe=yes` | Prefer opening booking UI in Lightframe when applicable. |
| `lightframe=always` | Avoid falling back to top-level navigation on touch / viewport constraints. |

---

## 4. Booking widget code (same user flow, not the frame DOM)

FareHarbor snippets often include placeholders like `[experience_id]` (mixed case). The following is **documented behavior**; keep it aligned with this file if you change the Vue code.

### 4.1 `msg-guest/src/components/shared/experience-detail/ExperienceBookingButton.vue`

- **`resolvedFull`:** template + `bookingSystemData` + `buildIdentifierSubstitutions(bookingSystemIdentifier)` — **includes** `<script>` tags.
- **`resolvedHtml`:** same as `resolvedFull` but with `<script>…</script>` removed for `v-html` (scripts are injected once via `useBookingWidget`).
- **`canShowWidget`:** `false` if no resolved HTML, if `bookingSystemIdentifier == null`, or if **any** `\[[A-Za-z0-9_]+\]` remains in **`resolvedFull`** (check the full string so placeholders inside `data-config` are not missed).
- Wrapper: `ref="bookingWidgetWrapperRef"`, `style="display:block"` — works together with the observer below if a third-party script toggles `display`.

### 4.2 `msg-guest/src/composables/useBookingWidget.ts`

- After `resolveTemplate`, **do not** call `injectScript` if `/\[[A-Za-z0-9_]+\]/` matches the resolved HTML (same rule as the button).
- **`buildIdentifierSubstitutions`:** supports a JSON string, a plain string fallback (`BOOKING_SYSTEM_IDENTIFIER`), and a **runtime object** when the API returns parsed JSON while TypeScript still types the field as `string`.
- **`MutationObserver` + `restoreWrapper`:** if the wrapper or its first child gets `display: none` via inline style (some embeds do this), force `display: block` with `!important`. If you verify your embed never does this, you could remove this block — only do so after testing.

---

## 5. Quick verification checklist

- [ ] `#fareharbor-lightframe` and two child divs exist in `msg-guest/index.html` as above.
- [ ] Script `src` includes `autolightframe=yes` and `lightframe=always`.
- [ ] Placeholder guard uses `\[[A-Za-z0-9_]+\]` on the **fully** resolved HTML in both the button and the composable.
- [ ] `bookingSystemIdentifier` is non-null before showing the widget block.
