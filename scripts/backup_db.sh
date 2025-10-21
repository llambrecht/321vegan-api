#!/bin/bash

# Load env variables from .env
set -a
source "$(dirname "$0")/../.env"
set +a

# Set output directory
BACKUP_DIR="$(dirname "$0")/../db_backups"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M")
BACKUP_FILE="$BACKUP_DIR/${POSTGRES_DB}_backup_$TIMESTAMP.sql"

# Run pg_dump
docker exec -t "$POSTGRES_HOST" pg_dump \
  -U "$POSTGRES_USER" "$POSTGRES_DB" > "$BACKUP_FILE"

# Compress the backup file
gzip "$BACKUP_FILE"

# Only keep last 7 backups
ls -1t "$BACKUP_DIR"/*.gz | tail -n +8 | xargs -r rm --

curl -fsS -m 10 https://hc-ping.com/dc26fb69-8001-4cc5-ad4b-e3804ec787b4 > /dev/null

echo "✅ Backup saved to: ${BACKUP_FILE}.gz"
