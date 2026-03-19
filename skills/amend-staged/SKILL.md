---
name: amend-staged
description: Amend the last commit with staged changes only
---

# Amend Staged Changes

Amend the most recent commit by adding currently staged changes to it, without staging new files.

## Context

- Current git status: {{GIT_STATUS}}
- Current branch: {{GIT_BRANCH}}
- Recent commits: {{GIT_LOG}}

## Safety Checks

Before amending, you MUST verify ALL of these conditions:

1. **HEAD commit was created by Claude**:
   - Run: `git log -1 --format='%an %ae'`
   - Must show: "Claude Sonnet 4.5 <noreply@anthropic.com>" in Co-Authored-By

2. **Commit has NOT been pushed**:
   - Run: `git status`
   - Must show "Your branch is ahead of" (not "up to date")
   - If already pushed, WARN user that amend requires force push

3. **There are staged changes**:
   - Must have "Changes to be committed" in git status
   - If no staged changes, inform user nothing to amend

## Your task

Based on the staged changes shown above, amend the last commit.

**IMPORTANT**:
- Do NOT run `git add`. Only amend with already-staged changes.
- Use `git commit --amend --no-edit` to keep the existing commit message
- If you need to update the commit message, use `git commit --amend` and provide new message

### Steps:

1. Run safety checks (verify conditions above)
2. If all checks pass, run: `git commit --amend --no-edit`
3. Report what was amended

### Example:

```bash
# Verify HEAD commit author
git log -1 --format='%an %ae'

# Verify not pushed
git status

# Amend with staged changes (keep message)
git commit --amend --no-edit
```

## Notes

- This follows Git Safety Protocol: only amend commits created by Claude in this conversation
- Never amend commits that have been pushed without explicit user request
- If user wants to change commit message, use `git commit --amend` without `--no-edit`
