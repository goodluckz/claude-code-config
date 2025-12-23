# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This directory (`~/.claude`) is the Claude Code configuration and state directory. It stores settings, plugins, skills, session history, and working state for all Claude Code operations.

## Directory Structure

### Core Configuration

- **settings.json**: Main configuration file controlling model selection and enabled plugins
  - `model`: Currently selected model (e.g., "haiku", "sonnet", "opus")
  - `enabledPlugins`: Map of plugin identifiers to boolean values

### Plugins and Skills

- **plugins/**: Installed Claude Code plugins and plugin marketplaces
  - `installed_plugins.json`: Registry of installed plugins with versions and paths
  - `known_marketplaces.json`: Configured plugin sources
  - `cache/`: Downloaded plugin files
  - `marketplaces/`: Cloned plugin marketplace repositories

- **skills/**: Custom skills directory for user-created skills
  - Each skill is a subdirectory with SKILL.md metadata and implementation files
  - Skills extend Claude Code's capabilities with specialized tools

### Session and Project Management

- **projects/**: Stores session data for each project Claude Code works on
  - Organized by project path encoding
  - Contains conversation logs and per-session state

- **todos/**: Task tracking data from TodoWrite tool
  - JSON files track todo lists, one file per todo list session
  - Stores task status and metadata

- **plans/**: Implementation plans created during planning mode
  - Markdown files with step-by-step implementation strategies

- **history.jsonl**: Global conversation history across all sessions
  - Line-delimited JSON format

### Development Support

- **shell-snapshots/**: Captured shell environment state for debugging
  - Preserves environment context from shell operations

- **file-history/**: Tracks file modifications and changes
  - Supports undo/revert functionality

- **debug/**: Debug logs and diagnostic information
  - Used for troubleshooting Claude Code issues

### Analytics and Cache

- **stats-cache.json**: Cached statistics about Claude Code usage
- **statsig/**: Feature flag and analytics data
- **session-env/**: Session-specific environment data
- **downloads/**: Temporary downloaded files

---

## Common Management Tasks

### 1. Changing the Default Model

Edit `settings.json` to change the model:

```json
{
  "model": "haiku"  // or "sonnet" or "opus"
}
```

Available models: haiku (fastest), sonnet (balanced), opus (most capable)

### 2. Installing Plugins

Plugins are installed from configured marketplaces:

- **Official plugins**: `claude-plugins-official` marketplace (GitHub: anthropics/claude-plugins-official)
- **Official skills**: `anthropic-agent-skills` marketplace (GitHub: anthropics/skills)

Plugin data is stored in:
- `installed_plugins.json`: Registry of what's installed
- `cache/`: Downloaded plugin files
- `marketplaces/`: Full repository clones for browsing

### 3. Creating Custom Skills

Create a new skill directory in `skills/`:

```
skills/my-skill/
├── SKILL.md           # Metadata and documentation
├── implementation/    # Implementation files (optional)
└── references/        # Reference documentation (optional)
```

**SKILL.md format**:
```yaml
---
name: my-skill
description: What this skill does
---

# Skill Title
[Instructions and usage guidelines]
```

Example: See `skills/translate-to-chinese/SKILL.md`

### 4. Enabling/Disabling Plugins

In `settings.json`, add or remove plugin entries from `enabledPlugins`:

```json
{
  "enabledPlugins": {
    "pyright-lsp@claude-plugins-official": true,
    "example-skills@anthropic-agent-skills": true,
    "some-plugin@marketplace": false  // disabled
  }
}
```

### 5. Managing Conversation History

- **Per-project history**: Stored in `projects/<encoded-path>/`
- **Global history**: Stored in `history.jsonl`

To clear old history:
1. Identify session logs in `projects/` directory
2. Remove session directories that are no longer needed
3. Note: `history.jsonl` is the canonical history log

### 6. Viewing Plans and Todos

- **Plans**: Browse markdown files in `plans/` directory
  - Each plan documents implementation strategy for a task

- **Todos**: Review JSON files in `todos/` directory
  - Each file contains task state, status, and metadata
  - Useful for tracking progress across sessions

### 7. Cleaning Up Old Data

Large directories that can be safely pruned:
- `projects/`: Session data older than 30 days
- `file-history/`: File modification history (40MB)
- `debug/`: Debug logs older than 7 days

Commands:
```bash
# List large directories
du -sh ~/.claude/* | sort -h

# Archive old session data
find ~/.claude/projects -type d -mtime +30 -exec rm -rf {} +

# Clear debug logs
find ~/.claude/debug -type f -mtime +7 -delete
```

---

## Plugin Management Details

### Marketplace Configuration

`known_marketplaces.json` defines plugin sources:

```json
{
  "marketplace-name": {
    "source": {
      "source": "github",
      "repo": "username/repo-name"
    },
    "installLocation": "/Users/../.claude/plugins/marketplaces/...",
    "lastUpdated": "ISO-8601-timestamp"
  }
}
```

To add a new marketplace:
1. Add entry to `known_marketplaces.json`
2. Specify GitHub repository source
3. Claude Code will clone/sync the marketplace

### Plugin Installation Data

`installed_plugins.json` tracks:
- Plugin version and installation path
- Installation timestamp and last update time
- Plugin scope (user)
- Whether it's a local installation

---

## Skills Development

### Skill Structure

Skills can be simple (single SKILL.md) or complex:

**Simple skill**:
```
skills/translation-skill/
└── SKILL.md
```

**Complex skill** (with references):
```
skills/advanced-skill/
├── SKILL.md
├── references/
│   ├── guide1.md
│   └── guide2.md
└── scripts/
    └── implementation.py
```

### Skill Frontmatter

Required frontmatter in SKILL.md:
```yaml
---
name: skill-identifier
description: One-line description of what skill does
---
```

### Skill Visibility

Skills in `skills/` directory are automatically available to Claude Code and can be invoked during sessions.

---

## Troubleshooting

### Plugin Issues

If plugins fail to load:
1. Check `installed_plugins.json` for valid install paths
2. Verify marketplace exists in `known_marketplaces.json`
3. Check `debug/` directory for error logs
4. Reinstall plugin if path is broken: Remove entry from `installed_plugins.json` and reinstall

### Missing Project History

If project history is missing:
1. Check `projects/` for encoded project path directory
2. Session logs are stored as `.jsonl` files
3. Global history is in `history.jsonl`
4. If both missing, session may not have created logs yet

### Storage Space Issues

Primary space consumers:
- `plugins/`: ~32MB (plugin caches and marketplaces)
- `projects/`: ~9MB (session data)
- `file-history/`: ~600KB (file change history)
- `debug/`: ~1.5MB (debug logs)

Safe to delete: Debug logs older than 1 week, session data older than 30 days

---

## Key Concepts

### Plugins vs Skills

- **Plugins**: Packages from official marketplaces that extend Claude Code with new capabilities
- **Skills**: Custom reusable instruction sets created and stored locally

### Project vs Session

- **Project**: A directory Claude Code is working in
- **Session**: A single Claude Code instance/conversation in a project

### Todos vs Plans

- **Todos**: Task lists for tracking work progress (created with TodoWrite tool)
- **Plans**: Detailed implementation strategies (created during planning mode)

---

## Data Format Reference

### history.jsonl
Line-delimited JSON with conversation entries. Each line is a complete JSON object representing a message or state change.

### installed_plugins.json
Version 2 format with structured plugin metadata including scope, paths, and timestamps.

### todo JSON files
Contains array of task objects with:
- `content`: Task description
- `status`: "pending", "in_progress", or "completed"
- `activeForm`: Present continuous form of the task
