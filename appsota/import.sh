#!/usr/bin/env bash
set -e

# 1) Migration e default roles
superset db upgrade
export FLASK_APP=superset

# 2) Crea admin user
superset fab create-admin \
  --username admin \
  --firstname Admin \
  --lastname User \
  --email admin@your.org \
  --password admin

# 3) Init
superset init

# 4) Aggiungi i datasources
# URIs con password url‑encoded: @ → %40
superset datasource add \
  --name UsersEvents \
  --database-uri "clickhouse://default:pwe%40123%40l%40@clickhouse:8123/nearyou" \
  --table-name user_events

superset datasource add \
  --name Shops \
  --database-uri "postgresql+psycopg2://nearuser:nearypass@postgres-postgis:5432/near_you_shops" \
  --table-name shops

# 5) Importa dashboard + charts
/app/import_dashboards_and_charts.sh

# 6) Avvia Superset
exec gunicorn \
  --bind 0.0.0.0:8088 \
  --workers 3 \
  --timeout 120 \
  "superset.app:create_app()"
