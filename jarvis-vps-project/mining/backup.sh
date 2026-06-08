#!/bin/bash

cd ~/ollama-monero-biz
source .env

BACKUP_DIR="backups"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

mkdir -p "$BACKUP_DIR"

# Backup whitelist
if [ -f "whitelist.txt" ]; then
    BACKUP_NAME="$BACKUP_DIR/whitelist_$(date +%Y%m%d_%H%M%S).txt"
    cp whitelist.txt "$BACKUP_NAME"
    gzip -f "$BACKUP_NAME"
    echo "[$(date)] ✅ Backup created: $BACKUP_NAME.gz"
fi

# Backup config
cp .env "$BACKUP_DIR/env_$(date +%Y%m%d_%H%M%S).backup"

# Delete old backups
find "$BACKUP_DIR" -name "whitelist_*.txt.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "env_*.backup" -mtime +$RETENTION_DAYS -delete

echo "[$(date)] 🧹 Cleaned backups older than $RETENTION_DAYS days"
