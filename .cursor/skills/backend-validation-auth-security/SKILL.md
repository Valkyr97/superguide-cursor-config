---
name: backend-validation-auth-security
description: >
  Implement authentication checks, authorization/ownership verification, input
  validation, and security hardening. Use when building endpoints that require
  auth, handle user-controlled input, or need ownership checks.
---

# Backend Validation, Auth, and Security

## When to use

- Endpoint requires authentication (most endpoints).
- Endpoint modifies a resource that belongs to a specific user/guide.
- Endpoint accepts complex or user-controlled input.
- Reviewing an endpoint for security gaps.

## When NOT to use

- Public endpoint using `@public_api()` that does not need auth.
- Simple read endpoint with no user-specific data.

## Auth check (required for most endpoints)

See [backend-invariants.mdc](.cursor/rules/backend-invariants.mdc) (Handler contract). You MUST check auth explicitly:

```python
@klug()
def lambda_handler(event, context):
    user_id = event.user_id()
    if not user_id:
        return event.error_response(401, 'Authentication required')
    # ... rest of handler
```

`@public_api()` is for endpoints that intentionally do not require auth. Never call identity methods in `@public_api()` handlers.

## Identity methods

| Method | Returns | Source |
|---|---|---|
| `event.email()` | User email or `None` | `requestContext.authorizer.email` |
| `event.user_id()` | User ID (UUID) or `None` | `authorizer.user_id` or `authorizer.sub` |
| `event.sub()` | Supabase `sub` claim or `None` | `authorizer.sub` |
| `event.get_guide_id()` | Guide ID or `None` | Queries `guides` table by `user_id` |

`event.get_guide_id()` makes a Supabase query. Cache the result if you call it multiple times.

## Authorization / ownership checks

For guide-owned resources:

```python
guide_id = event.get_guide_id()
if not guide_id:
    return event.error_response(403, 'Only guides can perform this action')

response = event.supabase.table("lists").select("id, guide_id").eq("id", list_id).execute()
if not response.data:
    return event.error_response(404, 'List not found')

if response.data[0]['guide_id'] != guide_id:
    return event.error_response(403, 'You do not own this list')
```

Never trust a client-provided `guide_id` or `user_id` in the request body for authorization decisions. Always derive it from the auth context.

## Input validation order

Validate in this sequence. Return early on first failure.

1. **Auth** -> 401 if missing
2. **Required parameters** -> 400 if missing
3. **Format** (UUIDs, types) -> 400 if invalid
4. **Entity existence** -> 404 if not found
5. **Ownership / authorization** -> 403 if not allowed
6. **Business rules** -> 400 or 409 as appropriate

## Validation helpers

```python
# Required fields on body
is_valid, error_msg = event.validate_required_fields(body, ['name', 'city_id'])
if not is_valid:
    return event.error_response(400, error_msg)

# UUID format
if not event.validate_uuid(city_id, 'city_id'):
    return event.error_response(400, 'Invalid city_id format')

# Batch UUID validation
uuid_error = event.validate_uuid_params({'city_id': city_id, 'tag_id': tag_id}, ['city_id', 'tag_id'])
if uuid_error:
    return uuid_error

# Required params (path/query)
param_error = event.validate_required_params({'id': record_id}, ['id'])
if param_error:
    return param_error
```

## Input sanitization

- **Strings:** Use `normalize_name()` for entity names (lowercase, collapse spaces, trim).
- **UUIDs:** Always validate with `event.validate_uuid()`.
- **SQL:** Never pass user input to `Event.select()` without parameterization. Prefer Supabase client queries.
- **S3 keys:** Never use user-provided strings as S3 key components. Use `uuid.uuid4()`.
- **Cache keys:** Never include raw user input in cache keys. Use validated IDs only.

## Secrets

- Access via `os.environ.get(...)`.
- AWS Secrets Manager for sensitive credentials.
- Never log tokens, passwords, or full auth headers.
- Never log the full request body if it might contain credentials.

## Common mistakes

- Assuming `@klug()` checks auth (it does not).
- Trusting `body.get('guide_id')` for authorization instead of `event.get_guide_id()`.
- Returning 404 instead of 403 when the user does not own the resource (leaks existence info).
- Forgetting to validate UUIDs on query parameters (not just path params).
- Passing user-controlled strings into raw SQL or cache keys.

## Definition of done

- Auth checked explicitly if endpoint requires it (401 on missing).
- Ownership verified for user-specific resources (403 on mismatch).
- No user input in SQL strings, S3 keys, or cache keys without sanitization.
- Validation follows the priority order (auth -> required -> format -> existence -> ownership -> business).
