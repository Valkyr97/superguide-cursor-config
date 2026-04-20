#!/usr/bin/env bash
# preToolUse hook: fires right before every Write / StrReplace / Delete call.
#
# Purpose: surface the Pre-flight gate from .cursor/rules/pre-implementation-gate.mdc
# at the exact moment the agent is about to bypass it. The gate is alwaysApply but
# LLMs can still skip it; this hook injects a structured reminder into the agent
# context just before each edit so skipping is visible and recoverable.
#
# Design notes:
#  - Does NOT block. Returns permission: "allow" with an agent_message. Zero LLM
#    tokens, ~ms of extra latency per edit.
#  - Fires on every edit on purpose. If the agent ignored the reminder on edit #1,
#    edit #2 gets another chance. Message is kept short to minimize noise.
#  - Targeted only at edit tools via matcher in hooks.json. Does not fire on Read,
#    Grep, Glob, Shell, Task, etc.

set -euo pipefail

cat <<'JSON'
{
  "permission": "allow",
  "agent_message": "PRE-FLIGHT GATE (always-apply rule from .cursor/rules/pre-implementation-gate.mdc). Before this edit lands, confirm in the current response: (1) a '## Pre-flight' block is present listing the applicable skills, the subagent decision, and the files to touch; (2) each listed skill has been read via the Read tool in this same response; (3) for any non-trivial task, a specialist subagent has been dispatched via the Task tool (vue-frontend-engineer for msg-guest/msg-guide, react-frontend-engineer for msg-marketplace, backend-engineer for api/*, database-engineer for msg-supabase-infra) instead of editing inline; inline is only acceptable for a trivial single-file change. If any of (1)(2)(3) is missing: STOP editing, write the Pre-flight block now, read the skills, and either dispatch the subagent or justify inline in one line. Also remember to close the response with a '## What was used' table as required by agent-workflow.mdc."
}
JSON
