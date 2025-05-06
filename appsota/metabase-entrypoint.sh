#!/usr/bin/env bash
set -e
java -jar /app/metabase.jar &

until curl -sSf http://localhost:3000/api/health | grep '"status":"ok"' >/dev/null; do
  sleep 2
done

for f in /appsota/definitions/cards/*.json; do
  curl -sX POST http://localhost:3000/api/card \
    -H "Content-Type: application/json" \
    -d @"$f"
done

curl -sX POST http://localhost:3000/api/dashboard \
  -H "Content-Type: application/json" \
  -d @/appsota/definitions/dashboards/admin-overview.json

wait
