#!/usr/bin/env bash
set -e

export MB_HOST="http://localhost:3000"
export MB_USER="${MB_ADMIN_EMAIL:-admin@admin.com}"
export MB_PASS="${MB_ADMIN_PASSWORD:-admin}"

# 1) Avvia Metabase in background
java -jar /app/metabase.jar &

# 2) Attendi che l’API sia pronta
until curl -sSf "$MB_HOST/api/health" | grep '"status":"ok"' >/dev/null; do
  sleep 2
done

# 3) Esegui setup 
curl -sSf -X POST "$MB_HOST/api/setup" \
  -H "Content-Type: application/json" \
  -d "{
    \"user\": {\"email\": \"$MB_USER\", \"password\": \"$MB_PASS\"},
    \"prefs\": {\"site_name\": \"Admin Overview\", \"allow_tracking\": false}
  }" \
  || echo "▶︎ Setup già eseguito, proseguo..."

# 4) Fai login e prendi il token di sessione
LOGIN_RESP=$(curl -sSf -X POST "$MB_HOST/api/session" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$MB_USER\",\"password\":\"$MB_PASS\"}")

SESSION_TOKEN=$(echo "$LOGIN_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

if [ -z "$SESSION_TOKEN" ]; then
  echo "❌ Impossibile ottenere session token!"
  exit 1
fi

# 5) Importa tutte le card
for f in /usr/local/appsota/definitions/cards/*.json; do
  curl -sSf -X POST "$MB_HOST/api/card" \
    -H "Content-Type: application/json" \
    -H "X-Metabase-Session: $SESSION_TOKEN" \
    -d @"$f"
done

# 6) Importa la dashboard admin-overview
curl -sSf -X POST "$MB_HOST/api/dashboard" \
  -H "Content-Type: application/json" \
  -H "X-Metabase-Session: $SESSION_TOKEN" \
  -d @/usr/local/appsota/definitions/dashboards/admin-overview.json

# 7) Mantieni il processo in foreground
wait
