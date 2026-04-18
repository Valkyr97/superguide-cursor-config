# Commit pending changes

Read and apply `.cursor/rules/commit-and-pr-standards.mdc` at the repository root before writing any commit message.

## Workflow

1. Run `git status`, `git diff`, and `git diff --staged` in parallel to understand the full picture.
2. If there are no changes, say so and stop.
3. Skip secrets, credentials, `.env` files, and anything `.gitignore` should exclude. Warn if found.
4. Group changes into logical commits — one concern per commit. Use `git add -p` when changes in a single file span multiple concerns.
5. Stage and commit each group in coherent order.
6. If pre-commit hooks fail, fix the issue and create a new commit (do not amend unless the failed commit was yours in this session).
7. Report: branch, each commit (short hash + subject), and anything left uncommitted with the reason.

Do not push or rewrite history unless explicitly asked.
