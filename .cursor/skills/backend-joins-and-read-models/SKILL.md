---
name: backend-joins-and-read-models
description: >
  Build read endpoints with PostgREST embeds, joins, pagination, and data transformation.
  Use when creating GET endpoints that need data from multiple related tables, or when
  optimizing existing read endpoints to reduce query count.
---

# Backend Joins and Read Models

## When to use

- GET endpoint needs data from 2+ tables.
- Endpoint currently makes multiple sequential queries that could be a single embedded select.
- Endpoint needs pagination.
- Response requires flattening or transforming nested Supabase embed results.

## When NOT to use

- Simple single-table CRUD -> use [backend-endpoint-crud](.cursor/skills/backend-endpoint-crud/SKILL.md).
- Endpoint primarily writes data -> use [backend-write-operations](.cursor/skills/backend-write-operations/SKILL.md).

## Checklist

1. **Identify all data needed** in the response shape.
2. **Design one Supabase query** with PostgREST embeds to fetch it all.
3. **If one query is not possible**, use `.in_()` batch or `ThreadPoolExecutor` for independent queries.
4. **Add pagination** for list endpoints that can return many rows.
5. **Transform the response** to match the expected shape.
6. **Consider caching** for expensive or stable data.

## PostgREST embeds

Supabase supports embedded (joined) selects through PostgREST syntax:

```python
response = event.supabase.table("experiences").select(
    "id, title, price, status, "
    "suppliers(id, name), "
    "experience_tags(tags(id, name)), "
    "experience_subcategories(subcategories(id, name))"
).eq("city_id", city_id).execute()
```

This fetches experiences with their supplier, tags, and subcategories in ONE query.

### Embed syntax reference

| Pattern | Meaning |
|---|---|
| `table(col1, col2)` | Join and select specific columns |
| `table(*)` | Join and select all columns |
| `junction_table(target_table(cols))` | Through a junction table |
| `table!fk_name(cols)` | Specify which foreign key to use |

### Real example from the codebase

```python
# From data_loader.py - tags with their groups via junction
response = event.supabase.table("experience_tags").select(
    "tag_id, "
    "tags!experience_tags_tag_id_fkey("
    "    id, name, s3_icon_key, tag_group_id, "
    "    tag_groups!tags_tag_group_id_fkey(id, name)"
    ")"
).in_("experience_id", experience_ids).execute()
```

## Query priority

Always prefer in this order:

1. **One embedded Supabase query** — best performance, simplest code.
2. **One query + `.in_()` batch** — when you need IDs from one query to filter another.
3. **Factory/loader** (`CityDataLoader`, entity factories) — when the pattern exists.
4. **`ThreadPoolExecutor`** — only when queries are truly independent and cannot be combined.

Do NOT introduce `ThreadPoolExecutor` unless you have 3+ independent queries that each take significant time.

## Pagination

For list endpoints, always support pagination:

```python
limit = event.safe_query_param("limit", 50, int)
offset = event.safe_query_param("offset", 0, int)

query = event.supabase.table("experiences").select("id, title, price").eq("city_id", city_id)
query = event.paginate_query(query, limit=limit, offset=offset)
response = query.execute()

return response.data or []
```

`event.paginate_query()` adds `.order("created_at", desc=True).range(offset, offset + limit - 1)`.

## Column selection

For list endpoints, select only the columns the response needs:

```python
# List endpoint - select specific columns
response = event.supabase.table("experiences").select("id, title, price, status").execute()

# Detail endpoint - select("*") is fine
response = event.supabase.table("experiences").select("*").eq("id", record_id).execute()
```

## Transforming nested results

PostgREST embeds return nested structures. Use `event.extract_nested_arrays()` or `event.flatten_nested_response()` to reshape:

```python
data = event.extract_nested_arrays(response.data, {
    'experience_subcategories': 'subcategories',
    'experience_tags': 'tags'
})
```

Or manually extract:
```python
for exp in response.data:
    raw_tags = exp.pop("experience_tags", []) or []
    exp["tags"] = [item["tags"] for item in raw_tags if item.get("tags")]
```

## Caching reads

For expensive or stable data, use the cache-aside pattern:

```python
cache_key = f"city_experiences:{city_id}"
cached = event.cache.get(cache_key)
if cached:
    return json.loads(cached)

response = event.supabase.table("experiences").select("*").eq("city_id", city_id).execute()
data = response.data or []

event.cache.set(cache_key, json.dumps(data), ex=1800)
return data
```

TTLs: 3600s for reference data (categories, sections), 1800s for transactional data (experiences, lists).

## Common mistakes

- Making N queries in a loop when one embedded query would work.
- Using `ThreadPoolExecutor` for 2 queries that could be one embed.
- Forgetting pagination on list endpoints.
- Selecting `*` on list endpoints that only need a few columns.
- Not handling empty embed results (nested arrays can be `None` or `[]`).

## Definition of done

- One or minimal queries to fetch all needed data.
- No N+1 patterns.
- Pagination supported on list endpoints.
- Only needed columns selected on list endpoints.
- Response shape matches what the frontend expects.
- Cache used where the data is stable and the query is expensive.
