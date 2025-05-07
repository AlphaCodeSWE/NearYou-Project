#!/bin/bash
set -e

echo "--- Inizio script di inizializzazione dashboard Grafana ---"
echo "Working directory: $(pwd)"

# Funzione per attendere che un servizio sia pronto
wait_for_service() {
    local service=$1
    local url=$2
    local max_attempts=$3
    local attempt=0
    
    echo "Attendo che $service sia pronto..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" > /dev/null; then
            echo "$service è pronto!"
            return 0
        fi
        
        attempt=$((attempt+1))
        echo "Tentativo $attempt/$max_attempts: $service non è ancora pronto. Attendo 10 secondi..."
        sleep 10
    done
    
    echo "Impossibile connettersi a $service dopo $max_attempts tentativi."
    return 1
}

# Attendi che tutti i servizi necessari siano pronti
wait_for_service "ClickHouse" "http://clickhouse-server:8123/ping" 50 || exit 1
wait_for_service "Grafana" "http://grafana:3000/api/health" 50 || exit 1

# Verifica che lo script di assemblaggio esista
if [ ! -f "/workspace/grafana/provisioning/assemble_dashboard.py" ]; then
    echo "ERRORE: Script di assemblaggio dashboard non trovato!"
    exit 1
fi

# Esegui lo script Python per assemblare la dashboard
echo "Esecuzione dello script di assemblaggio dashboard..."
python3 /workspace/grafana/provisioning/assemble_dashboard.py

echo "Inizializzazione dashboard Grafana completata."