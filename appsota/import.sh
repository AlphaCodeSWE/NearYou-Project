#!/usr/bin/env bash
set -e

# 1) Migrazioni & init
superset db upgrade
export FLASK_APP=superset

# 2) Crea admin user (solo se non esiste già)
superset fab create-admin \
  --username admin \
  --firstname Admin \
  --lastname User \
  --email admin@your.org \
  --password admin || true

superset init

# 3) Crea un file temporaneo di definizione dei database (yaml)
cat <<EOF >/app/definitions/databases.yml
databases:
  - database_name: clickhouse_nearyou
    sqlalchemy_uri: clickhouse://default:pwe@123@l@@clickhouse-server:8123/nearyou
  - database_name: postgres_shops
    sqlalchemy_uri: postgresql+psycopg2://nearuser:nearypass@postgres-postgis:5432/near_you_shops
EOF

# 4) Importa i database
superset import-databases \
  -p /app/definitions/databases.yml

# 5) Importa dashboard + charts già definiti
superset import-dashboards \
  --username admin \
  --password admin \
  -p /app/definitions/admin_overview.json

# 6) Avvia il server
exec gunicorn \
  --bind 0.0.0.0:8088 \
  --workers 3 \
  --timeout 120 \
  "superset.app:create_app()"
