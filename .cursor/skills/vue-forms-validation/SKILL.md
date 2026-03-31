---
name: vue-forms-validation
description: Guide form implementation, Zod validation, field state, and submission handling for msg-guest and msg-guide Vue apps. Use when building forms, adding validation rules, handling submission flows, or improving form UX feedback.
---

# Frontend Forms, Validation, and User Input

## Purpose

Guide form implementation, field validation, submission handling, and user input UX using this repository's Zod + manual ref-based pattern.

## When to Use

- Building a new form or input flow
- Adding or modifying validation rules
- Handling form submission (with or without API call)
- Designing multi-step input sequences (e.g., booking flow: date -> people -> payment)
- Improving form UX feedback (errors, loading, success)

## When NOT to Use

- API call logic beyond the submission itself — use `frontend-state-and-data-fetching`
- Component structure of form elements — use `frontend-component-architecture`
- Styling form inputs — use `frontend-styling-tailwind-and-design-system`

## Source Priority Reminder

1. Existing form patterns in `src/views/checkout.vue`, `src/components/shared/tour-details/Payment.vue`, `src/components/shared/SignUpModal.vue`
2. Project rules
3. This skill's checklist
4. `VUE3_DEVELOPMENT_STANDARDS.md` (VC6.8, VC8.12, VC13.47)
5. Official docs: [Zod](https://zod.dev/), [Vue 3 Forms](https://vuejs.org/guide/essentials/forms)

## Repository Context

### Validation library

- **Zod** (`zod` 3.24.1) for schema validation
- No form library (no VeeValidate, no FormKit). Forms use manual `ref()` + `reactive()` state.

### Established form pattern

```typescript
// Schema definition
const formSchema = z.object({
  email: z.string().email("Invalid email"),
  phone: z.string().min(9, "Invalid phone number"),
})

// State
const form = reactive({ email: "", phone: "" })
const formErrors = ref<Record<string, string>>({})
const isSubmitting = ref(false)

// Validation
const validateForm = (): boolean => {
  try {
    formSchema.parse(form)
    formErrors.value = {}
    return true
  } catch (e) {
    if (e instanceof z.ZodError) {
      formErrors.value = Object.fromEntries(
        e.errors.map((err) => [err.path[0], err.message])
      )
    }
    return false
  }
}

// Submission
const handleSubmit = async () => {
  if (!validateForm()) return
  isSubmitting.value = true
  try {
    await callApi("/endpoint", "POST", form)
  } finally {
    isSubmitting.value = false
  }
}
```

### Key form components

| Component | Location | Purpose |
|---|---|---|
| `FloatingInput.vue` | `src/components/shared/tour-details/FloatingInput.vue` | Text input with floating label animation |
| `CountryCodeSelect.vue` | `src/components/shared/CountryCodeSelect.vue` | Phone country code selector with flag icons |
| `PeopleCounter.vue` | `src/components/shared/tour-details/PeopleCounter.vue` | Increment/decrement counter for guest count |
| `DatePicker.vue` | `src/components/shared/tour-details/DatePicker.vue` | Date selection for bookings |
| `LanguageSelector.vue` | `src/components/shared/tour-details/LanguageSelector.vue` | Tour language preference picker |
| UI input | `src/components/ui/input/` | Base input primitive (shadcn-vue) |
| UI label | `src/components/ui/label/` | Base label primitive (shadcn-vue) |

### Form flows in the codebase

- **Checkout flow** (`src/views/checkout.vue`): email + phone validation with Zod, payment method selection
- **Payment flow** (`Payment.vue`): card number, expiry, CVV validation with regex patterns; MBWay phone validation
- **Sign-up modal** (`SignUpModal.vue`): OTP-based authentication
- **Booking selection** (`CheckAvailability.vue`): date/people/language selection stored in `localStorage` before navigating to `/bookings`

## Implementation Checklist

1. **Define a Zod schema for all validated fields.** Place the schema at the top of the `<script setup>` or extract to a shared file in `src/lib/` if reused across components.
2. **Use `reactive()` for form state and `ref()` for errors.** Follow the established pattern: `const form = reactive({...})`, `const formErrors = ref<Record<string, string>>({})`.
3. **Validate before submission.** Call `validateForm()` at the start of `handleSubmit()`. Return early if invalid. Never send unvalidated data to the API.
4. **Map Zod errors to field-level messages.** Use `e.errors.map(err => [err.path[0], err.message])` to populate `formErrors`. Display errors adjacent to the relevant field.
5. **Show real-time feedback.** PREFER validating on blur or on change for critical fields (email, phone). At minimum, clear field-level errors when the user corrects the input.
6. **Track submission state.** Use `isSubmitting` ref to disable the submit button and show a loading indicator during API calls.
7. **Use existing input components.** Use `FloatingInput.vue` for text fields when a floating-label style is needed. Use the base `Input` from `src/components/ui/input/` for simpler cases.
8. **Guard against double submission.** Disable the submit button or return early in `handleSubmit` when `isSubmitting.value` is true.
9. **Use `@submit.prevent` on form elements.** Prevent default form submission. Handle everything in the `handleSubmit` function.
10. **Provide accessible error markup.** Use `aria-invalid="true"` on invalid fields and `role="alert"` on error messages. Connect them with `aria-describedby`.
11. **Store intermediate state in `localStorage` only when the flow spans multiple pages** (like the booking flow in `CheckAvailability.vue`). For single-page forms, keep state in reactive refs.

## Common Pitfalls

- **Skipping validation before API call**: sending raw user input to `callApi`/`callPublicApi` without running the Zod schema first.
- **Not clearing errors on correction**: displaying stale error messages after the user fixes the input. Clear the specific field error on input/blur.
- **Missing `isSubmitting` guard**: allowing the user to spam the submit button and fire multiple API requests.
- **Mixing validation approaches**: using regex in some places and Zod in others for the same kind of data. PREFER Zod for all new validation. Regex is acceptable only for specialized formats (card numbers, CVV) where Zod `.regex()` would be equivalent.
- **Forgetting `@submit.prevent`**: letting the browser submit the form and reload the page.
- **Over-validating on every keystroke**: running the full Zod schema on every `input` event. PREFER blur-based or debounced validation for complex schemas.
- **Exposing secrets in form payloads**: never include tokens, keys, or other secrets in frontend form submissions. Auth headers are handled by the API layer.

## Output Expectations

- All form validation MUST use Zod schemas.
- Form state MUST use `reactive()` for the data and `ref()` for `formErrors` and `isSubmitting`.
- Validation MUST occur before any API call.
- Error messages MUST be displayed per-field, not only as a generic toast.
- Submit buttons MUST be disabled during submission.
- Accessible attributes (`aria-invalid`, `aria-describedby`, `role="alert"`) SHOULD be present on validated fields and error messages.
