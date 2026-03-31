---
name: backend-tests-and-observability
description: >
  Add backend tests and improve logging/observability. Use when creating tests
  for endpoints or shared layer, or when improving error logging and request tracing.
---

# Backend Tests and Observability

## When to use

- Writing tests for new or existing endpoints.
- Writing tests for shared layer utilities.
- Improving logging in an endpoint or shared module.
- Adding request tracing or error context.
- Investigating 500s, timeouts, integration failures.

## When NOT to use

- Building an endpoint (use the appropriate endpoint skill, then come here for tests).
- Frontend testing.

## Test structure

Tests mirror the `api/` structure:

```
tests/
  api/
    experiences/
      test_get.py
      test_post.py
      __id__/
        test_get.py
        test_put.py
        test_delete.py
  layers/
    shared/
      test_event.py
      test_helpers.py
      entities/
        test_experience.py
```

Use `pytest` as the runner.

## Testing an endpoint

### Setup: mock the Event

```python
import pytest
from unittest.mock import MagicMock, patch

def make_event(path_params=None, query_params=None, body=None, user_id=None, email=None):
    """Create a mock Event for testing."""
    event = MagicMock()
    event.path = MagicMock(side_effect=lambda name: (path_params or {}).get(name))
    event.query = MagicMock(side_effect=lambda name: (query_params or {}).get(name))
    event.safe_query = MagicMock(side_effect=lambda name, default=None: (query_params or {}).get(name, default))
    event.body = MagicMock(return_value=body or {})
    event.user_id = MagicMock(return_value=user_id)
    event.sub = MagicMock(return_value=user_id)
    event.email = MagicMock(return_value=email)
    event.validate_uuid = MagicMock(side_effect=lambda v, n: bool(v and len(v) == 36))
    event.error_response = MagicMock(side_effect=lambda code, msg, **kw: {'statusCode': code, 'body': {'error': msg}, 'message': msg})
    event.validate_required_fields = MagicMock(side_effect=lambda body, fields: (
        (True, None) if all(body.get(f) for f in fields) else (False, f"Required field '{next(f for f in fields if not body.get(f))}' is missing")
    ))
    event.supabase = MagicMock()
    event.cache = MagicMock()
    event.request_id = MagicMock(return_value='test-request-id')
    return event
```

### Test validation paths

```python
def test_post_missing_required_field():
    event = make_event(body={'city_id': 'some-uuid-value-here-36chars!'})
    from api.experiences.post import lambda_handler
    # The handler will call event.validate_required_fields
    # which will detect 'name' is missing
```

### Test success paths

```python
def test_get_returns_record():
    event = make_event(path_params={'id': 'a' * 36})
    mock_response = MagicMock()
    mock_response.data = [{'id': 'a' * 36, 'name': 'Test'}]
    event.supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
    # Call handler and assert result
```

## Test priority

1. **Input validation** — missing fields, invalid UUIDs, nonexistent entities.
2. **Response shape** — correct keys, types, status codes.
3. **Business logic** — calculations, filtering, transformations.
4. **Edge cases** — empty lists, null fields, boundary values.

## Observability minimum

The codebase uses `print()` for logging (known debt). For new code, make prints useful:

### Include context in log messages

```python
print(f"[{event.request_id()}] Creating experience for city={city_id}")
print(f"[{event.request_id()}] ERROR: Failed to create experience: {str(e)}")
```

### What to log

- Operation start with key parameters (resource ID, city ID).
- Failures with error detail and request_id.
- Cache hits/misses for debugging.

### What NOT to log

- Secrets, tokens, passwords.
- Full request bodies (may contain sensitive data).
- Full response bodies (too noisy, too large).
- Supabase keys or connection strings.

### Request tracing

`@klug` already adds `X-Request-ID` to response headers and logs `REQUEST_ID`, `USER_ID`, and `EMAIL` on unhandled exceptions. You can access it via:

```python
req_id = event.request_id()
```

## Debugging / troubleshooting

**When:** Investigating 500s, timeouts, integration failures, incorrect data.

**Checklist:**
1. Check `X-Request-ID` in response headers.
2. Search logs for `request_id` to trace the request.
3. Verify Supabase connectivity and credentials.
4. Use `event.error_response(..., include_traceback=True)` for domain-specific errors.
5. Reproduce with curl or Postman to isolate frontend vs backend.

**What NOT to log:** Do not log secrets, tokens, full request/response bodies (see Observability minimum above).

## Common mistakes

- Not mocking `event.supabase` (tests hit real database).
- Testing only the happy path and skipping validation.
- Logging secrets or full auth tokens.
- Over-logging (every line) instead of logging meaningful events.

## Definition of done

### For tests
- Validation paths tested (missing fields, bad UUIDs, not found).
- Success path tested with correct response shape.
- Mocks used for Supabase and cache.
- Tests run with `pytest`.

### For observability
- Log messages include `request_id`.
- No secrets in logs.
- Key operations (create, update, delete) have a log entry.
