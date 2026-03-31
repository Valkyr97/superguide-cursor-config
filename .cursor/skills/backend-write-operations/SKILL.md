---
name: backend-write-operations
description: >
  Build POST/PUT/DELETE endpoints with relationship management, bulk operations,
  and cache invalidation. Use when creating or editing write endpoints that touch
  junction tables, many-to-many relationships, or cascade deletes.
---

# Backend Write Operations

## When to use

- POST/PUT/DELETE endpoint that writes to multiple tables.
- Endpoint manages many-to-many relationships (junction tables).
- Endpoint needs cascade delete.
- Endpoint needs bulk insert/update.
- Any write that must invalidate cache.

## When NOT to use

- Simple single-table CRUD -> use [backend-endpoint-crud](.cursor/skills/backend-endpoint-crud/SKILL.md).
- Read-only endpoint -> use [backend-joins-and-read-models](.cursor/skills/backend-joins-and-read-models/SKILL.md).

## Checklist

1. **Validate all inputs** (required fields, UUIDs, entity existence).
2. **Check auth and ownership** if the endpoint modifies user-owned resources.
3. **Write the main record** first.
4. **Write relationships** using bulk helpers.
5. **Invalidate affected cache keys.**
6. **Return the result.**

## Bulk relationship helpers

### Creating relationships

```python
success = event.create_bulk_relationships(experience_id, {
    'experience_tags': tag_ids,
    'experience_subcategories': subcategory_ids,
})
if not success:
    return event.error_response(500, 'Failed to create relationships')
```

Known junction tables and their column mappings (hardcoded in `event.py`):
- `experience_subcategories` -> `(experience_id, subcategory_id)`
- `experience_search_categories` -> `(experience_id, search_category_id)`
- `experience_tags` -> `(experience_id, tag_id)`
- `related_experiences` -> `(experience_id_1, experience_id_2)`
- `list_experiences` -> `(list_id, experience_id)`
- `shared_list_experiences` -> `(shared_list_id, experience_id)`
- `guide_suppliers` -> `(guide_id, supplier_id)`
- `user_experiences` -> `(user_id, experience_id)`

### Deleting relationships

```python
success = event.bulk_delete_relationships(experience_id, {
    'experience_tags': 'experience_id',
    'experience_subcategories': 'experience_id',
})
```

### Update (replace) many-to-many

Delete existing then insert new:

```python
success = event.update_many_to_many_relationships('experiences', experience_id, {
    'experience_tags': new_tag_ids,
    'experience_subcategories': new_subcategory_ids,
})
```

This deletes all existing rows for the main ID and inserts the new ones.

## Cascade delete

```python
deleted = event.cascade_delete('experiences', experience_id, {
    'experience_tags': ['experience_id'],
    'experience_subcategories': ['experience_id'],
    'list_experiences': ['experience_id'],
})
if not deleted:
    return event.error_response(500, 'Failed to delete experience')
```

## Cache invalidation

Every write endpoint MUST invalidate affected cache keys. Common patterns:

```python
event.cache.delete(f"experience:{experience_id}")
event.cache.delete(f"city_experiences:{city_id}")
event.cache.delete(f"city_tags:{city_id}")
```

For guide-related changes, use the helper:
```python
from helpers import invalidate_guide_share_caches
invalidate_guide_share_caches(event, guide_id)
```

This invalidates `guide_experiences:{id}`, all `share_response:{id}`, and all `goto_share_response:{id}` for that guide.

### Cache key conventions

| Pattern | TTL | Used for |
|---|---|---|
| `{entity}:{id}` | 1800s | Single record |
| `{entity}:{scope}:{scope_id}` | 1800s | Scoped collection (e.g., `city_experiences:{city_id}`) |
| `{entity}:all` | 3600s | Global reference data (categories, sections) |

## Write + relationship pattern

Full example for a POST that creates a record with relationships:

```python
@klug()
def lambda_handler(event, context):
    body = event.body()

    is_valid, error_msg = event.validate_required_fields(body, ['title', 'city_id'])
    if not is_valid:
        return event.error_response(400, error_msg)

    if not event.validate_uuid(body['city_id'], 'city_id'):
        return event.error_response(400, 'Invalid city_id format')

    tag_ids = body.get('tag_ids', [])
    record_data = {
        'title': body['title'],
        'city_id': body['city_id'],
    }

    response = event.supabase.table("experiences").insert(record_data).execute()
    if not response.data:
        return event.error_response(500, 'Failed to create experience')

    experience = response.data[0]

    if tag_ids:
        event.create_bulk_relationships(experience['id'], {
            'experience_tags': tag_ids,
        })

    event.cache.delete(f"city_experiences:{body['city_id']}")

    return experience
```

## Common mistakes

- Forgetting to invalidate cache after a write.
- Not validating that relationship IDs (tag_ids, subcategory_ids) are valid UUIDs.
- Using `event.create_record()` when you need to check the insert result (it swallows errors).
- Writing relationships before the main record exists.
- Not handling partial failures (main record created but relationships failed).

## Definition of done

- All inputs validated (fields, UUIDs, existence).
- Auth/ownership checked if required.
- Main record written before relationships.
- Bulk helpers used for junction table writes (no loops).
- All affected cache keys invalidated.
- Reuse first: existing code was reviewed before writing; no duplicated logic.
- File discipline followed (see backend-invariants).
