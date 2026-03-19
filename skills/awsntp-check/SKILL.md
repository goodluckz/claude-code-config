---
name: awsntp-check
description: Check AWS NTP honeypot data status across 7 regions - local pcap files, S3/Google Drive sync logs, tcpdump processes, and NTP service. Use when user wants to check AWS NTP data or sync health.
---

# AWS NTP Data Status Check

Check data and sync status for the 7-region AWS NTP honeypot infrastructure.

## Instructions

When invoked, run the checks the user requests. If no specific check is mentioned, run **all checks** and present a summary dashboard. All Ansible commands must be run from the `ansible/` directory under the aws_ntp_prod project.

**Working directory**: `cd /Users/zhaoliang/Projects/aws_ntp_prod/ansible`

## Regions

7 regions: `tokyo`, `virginia`, `california`, `frankfurt`, `mumbai`, `sydney`, `saopaulo`

## Available Checks

### 1. Local PCAP Files (default)

List recent pcap files on all instances:

```bash
ansible all -m shell -a "ls -lht /home/ubuntu/backup/ntp/ | head -5"
```

File naming: `AWSNTP_<region>_YYYYMMDD.pcap`
Active capture is today's file (still being written by tcpdump).

### 2. Tcpdump Processes

```bash
ansible all -m shell -a "ps aux | grep '[t]cpdump'"
```

Expected: One tcpdump process per instance capturing on ens6.

### 3. NTP Service

```bash
ansible all -m shell -a "systemctl is-active ntpsec; ntpq -p | head -5"
```

Service name is `ntpsec` (not ntpd).

### 4. S3 Sync Status

```bash
ansible all -m shell -a "tail -5 /home/ubuntu/s3_sync.log"
```

S3 sync runs daily at **00:10 UTC**. The script also auto-cleans local pcap files that have been verified in S3 (keeping last 4 days).

### 5. Google Drive Sync Status

Check sync logs:

```bash
ansible all -m shell -a "tail -5 /home/ubuntu/gdrive_sync.log"
```

GDrive sync runs daily at **00:20 UTC** via rclone. Excludes today's active capture.

Check what's on Google Drive (use **tokyo** instance as the rclone gateway):

```bash
ansible tokyo -m shell -a "rclone ls gdrive:awsntp-backup/ | sort -k2"
```

GDrive path: `gdrive:awsntp-backup/`

### 6. Disk Usage

```bash
ansible all -m shell -a "df -h / | tail -1"
```

Instances are t3.micro with limited EBS. Watch for disk pressure especially on high-traffic regions (Tokyo, Mumbai).

### 7. Crontab

```bash
ansible all -m shell -a "crontab -l"
```

Expected cron jobs (UTC):
- `@reboot` — configure_ipv6_route.sh
- `0 0 * * *` — start_tcpdump.sh (midnight, rotate capture)
- `10 0 * * *` — s3.sh (S3 sync + cleanup)
- `20 0 * * *` — gdrive.sh (Google Drive sync)

## Output Format

Present results as a concise status dashboard table. Flag anomalies:
- Missing pcap files for expected dates
- Tcpdump not running
- S3 or GDrive sync errors (look for "ERROR" in logs)
- GDrive missing files compared to local/S3
- Disk usage above 80%
- NTP service not active
- Large file size spikes (may indicate traffic anomaly or sync timeout risk)

### Traffic Baselines (post-NTP Pool registration, Feb 11+)

Normal daily pcap sizes vary significantly by region:
- **Tokyo**: 600MB–3.6GB (highest traffic)
- **Mumbai**: 900MB–1.8GB
- **Sao Paulo**: varies, can spike
- **Virginia/California/Sydney**: 50–100MB
- **Frankfurt**: 10–25MB

Files over ~3GB may cause GDrive sync timeouts. If a region's GDrive sync fails repeatedly, check if large files are the cause — consider `--drive-chunk-size 256M` or pre-compression.

## Server Details

- Ansible inventory: `ansible/inventory/hosts.yml`
- SSH user: `ubuntu`
- Backup path: `/home/ubuntu/backup/ntp/`
- S3 bucket: `s3://aws-ntp-pool-backup/ntp/`
- GDrive path: `gdrive:awsntp-backup/`
- Capture interface: `ens6` (honeypot NIC with EIP + IPv6)
