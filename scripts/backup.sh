#!/bin/bash
set -e

# Configuration
CONTAINER_NAME="claude-code-main-postgres-1"
DB_USER="postgres"
DB_NAME="buddy"
BACKUP_DIR="./backups"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/buddy_backup_${DATE}.sql"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

echo "Starting database backup from container: $CONTAINER_NAME..."

# Execute pg_dump inside the docker container
docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" "$DB_NAME" -F c > "$BACKUP_FILE"

echo "Backup completed successfully! Saved to: $BACKUP_FILE"
