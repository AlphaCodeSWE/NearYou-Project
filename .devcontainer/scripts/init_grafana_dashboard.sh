#!/bin/bash
set -e

echo "--- Inizio script di inizializzazione dashboard Grafana ---"
echo "Working directory: $(pwd)"

echo "Attesa che Grafana sia pronto..."
COUNTER=0
MAX_RETRIES=30

while true; do
    if curl -s http://grafana:3000/api/health > /dev/null; then
        echo "Grafana è pronto. Procedo con la creazione della dashboard."
        break
    fi
    
    echo "Tentativo $(($COUNTER+1)): Grafana non è ancora pronto. Attendo 5 secondi..."
    sleep 5
    COUNTER=$(($COUNTER+1))
    
    if [ $COUNTER -ge $MAX_RETRIES ]; then
        echo "Limite massimo di tentativi raggiunto. Uscita."
        exit 1
    fi
done

# Esegui lo script Python per assemblare la dashboard
echo "Esecuzione dello script di assemblaggio dashboard..."
python3 /workspace/grafana/provisioning/assemble_dashboard.py

echo "Inizializzazione dashboard Grafana completata."