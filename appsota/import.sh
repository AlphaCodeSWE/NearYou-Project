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

# 2) Crea un file temporaneo di definizione dei database (yaml)
cat <<EOF >/app/databases.yml
databases:
  - database_name: clickhouse_nearyou
    sqlalchemy_uri: clickhouse://default:pwe@123@l@@clickhouse-server:8123/nearyou
  - database_name: postgres_shops
    sqlalchemy_uri: postgresql+psycopg2://nearuser:nearypass@postgres-postgis:5432/near_you_shops
EOF

# 3) Importa i database
superset import-databases -p /app/databases.yml

# 4) Importa dashboard + charts già definiti
superset import-dashboards -p /app/definitions/admin_overview.json

# 5) Avvia il server
exec gunicorn \
  --bind 0.0.0.0:8088 \
  --workers 3 \
  --timeout 120 \
  "superset.app:create_app()"
