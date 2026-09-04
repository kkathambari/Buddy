#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "Usage: ./restore.sh <backup_file.sql>"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: File $BACKUP_FILE does not exist."
    exit 1
fi

CONTAINER_NAME="claude-code-main-postgres-1"
DB_USER="postgres"
DB_NAME="buddy"

echo "WARNING: This will overwrite the current database in $CONTAINER_NAME."
read -p "Are you sure you want to proceed? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Restore aborted."
    exit 1
fi

echo "Dropping connections and recreating database..."
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -c "
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '$DB_NAME'
  AND pid <> pg_backend_pid();"
docker exec "$CONTAINER_NAME" dropdb -U "$DB_USER" "$DB_NAME" || true
docker exec "$CONTAINER_NAME" createdb -U "$DB_USER" "$DB_NAME"

echo "Restoring database from $BACKUP_FILE..."
cat "$BACKUP_FILE" | docker exec -i "$CONTAINER_NAME" pg_restore -U "$DB_USER" -d "$DB_NAME" -1

echo "Restore completed successfully!"
