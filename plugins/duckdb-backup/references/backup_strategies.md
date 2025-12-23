# DuckDB Backup Strategies

## Overview

This guide explains when to use each backup approach and how to set up scheduled backups.

## Backup Approaches

### 1. File-Based Backup (cp)

**Method:** Simple file copy using `cp` or `shutil.copy2()`

```bash
cp data/awsntp.duckdb data/backup-20251223.duckdb
```

**Pros:**
- Fastest for large databases (direct file copy)
- Simplest to implement
- Works offline (database doesn't need to be running)
- Minimal overhead
- Best for local backups

**Cons:**
- Database file locked during copy (briefly)
- Cannot backup to remote cloud storage directly
- Less portable across different environments

**Best for:**
- Local machine backups
- Pre-materialization snapshots
- Quick backup before risky operations
- Development/testing environments

### 2. ATTACH+COPY Backup (attach)

**Method:** DuckDB's native `ATTACH` + `COPY FROM DATABASE` approach

```sql
ATTACH 'source.duckdb' AS source_db (READ_ONLY);
ATTACH 'backup.duckdb' AS backup_db;
COPY FROM DATABASE source_db TO backup_db;
```

**Pros:**
- Database-agnostic (works with remote paths)
- Can backup to cloud storage (S3, GCS, etc.)
- Maintains DuckDB-specific metadata
- More flexible for complex scenarios
- Can backup while database is in use

**Cons:**
- Slower than file copy (table-by-table copy)
- Requires duckdb CLI available
- More overhead

**Best for:**
- Cloud/remote backups
- Cross-environment transfers
- When database is in active use
- Complex backup scenarios

## Choosing a Method

| Scenario | Recommended | Reason |
|----------|-------------|--------|
| Daily local backup | cp | Fast, simple, reliable |
| Pre-materialization safety | cp | Speed, no overhead |
| Cloud storage backup | attach | Native cloud support |
| Database in active use | attach | Doesn't block queries |
| Development snapshot | cp | Fastest |
| Production backup archive | attach | More robust, portable |

## Scheduled Backups

### macOS/Linux: Using cron

**Edit crontab:**
```bash
crontab -e
```

**Daily backup at 2 AM (using cp method):**
```cron
0 2 * * * /usr/bin/python3 /path/to/backup_duckdb.py --db /path/to/awsntp.duckdb --backup /path/to/backups/backup.duckdb --method cp --timestamp >> /var/log/duckdb_backup.log 2>&1
```

**Daily backup at 2 AM (using attach method):**
```cron
0 2 * * * /usr/bin/python3 /path/to/backup_duckdb.py --db /path/to/awsntp.duckdb --backup /path/to/backups/ --method attach --timestamp >> /var/log/duckdb_backup.log 2>&1
```

### Windows: Using Task Scheduler

**Create scheduled task:**
```powershell
$action = New-ScheduledTaskAction -Execute 'python.exe' -Argument '-m backup_duckdb --db C:\data\awsntp.duckdb --backup C:\backups\backup.duckdb --method cp --timestamp'
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
Register-ScheduledTask -TaskName "DuckDB Daily Backup" -Action $action -Trigger $trigger -Principal $principal
```

## Backup Naming Conventions

### Timestamp Format

The script supports timestamp-based naming:
```
backup-20251223-153045.duckdb
```

Format: `backup-YYYYMMDD-HHMMSS.duckdb`

### Advantages:
- Unique names prevent overwriting
- Chronological sorting works naturally
- Easy to identify backup age
- Supports retention policies (e.g., keep last 7 days)

## Retention Policies

### Keep Last N Backups

```bash
# Keep only the 7 most recent backups
ls -t /path/to/backups/backup-*.duckdb | tail -n +8 | xargs rm
```

### Keep by Age

```bash
# Delete backups older than 30 days
find /path/to/backups -name "backup-*.duckdb" -mtime +30 -delete
```

## Example: Complete Daily Backup Script

```bash
#!/bin/bash
# Daily backup with retention

DB_PATH="/Users/zhaoliang/LocalRepos/awsntpdagster/data/awsntp.duckdb"
BACKUP_DIR="/Users/zhaoliang/LocalRepos/awsntpdagster/data/backups"
RETENTION_DAYS=30

# Create backup
/usr/bin/python3 /path/to/backup_duckdb.py \
  --db "$DB_PATH" \
  --backup "$BACKUP_DIR" \
  --method cp \
  --timestamp

# Clean up old backups (older than 30 days)
find "$BACKUP_DIR" -name "backup-*.duckdb" -mtime +$RETENTION_DAYS -delete

echo "Backup completed at $(date)" >> "$BACKUP_DIR/backup.log"
```

## Verification

### Verify Backup Size

```bash
# Compare original and backup sizes
ls -lh data/awsntp.duckdb data/backup-*.duckdb
```

### Verify Backup Contents

```bash
# List tables in backup
duckdb data/backup-20251223-153045.duckdb "SELECT table_name FROM information_schema.tables ORDER BY table_name;"
```

### Verify Table Counts

```bash
# Compare row counts
duckdb data/awsntp.duckdb "SELECT 'original' as db, COUNT(*) as total FROM (SELECT COUNT(*) FROM honeynet_ntp_srcips_asn_v6 UNION ALL SELECT COUNT(*) FROM awsntp_srcips_asn_v6);"
duckdb data/backup-20251223-153045.duckdb "SELECT 'backup' as db, COUNT(*) as total FROM (SELECT COUNT(*) FROM honeynet_ntp_srcips_asn_v6 UNION ALL SELECT COUNT(*) FROM awsntp_srcips_asn_v6);"
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "duckdb: command not found" | Install DuckDB CLI or use full path to duckdb binary |
| "database is locked" | Ensure no active DuckDB connections; use attach method to avoid locks |
| "out of disk space" | Check available space; use attachment method with cloud storage |
| "permission denied" | Verify file/directory permissions; add execute permission to script |
| Slow backup | For large dbs, use cp method (faster); consider scheduled off-peak backups |
