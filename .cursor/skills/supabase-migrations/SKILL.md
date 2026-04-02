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

## Design-First Workflow

Schema changes follow a design-then-migrate flow:

1. **Design** — update `msg-data_model/ddl.sql` (canonical DDL) and `msg-data_model/CHANGES.md` (rationale). Read both before creating any migration.
2. **Migrate** — create the migration file in `msg-supabase-infra/supabase/migrations/`.
3. **Apply** — run via psql or Supabase CLI against the target environment.
4. **Verify** — confirm the change landed (see "Verification" section below).

For booking-integration schema, also read `msg-data_model/platform_mappings.md` for provider field/status mappings.

## Environment Targeting

Follow the `database-environments` rule (always-applied) for credential resolution and safety protocol. Key points:

- Default target is **WIP** (`develop` branch) unless the user explicitly says production.
- Build psql URIs from `SUPABASE_DB_*` vars in the project's env file (`.env.wip` for WIP, `.env.dev` for production).
- Always validate the connection with `psql "<uri>" -c "SELECT 1;"` before running real queries.
- If a connection fails, follow the 3-step fallback in `database-environments`.

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

### Supabase CLI (may hang)

The CLI binary may hang indefinitely on startup due to network checks — even for purely local commands like `migration new`. If a command does not complete within 10 seconds, kill it and use the direct alternative below.

```bash
# Create a new migration (preferred when CLI works)
supabase migration new <descriptive_name>

# Apply migrations locally
supabase db reset

# Push migrations to remote
supabase db push

# Pull remote schema
supabase db pull
```

### Direct migration file creation (CLI fallback)

If the CLI hangs, create migration files directly in `supabase/migrations/`:

```
YYYYMMDDHHMMSS_descriptive_name.sql
```

Generate the timestamp with `date -u +%Y%m%d%H%M%S`, or use a sequential counter (e.g. `20260401000001`, `20260401000002`) when creating multiple migrations in a batch. Apply via `psql -f` instead of `supabase db push`.

## Implementation Checklist

1. **Create migration files** in `supabase/migrations/` with timestamped names. Prefer `supabase migration new <name>`, but if the CLI hangs (>10s), create directly as `YYYYMMDDHHMMSS_descriptive_name.sql`.
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

## Direct Database Access (psql)

Use psql for schema inspection, migration verification, and ad-hoc reads.

### Inspecting current schema

```bash
# List all tables in public schema
psql "<uri>" -c "\dt public.*"

# Describe a specific table
psql "<uri>" -c "\d <table_name>"

# List columns for a table via information_schema
psql "<uri>" -c "select column_name, data_type, is_nullable, column_default from information_schema.columns where table_schema = 'public' and table_name = '<table>' order by ordinal_position;"

# List indexes on a table
psql "<uri>" -c "\di <table_name>*"

# List RLS policies
psql "<uri>" -c "select tablename, policyname, cmd, qual from pg_policies where schemaname = 'public' order by tablename;"
```

### Running a migration via psql

```bash
psql "<uri>" -f msg-supabase-infra/supabase/migrations/<migration_file>.sql
```

### Verification

After applying any migration, verify the result:

```bash
# Check columns exist with expected types
psql "<uri>" -c "select column_name, data_type from information_schema.columns where table_name = '<table>' order by ordinal_position;"

# Check indexes were created
psql "<uri>" -c "\di <table>*"

# Check RLS is enabled
psql "<uri>" -c "select relname, relrowsecurity from pg_class where relname = '<table>';"
```

## Common Pitfalls

- Forgetting to enable RLS on new tables.
- Missing `ON DELETE CASCADE` on foreign keys, causing orphaned records.
- Dropping columns that backend endpoints still reference.
- Creating migrations that are not idempotent (fail on re-run).
- Not testing migrations locally before pushing to shared environments.
- Adding indexes on low-cardinality columns (minimal benefit, storage cost).

## Definition of Done

- Migration file created with timestamped name (via CLI or directly).
- SQL is idempotent where possible (IF NOT EXISTS / IF EXISTS).
- RLS enabled with appropriate policies on new tables.
- Foreign keys have explicit ON DELETE/ON UPDATE behavior.
- Tested locally with `supabase db reset` or verified via psql on WIP.
- Backward compatible with all consuming apps (msg-guest, msg-guide, msg-marketplace).
- Verified on target environment: columns, indexes, and RLS confirmed via `information_schema` or `\d`.
