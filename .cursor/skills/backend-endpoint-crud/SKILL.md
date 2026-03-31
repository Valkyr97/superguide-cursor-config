---
name: backend-endpoint-crud
description: >
  Build simple CRUD endpoints in api/. Covers handler structure, parameter access,
  validation flow, response format, and Event CRUD helpers. Use when creating or
  editing single-table GET, POST, PUT, or DELETE endpoints.
---

# Backend Endpoint CRUD

## When to use

- Creating a new endpoint file (`get.py`, `post.py`, `put.py`, `delete.py`) in `api/`.
- Editing an existing simple endpoint that operates on one table.
- The endpoint does not involve joins, bulk relationship writes, or file uploads.

## When NOT to use

- Endpoint requires PostgREST embeds or joins across tables -> use [backend-joins-and-read-models](.cursor/skills/backend-joins-and-read-models/SKILL.md).
- Endpoint writes to junction/relationship tables -> use [backend-write-operations](.cursor/skills/backend-write-operations/SKILL.md).
- Endpoint handles S3/file uploads -> use [backend-file-upload-and-media](.cursor/skills/backend-file-upload-and-media/SKILL.md).

## Checklist

Work through these steps in order. Do not skip any.

1. **Place the file correctly.** The folder path under `api/` determines the URL. Match the naming convention of the surrounding resource tree (hyphens if siblings use hyphens, underscores for new top-level resources).
2. **Write the handler skeleton.**
3. **Auth check** (if required): verify `event.user_id()` or `event.sub()` is not `None`.
4. **Extract parameters:** path, query, body.
5. **Validate inputs:** required fields, UUID format, entity existence.
6. **Execute the operation** via Supabase.
7. **Return the result** directly (success) or via `event.error_response()` (error).
8. **Follow file discipline** — new files aim for ~200 lines (see [backend-invariants.mdc](.cursor/rules/backend-invariants.mdc) File discipline).

## Handler skeleton

```python
from main import *
from decorators import klug

@klug()
def lambda_handler(event, context):
    """Brief description of what this endpoint does."""
    # implementation
```

## Parameter access reference

| Need | Method | On missing |
|---|---|---|
| Path param (required) | `event.path("id")` | Raises `PathParameterError` (caught by @klug -> 500) |
| Query param (required) | `event.query("city_id")` | Raises `QueryParameterError` |
| Query param (optional) | `event.safe_query("city_id")` | Returns `None` |
| Query with type coercion | `event.safe_query_param("limit", 50, int)` | Returns default |
| Full body | `event.body()` | Raises `BadJsonError` on invalid JSON |
| Body field (optional) | `event.safe_body_param("name", default="")` | Returns default |

## Validation flow for POST/PUT

```python
body = event.body()

is_valid, error_msg = event.validate_required_fields(body, ['name', 'city_id'])
if not is_valid:
    return event.error_response(400, error_msg)

if not event.validate_uuid(body['city_id'], 'city_id'):
    return event.error_response(400, 'Invalid city_id format')

response = event.supabase.table("cities").select("id").eq("id", body['city_id']).execute()
if not response.data:
    return event.error_response(404, 'City not found')
```

Use a direct Supabase query for existence checks instead of `event.get_by_id()` when you need to distinguish "not found" from "query failed".

## Validation flow for GET with path param

```python
record_id = event.path("id")
if not event.validate_uuid(record_id, "id"):
    return event.error_response(400, 'Invalid ID format')

response = event.supabase.table("my_table").select("*").eq("id", record_id).execute()
if not response.data:
    return event.error_response(404, 'Record not found')

return response.data[0]
```

## Event CRUD helpers

For simple cases where you do not need to distinguish failure from empty:

```python
records = event.get_all("tags", filters={"city_id": city_id}, order_by="name")
record = event.get_by_id("experiences", record_id)
created = event.create_record("suppliers", {"name": name, "city_id": city_id})
updated = event.update_record("tags", tag_id, {"name": new_name})
deleted = event.delete_record("categories", category_id)
```

These return `None`/`[]`/`False` on BOTH "not found" and "query error". Use direct queries when the distinction matters.

## Response format

**Success:** return data directly. `@klug` wraps it in a 200.
```python
return response.data[0]    # single record
return response.data        # list
```

**Error:** always use `event.error_response()`.
```python
return event.error_response(400, 'Name is required')
return event.error_response(404, 'Experience not found')
return event.error_response(500, 'Failed to create', error=str(e), include_traceback=True)
```

Status codes: 400 (bad input), 401 (no auth), 403 (forbidden), 404 (not found), 409 (conflict), 500 (server error).

## Exception handling

`@klug` catches unhandled exceptions and returns a 500 with traceback. You do NOT need a blanket `try/except`. Use `try/except` only when you want a domain-specific error message:

```python
try:
    result = some_external_call()
except SomeSpecificError as e:
    return event.error_response(500, 'External service failed', error=str(e), include_traceback=True)
```

## Common mistakes

- Forgetting to validate UUIDs from path parameters.
- Using `event.get_by_id()` for an existence check before a write, then returning 404 when the actual problem was a Supabase error.
- Wrapping the entire handler in `try/except Exception` when `@klug` already does this.
- Creating the file in a folder with underscores when siblings use hyphens (or vice versa).

## Definition of done

- Reuse first: existing code was reviewed before writing; no duplicated logic.
- File discipline followed (see backend-invariants).
- Handler uses `@klug()` (or `@public_api()` for public endpoints).
- All path/query UUIDs are validated.
- Required fields are checked on POST/PUT.
- Auth is verified explicitly if the endpoint requires it.
- Success returns data directly.
