#!/usr/bin/env bash
set -euo pipefail

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.production}"

python backend/manage.py migrate --noinput
python backend/manage.py collectstatic --noinput

if [ "${DEMO_MODE:-false}" = "true" ]; then
  python backend/manage.py seed_demo
fi

exec gunicorn --chdir backend config.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --timeout "${GUNICORN_TIMEOUT:-60}" \
  --access-logfile - \
  --error-logfile -
