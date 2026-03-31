---
name: backend-performance-and-db-review
description: >
  Identify and fix database performance issues, N+1 queries, missing pagination,
  cache misuse, and inefficient data loading. Use when optimizing slow endpoints,
  reviewing query patterns, or adding caching.
---

# Backend Performance and DB Review

## When to use

- Endpoint is slow or suspected to have N+1 queries.
- Reviewing existing code for query efficiency.
- Adding or modifying caching strategy.
- Deciding between embeds, batch queries, and parallel execution.

## When NOT to use

- Building a new simple CRUD endpoint -> use [backend-endpoint-crud](.cursor/skills/backend-endpoint-crud/SKILL.md).
- The performance issue is on the frontend side.

## Query efficiency checklist

1. **Count the queries.** Each `.execute()` call is a network round-trip. Target 1-3 per endpoint.
2. **Check for loops.** Any query inside a `for`/`while` is a hard violation. Fix with embeds or `.in_()`.
3. **Check column selection.** List endpoints should not `select("*")` if they only return a few fields.
4. **Check pagination.** List endpoints without `.range()` or `paginate_query()` will fetch all rows.
5. **Check for sequential queries** that could be a single embedded select.

## Optimization priority

Always prefer in this order:

1. **Reduce query count** (combine with PostgREST embeds).
2. **Reduce data transferred** (select only needed columns).
3. **Add pagination** (limit row count).
4. **Add caching** (avoid repeated identical queries).
5. **Parallelize** (only for truly independent queries, 3+).

Do NOT jump to caching or threading before fixing the query itself.

## Detecting N+1 patterns

N+1 looks like:

```python
# BAD: N+1 pattern
experiences = event.supabase.table("experiences").select("*").eq("city_id", city_id).execute()
for exp in experiences.data:
    tags = event.supabase.table("experience_tags").select("tag_id").eq("experience_id", exp['id']).execute()
    exp['tags'] = tags.data
```

Fix with embed:
```python
# GOOD: single query
response = event.supabase.table("experiences").select(
    "*, experience_tags(tags(id, name))"
).eq("city_id", city_id).execute()
```

Or with batch:
```python
# GOOD: batch query
exp_ids = [exp['id'] for exp in experiences.data]
tags = event.supabase.table("experience_tags").select(
    "experience_id, tag_id, tags(id, name)"
).in_("experience_id", exp_ids).execute()
```

## Cache review checklist

1. **Is the data stable?** Reference data (categories, sections, tag_groups) -> cache at 3600s. Transactional data -> 1800s. Volatile data -> don't cache.
2. **Is there a write path?** Every cached read must have a corresponding invalidation on writes.
3. **Is the cache key correct?** Must include all query parameters that affect the result.
4. **Is deserialization handled?** Cache stores strings. Use `json.dumps()`/`json.loads()`.

## Cache-aside pattern

```python
cache_key = f"entity:{scope}:{scope_id}"
cached = event.cache.get(cache_key)
if cached:
    return json.loads(cached)

data = event.supabase.table("entity").select("*").eq("scope_id", scope_id).execute().data or []

event.cache.set(cache_key, json.dumps(data), ex=1800)
return data
```

## Known performance issues in this codebase

These are known debts to be aware of:

1. **`invalidate_guide_share_caches()` queries inside loops** — queries `shared_lists` and `shared_goto_lists`, then loops to delete cache keys. Acceptable for now since the number of shared lists per guide is small.
2. **`_get_city_tags()` uses `.in_()` with all experience IDs** — can exceed URL length for large cities. The embed-based approach would be better but requires schema awareness.
3. **`SharedListFactory.get_by_id()`** makes 3 separate queries (list, guide, supplier) that could potentially be joined.
4. **`Event.select()`** opens and closes a new `psycopg2` connection per call (no pooling).
5. **`BaseEntityFactory._get_single()`** has complex fallback logic for parsing Supabase response shapes.

When touching these areas, improve them if the fix is contained. Do not refactor broadly unless explicitly asked.

## Parallel execution

Use `ThreadPoolExecutor` only when:
- You have 3+ truly independent queries.
- Each query takes measurable time.
- They cannot be combined into embeds.

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    future_a = executor.submit(fetch_a, arg)
    future_b = executor.submit(fetch_b, arg)
    future_c = executor.submit(fetch_c, arg)
    result_a = future_a.result()
    result_b = future_b.result()
    result_c = future_c.result()
```

Reference: `CityDataLoader` in `data_loader.py` uses 8 workers for 10 parallel queries.

## Common mistakes

- Adding cache without adding invalidation on writes.
- Caching with a key that doesn't include all filtering parameters.
- Using `ThreadPoolExecutor` for 2 queries that could be one embed.
- Optimizing a query that runs once per request while ignoring an N+1 in the same handler.
- Adding cache for data that changes on every request.

## Definition of done

- No queries inside loops.
- List endpoints have pagination.
- List endpoints select only needed columns.
- Query count is 1-3 per endpoint.
- Cache has matching invalidation on write paths.
- No premature caching or threading.
