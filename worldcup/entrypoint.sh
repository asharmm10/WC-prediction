#!/bin/bash
set -e

echo "=== Starting World Cup 2026 Prediction League ==="

# Wait for MySQL to be ready
echo "Waiting for MySQL to be ready..."
while ! mysqladmin ping -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" --silent 2>/dev/null; do
    echo "MySQL is unavailable - sleeping..."
    sleep 2
done
echo "MySQL is up!"

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Load fixtures only if DB is empty (no participants yet)
PARTICIPANT_COUNT=$(python -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from predictor.models import Participant
print(Participant.objects.count())
" 2>/dev/null || echo "0")

if [ "$PARTICIPANT_COUNT" = "0" ]; then
    echo "Loading initial fixtures..."
    python manage.py loaddata participants matches || echo "Warning: Could not load fixtures"
else
    echo "Database already has data (Participant count: $PARTICIPANT_COUNT), skipping fixtures."
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput 2>/dev/null || true

# Start gunicorn
echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 300
