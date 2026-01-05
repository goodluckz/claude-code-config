---
name: git-submodule
description: Add a directory as a git submodule with its own remote repository. Use when user wants to track a directory with separate git history.
---

# Git Submodule Management

This skill helps convert directories to git submodules or add existing repositories as submodules.

## Usage

When the user asks to add a submodule, follow these steps:

### Option 1: Convert existing directory to submodule (with new remote)

If the directory already exists and has its own `.git`:

```bash
# 1. Navigate to the directory and commit any changes
cd <directory>
git add -A && git commit -m "chore: prepare for submodule conversion"

# 2. Create private GitHub repo and push
gh repo create <repo-name> --private --source=. --push

# 3. Go back to parent repo and remove the directory
cd <parent-repo>
rm -rf <directory>

# 4. Add as submodule
git submodule add git@github.com:<username>/<repo-name>.git <directory>

# 5. Commit the submodule addition
git commit -m "chore: add <directory> as git submodule"
```

### Option 2: Add existing remote repository as submodule

```bash
git submodule add git@github.com:<username>/<repo-name>.git <path>
git commit -m "chore: add <path> as git submodule"
```

### Option 3: Convert untracked directory to submodule

If the directory exists but has no git history:

```bash
# 1. Initialize git in the directory
cd <directory>
git init
git add -A
git commit -m "Initial commit"

# 2. Create remote and push
gh repo create <repo-name> --private --source=. --push

# 3. Remove and re-add as submodule (same as Option 1, steps 3-5)
```

## Common Submodule Commands

**Clone repo with submodules:**
```bash
git clone --recurse-submodules <repo-url>
```

**Initialize submodules after clone:**
```bash
git submodule update --init --recursive
```

**Update submodule to latest:**
```bash
cd <submodule-path>
git pull origin main
cd ..
git add <submodule-path>
git commit -m "chore: update <submodule-path> submodule"
```

**Remove a submodule:**
```bash
git submodule deinit -f <path>
git rm -f <path>
rm -rf .git/modules/<path>
git commit -m "chore: remove <path> submodule"
```

## Notes

- Submodules track a specific commit, not a branch
- After updating submodule content, commit in both the submodule AND parent repo
- Use `--recurse-submodules` with clone/pull for automatic submodule handling
