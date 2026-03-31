# superguide — Cursor Configuration

Cursor AI configuration for the superguide monorepo: agents, rules, and skills.

## Structure

```
.cursor/
├── agents/    — Custom AI agent personas with specialized instructions
├── rules/     — Workspace-level coding standards and framework conventions
└── skills/    — Reusable reference docs the agent reads on demand
```

## Agents

| File | Role |
|------|------|
| `backend-engineer.md` | Python/Node API endpoints, shared layer |
| `database-engineer.md` | Supabase/Postgres schema and migrations |
| `platform-architect.md` | Infrastructure, deployment, cross-cutting concerns |
| `react-frontend-engineer.md` | React marketplace admin (msg-marketplace) |
| `shared-layer-engineer.md` | Shared entities, factories, and utilities |
| `vue-frontend-engineer.md` | Vue 3 guest and guide apps (msg-guest / msg-guide) |

## Rules

Auto-applied guidelines per file pattern:

- `coding-standards.mdc` — file size limits, code quality, bugfix mode
- `vue-frontend.mdc` — Vue 3 + Tailwind conventions
- `react-frontend.mdc` — React 19 conventions
- `python-backend.mdc` — Python backend conventions
- `shared-layer.mdc` — Shared layer invariants
- `supabase-migrations.mdc` — SQL migration conventions
- `guest-reuse.mdc` — Component reuse in msg-guest
- `mobile-first.mdc` — Mobile-first UI guidelines
- `marketplace-backend-compatibility.mdc` / `marketplace-backend-invariants.mdc` — Marketplace API contracts

## Skills

On-demand reference documents the agent reads before tackling specific tasks:

- Backend: CRUD endpoints, write operations, joins/read models, validation/auth, file uploads, shared layer, tests, performance
- Vue: components, routing, state/data fetching, forms, styling, performance, testing, config/env
- Other: Supabase migrations, React component patterns, third-party integrations, parallel agent dispatching

## Usage

Clone this repo into the root of the superguide monorepo workspace so Cursor picks up `.cursor/` automatically:

```bash
git clone git@github.com:<your-username>/superguide-cursor-config.git superguide
```
