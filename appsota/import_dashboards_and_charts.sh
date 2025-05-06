#!/usr/bin/env bash
set -e

# Attendi che Superset sia in ascolto
until curl -sSf http://localhost:8088/health | grep '"database"' >/dev/null; do
  sleep 2
done

# Importa il JSON della dashboard
superset import-dashboards -p /app/definitions/admin_overview.json
