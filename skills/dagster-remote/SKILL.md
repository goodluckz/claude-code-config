---
name: dagster-remote
description: Manage remote Dagster server on dns-analy4 - start, stop, restart, check status, sync code, and view logs. Use when user wants to manage the remote Dagster deployment.
---

# Remote Dagster Server Manager

Manage the Dagster pipeline server running on `dns-analy4` for the `scan-analysis-prod` project.

## Environment

| Property | Value |
|----------|-------|
| **Remote Host** | `dns-analy4` |
| **Project Dir** | `/home/zhaoliang/Projects/scan-analysis-prod` |
| **Local Project** | `/Users/zhaoliang/Projects/scan-analysis-prod` |
| **Dagster Port** | 3000 |
| **Arkime Port** | 8042 (direct localhost on dns-analy4) |
| **DAGSTER_HOME** | `.dagster_home_remote` |
| **Config** | `.env.remote` → `.env` |
| **tmux Session** | `dagster` |
| **Startup Script** | `scripts/dagster-remote.sh` |
| **Setup Script** | `scripts/setup-remote.sh` (run from local) |

## Operations

### Check Status

```bash
# Check if tmux session exists and services are running
ssh dns-analy4 "tmux has-session -t dagster 2>&1 && echo 'tmux: running' || echo 'tmux: not running'"

# View recent log output
ssh dns-analy4 "tmux capture-pane -t dagster -p | tail -20"

# Check processes directly
ssh dns-analy4 "pgrep -fa 'dagster' | grep -v grep"
```

### Start Server

```bash
# Start in tmux (recommended)
ssh dns-analy4 "cd /home/zhaoliang/Projects/scan-analysis-prod && tmux new-session -d -s dagster 'bash scripts/dagster-remote.sh'"
```

### Stop Server

```bash
# Send Ctrl-C to tmux session (graceful shutdown)
ssh dns-analy4 "tmux send-keys -t dagster C-c"

# Or kill the tmux session
ssh dns-analy4 "tmux kill-session -t dagster"

# Force kill if needed
ssh dns-analy4 "pkill -f 'dagster-webserver|dagster-daemon'"
```

### Restart Server

```bash
# Kill existing session, then start fresh
ssh dns-analy4 "tmux kill-session -t dagster 2>/dev/null; cd /home/zhaoliang/Projects/scan-analysis-prod && tmux new-session -d -s dagster 'bash scripts/dagster-remote.sh'"
```

### Sync Code (Local → Remote)

Run the setup script from local machine to sync code and dependencies:

```bash
bash scripts/setup-remote.sh
```

This script:
1. Installs/updates `uv` on dns-analy4
2. Rsyncs project files (excludes `.venv`, data, results, `.git`)
3. Runs `uv sync` for dependencies
4. Copies `.env.remote` and symlinks as `.env`
5. Copies GeoIP database if missing
6. Initializes `DAGSTER_HOME`

**After syncing, restart the server** to pick up code changes.

### Sync Results (Remote → Local)

```bash
# Sync results (figures, tables)
rsync -avz dns-analy4:/home/zhaoliang/Projects/scan-analysis-prod/result/ ./result/

# Sync partitioned data
rsync -avz dns-analy4:/home/zhaoliang/Projects/scan-analysis-prod/data/partitions/ ./data/partitions/

# Sync non-partitioned assets
rsync -avz dns-analy4:/home/zhaoliang/Projects/scan-analysis-prod/data/assets/ ./data/assets/
```

### Access Dagster UI from Local

```bash
# SSH tunnel for web UI
ssh -L 3000:localhost:3000 dns-analy4

# Then open http://localhost:3000
```

### View Logs

```bash
# Live tmux output
ssh dns-analy4 "tmux capture-pane -t dagster -p -S -100"

# Check active/queued runs
ssh dns-analy4 "cd /home/zhaoliang/Projects/scan-analysis-prod && ~/.local/bin/uv run dagster run list -m awsntpdagster.definitions --limit 5"
```

## Configuration

### Dagster Config (`config/prod.yaml` → `DAGSTER_HOME/dagster.yaml`)

Key settings:
- `run_queue.max_concurrent_runs`: 10
- `concurrency.default_op_concurrency_limit`: 10
- `run_retries.enabled`: true (max 2 retries)

### Environment Variables (`.env.remote`)

- `ENVIRONMENT=remote`
- `ARKIME_PORT=8042`
- `DAGSTER_WEBSERVER_PORT=3000`
- `SKIP_EXTRACTION=0` (queries Arkime directly)
- `GEOIP_ASN_DB_PATH` points to local copy on dns-analy4

## Troubleshooting

### tmux "no server running"

The tmux server isn't running. Just start a new session:
```bash
ssh dns-analy4 "cd /home/zhaoliang/Projects/scan-analysis-prod && tmux new-session -d -s dagster 'bash scripts/dagster-remote.sh'"
```

### "uv not found" in dagster-remote.sh

The script adds `~/.local/bin` to PATH. If uv was installed elsewhere, check:
```bash
ssh dns-analy4 "which uv"
```

### Database Lock Error

If daemon and webserver both try to access SQLite simultaneously, the startup script has a 5-second delay between daemon and webserver starts. If it persists, restart.

### Redis Unavailable Warning

Expected — Redis is not installed on dns-analy4. The pipeline runs without caching (direct Arkime requests each time). This is a warning, not an error.

### Port Already in Use

```bash
ssh dns-analy4 "lsof -i :3000"
# Kill stale process if needed
ssh dns-analy4 "pkill -f 'dagster-webserver'"
```
