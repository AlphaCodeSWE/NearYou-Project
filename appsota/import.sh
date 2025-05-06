#!/usr/bin/env bash
set -e

# 1) Database migration e default roles
superset db upgrade
export FLASK_APP=superset

# 2) Crea admin user (admin/admin)
superset fab create-admin \
  --username admin \
  --firstname Admin \
  --lastname User \
  --email admin@your.org \
  --password admin

# 3) Init
superset init

# 4) Aggiungi i datasources
superset datasource add \
  --name UsersEvents \
  --database-uri clickhouse://default:pwe@123@l@@clickhouse:8123/nearyou \
  --table-name user_events

superset datasource add \
  --name Shops \
  --database-uri postgresql+psycopg2://nearuser:nearypass@postgres-postgis:5432/near_you_shops \
  --table-name shops

# 5) Importa dashboard + charts definita in JSON
superset import-dashboards -p /app/definitions/admin_overview.json

# 6) Avvia superset
exec gunicorn \
  --bind 0.0.0.0:8088 \
  --workers 3 \
  --timeout 120 \
  "superset.app:create_app()"
