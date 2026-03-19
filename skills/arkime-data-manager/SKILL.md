---
name: arkime-data-manager
description: Manage Arkime data (wipe database, import PCAPs)
---

# Arkime Data Manager

This skill provides commands and workflows for managing Arkime data: wiping the database and importing PCAP files.

## Environments

| Property | ENV-41 (Local) | ENV-42 (Remote) |
|----------|---------------|-----------------|
| **Host** | localhost | dns-analy4 |
| **Container** | `env-41_arkime` | `env-42_arkime` |
| **Arkime Port** | 8041 | 8042 |
| **OpenSearch** | 4-node (`env-41_os01:9200`) | 3-node (`env-42_os01:9200`) |
| **Project Dir** | `/Users/zhaoliang/LocalRepos/envs/ENV-41/` | `/export0/Work/zhaoliang/ENV-42/` (remote) |
| **Local Repo** | same as above | `/Users/zhaoliang/LocalRepos/envs/ENV-42/` |
| **PCAP Dir (host)** | `./env-41_pcap_dir/` | `/export0/Work/zhaoliang/env-42_pcap_dir/` |
| **PCAP Dir (container)** | `/data/pcap` | `/data/pcap` |
| **Config/Logs mount** | `./env-41_arkime_config` → `/data/config`, `./env-41_arkime_logs` → `/data/logs` | same dirs |
| **Credentials** | admin/admin (Digest Auth) | admin/admin (Digest Auth) |

## Prerequisites

- **Docker**: ENV-41 runs locally, ENV-42 runs on dns-analy4
- **SSH**: `ssh dns-analy4` for remote ENV-42 operations
- **Arkime Container**: `env-41_arkime` (local) or `env-42_arkime` (remote)

## Database Operations

### Wipe Database (Clear All Data)

**⚠️ WARNING**: This operation **permanently deletes all session data** from OpenSearch. PCAP files on disk are NOT deleted.

#### Prerequisites for Wipe

1. **Stop all captures and viewers** (recommended but not required for dev environments)
2. **Backup data first** (optional but recommended):
   ```bash
   docker exec env-41_arkime /opt/arkime/db/db.pl http://env-41_os01:9200 backup
   ```

#### Using db.pl wipe

**Location**: `/opt/arkime/db/db.pl` (inside Arkime container)

**Syntax**:
```bash
echo "WIPE" | docker exec -i env-41_arkime /opt/arkime/db/db.pl http://env-41_os01:9200 wipe
```

**Important Notes**:
- Must use `echo "WIPE" |` to provide confirmation input
- Must use `-i` flag with `docker exec` to enable stdin
- Use `env-41_os01:9200` (container network name) NOT `localhost:9200` when running from inside container
- Operation erases all indices and recreates them (returns to initial state)
- Does NOT delete PCAP files from disk
- Does NOT delete user accounts/settings

**Example Output**:
```
It is STRONGLY recommended that you stop ALL Arkime captures and viewers before proceeding.
Use 'db.pl http://env-41_os01:9200 backup' to backup db first.

There are 4 OpenSearch/Elasticsearch data nodes, if you expect more please fix first before proceeding.

This will delete ALL session data in OpenSearch/Elasticsearch! (It does not delete the pcap files on disk or user info.)

Type "WIPE" to continue - do you want to wipe everything??
Erasing
Creating
Finished
```

#### Verify Data Cleared

Check session count after wipe:
```bash
curl -s --digest -u admin:admin 'http://localhost:8041/api/sessions?length=0' | jq '{recordsTotal, recordsFiltered}'
```

Expected output:
```json
{
  "recordsTotal": 0,
  "recordsFiltered": 0
}
```

#### Check OpenSearch Cluster Health

Before running wipe, verify cluster is healthy:
```bash
curl -s -u admin:admin http://localhost:9200/_cluster/health | jq '.status'
```

Expected: `"green"` or `"yellow"` (avoid wiping if `"red"`)

## PCAP Import Operations

### Import PCAPs with Automatic Tagging

**Script**: `/Users/zhaoliang/LocalRepos/envs/ENV-41/scripts/import-env41-samples.sh`

This script imports PCAPs from organized subdirectories and automatically applies tags based on directory names.

#### Directory Naming Convention

Format: `{dataset}-{ip-version}-{protocol}-{region}`

**Examples**:
- `aws-v4-scan-tokyo/` → Tags: `dataset:aws,ip-version:v4,protocol:scan,region:tokyo`
- `aws-v6-ntp-california/` → Tags: `dataset:aws,ip-version:v6,protocol:ntp,region:california`
- `honeynet-v6-ntp-tokyo/` → Tags: `dataset:honeynet,ip-version:v6,protocol:ntp,region:tokyo`

**Tag Components**:
- **dataset**: `aws`, `honeynet`
- **ip-version**: `v4`, `v6` (also accepts `ipv4`, `ipv6`)
- **protocol**: `ntp`, `scan`
- **region**: `tokyo`, `sydney`, `virginia`, `california`, `mumbai`, `saopaulo`, `frankfurt`

#### Basic Usage

```bash
# Import all PCAPs from all subdirectories
cd /Users/zhaoliang/LocalRepos/envs/ENV-41
bash scripts/import-env41-samples.sh
```

#### Filtered Import

```bash
# Import only AWS NTP data
bash scripts/import-env41-samples.sh -d aws -p ntp

# Import only Tokyo region data
bash scripts/import-env41-samples.sh -r tokyo

# Import only IPv6 data
bash scripts/import-env41-samples.sh -i v6

# Import specific combination: AWS IPv6 NTP from California
bash scripts/import-env41-samples.sh -d aws -i v6 -p ntp -r california
```

#### Dry Run (Preview Without Importing)

```bash
bash scripts/import-env41-samples.sh -n
```

This shows what would be imported without actually processing files.

#### Script Options

```
-d, --dataset       Dataset filter: aws, honeynet, or all (default: all)
-r, --region        Region filter: tokyo, sydney, virginia, california, mumbai, saopaulo, frankfurt, or all (default: all)
-p, --protocol      Protocol filter: ntp, scan, or all (default: all)
-i, --ip-version    IP version filter: v4, v6, or all (default: all)
-n, --dry-run       Show what would be imported without actually importing
-h, --help          Show help message
```

#### How Import Works

1. **Scans** PCAP directory for subdirectories matching naming pattern
2. **Parses** directory names to extract tag metadata
3. **Filters** directories based on command-line options
4. **Counts** PCAP files in each directory
5. **Imports** using batch mode: `docker exec env-41_arkime /opt/arkime/bin/capture --pcapdir /data/pcap/subdir --recursive -t "tags"`
6. **Reports** success/failure for each directory

#### Verify Import Success

**Check total sessions**:
```bash
curl -s --digest -u admin:admin 'http://localhost:8041/api/sessions?length=0' | jq '.recordsTotal'
```

**Check sessions by tag**:
```bash
# Check specific dataset
curl -s --digest -u admin:admin \
  'http://localhost:8041/api/sessions?expression=tags%20%3D%3D%20dataset%3Aaws&length=0' \
  | jq '.recordsTotal'

# Check specific experiment
curl -s --digest -u admin:admin \
  'http://localhost:8041/api/sessions?expression=tags%20%3D%3D%20region%3Atokyo&length=0' \
  | jq '.recordsTotal'
```

## Complete Workflow: Wipe and Reimport

**Use Case**: Reset ENV-41 to clean state with fresh data import

### Step 1: Start ENV-41 Cluster

```bash
cd /Users/zhaoliang/LocalRepos/envs/ENV-41
docker-compose up -d
```

Wait for OpenSearch cluster to become healthy (~30-60 seconds):
```bash
# Check cluster health (wait for "green")
curl -s -u admin:admin http://localhost:9200/_cluster/health | jq '.status'
```

### Step 2: Wipe Existing Data

```bash
echo "WIPE" | docker exec -i env-41_arkime /opt/arkime/db/db.pl http://env-41_os01:9200 wipe
```

Expected output ends with:
```
Erasing
Creating
Finished
```

### Step 3: Verify Data Cleared

```bash
curl -s --digest -u admin:admin 'http://localhost:8041/api/sessions?length=0' | jq '.recordsTotal'
```

Expected: `0`

### Step 4: Import Fresh Data

```bash
bash scripts/import-env41-samples.sh
```

Or with filters (e.g., only AWS data):
```bash
bash scripts/import-env41-samples.sh -d aws
```

### Step 5: Verify Import

```bash
# Check total sessions imported
curl -s --digest -u admin:admin 'http://localhost:8041/api/sessions?length=0' | jq '.recordsTotal'

# Should show a number > 0 (e.g., 4278218 for full ENV-41 dataset)
```

## Troubleshooting

### Wipe Command Fails with "Couldn't GET http://localhost:9200"

**Error**: `Couldn't GET http://localhost:9200/_cluster/health the http status code is 500`

**Cause**: OpenSearch cluster not ready or using wrong endpoint

**Solutions**:
1. **Wait for cluster to become healthy**:
   ```bash
   curl -s -u admin:admin http://localhost:9200/_cluster/health | jq '.status'
   ```
   Wait until status is `"green"` (not `"red"`)

2. **Use correct endpoint from container**:
   - ✅ Correct: `http://env-41_os01:9200` (from inside arkime container)
   - ❌ Wrong: `http://localhost:9200` (not reachable from inside container)

### Import Script Hangs or Shows Empty Tags

**Symptom**: Tags show as `dataset:,ip-version:,protocol:,region:` (empty values)

**Cause**: Directory name doesn't match expected pattern

**Expected Pattern**: `{dataset}-{ip-version}-{protocol}-{region}`
- Example: `aws-v6-ntp-tokyo`, `honeynet-v4-scan-sydney`

**Solutions**:
1. **Rename directories** to match pattern
2. **Skip non-matching directories** (script will import them with empty tags but continue)
3. Directories like `aws/`, `honeynet/`, `aws-IPv4/` don't match pattern but will still be imported

### Docker Container Not Running

**Error**: `Error response from daemon: Container env-41_arkime is not running`

**Solution**:
```bash
cd /Users/zhaoliang/LocalRepos/envs/ENV-41
docker-compose up -d
```

### Permission Denied Accessing PCAP Files

**Cause**: PCAP directory not properly mounted in container

**Solution**: Check docker-compose.yml volume mount:
```yaml
volumes:
  - ./env-41_pcap_dir:/data/pcap
```

Ensure PCAP files are in `/Users/zhaoliang/LocalRepos/envs/ENV-41/env-41_pcap_dir/`

## Environment Configuration

**ENV-41 Directory**: `/Users/zhaoliang/LocalRepos/envs/ENV-41/`

**Key Files**:
- `docker-compose.yml`: Service configuration
- `.env`: Environment variables (ports, node names, paths)
- `scripts/import-env41-samples.sh`: PCAP import script
- `env-41_pcap_dir/`: PCAP files organized by subdirectory

**Services**:
- **Arkime**: `env-41_arkime` (port 8041)
- **OpenSearch Nodes**: `env-41_os01`, `env-41_os02`, `env-41_os03`, `env-41_os04`
  - OS01 exposed on localhost:9200 (REST API), localhost:9600 (Performance Analyzer)

**Credentials**:
- **Arkime Web UI**: admin/admin (HTTP Digest Auth)
- **OpenSearch**: admin/admin (when security enabled)

## ENV-42 Remote PCAP Import (Background)

ENV-42 runs on `dns-analy4`. All commands are executed via SSH. The import runs in the background inside the container using `docker exec -d`.

### PCAP Subdirectories

| Directory | Content | Files |
|-----------|---------|-------|
| `darknet-nii-202511` | Darknet traffic | ~30 |
| `honeynet-v6-ntp-tokyo` | Honeynet NTP | ~540 |
| `honeynet-v6-scan-tokyo` | Honeynet scan | ~1004 |

### Import Scripts

**1. Batch import with progress tracking** (`scripts/import-with-progress.sh`):
- Processes each subdirectory sequentially with timing
- Uses `-q` to suppress verbose capture output
- Uses `--skip` to avoid re-importing already imported files
- Logs to `/data/logs/import_progress.log`

**2. Tagged import** (`scripts/import-env42-pcaps.sh`):
- Auto-tags based on directory naming convention `{dataset}-{ipversion}-{protocol}-{region}`
- Supports filters: `-d dataset`, `-r region`, `-p protocol`, `-i ip-version`
- Supports dry run: `-n`

### Start Background Import

```bash
# Copy script into container (scripts dir is NOT volume-mounted)
ssh dns-analy4 "docker cp /export0/Work/zhaoliang/ENV-42/scripts/import-with-progress.sh env-42_arkime:/tmp/import-with-progress.sh"

# Start in detached mode (survives SSH disconnect)
ssh dns-analy4 "docker exec -d env-42_arkime bash /tmp/import-with-progress.sh"
```

### Monitor Progress

```bash
# View progress log
ssh dns-analy4 "docker exec env-42_arkime tail -10 /data/logs/import_progress.log"

# Check total imported file count
ssh dns-analy4 'curl -s --digest -u admin:admin "http://localhost:8042/api/files?length=1" | python3 -c "import json,sys; print(json.load(sys.stdin)[\"recordsTotal\"])"'

# Check if capture process is still running
ssh dns-analy4 "docker exec env-42_arkime pgrep -f 'capture.*pcapdir'"

# Check total session count
ssh dns-analy4 'curl -s --digest -u admin:admin "http://localhost:8042/api/sessions?length=0" | python3 -c "import json,sys; print(json.load(sys.stdin)[\"recordsTotal\"])"'
```

### Wipe ENV-42 Database

```bash
ssh dns-analy4 'echo "WIPE" | docker exec -i env-42_arkime /opt/arkime/db/db.pl http://env-42_os01:9200 wipe'
```

### Volume Mounts (ENV-42)

The `scripts/` directory is **NOT** mounted into the container. Only these paths are mounted:
- `./env-41_arkime_config` → `/data/config`
- `./env-41_arkime_logs` → `/data/logs` (root-owned)
- `$PCAP_DIR` (`/export0/Work/zhaoliang/env-42_pcap_dir`) → `/data/pcap`
- `./package` → `/data/package`

To get scripts into the container, use `docker cp`.

### Sync Remote Changes to Local

```bash
rsync -avz dns-analy4:/export0/Work/zhaoliang/ENV-42/scripts/ \
  /Users/zhaoliang/LocalRepos/envs/ENV-42/scripts/
```

## References

- Arkime Documentation: https://arkime.com/
- Arkime db.pl: `/opt/arkime/db/db.pl --help`
- ENV-41 Configuration: `/Users/zhaoliang/LocalRepos/envs/ENV-41/`
- ENV-42 Configuration: `/Users/zhaoliang/LocalRepos/envs/ENV-42/` (local) / `/export0/Work/zhaoliang/ENV-42/` (remote)
- Import Script (ENV-41): `/Users/zhaoliang/LocalRepos/envs/ENV-41/scripts/import-env41-samples.sh --help`
- Import Script (ENV-42): `/Users/zhaoliang/LocalRepos/envs/ENV-42/scripts/import-with-progress.sh`
