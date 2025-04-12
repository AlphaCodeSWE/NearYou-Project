#!/bin/bash
set -e

echo "--- Inizio script di inizializzazione per PostGIS ---"
echo "Working directory: $(pwd)"
echo "Elenco dei file nella directory:"
ls -l

echo "Attesa che Postgres con PostGIS sia pronto..."

until docker exec -i postgres-postgis psql -U nearuser -d near_you_shops -c "SELECT 1" >/dev/null 2>&1; do
    echo "Postgres non è ancora pronto, attendo 5 secondi..."
    sleep 5
done

echo "Postgres è pronto. Eseguo le query di inizializzazione per creare la tabella shops..."

docker exec -i postgres-postgis psql -U nearuser -d near_you_shops <<'EOF'
-- Creazione della tabella shops se non esiste
CREATE TABLE IF NOT EXISTS shops (
    shop_id       SERIAL PRIMARY KEY,
    shop_name     VARCHAR(255),
    address       TEXT,
    category      VARCHAR(100),
    geom          GEOMETRY(Point, 4326),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
EOF

echo "Inizializzazione di PostGIS completata."
