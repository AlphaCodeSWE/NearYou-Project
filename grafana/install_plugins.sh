#!/bin/bash
# Script per installare i plugin necessari per Grafana

# Controlla se stiamo eseguendo con privilegi di root
if [ "$EUID" -ne 0 ]; then
  echo "Questo script richiede privilegi di root. Eseguire con sudo."
  exit 1
fi

# Controlla se l'immagine Docker è in esecuzione
if ! docker ps | grep -q grafana; then
  echo "Il container Grafana non sembra in esecuzione."
  echo "Avviare prima il container e poi eseguire nuovamente questo script."
  exit 1
fi

echo "Installazione dei plugin per Grafana..."

# Installa plugin per ClickHouse
docker exec -it grafana grafana-cli plugins install grafana-clickhouse-datasource

# Installa plugin per la visualizzazione delle mappe
docker exec -it grafana grafana-cli plugins install grafana-worldmap-panel

# Installa altri plugin utili
docker exec -it grafana grafana-cli plugins install grafana-piechart-panel
docker exec -it grafana grafana-cli plugins install grafana-clock-panel
docker exec -it grafana grafana-cli plugins install volkovlabs-form-panel

# Riavvia il container di Grafana per applicare i plugin
echo "Riavvio di Grafana per applicare i plugin..."
docker restart grafana

echo "Installazione completata! Attendi il riavvio completo di Grafana..."
echo "La dashboard sarà disponibile all'indirizzo: http://localhost:3000"
echo "Credenziali predefinite: admin/admin"