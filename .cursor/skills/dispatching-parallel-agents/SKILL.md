---
name: dispatching-parallel-agents
description: Use when facing 2+ independent tasks that can be worked on without shared state or sequential dependencies
---

# Dispatching Parallel Agents

## Overview

You delegate tasks to specialized agents with isolated context. By precisely crafting their instructions and context, you ensure they stay focused and succeed at their task. They should never inherit your session's context or history — you construct exactly what they need. This also preserves your own context for coordination work.

**Core principle:** Dispatch one agent per independent problem domain. Let them work concurrently.

## When to Use

**Use when:**
- 2+ tasks targeting different projects or subsystems
- Multiple bug fixes across independent codebases
- Feature work that spans unrelated frontends (Vue + React)
- Multiple test files failing with different root causes
- Each problem can be understood without context from others

**Don't use when:**
- Tasks are related (fixing one might fix others)
- Need to understand full system state first
- Agents would edit the same files or shared modules
- There is a dependency chain (schema -> backend -> frontend)

## The Pattern

### 1. Identify Independent Domains

Group tasks by what they affect. Each domain must be independent — completing one does not require output from another.

### 2. Create Focused Agent Tasks

Each agent gets:
- **Specific scope:** One project, subsystem, or file group
- **Clear goal:** What to implement, fix, or investigate
- **Constraints:** What NOT to change (other projects, shared modules, API contracts)
- **Expected output:** Summary of what was done and what changed

### 3. Dispatch in Parallel

Launch all independent agents simultaneously using the Task tool. They run concurrently in isolated contexts.

### 4. Review and Integrate

When agents return:
- Read each summary
- Verify fixes don't conflict (especially shared files)
- Run relevant test suites or verify builds
- Integrate all changes

## Agent Prompt Structure

Good agent prompts are:
1. **Focused** - One clear problem domain
2. **Self-contained** - All context needed to understand the problem
3. **Specific about output** - What should the agent return?

### Example: Multi-project feature (superguide)

A new field `duration_minutes` needs to appear in all three frontends. The schema migration and backend are done.

```markdown
# Agent 1 → vue-frontend-engineer (msg-guest)
Add a "Duration" badge to the experience card in msg-guest.

- The API now returns `duration_minutes` (integer) in the experience object.
- Display it as "{N} min" in ExperienceCard.vue, next to the price badge.
- Use the existing badge component pattern from PriceBadge.
- Do NOT change msg-guide or msg-marketplace.

Return: which files you changed and a summary.
```

```markdown
# Agent 2 → vue-frontend-engineer (msg-guide)
Add a "Duration" field to the experience detail view in msg-guide.

- The API now returns `duration_minutes` (integer).
- Add it as a read-only field in ExperienceDetail.vue, in the metadata section.
- Follow existing field patterns in that view.
- Do NOT change msg-guest or msg-marketplace.

Return: which files you changed and a summary.
```

```markdown
# Agent 3 → react-frontend-engineer (msg-marketplace)
Add a "Duration" column to the experiences table in msg-marketplace.

- The API now returns `duration_minutes` (integer).
- Add a sortable column to the ExperiencesTable showing "{N} min".
- Follow existing column definition patterns.
- Do NOT change msg-guest or msg-guide.

Return: which files you changed and a summary.
```

All three agents run in parallel — they touch different projects with no shared files.

### Example: Independent bug fixes across apps

```markdown
# Agent 1 → backend-engineer
Fix the 500 error on GET /api/bookings in msg-guest.

Error: KeyError 'experience_id' in api/bookings/get_bookings.py line 47.
The response from Supabase uses 'experience' (embedded object) not 'experience_id'.

- Read the endpoint file and the Supabase query.
- Fix the key access. Do NOT change the query structure.

Return: root cause and fix summary.
```

```markdown
# Agent 2 → react-frontend-engineer
Fix the broken "Save" button on the city editor page in msg-marketplace.

User report: clicking Save shows loading spinner forever, no toast.
Likely cause: the onSubmit handler in CityEditor.tsx is not awaiting callApi().

- Read CityEditor.tsx and trace the save flow.
- Fix the async handling.

Return: root cause and fix summary.
```

## Common Mistakes

**❌ Too broad:** "Fix all the bugs" - agent gets lost
**✅ Specific:** "Fix GET /api/bookings KeyError in msg-guest" - focused scope

**❌ No context:** "Fix the API error" - agent doesn't know where
**✅ Context:** Include the error message, file path, and line number

**❌ No constraints:** Agent might refactor everything
**✅ Constraints:** "Do NOT change msg-guide" or "Fix only the endpoint file"

**❌ Vague output:** "Fix it" - you don't know what changed
**✅ Specific:** "Return summary of root cause and files changed"

## When NOT to Use

**Dependency chain:** Schema -> backend -> frontend must be sequential
**Related failures:** Fixing one might fix others — investigate together first
**Shared files:** Two agents editing `layers/shared/` will conflict
**Exploratory debugging:** You don't know what's broken yet
**Need full context:** Understanding requires seeing the entire system