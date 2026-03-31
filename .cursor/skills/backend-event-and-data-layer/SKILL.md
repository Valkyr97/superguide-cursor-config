---
name: backend-event-and-data-layer
description: Complete API reference for the Event class, Entity/Factory pattern, CityDataLoader, and shared utilities. Use when implementing, editing, or debugging backend endpoints to find existing methods before writing new code.
---

# Backend Event and Data Layer Reference

## Purpose

Provide a complete, searchable reference for the `Event` class methods, entity/factory classes, `CityDataLoader`, and shared utility modules. Consult this before writing any new backend logic to avoid duplicating existing functionality.

## When to Use

- Implementing a new endpoint and need to know what Event helpers exist
- Editing an existing endpoint and need the exact method signature
- Looking for existing CRUD, validation, relationship, or transformation helpers
- Working with entities, factories, or the data loader
- Checking cache API, response helpers, or parameter access patterns

## When NOT to Use

- Deciding project structure, decorator choice, or workflow — that's in the agent definition
- Frontend work — this is backend-only
- Deployment or infrastructure — check `setup/` directly

## Event Object — Complete API Reference

The `Event` class (`layers/shared/event.py`) is the primary interface for all endpoint logic. Created automatically by the `@klug()` or `@public_api()` decorator.

**Properties:**

| Property | Type | Description |
|---|---|---|
| `event.supabase` | `Client` | Supabase client instance (ready to use) |
| `event.cache` | `CacheWrapper` | kachy-based cache (always initialized; methods are no-ops if kachy unavailable) |
| `event.event` | `dict` | Raw Lambda event dict (rarely needed directly) |

### Parameter access

| Method | Signature | Description |
|---|---|---|
| `event.path()` | `(name: str) -> str` | Path parameter. Raises `PathParameterError` if missing. |
| `event.query()` | `(name: str) -> str` | Query parameter. Raises `QueryParameterError` if missing. |
| `event.body()` | `(name: str = None) -> dict \| Any` | Without args: full parsed body (no `json.loads()` needed). With `name`: returns `body.get(name)`. |
| `event.param()` | `(name: str) -> Any` | Universal lookup: tries path -> query -> body. Raises `ParameterError` if not found anywhere. |
| `event.safe_path()` | `(name: str, default=None) -> Any` | Safe path access, returns `default` on missing. |
| `event.safe_query()` | `(name: str, default=None) -> Any` | Safe query access, returns `default` on missing. |
| `event.safe_query_param()` | `(param_name, default=None, param_type=str) -> Any` | Safe query extraction with type coercion (e.g., `param_type=int`). |
| `event.safe_body_param()` | `(param_name, default=None, required=False) -> Any` | Safe body field extraction. Raises `ValueError` if `required=True` and missing. |

### Identity (authenticated endpoints)

| Method | Signature | Description |
|---|---|---|
| `event.user_id()` | `() -> str \| None` | User ID from auth context (`auth.user_id` or `auth.sub`). |
| `event.email()` | `() -> str \| None` | User email from authorizer context. |
| `event.username()` | `() -> str \| None` | Alias for `email()`. |
| `event.sub()` | `() -> str \| None` | Raw JWT `sub` claim. |
| `event.get_guide_id()` | `() -> str \| None` | Looks up guide ID via `guides` table for current user's `sub()`. Makes a DB query. |
| `event.get_guide_by_email()` | `(email: str) -> dict \| None` | Returns full guide row by email. |

### Validation

| Method | Signature | Description |
|---|---|---|
| `event.validate_required_fields()` | `(body: dict, required_fields: list) -> (bool, str \| None)` | Returns `(True, None)` or `(False, "Required field 'x' is missing")`. |
| `event.validate_uuid()` | `(value: str, param_name: str = "parameter") -> bool` | Validates UUID v4 format. |
| `event.validate_required_params()` | `(params: dict, param_names: list) -> dict \| None` | Returns `error_response(400, ...)` if any param missing, else `None`. |
| `event.validate_uuid_params()` | `(params: dict, param_names: list) -> dict \| None` | Returns `error_response(400, ...)` if any param is not a valid UUID, else `None`. |

### Responses

| Method | Signature | Description |
|---|---|---|
| `return data` | — | Decorator auto-wraps as `{ statusCode: 200, body: json(data) }`. Preferred for simple success. |
| `event.create_error_response()` | `(status_code: int, error_message: str, request_id=None) -> dict` | Returns `{ statusCode, body: { error, request_id } }`. Use this in endpoint code. |
| `event.create_success_response()` | `(data, status_code=200, request_id=None) -> dict` | Returns `{ statusCode, body: data, headers: { X-Request-ID } }`. |
| `event.error_response()` | `(status_code, message, error=None, include_traceback=False) -> dict` | **Internal — used by decorators only.** Do NOT call from endpoint code. |

**Decision tree — which response pattern?**
- Simple success -> `return data`
- Success with non-200 status -> `event.create_success_response(data, 201)`
- Client error (400, 404, etc.) -> `event.create_error_response(status_code, message)`
- Never build `{ statusCode, body }` dicts manually — always use the helpers

### Cache

| Method | Signature | Description |
|---|---|---|
| `event.cache.get()` | `(key: str) -> Any \| None` | Returns cached value or `None`. |
| `event.cache.set()` | `(key: str, value, ex=None)` | Set cache value. **`ex` is TTL in seconds** (e.g., `ex=1800` for 30 min). |
| `event.cache.delete()` | `(key: str)` | Delete cache entry. |
| `event.cache.exists()` | `(key: str) -> bool` | Check if key exists. |

All cache methods are safe no-ops if kachy is unavailable.

### CRUD helpers

| Method | Signature | Description |
|---|---|---|
| `event.get_all()` | `(table_name, select_fields="*", filters=None, order_by=None, order_desc=False) -> list` | Query all matching records. `filters` is `{ field: value }` dict. |
| `event.get_by_id()` | `(table_name, record_id, select_fields="*") -> dict \| None` | Get single record by ID (validates UUID first). |
| `event.create_record()` | `(table_name, data: dict) -> dict \| None` | Insert one record, return created row. |
| `event.update_record()` | `(table_name, record_id, data: dict) -> dict \| None` | Update by ID. Filters out `None` values from data before update. |
| `event.delete_record()` | `(table_name, record_id) -> bool` | Delete by ID. Returns `True` on success. |

### Relationship management

| Method | Signature | Description |
|---|---|---|
| `event.create_bulk_relationships()` | `(main_id, relationships_config: dict) -> bool` | Insert junction table rows. Config: `{ junction_table: [related_ids] }`. Has a built-in mapping for known junction tables. |
| `event.bulk_delete_relationships()` | `(main_id, relationships_config: dict) -> bool` | Delete from junction tables. Config: `{ junction_table: foreign_key_column }`. |
| `event.update_many_to_many_relationships()` | `(main_table, main_id, relationships_config: dict)` | Delete existing + insert new junction rows (full replace). |
| `event.get_related_data()` | `(main_table, main_id, relationships_config: dict) -> dict` | Fetch related data via junction tables. Config: `{ junction_table: select_query }`. |
| `event.cascade_delete()` | `(main_table, main_id, cascade_config: dict) -> bool` | Delete related records then main record. Config: `{ table: [foreign_key_columns] }`. |

### Data transformation and query building

| Method | Signature | Description |
|---|---|---|
| `event.flatten_nested_response()` | `(data: list, flatten_config: dict) -> list` | Flatten nested Supabase join responses. Config: `{ nested_key: target_key }`. |
| `event.extract_nested_arrays()` | `(data: list, extraction_config: dict) -> list` | Extract nested arrays from joined data. Config: `{ nested_field: target_field }`. |
| `event.build_query_with_joins()` | `(table_name, select_fields, joins=None, filters=None) -> query` | Build Supabase query with join syntax. `joins`: `{ alias: select_query }`. |
| `event.get_city_experiences()` | `(city_id, select_fields="*", include_foreign=True, include_subcategories=False) -> dict` | Returns `{ experiences: [...], foreign_experiences: [...] }`. Handles regular + foreign experiences with subcategory embedding. |

### Entity lookup helpers

| Method | Signature | Description |
|---|---|---|
| `event.get_entity_id_by_name()` | `(table_name, name, city_id=None, additional_filters=None) -> str \| None` | Look up a single entity ID by name. |
| `event.get_entity_ids_by_names()` | `(table_name, names: list, city_id=None) -> dict` | Batch lookup: returns `{ name: id }` mapping. |

### Other utilities

| Method | Signature | Description |
|---|---|---|
| `event.request_id()` | `() -> str` | AWS Lambda request ID (or `'unknown'`). |
| `event.get_current_time()` | `() -> str` | Current timestamp as ISO string. |
| `event.paginate_query()` | `(query, limit=50, offset=0) -> query` | Adds `.order("created_at", desc=True).range(offset, offset+limit-1)`. **Always orders by `created_at` DESC** — not configurable. |
| `event.safe_execute_with_traceback()` | `(operation_name, operation_func, *args, **kwargs) -> Any \| dict` | Wraps a callable in try/except. Returns result on success or `error_response(500, ...)` on failure. |
| `event.select()` | `(query: str) -> list[dict]` | Execute raw PostgreSQL SELECT via psycopg2. **Only use when Supabase client cannot express the query.** Requires `SUPABASE_DB_USER`, `SUPABASE_DB_PASSWORD`, `SUPABASE_DB_HOST` env vars. |

## Entity/Factory Pattern (`layers/shared/entities/`)

Domain entities with factory methods for data loading:

| Entity file | Entity class | Factory class | Key factory methods |
|---|---|---|---|
| `base.py` | `BaseEntity` | `BaseEntityFactory` | `create_from_data()`, `_execute_query()`, `_get_single()` |
| `city.py` | `City` | `CityFactory` | `get_by_id()`, `get_all()`, `get_by_name()`, `get_related_cities()` |
| `experience.py` | `Experience` | `ExperienceFactory` | `get_by_id()`, `get_by_ids()`, `get_city_experiences()`, `get_city_foreign_experience_ids()` |
| `category.py` | `Category` | `CategoryFactory` | `get_by_id()`, `get_all()`, `get_by_ids()` |
| `subcategory.py` | `Subcategory` | `SubcategoryFactory` | `get_by_id()`, `get_by_city_id()` |
| `section.py` | `Section` | `SectionFactory` | `get_by_id()`, `get_all()` |
| `list.py` | `List` | `ListFactory` | `get_by_id()`, `get_experiences()`, `load_data_with_metadata()` |
| `shared_list.py` | `SharedList` | `SharedListFactory` | `get_by_id()`, `load_data_with_metadata()` |
| `template.py` | `Template` | `TemplateFactory` | `get_by_id()`, `load_data_with_metadata()` |

**Factory constructor pattern:** All factories take `(supabase, cache=None)`:
```python
factory = CityFactory(event.supabase, cache=event.cache)
city = factory.get_by_name("Paris")
```

## CityDataLoader (`layers/shared/data_loader.py`)

Central data loader for city-scoped data. Uses `ThreadPoolExecutor(max_workers=8)` for parallel Supabase queries.

**Constructor:** `CityDataLoader(supabase, cache=None)`

| Method | Returns | Description |
|---|---|---|
| `load_city_data(city_id)` | `dict` | Parallel load of all city data. Returns `{ city_experiences, city_foreign_experience_ids, subcategories, sections, tags, tag_groups, neighborhoods, suppliers, categories, categorical_values }`. |
| `load_list_experiences(list_id)` | `list` | List-experience links (cached). |
| `load_shared_list_experiences(shared_list_id)` | `list` | Shared list experiences (cached). |
| `load_guide_experiences(guide_id)` | `list` | Guide experiences (cached). |

## Shared Utilities

| Module | Key exports | Description |
|---|---|---|
| `layers/shared/helpers.py` | `normalize_name()`, `invalidate_guide_share_caches(event, guide_id)` | Name normalization and cache invalidation for guide/share changes. |
| `layers/shared/utils.py` | `stopwatch(msg)` | Timing helper using `time.perf_counter()`. |
| `layers/shared/experience_utils.py` | `generate_thumbnail_url(image_key, size, uploads_cdn)` | Build thumbnail URL from image key and size. |
| `layers/shared/exceptions.py` | `BadJsonError`, `PathParameterError`, `QueryParameterError`, `ParameterError`, and others | Custom exceptions raised by Event methods. |
| `layers/shared/main.py` | Re-exports everything above | Central import hub — endpoints use `from main import *`. |
