#!/bin/bash
set -e

echo "=== DMDT Backend Entrypoint ==="

cd /app/database
echo "Running database migrations..."
alembic upgrade head

echo "Checking if seed data needed..."
LINE_COUNT=$(python -c "
from dmdt_db import get_session_factory, Line
sf = get_session_factory()
with sf() as s:
    print(s.query(Line).count())
")

if [ "$LINE_COUNT" = "0" ]; then
    echo "No existing data found — seeding network..."
    python /app/database/seed/seed_network.py
else
    echo "Database already has $LINE_COUNT lines — skipping seed."
fi

cd /app
echo "Starting backend server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
