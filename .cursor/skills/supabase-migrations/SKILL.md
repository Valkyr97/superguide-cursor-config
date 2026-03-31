---
name: supabase-migrations
description: Guide database migration creation, SQL conventions, and schema management for msg-supabase-infra. Use when creating migrations, modifying schema, managing RLS policies, or working with database dumps.
---

# Supabase Migrations

## Purpose

Guide the creation and management of Supabase database migrations, SQL conventions, RLS policies, and schema management for the `msg-supabase-infra` project.

## When to Use

- Creating a new database migration
- Modifying table schema (add/alter/drop columns or tables)
- Creating or modifying RLS (Row Level Security) policies
- Adding or modifying indexes
- Working with database dumps or schema snapshots
- Creating database functions or triggers

## When NOT to Use

- Endpoint implementation -> use backend skills
- Frontend data fetching -> use frontend skills

## Repository Context

### Structure

```
msg-supabase-infra/
  supabase/
    migrations/       # Timestamped migration SQL files
    .branches/        # Supabase branch metadata
    .temp/            # Temporary files
    dumps/
      develop/        # Dev environment dumps
      main/           # Production environment dumps
  schema.sql          # Reference schema snapshot
  data.sql            # Reference data snapshot
  roles.sql           # Reference roles snapshot
  package.json        # Supabase CLI dependency
```

### Supabase CLI

```bash
# Create a new migration
supabase migration new <descriptive_name>

# Apply migrations locally
supabase db reset

# Push migrations to remote
supabase db push

# Pull remote schema
supabase db pull
```

## Implementation Checklist

1. **Use the Supabase CLI** to generate migration files. Never manually create timestamped filenames.
2. **One logical change per migration.** Don't mix unrelated schema changes.
3. **Use `IF NOT EXISTS` / `IF EXISTS`** for safety on CREATE/DROP statements.
4. **Specify foreign key behavior.** Always include `ON DELETE` and `ON UPDATE` clauses.
5. **Add indexes** for columns frequently used in WHERE, JOIN, or ORDER BY clauses.
6. **Review RLS policies** for security implications. Every new table should have RLS enabled with appropriate policies.
7. **Test locally** before applying to shared environments: `supabase db reset`.
8. **Never drop columns/tables with data** without explicit user confirmation and a backup plan.
9. **Add comments** on non-obvious columns, constraints, or functions.
10. **Consider all consuming apps.** Schema changes affect msg-guest, msg-guide, and msg-marketplace backends. Verify compatibility.

## SQL Conventions

- Use lowercase for SQL keywords (`create table`, `alter table`, `select`).
- Use snake_case for table and column names.
- Primary keys: `id uuid default gen_random_uuid() primary key`.
- Timestamps: include `created_at timestamptz default now()` and `updated_at timestamptz default now()`.
- Use `text` over `varchar` unless there's a specific length constraint.
- Use `timestamptz` (with timezone) over `timestamp`.
- Enum-like values: prefer a reference table with foreign key over PostgreSQL enums (easier to modify).

## RLS Policy Patterns

```sql
-- Enable RLS on a new table
alter table my_table enable row level security;

-- Allow authenticated users to read their own data
create policy "Users can read own data"
  on my_table for select
  using (auth.uid() = user_id);

-- Allow service role full access
create policy "Service role has full access"
  on my_table for all
  using (auth.role() = 'service_role');
```

## Common Pitfalls

- Forgetting to enable RLS on new tables.
- Missing `ON DELETE CASCADE` on foreign keys, causing orphaned records.
- Dropping columns that backend endpoints still reference.
- Creating migrations that are not idempotent (fail on re-run).
- Not testing migrations locally before pushing to shared environments.
- Adding indexes on low-cardinality columns (minimal benefit, storage cost).

## Definition of Done

- Migration created via Supabase CLI with descriptive name.
- SQL is idempotent where possible (IF NOT EXISTS / IF EXISTS).
- RLS enabled with appropriate policies on new tables.
- Foreign keys have explicit ON DELETE/ON UPDATE behavior.
- Tested locally with `supabase db reset`.
- Backward compatible with all consuming apps (msg-guest, msg-guide, msg-marketplace).
