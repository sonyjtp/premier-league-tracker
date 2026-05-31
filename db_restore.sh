#!/bin/bash

BACKUP_FILE="./db_dumps/pl_db_backup_latest.dump"

if [ ! -f "$BACKUP_FILE" ]; then
  echo "Error: Backup file $BACKUP_FILE not found!"
  exit 1
fi

echo "Restoring PostgreSQL database from $BACKUP_FILE..."
# Drop and recreate schema inside container, or use pg_restore flags
docker compose exec -T db pg_restore -U pl_user -d pl_db -c --no-owner --clean < "$BACKUP_FILE"

if [ $? -eq 0 ]; then
  echo "Database successfully restored from $BACKUP_FILE!"
else
  echo "Error: Restore failed!"
  exit 1
fi
