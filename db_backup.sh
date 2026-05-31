#!/bin/bash

# Create db_dumps directory if it doesn't exist
mkdir -p db_dumps

# Define backup file name with timestamp
BACKUP_FILE="./db_dumps/pl_db_backup_$(date +%Y%m%d_%H%M%S).dump"

echo "Creating PostgreSQL backup from Docker container..."
docker compose exec -t db pg_dump -U pl_user -F c pl_db > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
  echo "Backup successfully created at $BACKUP_FILE"
  # Also copy it as the latest backup for easy restoring
  cp "$BACKUP_FILE" "./db_dumps/pl_db_backup_latest.dump"
  echo "Updated ./db_dumps/pl_db_backup_latest.dump"
else
  echo "Error: Backup failed!"
  exit 1
fi
