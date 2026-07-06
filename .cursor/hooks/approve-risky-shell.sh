#!/usr/bin/env bash
# beforeShellExecution hook: require user approval for npm/pnpm/yarn and git commands.
#
# Cursor sandbox auto-run can execute shell commands without prompting. This hook
# restores an explicit approval step for dependency and git operations.
#
# Returns:
#   permission "ask"  — Cursor shows Allow/Reject before running
#   permission "allow" — pass through unchanged

set -euo pipefail

input=$(cat)

command=$(
  python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except json.JSONDecodeError:
    print("")
    sys.exit(0)
print(data.get("command", "") or "")
' <<<"$input"
)

# npm / pnpm / yarn — install, uninstall, update, ci, add, remove, etc.
if echo "$command" | grep -Eiq '(^|[;&|[:space:]])(npm|pnpm|yarn)([[:space:]]|$)'; then
  cat <<'JSON'
{
  "permission": "ask",
  "user_message": "This command may install, remove, or change project dependencies. Review it before allowing.",
  "agent_message": "A project hook requires user approval for package-manager commands (npm/pnpm/yarn)."
}
JSON
  exit 0
fi

# git — writes, destructive ops, and remote pushes
if echo "$command" | grep -Eiq '(^|[;&|[:space:]])git([[:space:]]|$)'; then
  if echo "$command" | grep -Eiq 'git[[:space:]]+(commit|push|reset|checkout|restore|clean|rebase|merge|cherry-pick|revert|tag|stash|pull|fetch|clone|submodule|worktree)'; then
    cat <<'JSON'
{
  "permission": "ask",
  "user_message": "This command may change git history, remotes, or working tree state. Review it before allowing.",
  "agent_message": "A project hook requires user approval for git commands that can modify repository state."
}
JSON
    exit 0
  fi
fi

echo '{"permission": "allow"}'
exit 0
