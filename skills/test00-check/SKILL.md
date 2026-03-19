---
name: test00-check
description: Check test00 honeynet production server status - pcap files, tcpdump processes, containers, and Google Drive sync. Use when user wants to check test00 data or server health.
---

# Test00 Honeynet Status Check

Check the status of the test00 IPv6 honeynet production server, including pcap captures, Docker containers, and Google Drive backups.

## Instructions

When invoked, run the checks the user requests. If no specific check is mentioned, run all checks and present a summary dashboard.

## Available Checks

### 1. PCAP Files (default)

List pcap files in both capture directories:

```bash
ssh test00 "echo '=== NTP Traffic (port 123) ==='; ls -lh ~/backup/honeynet-v6-ntp-tokyo/ 2>&1; echo; echo '=== Scan Traffic (non-NTP) ==='; ls -lh ~/backup/honeynet-v6-scan-tokyo/ 2>&1"
```

Directories:
- `~/backup/honeynet-v6-ntp-tokyo/` — NTP (UDP port 123) traffic captures
- `~/backup/honeynet-v6-scan-tokyo/` — All other IPv6 traffic (TCP, ICMPv6, non-NTP UDP)

File naming: `honeynet-ipv6-{ntp,scan}-tokyo_YYYYMMDD.pcap` (gzipped after rotation)

### 2. Tcpdump Processes

Check if tcpdump capture processes are running:

```bash
ssh test00 "ps aux | grep '[t]cpdump'"
```

Expected: Two tcpdump processes per day — one for NTP, one for scan traffic. Old day's processes may linger until rotation completes.

### 3. Docker Containers

Check all honeynet containers are running:

```bash
ssh test00 "docker ps --format 'table {{.Names}}\t{{.Status}}'"
```

Expected containers: `darknet`, `honeynet`, `sink`, `ntp-dark`, `ntp-honey`, `db`

### 4. Google Drive Sync Status

Check sync logs:

```bash
ssh test00 "tail -20 ~/logs/pcap-sync-gdrive.log 2>&1"
```

Note: The sync script (`pcap-sync-gdrive.sh`) may not be configured. Check logs for errors.

## Output Format

Present results as a concise status dashboard. Flag any anomalies:
- Missing pcap files for expected dates
- Tcpdump not running
- Containers down
- Sync failures or missing Google Drive files
- Unexpected gaps in data

## Server Details

- Host: `test00` (SSH config alias)
- Project path: `~/TC-351_production_env/`
- Backup path: `~/backup/`
- Target network: `2001:200:0:c000::/56`
- Interface: `enp0s3`
