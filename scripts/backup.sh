#!/bin/bash
# CortexOS — Database backup script
# Usage: bash scripts/backup.sh
#        Cron: 0 2 * * * /opt/cortexos/scripts/backup.sh >> /var/log/cortexos-backup.log 2>&1
set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_DIR:-./backups}"
COMPOSE_FILE="${COMPOSE_FILE:--f docker-compose.yml}"
DB_USER="cortexos"
DB_NAME="cortexos"
KEEP_DAYS="${KEEP_DAYS:-30}"

# Ensure backup dir exists
mkdir -p "$BACKUP_DIR"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Starting backup..."

# Check postgres is running
if ! docker compose $COMPOSE_FILE ps postgres | grep -q "running"; then
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ERROR: postgres container is not running."
  exit 1
fi

# Dump PostgreSQL — compressed
BACKUP_FILE="$BACKUP_DIR/cortexos_${TIMESTAMP}.sql.gz"

docker compose $COMPOSE_FILE exec -T postgres \
  pg_dump -U "$DB_USER" "$DB_NAME" \
  | gzip > "$BACKUP_FILE"

# Verify backup was created and is non-empty
if [ ! -s "$BACKUP_FILE" ]; then
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ERROR: Backup file is empty. Something went wrong."
  rm -f "$BACKUP_FILE"
  exit 1
fi

BACKUP_SIZE=$(du -sh "$BACKUP_FILE" | cut -f1)
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Backup saved: $BACKUP_FILE ($BACKUP_SIZE)"

# Prune old backups
DELETED_COUNT=$(find "$BACKUP_DIR" -name "cortexos_*.sql.gz" -mtime +$KEEP_DAYS | wc -l)
find "$BACKUP_DIR" -name "cortexos_*.sql.gz" -mtime +$KEEP_DAYS -delete

if [ "$DELETED_COUNT" -gt 0 ]; then
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Pruned $DELETED_COUNT backup(s) older than $KEEP_DAYS days."
fi

# List current backups
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "cortexos_*.sql.gz" | wc -l)
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Total backups stored: $BACKUP_COUNT"
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Backup complete."
