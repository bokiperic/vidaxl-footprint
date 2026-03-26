---
name: commit-and-push
description: Commit all current changes and push to the remote git repository on the current branch. Use when the user wants to save and push their work.
disable-model-invocation: true
allowed-tools: Bash, Read, Glob, Grep
---

# Commit and Push

Commit all staged/unstaged changes and push to the remote repository on the **current branch**.

## Steps

1. **Review changes** — Run these in parallel:
   - `git status` to see all modified and untracked files
   - `git diff` to see the actual changes (staged + unstaged)
   - `git log --oneline -5` to see recent commit message style
   - `git branch --show-current` to determine the current branch name

2. **Stage relevant files** — Add modified and new files that are part of the change. Do NOT stage:
   - `.env` files or anything with secrets/credentials
   - `.claude/settings.local.json`
   - Temporary/generated files (e.g. `.playwright-mcp/`, `__pycache__/`, `.pyc`)

3. **Craft a commit message** — Follow the style of recent commits:
   - Concise first line summarizing the "why"
   - Optional body with bullet points for multi-part changes
   - End with: `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`
   - Use a HEREDOC to pass the message to `git commit -m`

4. **Push to remote** — Push to the **current branch**: `git push origin <current-branch-name>`. If the remote branch does not exist yet, use `git push -u origin <current-branch-name>`.

5. **Verify** — Run `git status` after push to confirm clean state and confirm the push succeeded.

If any step fails, stop and report the error. Do not force-push or skip hooks.
