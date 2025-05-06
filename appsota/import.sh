#!/usr/bin/env bash
set -e

# 1) Migrazioni & init
superset db upgrade
export FLASK_APP=superset
superset fab create-admin \
  --username admin \
  --firstname Admin \
  --lastname User \
  --email admin@your.org \
  --password admin
superset init

# 2) Importa dashboard + charts già definiti
superset import-dashboards -p /app/definitions/admin_overview.json

# 3) Avvia il server
exec gunicorn \
  --bind 0.0.0.0:8088 \
  --workers 3 \
  --timeout 120 \
  "superset.app:create_app()"
