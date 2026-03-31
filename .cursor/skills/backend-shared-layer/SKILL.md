---
name: backend-shared-layer
description: >
  Modify or extend layers/shared/ including Event, entities, factories, helpers,
  and data loaders. Use when adding shared utilities, creating new Entity/Factory
  classes, or refactoring the shared layer.
---

# Backend Shared Layer

## When to use

- Adding a new helper function to `layers/shared/`.
- Creating a new Entity/Factory pair in `layers/shared/entities/`.
- Modifying `Event` class methods.
- Adding to or modifying `CityDataLoader` or other data loaders.
- Extracting shared logic from endpoint files.

## When NOT to use

- Writing a simple endpoint that uses existing shared layer -> use [backend-endpoint-crud](.cursor/skills/backend-endpoint-crud/SKILL.md).
- The change is entirely within an endpoint file and no shared code is needed.

## Architecture overview

```
layers/shared/
  main.py               # Re-exports everything endpoints need
  decorators.py          # @klug(), @public_api()
  event.py               # Event class (~700 lines), CacheWrapper
  exceptions.py          # Custom exceptions (BadJsonError, etc.)
  helpers.py             # normalize_name(), invalidate_guide_share_caches()
  utils.py               # stopwatch()
  mixpanel_util.py       # track_event(), people_set()
  experience_utils.py    # generate_thumbnail_url()
  data_loader.py         # CityDataLoader (parallel fetch + cache)
  entities/
    __init__.py
    base.py              # BaseEntity, BaseEntityFactory
    city.py              # City, CityFactory
    category.py          # Category, CategoryFactory
    subcategory.py       # Subcategory, SubcategoryFactory
    section.py           # Section, SectionFactory
    experience.py        # Experience, ExperienceFactory
    list.py              # List, ListFactory
    shared_list.py       # SharedList, SharedListFactory
    template.py          # Template, TemplateFactory
```

## Key rules

1. **Keep `Event` small.** It is already ~700 lines (a known debt). Do not add methods unless they are genuinely cross-cutting. Prefer a new helper module or a factory method.
2. **Follow file discipline** — new modules focused; when editing large files, prefer extracting (see [backend-invariants.mdc](.cursor/rules/backend-invariants.mdc) File discipline).
3. **Re-export from `main.py`** if endpoints need the new utility. Endpoints import via `from main import *`.
4. **Do not add new dependencies** to the shared layer without checking `layers/thirdparty/requirements.txt`.

## Creating a new Entity/Factory

Follow the `BaseEntity`/`BaseEntityFactory` pattern:

```python
# layers/shared/entities/my_entity.py
from entities.base import BaseEntity, BaseEntityFactory
import json

class MyEntity(BaseEntity):
    @property
    def name(self):
        return self.get('name', '')

    @property
    def status(self):
        return self.get('status', '')

    def is_active(self):
        return self.status == 'active'


class MyEntityFactory(BaseEntityFactory):
    def __init__(self, supabase, cache=None):
        super().__init__(supabase, cache)
        self.table_name = 'my_entities'

    def create_from_data(self, data):
        return MyEntity(data)

    def get_by_id(self, entity_id):
        cache_key = f"my_entity:{entity_id}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return self.create_from_data(json.loads(cached))
        query = self.supabase.table(self.table_name).select("*").eq("id", entity_id)
        data = self._get_single(query)
        if data:
            if self.cache:
                self.cache.set(cache_key, json.dumps(data), ex=1800)
            return self.create_from_data(data)
        return None

    def get_all(self):
        cache_key = f"{self.table_name}:all"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return [self.create_from_data(item) for item in json.loads(cached)]
        query = self.supabase.table(self.table_name).select("*")
        data = self._execute_query(query)
        if self.cache and data:
            self.cache.set(cache_key, json.dumps(data), ex=3600)
        return [self.create_from_data(item) for item in data]
```

Then register in `entities/__init__.py` and `main.py`.

## Factory methods reference

From `BaseEntityFactory`:
- `_execute_query(query)` -> returns `list[dict]` or `[]`. Raises on error.
- `_get_single(query)` -> returns `dict` or `None`. Has complex fallback logic for Supabase response shapes.

## Cache conventions

| Data type | TTL | Key pattern |
|---|---|---|
| Reference data (categories, sections, tag_groups) | 3600s (1h) | `{table}:all` |
| City-scoped data (experiences, neighborhoods, suppliers) | 1800s (30m) | `{entity}:{city_id}` |
| Single records | 1800s (30m) | `{entity}:{id}` |

Always check `if self.cache:` before cache operations; cache may not be initialized.

## Adding helpers

For utility functions that endpoints need:

1. Add the function to the appropriate module in `layers/shared/` (or create a new module if no existing one fits).
2. Add it to `main.py` imports so endpoints can use it via `from main import *`.
3. Document parameters, return type, and side effects.

## Common mistakes

- Adding yet another method to `Event` when a standalone helper or factory method would be better.
- Forgetting to re-export from `main.py`.
- Creating a factory without cache support.
- Not checking `if self.cache:` before cache operations.
- Making a shared module grow without extracting when it gets large.

## Definition of done

- Reuse first: existing code was reviewed before writing; no duplicated logic.
- New code is in the right module (entity, helper, loader).
- Registered in `main.py` if endpoints need it.
- File discipline followed (see backend-invariants).
- Cache TTL is explicit and appropriate.
- Docstrings on public methods.
