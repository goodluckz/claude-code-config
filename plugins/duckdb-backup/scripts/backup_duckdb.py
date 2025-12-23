#!/usr/bin/env python3
"""
DuckDB Backup Script
Supports two backup approaches: ATTACH+COPY (native) and file-based (cp)
"""

import argparse
import subprocess
import shutil
import sys
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def backup_with_attach(db_path: str, backup_path: str) -> bool:
    """
    Backup using DuckDB's ATTACH + COPY FROM DATABASE approach.
    Best for: Remote backups, cloud storage, maintaining db-specific settings
    """
    logger.info(f"Starting ATTACH+COPY backup: {db_path} -> {backup_path}")

    try:
        abs_db = Path(db_path).resolve()
        abs_backup = Path(backup_path).resolve()

        # Create backup directory if needed
        abs_backup.parent.mkdir(parents=True, exist_ok=True)

        # SQL commands
        sql_commands = f"""
ATTACH '{abs_db}' AS source_db (READ_ONLY);
ATTACH '{abs_backup}' AS backup_db;
COPY FROM DATABASE source_db TO backup_db;
"""

        # Execute with duckdb CLI
        result = subprocess.run(
            ['duckdb'],
            input=sql_commands,
            text=True,
            capture_output=True,
            timeout=3600
        )

        if result.returncode != 0:
            logger.error(f"DuckDB backup failed: {result.stderr}")
            return False

        size_mb = abs_backup.stat().st_size / (1024 * 1024)
        logger.info(f"ATTACH+COPY backup completed: {size_mb:.2f} MB")
        return True

    except Exception as e:
        logger.error(f"ATTACH+COPY backup error: {e}")
        return False


def backup_with_cp(db_path: str, backup_path: str) -> bool:
    """
    Backup using file copy (cp/shutil).
    Best for: Local backups, quick snapshots, database migrations
    """
    logger.info(f"Starting file-based backup: {db_path} -> {backup_path}")

    try:
        source = Path(db_path)
        dest = Path(backup_path)

        if not source.exists():
            logger.error(f"Source database not found: {db_path}")
            return False

        # Create backup directory if needed
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Remove existing backup if present
        if dest.exists():
            logger.warning(f"Overwriting existing backup: {backup_path}")
            dest.unlink()

        # Copy file
        shutil.copy2(source, dest)

        size_mb = dest.stat().st_size / (1024 * 1024)
        logger.info(f"File-based backup completed: {size_mb:.2f} MB")
        return True

    except Exception as e:
        logger.error(f"File-based backup error: {e}")
        return False


def create_timestamped_backup(db_path: str, backup_dir: str, method: str = "cp") -> str:
    """Create a backup with timestamp in filename"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_filename = f"backup-{timestamp}.duckdb"
    backup_path = str(Path(backup_dir) / backup_filename)

    logger.info(f"Creating timestamped backup: {backup_filename}")

    if method == "cp":
        success = backup_with_cp(db_path, backup_path)
    elif method == "attach":
        success = backup_with_attach(db_path, backup_path)
    else:
        logger.error(f"Unknown backup method: {method}")
        return ""

    return backup_path if success else ""


def main():
    parser = argparse.ArgumentParser(
        description="DuckDB Backup Tool - Supports ATTACH+COPY and file-based backups"
    )
    parser.add_argument("--db", required=True, help="Path to source database")
    parser.add_argument("--backup", required=True, help="Path to backup location")
    parser.add_argument(
        "--method",
        choices=["cp", "attach"],
        default="cp",
        help="Backup method: cp (file copy) or attach (ATTACH+COPY). Default: cp"
    )
    parser.add_argument(
        "--timestamp",
        action="store_true",
        help="Add timestamp to backup filename (e.g., backup-20251223-153045.duckdb)"
    )

    args = parser.parse_args()

    if args.timestamp:
        backup_path = create_timestamped_backup(args.db, args.backup, args.method)
        if backup_path:
            print(backup_path)
            return 0
        else:
            return 1
    else:
        if args.method == "cp":
            success = backup_with_cp(args.db, args.backup)
        else:
            success = backup_with_attach(args.db, args.backup)

        return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
