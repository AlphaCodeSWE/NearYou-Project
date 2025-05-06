#!/usr/bin/env bash
set -e

# Avvia Metabase in background
java -jar /app/metabase.jar &

# Attendi che l'API sia pronta
until curl -sSf http://localhost:3000/api/health | grep '"status":"ok"' >/dev/null; do
  sleep 2
done

# Importa le Cards
for f in /appsota/definitions/cards/*.json; do
  curl -sX POST http://localhost:3000/api/card \
    -H "Content-Type: application/json" \
    -d @"$f"
done

# Importa la Dashboard
curl -sX POST http://localhost:3000/api/dashboard \
  -H "Content-Type: application/json" \
  -d @/appsota/definitions/dashboards/admin-overview.json


wait
