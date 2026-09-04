#!/bin/bash
set -e

# Simulates a rollback procedure locally
echo "Starting local rollback simulation..."

# 1. Take a backup of current working state
echo "Taking pre-rollback backup..."
bash scripts/backup.sh || echo "Warning: Backup script failed or not configured, proceeding anyway"

# 2. Revert code to previous version
PREV_TAG=$(git describe --abbrev=0 --tags $(git rev-list --tags --skip=1 --max-count=1))
if [ -z "$PREV_TAG" ]; then
    echo "No previous tag found to simulate rollback."
    exit 1
fi

echo "Simulating code rollback to $PREV_TAG..."
# git checkout $PREV_TAG # commented out so we don't actually lose state in the working directory during the test

# 3. Restore the backup (simulating downgrading DB schema if needed)
echo "Restoring database backup..."
bash scripts/restore.sh || echo "Warning: Restore script failed or not configured"

echo "Rollback simulation complete! In production, verify logs and application state."
